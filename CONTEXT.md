# CONTEXT.md: Quadro de Bordo e Rastreabilidade (`book-resurrect`)

## 1. Metadados e Propósito do Projeto
- **Objetivo:** Engenharia reversa editorial, tradução e recuperação acessível de livros escaneados (PDF) para formato vetorial compilável (LaTeX/TikZ) ou texto estruturado (Markdown/EPUB) via IA multimodal, servindo de base metodológica para TCC e projetos acadêmicos.
- **Repositório:** `book-resurrect`
- **Natureza deste workspace:** framework/motor universal. O livro de cálculo processado antes foi o caso piloto que validou a esteira (MiKTeX, TikZ e scripts). Os arquivos do livro piloto (`roadmap.json`, `progress.json`, `capitulos/`) não fazem parte deste repositório.

## 2. Regra de Governança de Estado (Obrigatória para Agentes)
- **Leitura no Início do Turno:** Antes de executar qualquer comando ou responder ao usuário, leia `CONTEXT.md` (visão macro e backlog de arquitetura). Se existirem, leia também `roadmap.json` e `progress.json` (estado micro dos lotes de páginas).
- **Escrita no Fim do Turno:** Antes de encerrar o turno após concluir uma entrega ou lote, atualize a seção "Status Atual", o "Próximo Passo Imediato" e os checkboxes do "Backlog Priorizado" neste arquivo.

## 3. Status Atual (Construído e Validado)
- [x] Scripts utilitários presentes em `scripts/`: `setup_env.py`, `slice_pdf.py`, `crop_figure.py`, `compile_check.py`. Validados no caso piloto (compilação local com MiKTeX e Tectonic, `exit code 0`).
- [x] Templates presentes em `templates/`: `main.tex` e `preambulo.tex` (caixas `tcolorbox`: `definicao`, `teorema`, `exemplo`, `caixaformulas`). Validados no caso piloto.
- [x] Skill canônica em `.agent/skills/book-resurrect/SKILL.md` com Fases 0, 1 e 2.
- [x] Adaptadores multi-IDE: `.cursor/`, `CLAUDE.md`, `.windsurfrules`, `.github/`.
- [x] Triagem Interativa e Protocolo de Tradução/Modernização integrados ao SKILL.md.
- [x] Fluxo de Humanas (Markdown/EPUB) e templates/metadata.yaml criados.
- [x] Provisionador global scripts/init_book.py implementado e operacional.
- [x] Instrução de build EPUB via Pandoc formalizada.
- [x] FASE 3 (Modo Esquadrão Paralelo: Operário/Maestro) integrada ao SKILL.md local e às pastas globais.

## 4. Próximo Passo Imediato (Foco Ativo)
- [x] Arquitetura v2.0 do motor concluída. Framework pronto para processamento de novos livros ou push remoto.

## 5. Backlog Priorizado e Critérios de Aceite
- [x] **Etapa 1: Triagem Interativa.** Questionário pré-Fase 0 no `SKILL.md` com 3 decisões: (1) Exatas/LaTeX vs. Humanas/Markdown; (2) Transcrição Fiel vs. Tradução vs. Modernização de linguagem arcaica; (3) Figuras Híbridas (TikZ + recorte) vs. 100% recorte tratado.
- [x] **Etapa 2: Tradução e Modernização Semântica.** Regras de tradução simultânea e atualização lexical no `SKILL.md`, preservando rigorosamente a notação matemática e as variáveis originais.
- [x] **Etapa 3: Suporte a Humanas/Markdown.** Fluxo de saída em Markdown/EPUB para livros sem notação matemática, com regras próprias de estrutura, notas e figuras.
- [x] **Etapa 4: Scaffolding Global.** A skill provisiona a estrutura de pastas (`capitulos/`, `figuras/`, `build/`, `scripts/`, `templates/`) ao receber um caminho de PDF em qualquer diretório.

## 6. Protocolo de Validação em Escala Menor (Definition of Done)
Nenhuma tarefa ou lote pode ser marcado como `[x]` sem cumprir os 3 critérios verificáveis abaixo:
1. **Verificação Sintática:** Equilíbrio exato de chaves `{}` e fechamento de todos os blocos `\begin{...}` / `\end{...}` nos arquivos `.tex` alterados.
2. **Compilação Limpa:** Execução de `pdflatex` ou `python scripts/compile_check.py` retornando `exit code 0` e gerando o PDF atualizado.
3. **Inspeção Visual por Amostragem:** Renderização das páginas recém-compiladas em PNG e inspeção visual confirmando ausência de equações cortadas (*overfull hbox*) ou sobreposição em diagramas TikZ.
