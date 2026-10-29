#!/usr/bin/env python3
"""
Extrai blocos tikzpicture de ambientes figure em capitulos/cap*.tex,
compila cada figura isoladamente via classe standalone e gera PNGs de alta
resolucao em build/figures_catalog/ junto ao manifesto manifest.json.
"""

import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
BIN_DIR = WORKSPACE_ROOT / "bin"

STANDALONE_TEMPLATE = r"""\documentclass[tikz,border=2pt]{standalone}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amssymb}
\usepackage{xcolor}
\definecolor{azuldef}{RGB}{26,54,93}
\definecolor{vinhoteo}{RGB}{114,28,36}
\definecolor{grafite}{RGB}{40,40,40}
\usetikzlibrary{arrows.meta,calc,positioning,patterns,angles,quotes,decorations.pathreplacing,shapes.geometric}
__EXTRA_PACKAGES__
\providecommand{\sen}{\sin}
\providecommand{\tg}{\tan}
\providecommand{\cotg}{\cot}
\providecommand{\cosec}{\csc}
\providecommand{\arctg}{\arctan}
\providecommand{\arcsen}{\arcsin}
\begin{document}
__TIKZ_BLOCK__
\end{document}
"""

FIGURE_ENV_RE = re.compile(
    r"\\begin\{figure\}(?:\[[^\]]*\])?.*?\\end\{figure\}",
    re.DOTALL,
)
TIKZ_ENV_RE = re.compile(
    r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}",
    re.DOTALL,
)
LABEL_FIG_RE = re.compile(r"\\label\{fig:([^}]+)\}")
CHAPTER_NUM_RE = re.compile(r"cap(\d+)", re.IGNORECASE)


def locate_compiler() -> tuple[str, str]:
    exe_name = "tectonic.exe" if platform.system().lower() == "windows" else "tectonic"
    local_tectonic = BIN_DIR / exe_name
    if local_tectonic.is_file():
        return "tectonic", str(local_tectonic)

    tectonic_bin = shutil.which("tectonic")
    if tectonic_bin:
        return "tectonic", tectonic_bin

    pdflatex_bin = shutil.which("pdflatex")
    if pdflatex_bin:
        return "pdflatex", pdflatex_bin

    raise RuntimeError("Nenhum compilador LaTeX encontrado (tectonic ou pdflatex).")


def derive_chapter_num(chapter_path: Path) -> int:
    m = CHAPTER_NUM_RE.search(chapter_path.stem)
    return int(m.group(1)) if m else 0


def extract_figures_from_chapters(capitulos_dir: Path, chapter_filter: str | None = None) -> list[dict]:
    tex_files = sorted(capitulos_dir.glob("cap*.tex"))
    if chapter_filter:
        norm_filter = Path(chapter_filter).name.lower()
        tex_files = [
            p for p in tex_files
            if p.name.lower() == norm_filter or norm_filter in p.name.lower()
        ]

    # Agrupa arquivos por numero de capitulo para numerar figuras sequencialmente dentro do capitulo
    chapter_counters: dict[int, int] = {}
    extracted: list[dict] = []

    for tex_path in tex_files:
        text = tex_path.read_text(encoding="utf-8", errors="replace")
        chap_num = derive_chapter_num(tex_path)
        rel_path = f"capitulos/{tex_path.name}"

        for fig_match in FIGURE_ENV_RE.finditer(text):
            fig_block = fig_match.group(0)
            tikz_matches = list(TIKZ_ENV_RE.finditer(fig_block))
            if not tikz_matches:
                continue

            line_start = text.count("\n", 0, fig_match.start()) + 1
            line_end = text.count("\n", 0, fig_match.end()) + 1

            chapter_counters[chap_num] = chapter_counters.get(chap_num, 0) + 1
            seq_idx = chapter_counters[chap_num]

            label_m = LABEL_FIG_RE.search(fig_block)
            fig_id = f"fig_{chap_num:02d}_{seq_idx:02d}"
            if label_m:
                raw_label = label_m.group(1).strip()
                num_m = re.match(r"^(\d+)[\._](\d+)$", raw_label)
                if num_m:
                    fig_id = f"fig_{int(num_m.group(1)):02d}_{int(num_m.group(2)):02d}"

            # Se houver mais de um tikzpicture no mesmo figure, empacota em tikz ou compila o bloco principal
            if len(tikz_matches) == 1:
                tikz_code = tikz_matches[0].group(0)
            else:
                tikz_code = "\n\\quad\n".join(m.group(0) for m in tikz_matches)

            extracted.append({
                "fig_id": fig_id,
                "chapter_file": rel_path,
                "line_start": line_start,
                "line_end": line_end,
                "png_path": f"build/figures_catalog/{fig_id}.png",
                "tikz_code": tikz_code,
            })

    # Desambiguacao caso rotulos se repitam
    seen_ids: dict[str, int] = {}
    for item in extracted:
        fid = item["fig_id"]
        if fid in seen_ids:
            seen_ids[fid] += 1
            new_id = f"{fid}_{seen_ids[fid]}"
            item["fig_id"] = new_id
            item["png_path"] = f"build/figures_catalog/{new_id}.png"
        else:
            seen_ids[fid] = 1

    return extracted


def compile_and_rasterize_single(
    item: dict,
    compiler_type: str,
    compiler_bin: str,
    temp_dir: Path,
    catalog_dir: Path,
    dpi: int,
) -> tuple[str, bool, float, str]:
    t0 = time.perf_counter()
    fig_id = item["fig_id"]
    work_dir = temp_dir / fig_id
    work_dir.mkdir(parents=True, exist_ok=True)

    tex_file = work_dir / f"{fig_id}.tex"
    pdf_file = work_dir / f"{fig_id}.pdf"
    png_file = catalog_dir / f"{fig_id}.png"

    extra_pkgs = ""
    if "\\begin{axis}" in item["tikz_code"] or "\\addplot" in item["tikz_code"]:
        extra_pkgs = "\\usepackage{pgfplots}\n\\pgfplotsset{compat=1.18}"

    tex_content = (
        STANDALONE_TEMPLATE
        .replace("__EXTRA_PACKAGES__", extra_pkgs)
        .replace("__TIKZ_BLOCK__", item["tikz_code"])
    )
    tex_file.write_text(tex_content, encoding="utf-8")

    if compiler_type == "tectonic":
        cmd = [compiler_bin, "--outdir", str(work_dir), str(tex_file)]
    else:
        cmd = [
            compiler_bin,
            "-interaction=nonstopmode",
            f"-output-directory={work_dir.as_posix()}",
            str(tex_file),
        ]

    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0 or not pdf_file.is_file():
        elapsed = time.perf_counter() - t0
        err_msg = (proc.stderr or proc.stdout or "Falha de compilacao").strip().splitlines()[-5:]
        return fig_id, False, elapsed, " | ".join(err_msg)

    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
        with fitz.open(pdf_file) as doc:
            page = doc.load_page(0)
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            pix.save(str(png_file))
    except Exception as exc:
        elapsed = time.perf_counter() - t0
        return fig_id, False, elapsed, f"Erro PyMuPDF: {exc}"

    elapsed = time.perf_counter() - t0
    return fig_id, True, elapsed, "OK"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Microcompilacao atomica de figuras TikZ em modo standalone e geracao de manifest.json."
    )
    parser.add_argument(
        "--capitulos",
        type=Path,
        default=Path("capitulos"),
        help="Diretorio contendo os arquivos cap*.tex (padrao: capitulos).",
    )
    parser.add_argument(
        "--catalog-dir",
        type=Path,
        default=Path("build/figures_catalog"),
        help="Diretorio de saida para os PNGs e manifest.json (padrao: build/figures_catalog).",
    )
    parser.add_argument(
        "--chapter",
        type=str,
        default=None,
        help="Filtra a compilacao para um arquivo de capitulo especifico (ex.: cap02).",
    )
    parser.add_argument(
        "--fig-id",
        type=str,
        default=None,
        help="Compila apenas uma figura especifica pelo seu fig_id (ex.: fig_02_04).",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=280,
        help="Resolucao DPI da rasterizacao PNG (padrao: 280).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Numero de threads paralelas para compilacao standalone (padrao: 8).",
    )
    parser.add_argument(
        "--set-status",
        type=str,
        choices=["pending", "approved"],
        default=None,
        help="Atualiza o status da(s) figura(s) selecionada(s) no manifest.json.",
    )
    parser.add_argument(
        "--extract-only",
        action="store_true",
        help="Apenas extrai o manifesto sem disparar a compilacao LaTeX.",
    )

    args = parser.parse_args()

    if not args.capitulos.is_dir():
        print(f"[ERRO] Diretorio de capitulos nao encontrado: {args.capitulos}", file=sys.stderr)
        return 1

    args.catalog_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.catalog_dir / "manifest.json"
    temp_dir = args.catalog_dir.parent / "temp_standalone"
    temp_dir.mkdir(parents=True, exist_ok=True)

    existing_status: dict[str, str] = {}
    if manifest_path.is_file():
        try:
            old_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(old_data, list):
                for entry in old_data:
                    if isinstance(entry, dict) and "fig_id" in entry and "status" in entry:
                        existing_status[entry["fig_id"]] = entry["status"]
        except Exception:
            pass

    all_figures = extract_figures_from_chapters(args.capitulos, chapter_filter=None)

    # Constroi lista de manifesto preservando status anterior
    manifest_entries: list[dict] = []
    for item in all_figures:
        fid = item["fig_id"]
        status = existing_status.get(fid, "pending")
        manifest_entries.append({
            "fig_id": fid,
            "chapter_file": item["chapter_file"],
            "line_start": item["line_start"],
            "line_end": item["line_end"],
            "png_path": item["png_path"],
            "status": status,
        })

    # Filtra quais figuras serao compiladas nesta execucao
    targets = all_figures
    if args.chapter:
        norm_c = Path(args.chapter).name.lower()
        targets = [
            t for t in targets
            if norm_c in Path(t["chapter_file"]).name.lower()
        ]
    if args.fig_id:
        targets = [t for t in targets if t["fig_id"] == args.fig_id]

    if args.set_status:
        target_ids = {t["fig_id"] for t in targets}
        for entry in manifest_entries:
            if entry["fig_id"] in target_ids:
                entry["status"] = args.set_status

    manifest_path.write_text(
        json.dumps(manifest_entries, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if args.extract_only:
        print(f"[OK] Manifesto atualizado com {len(manifest_entries)} figuras em {manifest_path.as_posix()}")
        return 0

    if not targets:
        print("[AVISO] Nenhuma figura encontrada para os filtros informados.")
        return 0

    compiler_type, compiler_bin = locate_compiler()
    print(f"[INFO] Compilando {len(targets)} figura(s) em modo standalone via {compiler_type}...")

    t_start = time.perf_counter()
    ok_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {
            pool.submit(
                compile_and_rasterize_single,
                item,
                compiler_type,
                compiler_bin,
                temp_dir,
                args.catalog_dir,
                args.dpi,
            ): item
            for item in targets
        }
        for fut in as_completed(futures):
            fid, success, elapsed, msg = fut.result()
            if success:
                ok_count += 1
                print(f"  [OK] {fid} -> {args.catalog_dir.as_posix()}/{fid}.png ({elapsed:.2f}s)")
            else:
                fail_count += 1
                print(f"  [ERRO] {fid} ({elapsed:.2f}s): {msg}", file=sys.stderr)

    total_elapsed = time.perf_counter() - t_start
    avg_time = total_elapsed / len(targets) if targets else 0.0
    print(
        f"[RESUMO] {ok_count}/{len(targets)} compiladas com sucesso | "
        f"Tempo total: {total_elapsed:.2f}s (media efetiva: {avg_time:.2f}s/fig) | "
        f"Manifesto: {manifest_path.as_posix()}"
    )
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
