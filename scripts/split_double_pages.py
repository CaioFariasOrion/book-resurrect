"""
split_double_pages.py - Pre-processador para PDFs em folha dupla (booklet / paisagem).
Divide verticalmente cada pagina de largura > altura em duas paginas verticais ordenadas.
"""
import sys
import os
from pypdf import PdfReader, PdfWriter

def split_pdf(input_path, output_path=None):
    if not os.path.exists(input_path):
        print(f"Erro: Arquivo {input_path} nao encontrado.")
        sys.exit(1)
        
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_single_pages{ext}"
        
    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    total_original = len(reader.pages)
    print(f"Inspecionando '{input_path}' ({total_original} paginas)...")
    
    has_spreads = False
    for page in reader.pages:
        mb = page.mediabox
        if float(mb.width) > float(mb.height):
            has_spreads = True
            break

    if not has_spreads:
        print("PDF ja se encontra em formato vertical de pagina simples. Nenhuma divisao necessaria.")
        return input_path

    print("Detectado formato booklet/folha dupla (largura > altura). Executando split vertical...")
    for page in reader.pages:
        mb = page.mediabox
        w, h = float(mb.width), float(mb.height)
        if w > h:
            mid_x = w / 2.0
            p_left = writer.add_page(page)
            p_left.mediabox.lower_left = (mb.lower_left[0], mb.lower_left[1])
            p_left.mediabox.upper_right = (mb.lower_left[0] + mid_x, mb.upper_right[1])

            p_right = writer.add_page(page)
            p_right.mediabox.lower_left = (mb.lower_left[0] + mid_x, mb.lower_left[1])
            p_right.mediabox.upper_right = (mb.upper_right[0], mb.upper_right[1])
        else:
            writer.add_page(page)
            
    with open(output_path, "wb") as f_out:
        writer.write(f_out)
        
    print(f"Sucesso! Gerado '{output_path}' com {len(writer.pages)} paginas verticais.")
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python split_double_pages.py <arquivo.pdf> [arquivo_saida.pdf]")
        sys.exit(1)
    in_pdf = sys.argv[1]
    out_pdf = sys.argv[2] if len(sys.argv) > 2 else None
    split_pdf(in_pdf, out_pdf)
