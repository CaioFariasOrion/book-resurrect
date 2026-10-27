# Instruções para GitHub Copilot — `book-resurrect`

Este repositório implementa a skill universal **`book-resurrect`**, um pipeline autônomo de engenharia reversa e recuperação editorial de livros escaneados em PDF para LaTeX vetorial compilável.

Sempre que o usuário pedir para transcrever, digitalizar, converter ou recuperar um livro em PDF, iniciar um novo livro (`Fase 0`), ou continuar lotes pendentes do `progress.json` (*"Continue de onde parou"*, *"Execute os próximos N lotes"*), você **DEVE** carregar e seguir rigorosamente o protocolo mestre localizado em:

- **[`.agent/skills/book-resurrect/SKILL.md`](../.agent/skills/book-resurrect/SKILL.md)**

## Diretrizes Operacionais Essenciais

1. **Verificação de Estado (`roadmap.json` e `progress.json`)**:
   - Caso `roadmap.json` não exista na raiz, execute a **Fase 0** conforme detalhado em `.agent/skills/book-resurrect/SKILL.md`: rode `python scripts/setup_env.py`, copie `templates/main.tex` e `templates/preambulo.tex` para a raiz, renderize as páginas iniciais com `python scripts/slice_pdf.py`, calcule o deslocamento (`offset = pagina_pdf - pagina_livro`), divida o livro em lotes semânticos por subcapítulos (10–25 páginas, separando Teoria de Exercícios) e salve `roadmap.json` e `progress.json`.
   - Caso `roadmap.json` e `progress.json` já existam, identifique o primeiro lote com status `"pending"` em `progress.json` e execute a **Fase 1** e **Fase 2** sem refazer lotes já concluídos (`"completed"`).
2. **Controle de Lotes por Turno**:
   - Por padrão, execute **1 lote completo** por turno e pare no checkpoint.
   - Se o usuário pedir explicitamente *"Rode N lotes seguidos"*, execute exatamente $N$ lotes em sequência, compilando e salvando `progress.json` ao final de cada lote.
3. **Visão Computacional Estrita**:
   - É **proibido** extrair texto bruto de PDFs escaneados via `pypdf`/`pdfminer` ou carregar o PDF inteiro na memória.
   - Renderize apenas o intervalo `[pdf_start, pdf_end]` do lote atual com `python scripts/slice_pdf.py` e inspecione visualmente cada imagem `.png` em `build/temp_pages/`.
4. **Qualidade LaTeX, Figuras e Auto-Cura**:
   - Transcreva 100% do conteúdo sem resumir ou omitir exercícios/demonstrações, usando os ambientes de `preambulo.tex` (`definicao`, `teorema`, `exemplo`, `caixaformulas`).
   - Recrie gráficos e diagramas geométricos em `TikZ` / `pgfplots` e recorte ilustrações manuais complexas com `python scripts/crop_figure.py`.
   - Ao final de cada lote, execute `python scripts/compile_check.py`, corrija eventuais erros de compilação em loop até obter `exit code 0` e inspecione as páginas renderizadas em `build/compiled_preview/`.
