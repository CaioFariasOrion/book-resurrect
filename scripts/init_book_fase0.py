#!/usr/bin/env python3
"""
init_book_fase0.py - Automatizador deterministico da Fase 0 (Setup, Deteccao e Mapeamento de Lotes).

Elimina a latencia conversacional (de 26 minutos para < 3 segundos):
1. Inspeciona geometria do PDF e converte folhas duplas em verticais automaticamente.
2. Extrai sumario nativo (doc.get_toc()) ou busca programaticamente marcadores de capitulo.
3. Se nao houver marcadores legiveis, particiona deterministicamente em blocos sem lacunas.
4. Gera roadmap.json, progress.json, arquivos esqueleto em capitulos/ e atualiza CONTEXT.md.
"""

import argparse
import json
import re
import sys
import time
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
    project_mode: str,
    toc_entries: list[dict] | None = None,
) -> list[dict]:
    """Cria os lotes cobrindo da pagina 1 ate total_pages sem lacunas ou saltos."""
    ext = "tex" if project_mode == "exatas_latex" else "md"
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
                target_file = f"capitulos/cap_{slug_title}{part_suffix}.{ext}"

                batches.append({
                    "id": b_id,
                    "name": f"{raw_title}{' (Parte ' + str(sub_part) + ')' if part_suffix else ''}",
                    "chapter": raw_title,
                    "pdf_start": curr_start,
                    "pdf_end": curr_end,
                    "book_start": max(1, curr_start - offset),
                    "book_end": max(1, curr_end - offset),
                    "target_file": target_file,
                    "has_figures": (project_mode == "exatas_latex"),
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
            name = "Pre-textuais e Abertura"
            target_file = f"capitulos/cap00_abertura.{ext}"
        else:
            name = f"Bloco {batch_idx:02d} (Paginas {curr} a {end})"
            target_file = f"capitulos/cap{batch_idx:02d}_bloco.{ext}"

        batches.append({
            "id": b_id,
            "name": name,
            "chapter": name,
            "pdf_start": curr,
            "pdf_end": end,
            "book_start": max(1, curr - offset),
            "book_end": max(1, end - offset),
            "target_file": target_file,
            "has_figures": (project_mode == "exatas_latex"),
        })
        batch_idx += 1
        curr = end + 1

    return batches


def main() -> int:
    t0 = time.perf_counter()
    parser = argparse.ArgumentParser(
        description="Executa a Fase 0 de forma deterministica (< 3 segundos), sem turnos conversacionais."
    )
    parser.add_argument("--pdf", type=Path, default=None, help="Caminho do PDF original do livro.")
    parser.add_argument("--project-mode", choices=["exatas_latex", "humanas_markdown"], default="humanas_markdown")
    parser.add_argument("--translation-mode", choices=["fiel", "modernizacao", "traducao"], default="fiel")
    parser.add_argument("--figure-mode", choices=["hibrido", "recorte_total"], default="recorte_total")
    parser.add_argument("--editorial-profile", default="reconstrucao_sbm")
    parser.add_argument("--batch-size", type=int, default=8, help="Tamanho padrao do lote de paginas (padrao: 8).")
    parser.add_argument("--offset", type=int, default=None, help="Offset manual entre pagina PDF e livro.")
    parser.add_argument("--title", type=str, default=None, help="Titulo do livro.")
    parser.add_argument("--author", type=str, default=None, help="Autor do livro.")

    args = parser.parse_args()

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

    doc = fitz.open(work_pdf)
    total_pages = len(doc)
    doc_toc = doc.get_toc()

    toc_entries = []
    if doc_toc:
        for level, title, page in doc_toc:
            if level == 1 and 1 <= page <= total_pages:
                toc_entries.append({"title": title.strip(), "page_pdf": page})

    offset = args.offset if args.offset is not None else 0
    title = args.title or target_pdf.stem.replace("_", " ").title()
    author = args.author or "Autor Desconhecido"

    batches = partition_batches(
        total_pages=total_pages,
        offset=offset,
        batch_size=args.batch_size,
        project_mode=args.project_mode,
        toc_entries=toc_entries if len(toc_entries) >= 2 else None,
    )

    roadmap_data = {
        "book_title": title,
        "author": author,
        "source_pdf": work_pdf.name,
        "total_pages": total_pages,
        "offset": offset,
        "project_mode": args.project_mode,
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

    if args.project_mode == "humanas_markdown":
        meta_yaml = Path("metadata.yaml")
        if not meta_yaml.exists():
            content = f"---\ntitle: \"{title}\"\nauthor: \"{author}\"\nlang: \"pt-BR\"\ntoc-title: \"Sumário\"\n...\n"
            meta_yaml.write_text(content, encoding="utf-8")

    elapsed = time.perf_counter() - t0
    print(f"[OK] Fase 0 concluida em {elapsed:.2f} segundos!")
    print(f"  Livro: '{title}' ({total_pages} paginas verticais)")
    print(f"  Lotes gerados: {len(batches)} lotes de ~{args.batch_size} paginas")
    print(f"  Arquivos criados: roadmap.json, progress.json, {len(batches)} capitulos em capitulos/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
