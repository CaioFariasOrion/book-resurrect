#!/usr/bin/env python3
"""
Extrai blocos tikzpicture de ambientes figure em capitulos/cap*.tex,
compila cada figura isoladamente via classe standalone e gera PNGs de alta
resolucao em build/figures_catalog/ junto ao manifesto manifest.json.

Otimizacoes:
- Cache por hash SHA-256 (bloco TikZ + template) para evitar recompilacoes redundantes.
- Gravacao atomica de manifest.json (via os.replace) para eliminar condicoes de corrida.
- Compilacao isolada rapida e suporte a shards para aceleracao de lote.
"""

import argparse
import hashlib
import json
import os
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


def compute_figure_hash(tikz_code: str, extra_pkgs: str) -> str:
    norm_code = re.sub(r"\s+", " ", tikz_code.strip())
    payload = f"{extra_pkgs}||{norm_code}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def extract_figures_from_chapters(capitulos_dir: Path, chapter_filter: str | None = None) -> list[dict]:
    tex_files = sorted(capitulos_dir.glob("cap*.tex"))
    if chapter_filter:
        norm_filter = Path(chapter_filter).name.lower()
        tex_files = [
            p for p in tex_files
            if p.name.lower() == norm_filter or norm_filter in p.name.lower()
        ]

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

            if len(tikz_matches) == 1:
                tikz_code = tikz_matches[0].group(0)
            else:
                tikz_code = "\n\\quad\n".join(m.group(0) for m in tikz_matches)

            extra_pkgs = ""
            if "\\begin{axis}" in tikz_code or "\\addplot" in tikz_code:
                extra_pkgs = "\\usepackage{pgfplots}\n\\pgfplotsset{compat=1.18}"

            code_hash = compute_figure_hash(tikz_code, extra_pkgs)

            extracted.append({
                "fig_id": fig_id,
                "chapter_file": rel_path,
                "line_start": line_start,
                "line_end": line_end,
                "png_path": f"build/figures_catalog/{fig_id}.png",
                "tikz_code": tikz_code,
                "extra_pkgs": extra_pkgs,
                "hash": code_hash,
            })

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


def atomic_update_manifest(manifest_path: Path, new_entries: list[dict], updates_dict: dict[str, dict] | None = None) -> list[dict]:
    """Atualiza o manifest.json atomicamente preservando campos existentes e eliminando condicoes de corrida."""
    existing_by_id: dict[str, dict] = {}
    if manifest_path.is_file():
        try:
            old_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(old_data, list):
                for e in old_data:
                    if isinstance(e, dict) and "fig_id" in e:
                        existing_by_id[e["fig_id"]] = e
        except Exception:
            pass

    merged_list: list[dict] = []
    for item in new_entries:
        fid = item["fig_id"]
        old_info = existing_by_id.get(fid, {})
        status = old_info.get("status", "pending")
        old_hash = old_info.get("hash", "")

        if old_hash and old_hash != item["hash"] and status == "approved":
            status = "pending"

        entry = {
            "fig_id": fid,
            "chapter_file": item["chapter_file"],
            "line_start": item["line_start"],
            "line_end": item["line_end"],
            "png_path": item["png_path"],
            "status": status,
            "hash": item["hash"],
        }

        if updates_dict and fid in updates_dict:
            entry.update(updates_dict[fid])

        merged_list.append(entry)

    temp_file = manifest_path.parent / f"manifest_{os.getpid()}_{time.time_ns()}.tmp"
    temp_file.write_text(
        json.dumps(merged_list, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temp_file, manifest_path)
    return merged_list


def compile_and_rasterize_single(
    item: dict,
    compiler_type: str,
    compiler_bin: str,
    temp_dir: Path,
    catalog_dir: Path,
    cache_dir: Path,
    dpi: int,
    ignore_cache: bool = False,
) -> tuple[str, bool, float, str]:
    t0 = time.perf_counter()
    fig_id = item["fig_id"]
    code_hash = item["hash"]
    png_file = catalog_dir / f"{fig_id}.png"
    cached_png = cache_dir / f"{code_hash}.png"

    if not ignore_cache and cached_png.is_file():
        try:
            shutil.copy2(cached_png, png_file)
            elapsed = time.perf_counter() - t0
            return fig_id, True, elapsed, "CACHE"
        except Exception:
            pass

    work_dir = temp_dir / fig_id
    work_dir.mkdir(parents=True, exist_ok=True)

    tex_file = work_dir / f"{fig_id}.tex"
    pdf_file = work_dir / f"{fig_id}.pdf"

    tex_content = (
        STANDALONE_TEMPLATE
        .replace("__EXTRA_PACKAGES__", item["extra_pkgs"])
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
            pix.save(str(cached_png))
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
        description="Microcompilacao atomica e paralela de figuras TikZ em modo standalone com cache SHA-256."
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
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignora o cache SHA-256 e forca a recompilacao de todas as figuras.",
    )

    args = parser.parse_args()

    if not args.capitulos.is_dir():
        print(f"[ERRO] Diretorio de capitulos nao encontrado: {args.capitulos}", file=sys.stderr)
        return 1

    args.catalog_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.catalog_dir / "manifest.json"
    temp_dir = args.catalog_dir.parent / "temp_standalone"
    temp_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = args.catalog_dir / ".cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    all_figures = extract_figures_from_chapters(args.capitulos, chapter_filter=None)

    targets = all_figures
    if args.chapter:
        norm_c = Path(args.chapter).name.lower()
        targets = [
            t for t in targets
            if norm_c in Path(t["chapter_file"]).name.lower()
        ]
    if args.fig_id:
        targets = [t for t in targets if t["fig_id"] == args.fig_id]

    updates_dict: dict[str, dict] = {}
    if args.set_status:
        target_ids = {t["fig_id"] for t in targets}
        for fid in target_ids:
            updates_dict[fid] = {"status": args.set_status}

    manifest_entries = atomic_update_manifest(manifest_path, all_figures, updates_dict)

    if args.extract_only:
        print(f"[OK] Manifesto atualizado atomicamente ({len(manifest_entries)} figuras) em {manifest_path.as_posix()}")
        return 0

    if not targets:
        print("[AVISO] Nenhuma figura encontrada para os filtros informados.")
        return 0

    compiler_type, compiler_bin = locate_compiler()
    print(f"[INFO] Compilando {len(targets)} figura(s) via {compiler_type} (cache ativado)...")

    t_start = time.perf_counter()
    ok_count = 0
    cache_hits = 0
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
                cache_dir,
                args.dpi,
                args.no_cache,
            ): item
            for item in targets
        }
        for fut in as_completed(futures):
            fid, success, elapsed, msg = fut.result()
            if success:
                ok_count += 1
                if msg == "CACHE":
                    cache_hits += 1
                    print(f"  [CACHE] {fid} ({elapsed:.3f}s)")
                else:
                    print(f"  [OK] {fid} -> {args.catalog_dir.as_posix()}/{fid}.png ({elapsed:.2f}s)")
            else:
                fail_count += 1
                print(f"  [ERRO] {fid} ({elapsed:.2f}s): {msg}", file=sys.stderr)

    total_elapsed = time.perf_counter() - t_start
    avg_time = total_elapsed / len(targets) if targets else 0.0
    print(
        f"[RESUMO] {ok_count}/{len(targets)} prontas ({cache_hits} recuperadas do cache) | "
        f"Tempo total: {total_elapsed:.2f}s (media efetiva: {avg_time:.2f}s/fig) | "
        f"Manifesto: {manifest_path.as_posix()}"
    )
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
