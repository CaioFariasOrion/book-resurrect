# CONTEXT.md: Quadro de Bordo e Rastreabilidade (`book-resurrect`)

## 1. Metadados e Propósito do Projeto
- **Objetivo:** Engenharia reversa editorial, tradução e recuperação acessível de livros escaneados (PDF) para um único pipeline em LaTeX compilado em PDF pelo Tectonic, com suporte aos perfis `tecnico` (exatas/TikZ) e `texto` (humanas/texto corrido).
- **Repositório:** `book-resurrect`
- **Natureza deste workspace:** framework/motor universal limpo. Nenhum livro de estudo de caso deve permanecer dentro desta pasta.

## 2. Regra de Governança de Estado (Obrigatória para Agentes)
- **Leitura no Início do Turno:** Antes de executar qualquer comando, leia `CONTEXT.md` (e, em pastas de livros, `metadata.yaml`, `roadmap.json` e `progress.json`).
- **Escrita no Fim do Turno:** Ao concluir uma evolução estrutural ou lote, atualize o status correspondente.

## 3. Status Atual (Construído e Validado)
- [x] Pipeline unificado 100% em LaTeX (Tectonic) com saída exclusiva em PDF.
- [x] Preâmbulo modularizado em `templates/preambulo_base.tex`, `templates/perfil_tecnico.tex` e `templates/perfil_texto.tex`.
- [x] Abertura canônica universal nas páginas 1 a 4 (`\inserircapa`, `\folhaderosto`, `\manifestoeditorial` com `assets/logo-blue.png` e `\tableofcontents`).
- [x] Descarte obrigatório de pré-textuais comerciais anteriores ao sumário e proibição de transcrever o sumário impresso.
- [x] Fase 0 determinística em `scripts/init_book_fase0.py` (< 3s) com split automático de folha dupla via PyMuPDF e extração de `capa.png`.
- [x] Compilador único `scripts/compile_check.py` com linter editorial estático (`--lint`) e compilação atômica (`--only`).
- [x] Fase 4 para o perfil `tecnico` com `scripts/render_isolated_figures.py` (cache SHA-256 e lock de manifesto) e `scripts/audit_and_fix_tikz.py` (transparência 100% natural, sem `fill=white`).
- [x] Sincronizador `instalar_skills.py` com carregamento dinâmico dos arquivos do repositório.

## 4. Próximo Passo Imediato (Foco Ativo)
- [x] Motor unificado em LaTeX concluído e pronto para validação em estudos de caso externos.

## 5. Protocolo de Validação (Definition of Done)
Nenhum lote ou livro pode ser considerado concluído sem cumprir:
1. **Lint Editorial Limpo:** `python scripts/compile_check.py --lint-only` sem alertas de escape (`%`, `&`, `#`, `_`), sem `\chapter` duplicado, sem número manual no título e sem macros proibidas no perfil.
2. **Compilação Limpa:** `python scripts/compile_check.py --lint` retornando `exit code 0` e gerando o PDF final.
3. **Inspeção Visual Página a Página:** Capa na pág. 1, Folha de Rosto com chancela na pág. 2, Manifesto com logo na pág. 3, Sumário automático clicável na pág. 4 e capítulos íntegros.
