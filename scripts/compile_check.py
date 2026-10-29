#!/usr/bin/env python3
"""
compile_check.py: Compilador unico (Tectonic) e linter editorial para os perfis 'tecnico' e 'texto'.

Responsabilidades:
1. Ler metadata.yaml para identificar o perfil ('tecnico' ou 'texto') e sincronizar preambulos.
2. Executar lint editorial rapido (--lint) verificando escapes, \\chapter duplicado, numero solto no titulo e macros fora da lista do perfil.
3. Compilar main.tex (ou versao parcial via --only capXX) gerando o PDF em build/.
4. Renderizar paginas sob demanda via --render-last N e despachar o PDF final para a raiz.
"""

import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
BIN_DIR = WORKSPACE_ROOT / "bin"

FORBIDDEN_IN_TEXTO_PROFILE = {
    "tikzpicture",
    "axis",
    "definicao",
    "teorema",
    "exemplo",
    "caixaformulas",
    "demonstracao",
    "solucao",
}

FORBIDDEN_IN_CHAPTER_FILES = (
    r"\documentclass",
    r"\usepackage",
    r"\begin{document}",
    r"\end{document}",
)


def read_project_metadata() -> dict:
    """Le metadata.yaml e roadmap.json na pasta de trabalho atual."""
    meta = {
        "title": "Livro",
        "author": "",
        "profile": "tecnico",
        "source_pdf": "",
    }
    meta_yaml = Path("metadata.yaml")
    if meta_yaml.is_file():
        try:
            for line in meta_yaml.read_text(encoding="utf-8", errors="replace").splitlines():
                if ":" in line and not line.strip().startswith("#"):
                    k, v = line.split(":", 1)
                    k = k.strip().lower()
                    v = v.strip().strip('"').strip("'")
                    if k in ("title", "author", "profile") and v:
                        meta[k] = v
        except Exception:
            pass

    roadmap_path = Path("roadmap.json")
    if roadmap_path.is_file():
        try:
            data = json.loads(roadmap_path.read_text(encoding="utf-8"))
            if data.get("book_title") and meta["title"] == "Livro":
                meta["title"] = data["book_title"]
            if data.get("author") and not meta["author"]:
                meta["author"] = data["author"]
            if data.get("profile") in ("tecnico", "texto"):
                meta["profile"] = data["profile"]
            elif data.get("project_mode") == "humanas_markdown" and not meta_yaml.is_file():
                meta["profile"] = "texto"
            meta["source_pdf"] = data.get("source_pdf", "")
        except Exception:
            pass

    if meta["profile"] not in ("tecnico", "texto"):
        meta["profile"] = "tecnico"
    return meta


def ensure_preamble_files(profile: str, main_tex: Path) -> None:
    """Garante que preambulo_base.tex e perfil_<profile>.tex estejam na raiz e referenciados em main.tex."""
    repo_templates = WORKSPACE_ROOT / "templates"
    for name in ("preambulo_base.tex", "perfil_tecnico.tex", "perfil_texto.tex", "preambulo.tex"):
        dst = main_tex.parent / name
        if not dst.is_file():
            for src_dir in (main_tex.parent / "templates", repo_templates):
                if (src_dir / name).is_file():
                    shutil.copy2(src_dir / name, dst)
                    break

    if main_tex.is_file():
        text = main_tex.read_text(encoding="utf-8", errors="replace")
        target_profile_tex = f"perfil_{profile}.tex"
        updated = re.sub(
            r"\\input\{perfil_(?:tecnico|texto)\.tex\}",
            lambda _: f"\\input{{{target_profile_tex}}}",
            text,
        )
        if "\\input{preambulo.tex}" in updated and "\\input{preambulo_base.tex}" not in updated:
            updated = updated.replace(
                "\\input{preambulo.tex}",
                f"\\input{{preambulo_base.tex}}\n\\input{{{target_profile_tex}}}",
            )
        if updated != text:
            main_tex.write_text(updated, encoding="utf-8")


def lint_chapter_file(tex_path: Path, profile: str) -> list[str]:
    """Verifica erros estruturais e de escape em um arquivo capitulos/*.tex."""
    issues: list[str] = []
    if not tex_path.is_file():
        return [f"{tex_path.name}: arquivo nao encontrado."]

    lines = tex_path.read_text(encoding="utf-8", errors="replace").splitlines()
    chapter_count = 0
    in_tabular_or_math = False

    for idx, raw_line in enumerate(lines, start=1):
        # Remove comentarios legitimos (onde % nao eh precedido por \)
        code_part = re.split(r"(?<!\\)%", raw_line, maxsplit=1)[0]

        for forbidden_cmd in FORBIDDEN_IN_CHAPTER_FILES:
            if forbidden_cmd in code_part:
                issues.append(f"{tex_path.name}:{idx}: comando de preambulo proibido em capitulo ('{forbidden_cmd}').")

        # Verifica \chapter
        for chap_m in re.finditer(r"\\chapter(\*)?\{([^}]*)\}", code_part):
            chapter_count += 1
            is_starred = bool(chap_m.group(1))
            chap_title = chap_m.group(2).strip()
            if re.match(r"^\d+$", chap_title):
                issues.append(f"{tex_path.name}:{idx}: titulo de \\chapter contem apenas numero solto ('{chap_title}').")
            elif not is_starred and re.match(r"^(?:Cap[ií]tulo\s+\d+|\d+[\.\-\s:])", chap_title, re.IGNORECASE):
                issues.append(
                    f"{tex_path.name}:{idx}: numero de capitulo digitado manualmente em \\chapter ('{chap_title}'). "
                    "O LaTeX ja numera automaticamente."
                )

        # Verifica ambientes proibidos no perfil texto
        if profile == "texto":
            for env_m in re.finditer(r"\\begin\{([^}]+)\}", code_part):
                env_name = env_m.group(1).strip()
                if env_name in FORBIDDEN_IN_TEXTO_PROFILE:
                    issues.append(
                        f"{tex_path.name}:{idx}: ambiente '{env_name}' nao permitido no perfil 'texto'."
                    )

        # Controle simples de ambientes onde & e _ sao livres
        if re.search(r"\\begin\{(?:tabular|array|align\*?|gather\*?|cases|pmatrix|bmatrix|vmatrix|tikzpicture)\}", code_part):
            in_tabular_or_math = True
        if re.search(r"\\end\{(?:tabular|array|align\*?|gather\*?|cases|pmatrix|bmatrix|vmatrix|tikzpicture)\}", code_part):
            in_tabular_or_math = False

        # Verifica % apos digito sem escape (ex: 100%)
        if re.search(r"\d%", raw_line) and not re.search(r"\d\\%", raw_line):
            issues.append(f"{tex_path.name}:{idx}: possivel simbolo '%' sem escape apos numero (use '\\%').")

        # Remove trechos matematicos inline ($...$, \(...\)) e comandos com paths/labels antes de checar # & _
        stripped = re.sub(r"\$[^$]*\$", "", code_part)
        stripped = re.sub(r"\\(?:label|ref|eqref|cite|includegraphics|input|include|url|href)\b(?:\[[^\]]*\])?\{[^}]*\}", "", stripped)

        if re.search(r"(?<!\\)#", stripped):
            issues.append(f"{tex_path.name}:{idx}: caractere '#' sem escape fora de macro (use '\\#').")

        if not in_tabular_or_math:
            if re.search(r"(?<!\\)&", stripped):
                issues.append(f"{tex_path.name}:{idx}: caractere '&' sem escape fora de tabela/align (use '\\&').")
            if re.search(r"(?<!\\)_", stripped):
                issues.append(f"{tex_path.name}:{idx}: caractere '_' sem escape fora de modo matematico (use '\\_').")

    if chapter_count > 1:
        issues.append(f"{tex_path.name}: multiplos comandos \\chapter ({chapter_count}) no mesmo arquivo.")

    return issues


def run_lint(capitulos_dir: Path, profile: str, only_target: str | None = None) -> list[str]:
    """Executa o lint em todos os capitulos .tex (ou apenas no capitulo filtrado por --only)."""
    if not capitulos_dir.is_dir():
        return []
    tex_files = sorted(capitulos_dir.glob("*.tex"))
    if only_target:
        clean = Path(only_target).stem.lower()
        tex_files = [p for p in tex_files if p.stem.lower() == clean or p.stem.lower().startswith(clean)]
    all_issues: list[str] = []
    for p in tex_files:
        all_issues.extend(lint_chapter_file(p, profile))
    return all_issues


def resolve_compiler(main_tex: Path, outdir: Path) -> tuple[str, list[str]]:
    """Localiza tectonic (local ou PATH) ou retorna comando fallback com latexmk/pdflatex."""
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
    """Renderiza as ultimas `count` paginas do PDF compilado em PNG."""
    if count <= 0:
        return []

    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
    except ImportError:
        print("[AVISO] PyMuPDF ausente; pulando renderizacao de preview.", file=sys.stderr)
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
    """Extrai as ultimas `max_lines` linhas combinando saida do processo e arquivo .log."""
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


def dispatch_to_root(compiled_pdf: Path, meta: dict) -> Path | None:
    """Copia o PDF compilado para a raiz com o nome semantico da obra."""
    title = meta.get("title", "Livro")
    author = meta.get("author", "")
    source_pdf = meta.get("source_pdf", "")

    def sanitize(s: str) -> str:
        s = re.sub(r'[\\/*?:"<>|]', "", s)
        return s.strip().replace(" ", "_")

    s_title = sanitize(title)
    s_author = sanitize(author) if author and author != "Autor Desconhecido" else ""
    target_name = f"{s_title}_{s_author}.pdf" if s_author else f"{s_title}.pdf"
    target_path = Path(".") / target_name

    source_stem = Path(source_pdf).stem.lower() if source_pdf else ""
    if target_path.name.lower() == source_pdf.lower() or (source_stem and source_stem == target_path.stem.lower()):
        target_name = f"{target_path.stem}_Recuperado.pdf"
        target_path = Path(".") / target_name

    try:
        shutil.copy2(compiled_pdf, target_path)
        print(f"[OK] Despacho semantico concluido: {target_path.name}")
        return target_path
    except Exception as exc:
        print(f"[AVISO] Falha no despacho semantico para a raiz: {exc}", file=sys.stderr)
        return None


def prepare_includeonly_wrapper(main_tex: Path, chapter_target: str) -> Path:
    """Gera um arquivo wrapper temporario na raiz com \\includeonly para compilacao atomica de capitulo."""
    content = main_tex.read_text(encoding="utf-8", errors="replace")

    clean_target = chapter_target.replace("\\", "/").strip()
    if clean_target.endswith(".tex"):
        clean_target = clean_target[:-4]
    if not clean_target.startswith("capitulos/"):
        matching = list((main_tex.parent / "capitulos").glob(f"{clean_target}*.tex"))
        if matching:
            clean_target = f"capitulos/{matching[0].stem}"
        else:
            clean_target = f"capitulos/{clean_target}"

    includeonly_directive = f"\\includeonly{{{clean_target}}}\n"

    # Se main.tex usar \input{capitulos/...}, comenta os outros capitulos no wrapper
    def filter_input_line(match: re.Match) -> str:
        cmd_type = match.group(1)
        path_arg = match.group(2).strip()
        if path_arg == clean_target or path_arg.startswith(clean_target):
            return match.group(0)
        if cmd_type == "input":
            return f"% {match.group(0)}"
        return match.group(0)

    filtered_content = re.sub(
        r"^(\s*\\(input|include)\{(capitulos/[^}]+)\})",
        filter_input_line,
        content,
        flags=re.MULTILINE,
    )

    if "\\begin{document}" in filtered_content:
        new_content = filtered_content.replace("\\begin{document}", f"{includeonly_directive}\\begin{{document}}")
    else:
        new_content = f"{includeonly_directive}{filtered_content}"

    wrapper_path = main_tex.parent / f"main_only_{Path(clean_target).stem}.tex"
    wrapper_path.write_text(new_content, encoding="utf-8")
    return wrapper_path


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Linter editorial e compilador unico LaTeX via Tectonic para perfis 'tecnico' e 'texto'."
    )
    parser.add_argument("--main", type=Path, default=Path("main.tex"), help="Arquivo mestre LaTeX (padrao: main.tex).")
    parser.add_argument("--outdir", type=Path, default=Path("build"), help="Diretorio de saida (padrao: build).")
    parser.add_argument("--only", type=str, default=None, help="Compila apenas o capitulo indicado via \\includeonly.")
    parser.add_argument("--render-last", type=int, default=0, help="Renderiza as N ultimas paginas compiladas em PNG.")
    parser.add_argument("--dispatch", action="store_true", help="Forca despacho semantico mesmo em compilacao parcial.")
    parser.add_argument("--lint", action="store_true", help="Executa lint estatico nos capitulos antes de compilar.")
    parser.add_argument("--lint-only", action="store_true", help="Executa apenas o lint estatico sem chamar o Tectonic.")

    args = parser.parse_args()
    t0 = time.perf_counter()

    meta = read_project_metadata()
    profile = meta["profile"]

    if args.lint or args.lint_only:
        issues = run_lint(args.main.parent / "capitulos", profile=profile, only_target=args.only)
        if issues:
            print(f"[LINT] {len(issues)} problema(s) encontrado(s) (perfil: {profile}):", file=sys.stderr)
            for iss in issues:
                print(f"  - {iss}", file=sys.stderr)
            return 1
        print(f"[OK] Lint editorial aprovado sem alertas (perfil: {profile}).")
        if args.lint_only:
            return 0

    if not args.main.is_file():
        print(f"[ERRO] Arquivo mestre nao encontrado: {args.main}", file=sys.stderr)
        return 1

    ensure_preamble_files(profile, args.main)
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "capitulos").mkdir(parents=True, exist_ok=True)

    target_tex = args.main
    is_partial = bool(args.only)

    if is_partial:
        target_tex = prepare_includeonly_wrapper(args.main, args.only)
        print(f"[INFO] Modo atomico ativado (perfil: {profile}): compilando '{args.only}' via {target_tex.name}...")

    try:
        compiler_name, cmd = resolve_compiler(target_tex, args.outdir)
        print(f"[INFO] Compilando '{target_tex}' com {compiler_name} (perfil: {profile})...")
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    except RuntimeError as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1
    finally:
        if is_partial and target_tex.is_file():
            target_tex.unlink(missing_ok=True)

    stem = target_tex.stem
    log_file = args.outdir / f"{stem}.log"
    compiled_pdf = args.outdir / f"{stem}.pdf"

    if proc.returncode != 0 or not compiled_pdf.is_file():
        print(
            f"[ERRO] Compilacao LaTeX falhou (exit code {proc.returncode}). Ultimas 40 linhas do log:",
            file=sys.stderr,
        )
        print("=" * 72, file=sys.stderr)
        print(extract_error_tail(proc.stdout, proc.stderr, log_file, max_lines=40), file=sys.stderr)
        print("=" * 72, file=sys.stderr)
        return 1

    elapsed = time.perf_counter() - t0
    print(f"[OK] Compilacao concluida em {elapsed:.2f}s: {compiled_pdf.as_posix()}")

    if not is_partial or args.dispatch:
        dispatch_to_root(compiled_pdf, meta)

    if args.render_last > 0:
        preview_dir = args.outdir / "compiled_preview"
        previews = render_last_compiled_pages(
            pdf_path=compiled_pdf,
            preview_dir=preview_dir,
            count=args.render_last,
        )
        if previews:
            print(f"[OK] {len(previews)} pagina(s) renderizada(s) para revisao visual:")
            for p in previews:
                print(p.as_posix())

    return 0


if __name__ == "__main__":
    sys.exit(main())
