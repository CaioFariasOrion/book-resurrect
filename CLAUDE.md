# CLAUDE.md — Adaptador Claude Code para `book-resurrect`

Este workspace contém a skill universal **`book-resurrect`** para engenharia reversa e recuperação editorial de livros escaneados (PDF) para LaTeX vetorial compilável.

Sempre que o usuário solicitar a transcrição, digitalização ou recuperação de um livro em PDF, ou pedir para continuar a execução dos lotes (*"Continue de onde parou"*, *"Execute os próximos N lotes"*), você **DEVE** ler e seguir integralmente o protocolo canônico em:

👉 **[`.agent/skills/book-resurrect/SKILL.md`](.agent/skills/book-resurrect/SKILL.md)**

## Resumo do Fluxo Obrigatório

1. **Leitura do Protocolo**: Leia `.agent/skills/book-resurrect/SKILL.md` antes de iniciar qualquer operação.
2. **Fase 0 (Se `roadmap.json` não existir)**:
   - Execute `python scripts/setup_env.py` para verificar/instalar `PyMuPDF`, `Pillow` e o compilador portátil `tectonic`.
   - Copie `templates/main.tex` e `templates/preambulo.tex` para a raiz (se ainda não existirem) e crie `capitulos/`, `figuras/` e `build/`.
   - Renderize as páginas iniciais do PDF (`python scripts/slice_pdf.py --pdf "<arquivo.pdf>" --start 1 --end 15 --out build/temp_pages`), inspecione visualmente o Sumário, calcule `offset = pagina_pdf - pagina_livro` e estruture os lotes por subcapítulos completos (10–25 páginas, separando Teoria e Exercícios).
   - Gere `roadmap.json`, `progress.json`, os arquivos `.tex` em `capitulos/` e os `\include{...}` em `main.tex`. Apresente a tabela de lotes ao usuário e aguarde confirmação.
3. **Fase 1 (Loop de Execução e Retomada de Sessão)**:
   - Leia `progress.json` e `roadmap.json` e localize o primeiro lote com status `"pending"`.
   - Execute **1 lote por turno** por padrão, ou exatamente **$N$ lotes seguidos** se solicitado pelo usuário.
   - **Restrição Crítica de Visão**: Jamais use extração de texto bruto (`pypdf`, `pdfminer`, `get_text()`). Renderize apenas o intervalo `[pdf_start, pdf_end]` do lote com `python scripts/slice_pdf.py` e leia visualmente cada `.png`.
4. **Fase 2 (Transcrição LaTeX, Figuras e Auto-Cura)**:
   - Transcreva 100% do conteúdo sem omissões, removendo marcas d'água de scanner e usando os ambientes de `preambulo.tex` (`definicao`, `teorema`, `exemplo`, `caixaformulas`).
   - Vetorize gráficos/diagramas com `TikZ`/`pgfplots` e recorte figuras manuais complexas com `python scripts/crop_figure.py`.
   - Valide cada lote executando `python scripts/compile_check.py`, corrigindo qualquer erro LaTeX em loop até obter `exit code 0` e inspecionando visualmente `build/compiled_preview/` antes de marcar o lote como `"completed"` em `progress.json`.
