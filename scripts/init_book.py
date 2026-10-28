#!/usr/bin/env python3
"""
init_book.py: provisiona a pasta de um novo livro a partir do repositório book-resurrect.

Cria a estrutura de pastas, copia scripts, templates, a skill e os adaptadores de IDE,
copia o PDF de origem e gera um CONTEXT.md pronto para a Triagem Interativa.
"""

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SUBDIRS = ("capitulos", "figuras", "build", "scripts", "templates", "assets")

# Itens que fazem a skill funcionar nas IDEs; sem eles a pasta nova não ativa o protocolo.
SKILL_ITEMS = (".agent", ".cursor", ".github", "CLAUDE.md", ".windsurfrules", ".gitignore")

CONTEXT_TEMPLATE = """# CONTEXT.md: Quadro de Bordo do Livro (`{pdf_name}`)

## 1. Metadados e Propósito do Projeto
- **Objetivo:** recuperar o livro `{pdf_name}` a partir do PDF escaneado usando a skill `book-resurrect`.
- **Natureza deste workspace:** pasta de um único livro, provisionada por `scripts/init_book.py`.

## 2. Regra de Governança de Estado (Obrigatória para Agentes)
- **Leitura no Início do Turno:** Antes de executar qualquer comando ou responder ao usuário, leia `CONTEXT.md`. Se existirem, leia também `roadmap.json` e `progress.json` (estado micro dos lotes de páginas).
- **Escrita no Fim do Turno:** Antes de encerrar o turno após concluir uma entrega ou lote, atualize a seção "Status Atual", o "Próximo Passo Imediato" e os checkboxes do "Backlog Priorizado" neste arquivo.

## 3. Status Atual (Construído e Validado)
- [x] Pasta provisionada com `capitulos/`, `figuras/`, `build/`, `scripts/` e `templates/`.
- [x] PDF de origem copiado para a raiz: `{pdf_name}`.

## 4. Próximo Passo Imediato (Foco Ativo)
- [ ] Executar a Triagem Interativa (Pré-Fase 0) do `SKILL.md` para `{pdf_name}`.

## 5. Backlog Priorizado e Critérios de Aceite
- [ ] **Triagem Interativa:** responder as 3 perguntas e gravar `project_mode`, `translation_mode` e `figure_mode` no `roadmap.json`.
- [ ] **Fase 0:** `python scripts/setup_env.py`, mapeamento do sumário e geração de `roadmap.json` e `progress.json`.
- [ ] **Fases 1 e 2:** transcrição lote a lote, com validação de fechamento a cada lote.

## 6. Protocolo de Validação em Escala Menor (Definition of Done)
Nenhum lote pode ser marcado como concluído sem cumprir os critérios do modo escolhido na triagem:
1. **Modo LaTeX:** chaves `{{}}` balanceadas, `python scripts/compile_check.py` com `exit code 0` e inspeção visual das páginas compiladas.
2. **Modo Markdown:** sintaxe Markdown válida (notas `[^n]` com definição) e todos os caminhos `figuras/...` existentes.
"""


def copy_tree(src: Path, dst: Path) -> int:
    """Copia a pasta ignorando caches do Python e devolve o número de arquivos copiados."""
    copied = 0
    for item in sorted(src.rglob("*")):
        if "__pycache__" in item.parts or item.suffix == ".pyc":
            continue
        target = dst / item.relative_to(src)
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
            copied += 1
    return copied


def init_book(pdf: Path, dest: Path) -> dict:
    """Provisiona a pasta do livro e devolve um resumo do que foi criado."""
    if not pdf.is_file():
        raise FileNotFoundError(f"PDF de origem não encontrado: {pdf}")
    if pdf.suffix.lower() != ".pdf":
        raise ValueError(f"O arquivo de origem não é um PDF: {pdf.name}")

    dest = dest.resolve()
    if dest == REPO_ROOT:
        raise ValueError("O destino não pode ser a própria pasta do repositório book-resurrect.")
    if (dest / "roadmap.json").exists():
        raise FileExistsError(f"Já existe um livro em andamento em {dest} (roadmap.json presente).")

    dest.mkdir(parents=True, exist_ok=True)
    for name in SUBDIRS:
        (dest / name).mkdir(exist_ok=True)

    summary = {"scripts": 0, "templates": 0, "skill_items": [], "pdf": None, "context": None}
    summary["scripts"] = copy_tree(REPO_ROOT / "scripts", dest / "scripts")
    summary["templates"] = copy_tree(REPO_ROOT / "templates", dest / "templates")
    if (REPO_ROOT / "assets").is_dir():
        summary["assets"] = copy_tree(REPO_ROOT / "assets", dest / "assets")

    for name in SKILL_ITEMS:
        src = REPO_ROOT / name
        if src.is_dir():
            copy_tree(src, dest / name)
            summary["skill_items"].append(name + "/")
        elif src.is_file():
            shutil.copy2(src, dest / name)
            summary["skill_items"].append(name)

    pdf_dest = dest / pdf.name
    if pdf.resolve() != pdf_dest.resolve():
        shutil.copy2(pdf, pdf_dest)
    summary["pdf"] = pdf_dest

    context_path = dest / "CONTEXT.md"
    context_path.write_text(CONTEXT_TEMPLATE.format(pdf_name=pdf.name), encoding="utf-8")
    summary["context"] = context_path
    summary["dest"] = dest
    return summary


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Provisiona a pasta de um novo livro com scripts, templates, skill e CONTEXT.md."
    )
    parser.add_argument("--pdf", required=True, type=Path, help="Caminho do PDF do livro.")
    parser.add_argument("--dest", required=True, type=Path, help="Pasta de destino do novo livro.")
    args = parser.parse_args()

    try:
        summary = init_book(args.pdf, args.dest)
    except Exception as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1

    print("=== book-resurrect: Livro provisionado ===")
    print(f"[OK] Pasta do livro: {summary['dest']}")
    print(f"[OK] Estrutura criada: {', '.join(n + '/' for n in SUBDIRS)}")
    print(f"[OK] Scripts copiados: {summary['scripts']} | Templates copiados: {summary['templates']}")
    print(f"[OK] Skill e adaptadores: {', '.join(summary['skill_items']) or 'nenhum'}")
    print(f"[OK] PDF na raiz: {summary['pdf'].name}")
    print(f"[OK] CONTEXT.md criado: {summary['context'].name}")
    print("Próximo passo: abra a pasta na IDE e peça a Triagem Interativa do book-resurrect.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
