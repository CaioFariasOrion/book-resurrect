#!/usr/bin/env python3
"""
crop_figure.py — Recorte e limpeza de figuras não vetorizáveis de páginas escaneadas.

Recorta uma bounding box normalizada (x0,y0,x1,y1 em [0.0, 1.0]) de uma imagem PNG,
converte para tons de cinza limpos com ganho de contraste e remoção de fundo
acinzentado típico de scanners/fotos, salvando o resultado em alta nitidez.
"""

import argparse
import sys
from pathlib import Path


def parse_bbox(bbox_str: str) -> tuple[float, float, float, float]:
    """Valida e converte a string 'x0,y0,x1,y1' em 4 floats normalizados [0.0, 1.0]."""
    parts = [p.strip() for p in bbox_str.split(",")]
    if len(parts) != 4:
        raise ValueError(
            f"--bbox deve conter exatamente 4 valores separados por vírgula 'x0,y0,x1,y1' (recebido: '{bbox_str}')"
        )
    try:
        x0, y0, x1, y1 = (float(v) for v in parts)
    except ValueError as exc:
        raise ValueError(f"Valores numéricos inválidos em --bbox: '{bbox_str}'") from exc

    if not (0.0 <= x0 < x1 <= 1.0 and 0.0 <= y0 < y1 <= 1.0):
        raise ValueError(
            f"Coordenadas --bbox devem respeitar 0.0 <= x0 < x1 <= 1.0 e 0.0 <= y0 < y1 <= 1.0 "
            f"(recebido: {x0}, {y0}, {x1}, {y1})"
        )
    return x0, y0, x1, y1


def crop_and_clean_figure(
    image_path: Path,
    bbox: tuple[float, float, float, float],
    out_path: Path,
    white_threshold: int = 215,
) -> Path:
    """Recorta a região especificada e aplica limpeza de fundo de scanner e nitidez."""
    try:
        from PIL import Image, ImageEnhance, ImageOps
    except ImportError:
        print(
            "[ERRO] Pillow (PIL) não está instalado. Execute `python scripts/setup_env.py` primeiro.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not image_path.is_file():
        raise FileNotFoundError(f"Imagem de entrada não encontrada: {image_path}")

    with Image.open(image_path) as img:
        width, height = img.size
        x0, y0, x1, y1 = bbox
        left = max(0, int(round(x0 * width)))
        top = max(0, int(round(y0 * height)))
        right = min(width, int(round(x1 * width)))
        bottom = min(height, int(round(y1 * height)))

        if right <= left or bottom <= top:
            raise ValueError("Região recortada possui dimensões nulas ou inválidas.")

        cropped = img.crop((left, top, right, bottom))

        # Converte para escala de cinza e normaliza os níveis
        gray = cropped.convert("L")
        normalized = ImageOps.autocontrast(gray, cutoff=1)

        # Aumenta contraste e nitidez para destacar traços de ilustrações
        contrasted = ImageEnhance.Contrast(normalized).enhance(1.35)
        sharpened = ImageEnhance.Sharpness(contrasted).enhance(1.5)

        # Remove o fundo acinzentado típico de digitalização tornando brancos puros os tons claros
        cleaned = sharpened.point(lambda p: 255 if p >= white_threshold else p)
        final_rgb = cleaned.convert("RGB")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        final_rgb.save(str(out_path), format="PNG", optimize=True)

    return out_path


def list_page_boxes(pdf_path: Path, page_num: int) -> list[tuple[str, tuple[float, float, float, float]]]:
    """Devolve as caixas normalizadas (x0,y0,x1,y1) de imagens e desenhos vetoriais da página (base 1)."""
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
    except ImportError:
        print("[ERRO] PyMuPDF não está instalado.", file=sys.stderr)
        sys.exit(1)

    if not pdf_path.is_file():
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {pdf_path}")

    with fitz.open(pdf_path) as doc:
        if not 1 <= page_num <= len(doc):
            raise ValueError(f"--page deve estar entre 1 e {len(doc)} (recebido: {page_num})")
        page = doc.load_page(page_num - 1)
        w, h = page.rect.width, page.rect.height
        found: list[tuple[str, fitz.Rect]] = []
        for info in page.get_image_info():
            found.append(("imagem", fitz.Rect(info["bbox"])))
        try:
            for rect in page.cluster_drawings():
                found.append(("desenho", fitz.Rect(rect)))
        except Exception:
            pass

    boxes = []
    for kind, r in found:
        r = r & fitz.Rect(0, 0, w, h)
        if r.is_empty or r.width < 24 or r.height < 24:
            continue
        boxes.append((kind, (
            round(max(0.0, r.x0 / w), 3),
            round(max(0.0, r.y0 / h), 3),
            round(min(1.0, r.x1 / w), 3),
            round(min(1.0, r.y1 / h), 3),
        )))
    return boxes


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Recorta e limpa figuras de páginas escaneadas usando coordenadas relativas [0.0, 1.0]."
    )
    parser.add_argument(
        "--list-boxes",
        action="store_true",
        help="Lista as caixas de imagens/desenhos de uma página do PDF (usa --pdf e --page) e sai.",
    )
    parser.add_argument("--pdf", type=Path, help="PDF de origem (somente com --list-boxes).")
    parser.add_argument("--page", type=int, help="Página do PDF, base 1 (somente com --list-boxes).")
    parser.add_argument(
        "--image",
        type=Path,
        help="Caminho da imagem PNG da página (ex.: build/temp_pages/page_010.png).",
    )
    parser.add_argument(
        "--bbox",
        type=str,
        help="Coordenadas relativas 'x0,y0,x1,y1' no intervalo de 0.0 a 1.0.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Caminho do arquivo PNG de saída (ex.: figuras/fig_1_1.png).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=215,
        help="Limiar de branqueamento de fundo (0-255, padrão: 215).",
    )

    args = parser.parse_args()

    if args.list_boxes:
        if not args.pdf or not args.page:
            parser.error("--list-boxes exige --pdf e --page")
        try:
            boxes = list_page_boxes(args.pdf, args.page)
        except Exception as exc:
            print(f"[ERRO] {exc}", file=sys.stderr)
            return 1
        if not boxes:
            print("[AVISO] Nenhuma imagem ou desenho encontrado (página escaneada inteira? use --bbox manual).")
            return 0
        for kind, (x0, y0, x1, y1) in boxes:
            print(f"{kind}: --bbox {x0},{y0},{x1},{y1}")
        return 0

    if not (args.image and args.bbox and args.out):
        parser.error("--image, --bbox e --out são obrigatórios (ou use --list-boxes)")

    try:
        bbox = parse_bbox(args.bbox)
        saved_path = crop_and_clean_figure(
            image_path=args.image,
            bbox=bbox,
            out_path=args.out,
            white_threshold=args.threshold,
        )
    except Exception as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1

    print(f"[OK] Figura recortada e tratada salva em: {saved_path.as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
