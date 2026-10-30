#!/usr/bin/env python3
"""
init_book_fase0.py: Automatizador deterministico da Fase 0 (Setup, Deteccao e Mapeamento de Lotes em LaTeX).

Responsabilidades:
1. Inspeciona geometria do PDF e converte folhas duplas em verticais automaticamente.
2. Extrai capa.png na raiz a partir da pagina 1 do PDF se ainda nao existir capa.
3. Extrai sumario nativo (doc.get_toc()) ou particiona em blocos sem lacunas.
4. Gera metadata.yaml (com profile tecnico ou texto), roadmap.json, progress.json e capitulos/*.tex.
5. Sincroniza main.tex, preambulo_base.tex e perfil_<profile>.tex na raiz.
"""

import argparse
import json
import re
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        print("[ERRO] PyMuPDF (fitz) obrigatorio para init_book_fase0.py", file=sys.stderr)
        sys.exit(1)


def detect_and_split_double_pages(pdf_path: Path) -> Path:
    """Verifica se o PDF possui paginas em folha dupla e executa split vertical se necessario."""
    doc = fitz.open(pdf_path)
    has_spreads = False
    for i in range(min(5, len(doc))):
        page = doc.load_page(i)
        rect = page.rect
        if rect.width > rect.height:
            has_spreads = True
            break
    doc.close()

    if not has_spreads:
        return pdf_path

    out_name = f"{pdf_path.stem}_single_pages.pdf"
    out_path = pdf_path.parent / out_name
    if out_path.is_file():
        return out_path

    print(f"[INFO] Detectado formato folha dupla em '{pdf_path.name}'. Dividindo em paginas verticais...")
    doc = fitz.open(pdf_path)
    split_doc = fitz.open()

    for page in doc:
        rect = page.rect
        if rect.width > rect.height:
            mid_x = rect.width / 2.0
            p_left = split_doc.new_page(width=mid_x, height=rect.height)
            p_left.show_pdf_page(p_left.rect, doc, page.number, clip=fitz.Rect(0, 0, mid_x, rect.height))
            p_right = split_doc.new_page(width=mid_x, height=rect.height)
            p_right.show_pdf_page(p_right.rect, doc, page.number, clip=fitz.Rect(mid_x, 0, rect.width, rect.height))
        else:
            p = split_doc.new_page(width=rect.width, height=rect.height)
            p.show_pdf_page(p.rect, doc, page.number)

    split_doc.save(str(out_path))
    doc.close()
    split_doc.close()
    print(f"[OK] Divisao concluida: '{out_path.name}' com {len(fitz.open(out_path))} paginas verticais.")
    return out_path


def ensure_cover_extracted(pdf_path: Path) -> None:
    """Preserva capa externa se ja fornecida pelo usuario na raiz;
    caso contrario, extrai a pagina 1 do PDF em 200 DPI como fallback."""
    for name in ("capa.png", "capa.jpg", "capa.jpeg", "CAPA.jpg", "CAPA.png"):
        p = Path(name)
        if p.is_file() and p.stat().st_size > 0:
            print(f"[INFO] Capa pre-existente detectada ('{name}'). Preservando arquivo de alta definicao.")
            return
    try:
        with fitz.open(pdf_path) as doc:
            if len(doc) > 0:
                pix = doc.load_page(0).get_pixmap(dpi=200, alpha=False)
                pix.save("capa.png")
                print("[OK] Capa extraida da pagina 1 do PDF para 'capa.png'.")
    except Exception as exc:
        print(f"[AVISO] Nao foi possivel extrair capa automaticamente: {exc}", file=sys.stderr)


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[áàãâä]", "a", s)
    s = re.sub(r"[éèêë]", "e", s)
    s = re.sub(r"[íìîï]", "i", s)
    s = re.sub(r"[óòõôö]", "o", s)
    s = re.sub(r"[úùûü]", "u", s)
    s = re.sub(r"[ç]", "c", s)
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def partition_batches(
    total_pages: int,
    offset: int,
    batch_size: int,
    profile: str,
    toc_entries: list[dict] | None = None,
) -> list[dict]:
    """Cria os lotes .tex cobrindo da pagina 1 ate total_pages sem lacunas."""
    batches = []

    if toc_entries and len(toc_entries) >= 2:
        batch_idx = 1
        for idx, entry in enumerate(toc_entries):
            p_start = entry["page_pdf"]
            if idx + 1 < len(toc_entries):
                p_end = toc_entries[idx + 1]["page_pdf"] - 1
            else:
                p_end = total_pages

            if p_end < p_start:
                p_end = p_start

            curr_start = p_start
            sub_part = 1
            while curr_start <= p_end:
                curr_end = min(curr_start + batch_size - 1, p_end)
                if p_end - curr_end in (1, 2):
                    curr_end = p_end

                b_id = f"lote_{batch_idx:02d}"
                raw_title = entry["title"]
                slug_title = slugify(raw_title)[:24]
                part_suffix = f"_p{sub_part}" if (p_end - p_start + 1) > batch_size else ""
                target_file = f"capitulos/cap{batch_idx:02d}_{slug_title}{part_suffix}.tex"

                batches.append({
                    "id": b_id,
                    "name": f"{raw_title}{' (Parte ' + str(sub_part) + ')' if part_suffix else ''}",
                    "chapter": raw_title,
                    "pdf_start": curr_start,
                    "pdf_end": curr_end,
                    "book_start": max(1, curr_start - offset),
                    "book_end": max(1, curr_end - offset),
                    "target_file": target_file,
                    "has_figures": (profile == "tecnico"),
                })
                batch_idx += 1
                sub_part += 1
                curr_start = curr_end + 1

        return batches

    batch_idx = 1
    curr = 1
    while curr <= total_pages:
        end = min(curr + batch_size - 1, total_pages)
        if total_pages - end in (1, 2):
            end = total_pages

        b_id = f"lote_{batch_idx:02d}"
        if curr == 1 and offset > 0:
            name = "Introducao"
            target_file = "capitulos/cap00_introducao.tex"
        else:
            name = f"Bloco {batch_idx:02d} (Paginas {curr} a {end})"
            target_file = f"capitulos/cap{batch_idx:02d}_bloco.tex"

        batches.append({
            "id": b_id,
            "name": name,
            "chapter": name,
            "pdf_start": curr,
            "pdf_end": end,
            "book_start": max(1, curr - offset),
            "book_end": max(1, end - offset),
            "target_file": target_file,
            "has_figures": (profile == "tecnico"),
        })
        batch_idx += 1
        curr = end + 1

    return batches


def _render_range(pdf: str, start: int, end: int, out_dir: str, dpi: int) -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from slice_pdf import slice_pdf

    return len(slice_pdf(Path(pdf), start, end, Path(out_dir), dpi=dpi, grayscale=True))


def pre_render_pages(pdf_path: Path, total_pages: int, out_dir: Path, workers: int = 4, dpi: int = 150) -> int:
    """Renderiza todas as paginas em PNG cinza em processos paralelos."""
    chunk = max(1, -(-total_pages // max(1, workers)))
    ranges = [(s, min(s + chunk - 1, total_pages)) for s in range(1, total_pages + 1, chunk)]
    with ProcessPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = [pool.submit(_render_range, str(pdf_path), s, e, str(out_dir), dpi) for s, e in ranges]
        return sum(f.result() for f in futures)


def setup_latex_project(batches: list[dict], title: str, author: str, profile: str) -> None:
    """Copia preambulo_base.tex, perfil_<profile>.tex e main.tex para a raiz e registra os \\include."""
    repo_templates = Path(__file__).resolve().parent.parent / "templates"
    template_files = ("preambulo_base.tex", "perfil_tecnico.tex", "perfil_texto.tex", "preambulo.tex", "main.tex")

    for name in template_files:
        dst = Path(name)
        for src_dir in (Path("templates"), repo_templates):
            if (src_dir / name).is_file():
                if name != "main.tex" or not dst.exists():
                    shutil.copy2(src_dir / name, dst)
                break

    main_tex = Path("main.tex")
    if not main_tex.is_file():
        return

    profile_tex = f"perfil_{profile}.tex"
    text = main_tex.read_text(encoding="utf-8")
    text = re.sub(r"\\input\{perfil_(?:tecnico|texto)\.tex\}", lambda _: f"\\input{{{profile_tex}}}", text)
    if "\\input{preambulo.tex}" in text and "\\input{preambulo_base.tex}" not in text:
        text = text.replace(
            "\\input{preambulo.tex}",
            f"\\input{{preambulo_base.tex}}\n\\input{{{profile_tex}}}",
        )

    text = text.replace("Título do Livro Recuperado", title).replace("Autor Original", author)

    seen = []
    for b in batches:
        stem = Path(b["target_file"]).with_suffix("").as_posix()
        if stem not in seen:
            seen.append(stem)

    text = re.sub(r"^\s*\\(?:include|input)\{capitulos/[^}]+\}\s*\n?", "", text, flags=re.MULTILINE)
    include_block = "\n".join(f"\\input{{{s}}}" for s in seen)
    if "\\end{document}" in text:
        text = text.replace("\\end{document}", f"{include_block}\n\n\\end{{document}}")

    main_tex.write_text(text, encoding="utf-8")


def write_metadata_yaml(
    title: str,
    author: str,
    profile: str,
    translation_mode: str,
    figure_mode: str,
    editorial_profile: str,
) -> None:
    content = (
        "---\n"
        f"title: \"{title}\"\n"
        f"author: \"{author}\"\n"
        f"profile: \"{profile}\"\n"
        f"translation_mode: \"{translation_mode}\"\n"
        f"figure_mode: \"{figure_mode}\"\n"
        f"editorial_profile: \"{editorial_profile}\"\n"
        "language: \"pt-BR\"\n"
        "---\n"
    )
    Path("metadata.yaml").write_text(content, encoding="utf-8")


def main() -> int:
    t0 = time.perf_counter()
    parser = argparse.ArgumentParser(
        description="Executa a Fase 0 de forma deterministica (< 3 segundos) no pipeline unico LaTeX."
    )
    parser.add_argument("--pdf", type=Path, default=None, help="Caminho do PDF original do livro.")
    parser.add_argument(
        "--profile",
        choices=["tecnico", "texto"],
        default=None,
        help="Perfil de preambulo LaTeX: 'tecnico' (exatas/TikZ) ou 'texto' (humanas/prosa).",
    )
    parser.add_argument(
        "--project-mode",
        choices=["exatas_latex", "humanas_markdown", "tecnico", "texto"],
        default=None,
        help="Alias legado para --profile.",
    )
    parser.add_argument("--translation-mode", choices=["fiel", "modernizacao", "traducao"], default="fiel")
    parser.add_argument("--figure-mode", choices=["hibrido", "recorte_total"], default="hibrido")
    parser.add_argument("--editorial-profile", default="reconstrucao_sbm")
    parser.add_argument("--batch-size", type=int, default=8, help="Tamanho padrao do lote de paginas (padrao: 8).")
    parser.add_argument("--offset", type=int, default=None, help="Offset manual entre pagina PDF e livro.")
    parser.add_argument("--title", type=str, default=None, help="Titulo do livro.")
    parser.add_argument("--author", type=str, default=None, help="Autor do livro.")
    parser.add_argument("--pre-render", action="store_true", help="Pre-renderiza todas as paginas em build/temp_pages.")

    args = parser.parse_args()

    profile = args.profile
    if not profile:
        if args.project_mode in ("humanas_markdown", "texto"):
            profile = "texto"
        else:
            profile = "tecnico"

    target_pdf = args.pdf
    if not target_pdf:
        pdfs = [p for p in Path(".").glob("*.pdf") if not p.name.endswith("_single_pages.pdf")]
        if pdfs:
            target_pdf = pdfs[0]
        else:
            print("[ERRO] Nenhum PDF encontrado na pasta.", file=sys.stderr)
            return 1

    for d in ["capitulos", "figuras", "build"]:
        Path(d).mkdir(exist_ok=True)

    work_pdf = detect_and_split_double_pages(target_pdf)
    ensure_cover_extracted(work_pdf)

    doc = fitz.open(work_pdf)
    total_pages = len(doc)
    doc_toc = doc.get_toc()

    toc_entries = []
    if doc_toc:
        for level, title_toc, page in doc_toc:
            if level == 1 and 1 <= page <= total_pages:
                toc_entries.append({"title": title_toc.strip(), "page_pdf": page})
    doc.close()

    if len(toc_entries) >= 2 and toc_entries[0]["page_pdf"] > 1:
        toc_entries.insert(0, {"title": "Introducao", "page_pdf": 1})

    offset = args.offset if args.offset is not None else 0
    title = args.title or target_pdf.stem.replace("_", " ").title()
    author = args.author or "Autor Desconhecido"

    batches = partition_batches(
        total_pages=total_pages,
        offset=offset,
        batch_size=args.batch_size,
        profile=profile,
        toc_entries=toc_entries if len(toc_entries) >= 2 else None,
    )

    write_metadata_yaml(
        title=title,
        author=author,
        profile=profile,
        translation_mode=args.translation_mode,
        figure_mode=args.figure_mode,
        editorial_profile=args.editorial_profile,
    )

    roadmap_data = {
        "book_title": title,
        "author": author,
        "source_pdf": work_pdf.name,
        "total_pages": total_pages,
        "offset": offset,
        "profile": profile,
        "translation_mode": args.translation_mode,
        "figure_mode": args.figure_mode,
        "editorial_profile": args.editorial_profile,
        "max_concurrent_workers": 8,
        "batches": batches,
    }
    Path("roadmap.json").write_text(json.dumps(roadmap_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    progress_data = {b["id"]: "pending" for b in batches}
    Path("progress.json").write_text(json.dumps(progress_data, indent=2) + "\n", encoding="utf-8")

    for b in batches:
        t_file = Path(b["target_file"])
        t_file.parent.mkdir(parents=True, exist_ok=True)
        if not t_file.exists():
            t_file.touch()

    setup_latex_project(batches, title, author, profile)

    if args.pre_render:
        n_pages = pre_render_pages(work_pdf, total_pages, Path("build/temp_pages"))
        print(f"  Paginas pre-renderizadas: {n_pages} em build/temp_pages (150 DPI, cinza)")

    elapsed = time.perf_counter() - t0
    print(f"[OK] Fase 0 concluida em {elapsed:.2f} segundos! (Perfil: {profile})")
    print(f"  Livro: '{title}' ({total_pages} paginas verticais)")
    print(f"  Lotes gerados: {len(batches)} lotes de ~{args.batch_size} paginas")
    print(f"  Arquivos criados: metadata.yaml, roadmap.json, progress.json, main.tex e {len(batches)} capitulos .tex")
    return 0


if __name__ == "__main__":
    sys.exit(main())
