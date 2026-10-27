#!/usr/bin/env python3
"""
compile_check.py — Compilador e verificador visual de fechamento de lote (Self-Healing).

Responsabilidades:
1. Localizar o binário `tectonic` (em ./bin/ ou no PATH) ou fazer fallback para `latexmk`.
2. Compilar `main.tex` gerando o PDF em `build/main.pdf`.
3. Em caso de falha (exit code != 0), exibir as últimas 40 linhas do log de erro
   e encerrar com código 1 para que o agente corrija a sintaxe LaTeX em loop.
4. Em caso de sucesso (exit code == 0), renderizar as últimas N páginas compiladas
   em `build/compiled_preview/comp_page_XXX.png` para revisão visual do agente.
"""

import argparse
import platform
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
    try:
        import fitz
    except ImportError:
        print(
            "[AVISO] PyMuPDF (fitz) ausente; pulando renderização de preview.",
            file=sys.stderr,
        )
        return []

    preview_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []

    with fitz.open(pdf_path) as doc:
        total = len(doc)
        if total == 0 or count <= 0:
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


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Compila main.tex via Tectonic (ou latexmk) e renderiza páginas compiladas para inspeção."
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
        "--render-last",
        type=int,
        default=5,
        help="Quantidade de páginas finais do PDF compilado para converter em PNG (padrão: 5).",
    )

    args = parser.parse_args()

    if not args.main.is_file():
        print(f"[ERRO] Arquivo mestre não encontrado: {args.main}", file=sys.stderr)
        return 1

    args.outdir.mkdir(parents=True, exist_ok=True)
    # Garante também que o subdiretório build/capitulos exista para arquivos .aux de \include
    (args.outdir / "capitulos").mkdir(parents=True, exist_ok=True)

    try:
        compiler_name, cmd = resolve_compiler(args.main, args.outdir)
    except RuntimeError as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1

    print(f"[INFO] Compilando '{args.main}' com {compiler_name}...")
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

    stem = args.main.stem
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
