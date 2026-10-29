#!/usr/bin/env python3
"""
setup_env.py — Inicializador e verificador de ambiente do book-resurrect.

Responsabilidades:
1. Verificar se PyMuPDF (fitz) e Pillow (PIL) estão instalados; caso contrário,
   instalá-los via pip.
2. Verificar se o compilador LaTeX portátil Tectonic está disponível no PATH
   ou em ./bin/tectonic(.exe). Caso não esteja, baixar automaticamente o binário
   oficial da API de Releases do GitHub (tectonic-typesetting/tectonic) e extraí-lo
   em ./bin/.
"""

import argparse
import importlib.util
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
BIN_DIR = WORKSPACE_ROOT / "bin"

FALLBACK_VERSION = "0.15.0"
FALLBACK_BASE_URL = (
    f"https://github.com/tectonic-typesetting/tectonic/releases/download/"
    f"tectonic%40{FALLBACK_VERSION}"
)


def check_and_install_python_deps() -> bool:
    """Verifica e instala pymupdf (fitz) e pillow (PIL) caso ausentes."""
    missing = []
    if importlib.util.find_spec("fitz") is None:
        missing.append("pymupdf")
    if importlib.util.find_spec("PIL") is None:
        missing.append("pillow")

    if not missing:
        print("[OK] Dependências Python verificadas: PyMuPDF (fitz) e Pillow (PIL).")
        return True

    print(f"[INFO] Instalando pacotes Python ausentes: {', '.join(missing)}...")
    cmd = [sys.executable, "-m", "pip", "install", *missing]
    try:
        subprocess.run(cmd, check=True)
        print("[OK] Pacotes Python instalados com sucesso.")
        return True
    except subprocess.CalledProcessError as exc:
        print(
            f"[ERRO] Falha ao instalar pacotes Python ({', '.join(missing)}): {exc}",
            file=sys.stderr,
        )
        return False


def get_local_tectonic_path() -> Path:
    """Retorna o caminho esperado para o binário portátil do Tectonic em ./bin/."""
    exe_name = "tectonic.exe" if platform.system().lower() == "windows" else "tectonic"
    return BIN_DIR / exe_name


def find_tectonic_binary() -> str | None:
    """Procura pelo executável tectonic em ./bin/ ou no PATH do sistema."""
    local_bin = get_local_tectonic_path()
    if local_bin.is_file():
        return str(local_bin)

    system_bin = shutil.which("tectonic")
    if system_bin:
        return system_bin

    return None


def _select_target_suffix() -> tuple[str, str]:
    """Determina o sufixo de plataforma e o nome do arquivo fallback do Tectonic."""
    sys_name = platform.system().lower()
    machine = platform.machine().lower()

    if sys_name == "windows":
        return (
            "x86_64-pc-windows-msvc.zip",
            f"tectonic-{FALLBACK_VERSION}-x86_64-pc-windows-msvc.zip",
        )
    if sys_name == "darwin":
        if machine in ("arm64", "aarch64"):
            return (
                "aarch64-apple-darwin.tar.gz",
                f"tectonic-{FALLBACK_VERSION}-aarch64-apple-darwin.tar.gz",
            )
        return (
            "x86_64-apple-darwin.tar.gz",
            f"tectonic-{FALLBACK_VERSION}-x86_64-apple-darwin.tar.gz",
        )
    # Linux
    if machine in ("arm64", "aarch64"):
        return (
            "aarch64-unknown-linux-musl.tar.gz",
            f"tectonic-{FALLBACK_VERSION}-aarch64-unknown-linux-musl.tar.gz",
        )
    return (
        "x86_64-unknown-linux-musl.tar.gz",
        f"tectonic-{FALLBACK_VERSION}-x86_64-unknown-linux-musl.tar.gz",
    )


def _resolve_download_url() -> str:
    """Consulta a API do GitHub Releases ou retorna a URL oficial estável de fallback."""
    target_suffix, fallback_filename = _select_target_suffix()
    api_url = "https://api.github.com/repos/tectonic-typesetting/tectonic/releases?per_page=10"

    req = urllib.request.Request(
        api_url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "book-resurrect-setup"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            releases = json.loads(resp.read().decode("utf-8"))
            for rel in releases:
                for asset in rel.get("assets", []):
                    name = asset.get("name", "")
                    if name.endswith(target_suffix):
                        return asset["browser_download_url"]
    except Exception as exc:
        print(f"[AVISO] Não foi possível consultar a API do GitHub ({exc}). Usando URL estável.")

    return f"{FALLBACK_BASE_URL}/{fallback_filename}"


def download_and_extract_tectonic() -> Path | None:
    """Baixa e extrai o binário portátil do Tectonic para ./bin/."""
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    download_url = _resolve_download_url()
    print(f"[INFO] Baixando Tectonic portátil de: {download_url}")

    req = urllib.request.Request(
        download_url, headers={"User-Agent": "book-resurrect-setup"}
    )
    suffix = ".zip" if download_url.endswith(".zip") else ".tar.gz"

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_path = Path(tmp_file.name)
            with urllib.request.urlopen(req, timeout=60) as response:
                shutil.copyfileobj(response, tmp_file)
    except urllib.error.URLError as exc:
        print(f"[ERRO] Falha no download do Tectonic: {exc}", file=sys.stderr)
        return None

    target_bin = get_local_tectonic_path()
    try:
        if suffix == ".zip":
            with zipfile.ZipFile(tmp_path, "r") as zf:
                for member in zf.namelist():
                    if Path(member).name.lower() in ("tectonic.exe", "tectonic"):
                        with zf.open(member) as src, open(target_bin, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                        break
        else:
            with tarfile.open(tmp_path, "r:gz") as tf:
                for member in tf.getmembers():
                    if Path(member.name).name in ("tectonic", "tectonic.exe"):
                        extracted = tf.extractfile(member)
                        if extracted is not None:
                            with extracted as src, open(target_bin, "wb") as dst:
                                shutil.copyfileobj(src, dst)
                            break

        if target_bin.is_file() and platform.system().lower() != "windows":
            target_bin.chmod(target_bin.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

        if target_bin.is_file():
            print(f"[OK] Tectonic extraído com sucesso em: {target_bin}")
            return target_bin
        print("[ERRO] Arquivo baixado não continha o executável tectonic.", file=sys.stderr)
        return None
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def verify_tectonic(bin_path: str) -> bool:
    """Executa `tectonic --version` para confirmar que o binário está operacional."""
    try:
        res = subprocess.run(
            [bin_path, "--version"],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
        version_str = res.stdout.strip() or res.stderr.strip()
        print(f"[OK] Compilador Tectonic operacional: {version_str} ({bin_path})")
        return True
    except Exception as exc:
        print(f"[ERRO] Falha ao executar Tectonic ({bin_path}): {exc}", file=sys.stderr)
        return False


def ensure_workspace_structure(init_dirs: bool = False) -> None:
    """Opcionalmente inicializa as pastas capitulos/, figuras/, build/ e templates na raiz."""
    if not init_dirs:
        return

    for folder in ("capitulos", "figuras", "build"):
        folder_path = WORKSPACE_ROOT / folder
        folder_path.mkdir(parents=True, exist_ok=True)

    templates_dir = WORKSPACE_ROOT / "templates"
    for tex_name in ("main.tex", "preambulo.tex"):
        src = templates_dir / tex_name
        dst = WORKSPACE_ROOT / tex_name
        if src.is_file() and not dst.exists():
            shutil.copy2(src, dst)
            print(f"[OK] Template copiado para a raiz: {tex_name}")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Verifica e instala PyMuPDF, Pillow e o compilador portátil Tectonic."
    )
    parser.add_argument(
        "--init-workspace",
        action="store_true",
        help="Cria as pastas capitulos/, figuras/, build/ e copia main.tex/preambulo.tex se ausentes.",
    )
    args = parser.parse_args()

    print("=== book-resurrect: Verificação de Ambiente ===")
    deps_ok = check_and_install_python_deps()

    tectonic_bin = find_tectonic_binary()
    if not tectonic_bin:
        print("[INFO] Tectonic não encontrado no PATH ou em ./bin/. Iniciando download portátil...")
        downloaded = download_and_extract_tectonic()
        if downloaded:
            tectonic_bin = str(downloaded)

    tectonic_ok = False
    if tectonic_bin:
        tectonic_ok = verify_tectonic(tectonic_bin)
    else:
        latexmk_bin = shutil.which("latexmk")
        if latexmk_bin:
            print(f"[AVISO] Tectonic indisponível, mas fallback latexmk detectado: {latexmk_bin}")
            tectonic_ok = True
        else:
            print(
                "[ERRO] Nenhum compilador LaTeX (tectonic ou latexmk) disponível.",
                file=sys.stderr,
            )

    ensure_workspace_structure(init_dirs=args.init_workspace)

    if deps_ok and tectonic_ok:
        print("=== Ambiente pronto para o book-resurrect! ===")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
