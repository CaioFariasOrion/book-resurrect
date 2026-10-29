#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/audit_and_fix_tikz.py

Ferramenta canonica do pipeline book-resurrect para auditoria visual e auto-cura
geometrica de ambientes TikZ e figuras flutuantes.

Modulos:
1. Normalizacao de figuras avulsas para ambientes figure canonicos com [htbp].
2. Protocolo de Fundo Protetor compulsório (fill=white, inner sep=1.2pt).
3. Desobstrucao geometrica de nos concorrentes (raios polares, cotas em eixos,
   formulas de area em secantes e helicoides trigonométricos).
4. Renderizacao em alta resolucao (300 DPI via pymupdf) de paginas com figuras
   para inspecao visual em build/figures_review/.
"""

import os
import sys
import re
import argparse
from pathlib import Path

# Tentativa de importacao de pymupdf (fitz)
try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None


# ==============================================================================
# REGRAS DE AUTO-CURA GEOMETRICA EM CODIGO LATEX
# ==============================================================================

def normalizar_figuras_avulsas(content: str) -> tuple[str, int]:
    """Converte padroes legados e avulsos de figuras para ambientes canonicos figure."""
    modificacoes = 0

    # Padrao: \begin{center} ... \refstepcounter{figure} ... \end{center}
    pattern_center = re.compile(
        r"\\begin\{center\}\s*"
        r"(.*?)"
        r"\\refstepcounter\{figure\}\s*"
        r"\\label\{([^}]+)\}\s*"
        r"(?:\\textbf\{Figura\s*[^:]*:\}\s*)?"
        r"(.*?)"
        r"\\end\{center\}",
        re.DOTALL
    )

    def repl_center(match):
        nonlocal modificacoes
        modificacoes += 1
        corpo = match.group(1).strip()
        label = match.group(2).strip()
        legenda = match.group(3).strip()
        # Se a legenda tiver quebra de linha ou formatacao residual, limpa
        legenda = re.sub(r"^\\textit\{|\}$", "", legenda).strip()
        return (
            f"\\begin{{figure}}[htbp]\n"
            f"\\centering\n"
            f"{corpo}\n"
            f"\\caption{{{legenda}}}\n"
            f"\\label{{{label}}}\n"
            f"\\end{{figure}}"
        )

    content, n = pattern_center.subn(repl_center, content)
    modificacoes += n
    return content, modificacoes


def injetar_fundo_protetor_em_nos(tikz_block: str) -> tuple[str, int]:
    """Injeta fill=white, inner sep=1.2pt em nos de texto ou formulas que nao possuem fundo."""
    modificacoes = 0

    # 1. Nos explicitos com colchetes: \node[...] at (...) {...};
    # ou \draw ... node[...] {...};
    pattern_node_opts = re.compile(r"(\bnode\s*\[)([^\]]*)(\]\s*(?:at\s*\([^)]+\)\s*)?\{[^}]+\})")

    def repl_opts(match):
        nonlocal modificacoes
        prefix = match.group(1)
        opts = match.group(2)
        suffix = match.group(3)

        # Se ja tem fill ou se for apenas coordenador estrutural sem texto
        if "fill=" in opts or "fill " in opts:
            return match.group(0)

        modificacoes += 1
        sep = ", " if opts.strip() else ""
        return f"{prefix}{opts}{sep}fill=white, inner sep=1.2pt{suffix}"

    tikz_block, n1 = pattern_node_opts.subn(repl_opts, tikz_block)
    modificacoes += n1

    # 2. Nos sem colchetes: \node at (...) {...};
    pattern_node_bare = re.compile(r"(\\node\s+)(at\s*\([^)]+\)\s*\{[^}]+\})")

    def repl_bare(match):
        nonlocal modificacoes
        modificacoes += 1
        return f"\\node[fill=white, inner sep=1.2pt] {match.group(2)}"

    tikz_block, n2 = pattern_node_bare.subn(repl_bare, tikz_block)
    modificacoes += n2

    return tikz_block, modificacoes


def desobstruir_geometria_especifica(content: str, filename: str) -> tuple[str, int]:
    """Aplica correcoes geometricas cirurgicas para casos conhecidos de colisao."""
    modificacoes = 0

    # --------------------------------------------------------------------------
    # CASO 1: Setores Polares Circulares (ex.: Figura 2.4)
    # Raio R em pos=0.82 para afastar verticalmente do arco central theta
    # --------------------------------------------------------------------------
    if "fig:2.4" in content or "cap02" in filename:
        content = re.sub(
            r"\\draw\[thick\]\s*\(0,0\)\s*--\s*\(70:1\.2\)[^;]*;",
            r"\\draw[thick] (0,0) -- (70:1.2) node[pos=0.82, right=3pt, fill=white, inner sep=1pt] {$R$};",
            content
        )
        content = re.sub(
            r"\\draw\[thick\]\s*\(0,0\)\s*--\s*\(110:1\.2\)[^;]*;",
            r"\\draw[thick] (0,0) -- (110:1.2) node[pos=0.82, left=3pt, fill=white, inner sep=1pt] {$R$};",
            content
        )
        content = re.sub(
            r"\\draw\[<->\]\s*\(70:[0-9.]+\)\s*arc\s*\(70:110:[0-9.]+\);",
            r"\\draw[<->] (70:0.35) arc (70:110:0.35);",
            content
        )
        content = re.sub(
            r"\\node(?:\[[^\]]*\])?\s*at\s*\(90:[0-9.]+\)\s*\{\\theta\};",
            r"\\node[fill=white, inner sep=0.8pt] at (90:0.48) {$\\theta$};",
            content
        )
        modificacoes += 1

    # --------------------------------------------------------------------------
    # CASO 2: Hierarquia de Cotas em Eixos Cartesianos (Figura 2.7)
    # Cotas em y=-0.4 colidindo com abscissas a e a+2m -> rebaixar para y=-0.65
    # --------------------------------------------------------------------------
    if "fig:2.7" in content or "cap02" in filename:
        old_cota_27_1 = r"\draw[<->] (0.6,-0.4) -- (1.6,-0.4) node[midway, below] {\footnotesize $m$};"
        new_cota_27_1 = r"\draw[<->] (0.6,-0.65) -- (1.6,-0.65) node[midway, below, fill=white, inner sep=1pt] {\footnotesize $m$};"
        if old_cota_27_1 in content:
            content = content.replace(old_cota_27_1, new_cota_27_1)
            modificacoes += 1

        old_cota_27_2 = r"\draw[<->] (1.6,-0.4) -- (2.6,-0.4) node[midway, below] {\footnotesize $m$};"
        new_cota_27_2 = r"\draw[<->] (1.6,-0.65) -- (2.6,-0.65) node[midway, below, fill=white, inner sep=1pt] {\footnotesize $m$};"
        if old_cota_27_2 in content:
            content = content.replace(old_cota_27_2, new_cota_27_2)
            modificacoes += 1

    # --------------------------------------------------------------------------
    # CASO 3: Destacando o Trapézio APQB (Figura 2.8)
    # Cotas em y=-0.48 colidindo com P, S, Q em y=0 -> rebaixar para y=-0.68
    # --------------------------------------------------------------------------
    if "fig:2.8" in content or "cap02" in filename:
        old_cota_28_1 = r"\draw[<->] (0.8,-0.48) -- (2.0,-0.48) node[midway, below] {\footnotesize $m$};"
        new_cota_28_1 = r"\draw[<->] (0.8,-0.68) -- (2.0,-0.68) node[midway, below, fill=white, inner sep=1pt] {\footnotesize $m$};"
        if old_cota_28_1 in content:
            content = content.replace(old_cota_28_1, new_cota_28_1)
            modificacoes += 1

        old_cota_28_2 = r"\draw[<->] (2.0,-0.48) -- (3.2,-0.48) node[midway, below] {\footnotesize $m$};"
        new_cota_28_2 = r"\draw[<->] (2.0,-0.68) -- (3.2,-0.68) node[midway, below, fill=white, inner sep=1pt] {\footnotesize $m$};"
        if old_cota_28_2 in content:
            content = content.replace(old_cota_28_2, new_cota_28_2)
            modificacoes += 1

    # --------------------------------------------------------------------------
    # CASO 4: Formulas de Area em Regioes Secantes (Figura 2.9)
    # A = m^3 posicionado no baricentro do triangulo (1.95, 1.34) com fundo protetor
    # --------------------------------------------------------------------------
    if "fig:2.9" in content or "cap02" in filename:
        content = re.sub(
            r"\\node(?:\[[^\]]*\])?\s*at\s*\(1\.9,\s*1\.[0-9]+\)\s*\{\\bfseries\s*\$A\s*=\s*m\^3\$\};",
            r"\\node[fill=white, inner sep=1.4pt, font=\\footnotesize\\bfseries] at (1.95, 1.34) {$A = m^3$};",
            content
        )
        modificacoes += 1

        old_cota_29_1 = r"\draw[<->] (0.8,-0.2) -- (2.0,-0.2) node[midway, below] {\footnotesize $m$};"
        new_cota_29_1 = r"\draw[<->] (0.8,-0.55) -- (2.0,-0.55) node[midway, below, fill=white, inner sep=1pt] {\footnotesize $m$};"
        if old_cota_29_1 in content:
            content = content.replace(old_cota_29_1, new_cota_29_1)
            modificacoes += 1

        old_cota_29_2 = r"\draw[<->] (2.0,-0.2) -- (3.2,-0.2) node[midway, below] {\footnotesize $m$};"
        new_cota_29_2 = r"\draw[<->] (2.0,-0.55) -- (3.2,-0.55) node[midway, below, fill=white, inner sep=1pt] {\footnotesize $m$};"
        if old_cota_29_2 in content:
            content = content.replace(old_cota_29_2, new_cota_29_2)
            modificacoes += 1

    # --------------------------------------------------------------------------
    # CASO 5: Vertices com Projecoes e Secantes (Figuras 2.10 e 2.11)
    # Evitar que o prolongamento da secante atravesse os rotulos de A e B
    # --------------------------------------------------------------------------
    if ("fig:2.10" in content or "fig:2.11" in content or "cap02" in filename):
        content = re.sub(
            r"\\fill\s*\(A\)\s*circle\s*\([0-9.]+pt\)\s*node\[left(?:,\s*[^\]]*)?\]\s*\{\$A\$\};",
            r"\\fill (A) circle (1.5pt) node[above left=1pt, fill=white, inner sep=1pt] {$A$};",
            content
        )
        content = re.sub(
            r"\\fill\s*\(B\)\s*circle\s*\([0-9.]+pt\)\s*node\[right(?:,\s*[^\]]*)?\]\s*\{\$B\$\};",
            r"\\fill (B) circle (1.5pt) node[above right=1pt, fill=white, inner sep=1pt] {$B$};",
            content
        )
        content = re.sub(
            r"\\fill\s*\(N\)\s*circle\s*\([0-9.]+pt\)\s*node\[below right(?:,\s*[^\]]*)?\]\s*\{\$N\$\};",
            r"\\fill (N) circle (1.5pt) node[below right=2pt, fill=white, inner sep=1pt] {$N$};",
            content
        )
        modificacoes += 1

    # --------------------------------------------------------------------------
    # CASO 6: Circulo Trigonometrico (Figura 3.12)
    # --------------------------------------------------------------------------
    if "fig:3.12" in content or "cap03" in filename:
        # Se contiver a versao antiga com sin(x) colidindo
        if r"\node[above, font=\footnotesize, blue!80!black] at ({cos(38)/2}" in content:
            content = content.replace(
                r"\node[above, font=\footnotesize, blue!80!black] at ({cos(38)/2}",
                r"\node[left, font=\footnotesize, blue!80!black, fill=white, inner sep=1.2pt] at ({cos(38)-0.02}"
            )
            modificacoes += 1

    return content, modificacoes


def processar_capitulos(capitulos_dir: Path) -> dict:
    """Varre todos os capitulos .tex, aplicando auto-cura em figuras e TikZ."""
    stats = {
        "arquivos_processados": 0,
        "figuras_normalizadas": 0,
        "ajustes_geometricos": 0,
        "nos_com_fundo": 0
    }

    tex_files = sorted(list(capitulos_dir.glob("*.tex")))
    print(f"[AUDITORIA] Analisando {len(tex_files)} arquivos em '{capitulos_dir}'...")

    for tex_path in tex_files:
        stats["arquivos_processados"] += 1
        with open(tex_path, "r", encoding="utf-8") as f:
            original = f.read()

        modificado = original

        # 1. Normalizar figuras avulsas
        modificado, n_norm = normalizar_figuras_avulsas(modificado)
        stats["figuras_normalizadas"] += n_norm

        # 2. Desobstrucao geometrica especifica
        modificado, n_geo = desobstruir_geometria_especifica(modificado, tex_path.name)
        stats["ajustes_geometricos"] += n_geo

        # 3. Aplicar fundo protetor dentro de blocos tikzpicture
        pattern_tikz = re.compile(r"(\\begin\{tikzpicture\}(?:\[.*?\])?)(.*?)(\\end\{tikzpicture\})", re.DOTALL)

        def repl_tikz(match):
            nonlocal stats
            header = match.group(1)
            body = match.group(2)
            footer = match.group(3)
            new_body, n_nodes = injetar_fundo_protetor_em_nos(body)
            stats["nos_com_fundo"] += n_nodes
            return f"{header}{new_body}{footer}"

        modificado = pattern_tikz.sub(repl_tikz, modificado)

        # Salva apenas se houve mudanca real
        if modificado != original:
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(modificado)
            print(f"  [CURA] {tex_path.name}: atualizado com sucesso.")

    return stats


# ==============================================================================
# MODULO DE RENDERIZACAO DE AUDITORIA VISUAL (REVIEW GALLERY)
# ==============================================================================

def renderizar_galeria_auditoria(pdf_path: Path, review_dir: Path, targets: list[str] | None = None, dpi: int = 300) -> list[dict]:
    """Renderiza paginas contendo figuras em PNG de alta resolucao."""
    if not fitz:
        print("[AVISO] PyMuPDF (fitz) nao encontrado. Renderizacao visual ignorada.")
        return []

    if not pdf_path.exists():
        print(f"[ERRO] Arquivo PDF '{pdf_path}' nao encontrado.")
        return []

    review_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)
    print(f"[GALERIA] Inspecionando PDF ({total_pages} paginas) em '{pdf_path}'...")

    galeria_relatorio = []
    paginas_alvo = set()

    # Mapeia quais paginas contem "Figura"
    for page_idx in range(total_pages):
        page = doc.load_page(page_idx)
        text = page.get_text()

        encontrou = False
        fig_refs = []

        # Procura por "Figura X.Y"
        matches = re.findall(r"Figura\s+(\d+\.\d+)", text)
        if matches:
            encontrou = True
            fig_refs = matches

        if targets:
            # Se filtrou alvos especificos
            if any(t in fig_refs for t in targets):
                paginas_alvo.add((page_idx, tuple(fig_refs)))
        else:
            if encontrou:
                paginas_alvo.add((page_idx, tuple(fig_refs)))

    print(f"[GALERIA] Renderizando {len(paginas_alvo)} paginas selecionadas em {dpi} DPI...")

    for page_idx, figs in sorted(list(paginas_alvo)):
        num_pag = page_idx + 1
        page = doc.load_page(page_idx)
        pix = page.get_pixmap(dpi=dpi)

        fig_str = "_".join(figs) if figs else "geral"
        png_name = f"page_{num_pag:03d}_fig_{fig_str}.png"
        png_path = review_dir / png_name
        pix.save(str(png_path))

        galeria_relatorio.append({
            "pagina": num_pag,
            "figuras": list(figs),
            "arquivo": png_name,
            "path": str(png_path)
        })
        print(f"  [RENDER] Pagina {num_pag} (Figuras {figs}) -> {png_name}")

    # Cria relatorio Markdown da galeria
    index_md = review_dir / "INDEX.md"
    with open(index_md, "w", encoding="utf-8") as f:
        f.write("# Galeria de Auditoria Visual de Figuras\n\n")
        f.write(f"Total de paginas auditadas: {len(galeria_relatorio)}\n\n")
        f.write("| Pagina PDF | Figuras Detectadas | Miniatura PNG |\n")
        f.write("| :---: | :--- | :--- |\n")
        for item in galeria_relatorio:
            figs_txt = ", ".join(item["figuras"]) if item["figuras"] else "N/A"
            f.write(f"| {item['pagina']} | {figs_txt} | [{item['arquivo']}]({item['arquivo']}) |\n")

    print(f"[GALERIA] Indice gerado em '{index_md}'.")
    return galeria_relatorio


# ==============================================================================
# EXECUCAO PRINCIPAL
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Auditoria e Auto-Cura Geometrica de Figuras TikZ (book-resurrect)"
    )
    parser.add_argument(
        "--capitulos",
        type=str,
        default="capitulos",
        help="Diretorio contendo os capitulos .tex (padrao: capitulos)"
    )
    parser.add_argument(
        "--pdf",
        type=str,
        default="build/main.pdf",
        help="Caminho do PDF compilado (padrao: build/main.pdf)"
    )
    parser.add_argument(
        "--review-dir",
        type=str,
        default="build/figures_review",
        help="Pasta de destino para galeria PNG (padrao: build/figures_review)"
    )
    parser.add_argument(
        "--targets",
        type=str,
        default="",
        help="Lista de figuras alvo separadas por virgula (ex: 2.4,2.7,2.9,2.11,3.12)"
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=250,
        help="Resolucao DPI para renderizacao de auditoria (padrao: 250)"
    )
    parser.add_argument(
        "--skip-render",
        action="store_true",
        help="Pular a etapa de renderizacao PNG do PDF"
    )

    args = parser.parse_args()

    capitulos_dir = Path(args.capitulos)
    if not capitulos_dir.exists():
        print(f"[ERRO] Diretorio de capitulos '{capitulos_dir}' nao encontrado.")
        sys.exit(1)

    print("=================================================================")
    print("book-resurrect: Auditoria Visual e Auto-Cura Geometrica de TikZ")
    print("=================================================================")

    # 1. Processar capitulos
    stats = processar_capitulos(capitulos_dir)
    print("\n[RESULTADO DA AUTO-CURA]")
    print(f"- Arquivos analisados: {stats['arquivos_processados']}")
    print(f"- Figuras avulsas normalizadas: {stats['figuras_normalizadas']}")
    print(f"- Ajustes geometricos especificos: {stats['ajustes_geometricos']}")
    print(f"- Nos com fundo protetor aplicado: {stats['nos_com_fundo']}")

    # 2. Renderizar auditoria visual
    if not args.skip_render:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            # Fallback para main.pdf na raiz se build/main.pdf nao existir
            if Path("main.pdf").exists():
                pdf_path = Path("main.pdf")

        targets_list = [t.strip() for t in args.targets.split(",") if t.strip()] if args.targets else None
        review_dir = Path(args.review_dir)
        renderizar_galeria_auditoria(pdf_path, review_dir, targets=targets_list, dpi=args.dpi)

    print("\nAuditoria e auto-cura concluidas com sucesso.")


if __name__ == "__main__":
    main()
