#!/usr/bin/env python3
"""
compile_check.py — Compilador e verificador de fechamento de lote e capítulos.

Responsabilidades:
1. Localizar o binário `tectonic` (em ./bin/ ou no PATH) ou fazer fallback para `latexmk`/`pdflatex`.
2. Compilar `main.tex` (ou versão parcial via `--only capXX`) gerando o PDF em `build/`.
3. Em caso de falha (exit code != 0), exibir as últimas 40 linhas do log de erro.
4. Renderização de páginas sob demanda via `--render-last N` (padrão: 0, desativado).
5. Despacho semântico para a raiz apenas quando compilando o livro completo com sucesso.
"""

import argparse
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
BIN_DIR = WORKSPACE_ROOT / "bin"


def resolve_compiler(main_tex: Path, outdir: Path) -> tuple[str, list[str]]:
    """Localiza tectonic (local ou PATH) ou retorna comando fallback com latexmk."""
    exe_name = "tectonic.exe" if platform.system().lower() == "windows" else "tectonic"
    local_tectonic = BIN_DIR / exe_name

    tectonic_bin: str | None = None
    if local_tectonic.is_file():
        tectonic_bin = str(local_tectonic)
    else:
        tectonic_bin = shutil.which("tectonic")

    if tectonic_bin:
        cmd = [
            tectonic_bin,
            "--outdir",
            str(outdir),
            "--keep-logs",
            str(main_tex),
        ]
        return "tectonic", cmd

    latexmk_bin = shutil.which("latexmk")
    if latexmk_bin:
        cmd = [
            latexmk_bin,
            "-pdf",
            "-interaction=nonstopmode",
            f"-output-directory={outdir.as_posix()}",
            str(main_tex),
        ]
        return "latexmk", cmd

    pdflatex_bin = shutil.which("pdflatex")
    if pdflatex_bin:
        cmd = [
            pdflatex_bin,
            "-interaction=nonstopmode",
            f"-output-directory={outdir.as_posix()}",
            str(main_tex),
        ]
        return "pdflatex", cmd

    raise RuntimeError(
        "Nenhum compilador LaTeX encontrado (tectonic, latexmk ou pdflatex). "
        "Execute `python scripts/setup_env.py` primeiro."
    )


def render_last_compiled_pages(
    pdf_path: Path, preview_dir: Path, count: int, dpi: int = 160
) -> list[Path]:
    """Renderiza as últimas `count` páginas do PDF compilado em PNG."""
    if count <= 0:
        return []

    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
    except ImportError:
        print(
            "[AVISO] PyMuPDF ausente; pulando renderização de preview.",
            file=sys.stderr,
        )
        return []

    preview_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []

    with fitz.open(pdf_path) as doc:
        total = len(doc)
        if total == 0:
            return []
        start_page = max(1, total - count + 1)
        for page_num in range(start_page, total + 1):
            page = doc.load_page(page_num - 1)
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            out_png = preview_dir / f"comp_page_{page_num:03d}.png"
            pix.save(str(out_png))
            rendered.append(out_png)

    return rendered


def extract_error_tail(stdout_text: str, stderr_text: str, log_file: Path, max_lines: int = 40) -> str:
    """Extrai as últimas `max_lines` linhas combinando saída do processo e arquivo .log."""
    combined_lines: list[str] = []
    for stream_text in (stdout_text, stderr_text):
        if stream_text:
            combined_lines.extend(stream_text.splitlines())

    if log_file.is_file():
        try:
            log_lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
            combined_lines.extend(["--- Trecho final do arquivo .log ---", *log_lines[-max_lines:]])
        except Exception:
            pass

    tail = combined_lines[-max_lines:] if len(combined_lines) > max_lines else combined_lines
    return "\n".join(tail)


def dispatch_to_root(compiled_pdf: Path) -> Path | None:
    """Copia o PDF compilado para a raiz com o nome semântico da obra."""
    import json

    roadmap_path = WORKSPACE_ROOT / "roadmap.json"
    title = "Livro"
    source_pdf = ""
    author = ""

    if roadmap_path.is_file():
        try:
            with open(roadmap_path, encoding="utf-8") as f:
                data = json.load(f)
                title = data.get("book_title", title)
                source_pdf = data.get("source_pdf", "")
        except Exception:
            pass

    context_path = WORKSPACE_ROOT / "CONTEXT.md"
    if context_path.is_file():
        try:
            for line in context_path.read_text(encoding="utf-8", errors="replace").splitlines():
                if "Autores:" in line or "Autor:" in line:
                    author = line.split(":", 1)[1].strip()
                    author = re.sub(r"\(.*?\)", "", author).strip()
                    break
        except Exception:
            pass

    def sanitize(s: str) -> str:
        s = re.sub(r'[\\/*?:"<>|]', "", s)
        return s.strip().replace(" ", "_")

    s_title = sanitize(title)
    s_author = sanitize(author) if author else ""
    target_name = f"{s_title}_{s_author}.pdf" if s_author else f"{s_title}.pdf"
    target_path = WORKSPACE_ROOT / target_name

    source_stem = Path(source_pdf).stem.lower() if source_pdf else ""
    if target_path.name.lower() == source_pdf.lower() or (source_stem and source_stem in target_path.stem.lower()):
        target_name = f"{target_path.stem}_Recuperado.pdf"
        target_path = WORKSPACE_ROOT / target_name

    try:
        shutil.copy2(compiled_pdf, target_path)
        print(f"[OK] Despacho semântico concluído: {target_path.name}")
        return target_path
    except Exception as exc:
        print(f"[AVISO] Falha no despacho semântico para a raiz: {exc}", file=sys.stderr)
        return None


def prepare_includeonly_wrapper(main_tex: Path, outdir: Path, chapter_target: str) -> Path:
    """Gera um arquivo wrapper temporário com \\includeonly para compilação atômica de capítulo."""
    content = main_tex.read_text(encoding="utf-8", errors="replace")

    clean_target = chapter_target.replace("\\", "/").strip()
    if clean_target.endswith(".tex"):
        clean_target = clean_target[:-4]
    if not clean_target.startswith("capitulos/"):
        matching = list((WORKSPACE_ROOT / "capitulos").glob(f"{clean_target}*.tex"))
        if matching:
            clean_target = f"capitulos/{matching[0].stem}"
        else:
            clean_target = f"capitulos/{clean_target}"

    includeonly_directive = f"\\includeonly{{{clean_target}}}\n"

    if "\\begin{document}" in content:
        new_content = content.replace("\\begin{document}", f"{includeonly_directive}\\begin{document}")
    else:
        new_content = f"{includeonly_directive}{content}"

    wrapper_path = outdir / f"main_only_{Path(clean_target).stem}.tex"
    wrapper_path.write_text(new_content, encoding="utf-8")
    return wrapper_path


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Compila main.tex via Tectonic (ou latexmk) com suporte a compilação atômica por capítulo."
    )
    parser.add_argument(
        "--main",
        type=Path,
        default=Path("main.tex"),
        help="Arquivo mestre LaTeX a ser compilado (padrão: main.tex).",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("build"),
        help="Diretório de saída da compilação (padrão: build).",
    )
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        help="Compila exclusivamente o capítulo especificado via \\includeonly (ex.: cap02 ou capitulos/cap02_como_surgiram_as_ideias).",
    )
    parser.add_argument(
        "--render-last",
        type=int,
        default=0,
        help="Quantidade de páginas finais do PDF compilado para converter em PNG (padrão: 0, desativado).",
    )
    parser.add_argument(
        "--dispatch",
        action="store_true",
        help="Força o despacho semântico para a raiz mesmo em compilações parciais.",
    )

    args = parser.parse_args()

    if not args.main.is_file():
        print(f"[ERRO] Arquivo mestre não encontrado: {args.main}", file=sys.stderr)
        return 1

    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "capitulos").mkdir(parents=True, exist_ok=True)

    target_tex = args.main
    is_partial = bool(args.only)

    if is_partial:
        target_tex = prepare_includeonly_wrapper(args.main, args.outdir, args.only)
        print(f"[INFO] Modo atômico ativado: compilando apenas '{args.only}' via wrapper {target_tex.name}...")

    try:
        compiler_name, cmd = resolve_compiler(target_tex, args.outdir)
    except RuntimeError as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1

    print(f"[INFO] Compilando '{target_tex}' com {compiler_name}...")
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

    stem = target_tex.stem
    log_file = args.outdir / f"{stem}.log"
    compiled_pdf = args.outdir / f"{stem}.pdf"

    if proc.returncode != 0 or not compiled_pdf.is_file():
        print(
            f"[ERRO] Compilação LaTeX falhou (exit code {proc.returncode}). "
            "Últimas 40 linhas do log:",
            file=sys.stderr,
        )
        print("=" * 72, file=sys.stderr)
        print(extract_error_tail(proc.stdout, proc.stderr, log_file, max_lines=40), file=sys.stderr)
        print("=" * 72, file=sys.stderr)
        return 1

    print(f"[OK] Compilação concluída com sucesso: {compiled_pdf.as_posix()}")

    if not is_partial or args.dispatch:
        dispatch_to_root(compiled_pdf)

    if args.render_last > 0:
        preview_dir = args.outdir / "compiled_preview"
        previews = render_last_compiled_pages(
            pdf_path=compiled_pdf,
            preview_dir=preview_dir,
            count=args.render_last,
        )
        if previews:
            print(f"[OK] {len(previews)} página(s) renderizada(s) para revisão visual:")
            for p in previews:
                print(p.as_posix())

    return 0


if __name__ == "__main__":
    sys.exit(main())
