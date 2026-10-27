#!/usr/bin/env python3
"""
slice_pdf.py — Fatiador e renderizador de páginas de PDF para PNG (150-200 DPI).

Converte apenas o intervalo [start, end] (base 1, inclusivo) de um arquivo PDF
em imagens PNG numeradas (`page_001.png`, `page_002.png`, ...) para inspeção
visual multimodal do agente de IA sem sobrecarregar a memória.
"""

import argparse
import sys
from pathlib import Path


def slice_pdf(
    pdf_path: Path,
    start_page: int,
    end_page: int,
    out_dir: Path,
    dpi: int = 180,
) -> list[Path]:
    """Renderiza o intervalo [start_page, end_page] (1-based) do PDF em imagens PNG."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print(
            "[ERRO] PyMuPDF (fitz) não está instalado. Execute `python scripts/setup_env.py` primeiro.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not pdf_path.is_file():
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {pdf_path}")

    if start_page < 1:
        raise ValueError(f"--start deve ser >= 1 (recebido: {start_page})")
    if end_page < start_page:
        raise ValueError(
            f"--end ({end_page}) deve ser maior ou igual a --start ({start_page})"
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    generated_files: list[Path] = []

    with fitz.open(pdf_path) as doc:
        total_pages = len(doc)
        if start_page > total_pages:
            raise ValueError(
                f"Página inicial ({start_page}) excede o total de páginas do PDF ({total_pages})."
            )

        actual_end = min(end_page, total_pages)
        print(
            f"[INFO] PDF: '{pdf_path.name}' | Total de páginas: {total_pages} | "
            f"Renderizando intervalo: {start_page} a {actual_end} ({dpi} DPI)"
        )

        for page_num in range(start_page, actual_end + 1):
            page = doc.load_page(page_num - 1)
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            out_file = out_dir / f"page_{page_num:03d}.png"
            pix.save(str(out_file))
            generated_files.append(out_file)

    return generated_files


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Renderiza um intervalo de páginas de um PDF em arquivos PNG numerados."
    )
    parser.add_argument(
        "--pdf",
        required=True,
        type=Path,
        help="Caminho para o arquivo PDF de entrada.",
    )
    parser.add_argument(
        "--start",
        required=True,
        type=int,
        help="Página inicial do intervalo (base 1, inclusiva).",
    )
    parser.add_argument(
        "--end",
        required=True,
        type=int,
        help="Página final do intervalo (base 1, inclusiva).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("build/temp_pages"),
        help="Diretório de saída para as imagens PNG (padrão: build/temp_pages).",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=180,
        help="Resolução em DPI para renderização (padrão: 180).",
    )

    args = parser.parse_args()

    try:
        files = slice_pdf(
            pdf_path=args.pdf,
            start_page=args.start,
            end_page=args.end,
            out_dir=args.out,
            dpi=args.dpi,
        )
    except Exception as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1

    print(f"[OK] {len(files)} página(s) gerada(s):")
    for fpath in files:
        print(fpath.as_posix())

    return 0


if __name__ == "__main__":
    sys.exit(main())
