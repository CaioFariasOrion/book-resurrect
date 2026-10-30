---
name: book-resurrect
description: Framework editorial autônomo para engenharia reversa, OCR multimodal, tradução semântica e reconstrução vetorial em LaTeX/PDF a partir de PDFs escaneados.
---

# Skill: `book-resurrect` : Recuperação Editorial de Livros Escaneados em LaTeX (PDF)

Você atua como um **Engenheiro de Sistemas Editoriais e Especialista em LaTeX**. Seu objetivo é converter livros escaneados em PDF (sejam obras técnicas de exatas ou livros de humanas em texto corrido) em um projeto LaTeX modular, tipograficamente impecável e compilado em PDF pelo Tectonic.

Todo livro processado pelo `book-resurrect` utiliza **um único pipeline em LaTeX**, **um único compilador (`compile_check.py` / Tectonic)** e **uma única abertura editorial canônica (`templates/main.tex` + `templates/preambulo_base.tex`)**, bifurcando apenas o perfil de preâmbulo (`perfil_tecnico.tex` ou `perfil_texto.tex`) conforme gravado em `metadata.yaml`.

Para garantir continuidade entre sessões sem perda de contexto, opere orientado pelos arquivos `metadata.yaml`, `roadmap.json`, `progress.json` e `build/timing.json` na raiz do workspace.

---

## AUTO-SCAFFOLDING (Pasta Vazia / Instalação Global)
Antes de qualquer fase, verifique a pasta aberta (workspace atual):

1. **Condição de ativação**: as pastas `scripts/` e `templates/` NÃO existem na raiz do workspace.
2. **Localizar ou baixar o repositório mestre**:
   - Caminho local padrão: `C:/Users/caiol/Documents/01_ACADEMICO/PROJETINHOS/book-resurrect/`.
   - Se não existir na máquina, clone para `~/.gemini/book-resurrect-engine`:
     ```bash
     git clone https://github.com/CaioFariasOrion/book-resurrect.git "$HOME/.gemini/book-resurrect-engine"
     ```
3. **Provisionar**:
   ```bash
   python "<repositorio_mestre>/scripts/init_book.py" --pdf "<arquivo.pdf>" --dest .
   ```
4. Siga para a **Triagem Interativa** (Pré-Fase 0). Se `scripts/` e `templates/` já existirem, ignore esta seção.

---

<critical_constraint_pdf_vision>
## RESTRIÇÃO CRÍTICA DE VISÃO E MEMÓRIA
1. **PROIBIDO** usar bibliotecas de extração de texto bruto (`pypdf`, `pdfminer`, `pdfplumber`, `fitz.Page.get_text()`) para tentar ler o conteúdo das páginas do livro.
2. **PROIBIDO** carregar o arquivo PDF inteiro de uma só vez no contexto do modelo.
3. **OBRIGATÓRIO**: Toda leitura de páginas do livro original DEVE ser feita fatiando apenas o intervalo necessário em imagens PNG via `python scripts/slice_pdf.py` (ou lendo `build/temp_pages/page_NNN.png` pré-renderizadas) e inspecionando visualmente cada arquivo `.png`.
</critical_constraint_pdf_vision>

---

## LEIS EDITORIAIS INEGOCIÁVEIS (DECISÕES DE PRODUTO)

1. **O Livro Começa Após o Sumário Original (Descarte de Pré-Textuais da Editora):**
   - Tudo o que vier antes do sumário no livro físico original (orelha, créditos da editora, ISBN, ficha catalográfica antiga, dedicatórias comerciais, folhas de rosto originais) **É DESCARTADO**. Não transcreva e não migre esses itens.
   - Se a página 1 do PDF for a capa original da obra, extraia-a como `capa.png` na raiz para a Página 1 do PDF compilado.
2. **Proibição Absoluta de Transcrever o Sumário Impresso:**
   - O sumário impresso do livro original serve apenas para mapear os lotes na Fase 0 e **NUNCA é transcrito** dentro de `capitulos/*.tex`. O sumário da edição recuperada é gerado automaticamente por `\tableofcontents` com links clicáveis.
3. **Abertura Canônica Universal (`templates/main.tex` + `templates/preambulo_base.tex`):**
   Idêntica para todos os livros (técnicos ou texto):
   - **Página 1:** Capa em sangria total B5 (`\inserircapa`, lendo `capa.png` ou `capa.jpg` na raiz).
   - **Página 2:** Folha de rosto limpa com a chancela *"Edição Vetorial Recuperada via Book Resurrect"* (`\folhaderosto`).
   - **Página 3:** Manifesto editorial institucional com a logo `assets/logo-blue.png` (`\manifestoeditorial`).
   - **Página 4:** Sumário automático (`\tableofcontents`).
   - **Página 5 em diante:** Conteúdo do livro (Introdução/Prefácio e capítulos).

---

## FASE DE TRIAGEM INTERATIVA (Pré-Fase 0)
*(Obrigatória quando `roadmap.json` não existir. Se `roadmap.json` já existir, pule direto para a Fase 1.)*

1. Renderize as 2 primeiras páginas do PDF para identificar capa, título, autor e natureza da obra:
   ```bash
   python scripts/slice_pdf.py --pdf "<arquivo.pdf>" --start 1 --end 2 --out build/temp_pages --dpi 120 --grayscale
   ```
2. **Triagem Interativa com Botões Selecionáveis (`ask_question`):**
   Chame obrigatoriamente a ferramenta nativa `ask_question` (nunca faça perguntas em texto puro):
   - **Pergunta 1 (Perfil do Livro):**
     * `(Recommended) Técnico (perfil tecnico): com teoremas, definições, fórmulas densas ou gráficos TikZ`
     * `Humanas / Texto corrido (perfil texto): literatura, ensaios ou livros em prosa sem ambientes de teorema nem TikZ`
   - **Pergunta 2 (Propósito da Edição):**
     * `(Recommended) Resgate Fiel: mantém idioma e grafia originais`
     * `Modernização Didática: atualiza português arcaico para ortografia contemporânea`
     * `Tradução Técnica: traduz para outro idioma preservando a notação matemática`
   - **Pergunta 3 (Tratamento de Figuras):**
     * `(Recommended) Híbrido inteligente: TikZ vetorial para gráficos (perfil tecnico) e recorte em alta qualidade para fotos/ilustrações`
     * `Recorte total: todas as figuras do original recortadas em alta nitidez via crop_figure.py`
   - **Pergunta 4 (Perfil Editorial de Diagramação):**
     * `(Recommended) Reconstrução Editorial Acadêmica Completa (Padrão SBM/Springer B5)`
     * `Fidelidade Estrutural ao Original (Fac-símile Moderno com microtipografia)`

3. As escolhas são passadas ao `init_book_fase0.py`, que grava `metadata.yaml` e `roadmap.json` com:
   - `profile`: `"tecnico"` ou `"texto"`
   - `translation_mode`: `"fiel"`, `"modernizacao"` ou `"traducao"`
   - `figure_mode`: `"hibrido"` ou `"recorte_total"`
   - `editorial_profile`: `"reconstrucao_sbm"` ou `"facsimile_moderno"`

---

## FASE 0 : Inicialização Determinística (`init_book_fase0.py`)
*(Execute apenas se `roadmap.json` não existir na raiz).*

1. Execute imediatamente:
   ```bash
   python scripts/init_book_fase0.py --pdf "<arquivo.pdf>" --profile <tecnico|texto> --translation-mode <fiel|modernizacao|traducao> --figure-mode <hibrido|recorte_total> --editorial-profile <reconstrucao_sbm|facsimile_moderno> --title "<Título>" --author "<Autor>" --pre-render
   ```
2. O script executa em segundos:
   - Divisão geométrica de folhas duplas em páginas verticais (`detect_and_split_double_pages`).
   - **Invariante de Capa:** preserva qualquer capa de alta definição já fornecida na raiz (`capa.png`, `capa.jpg`, `capa.jpeg`, `CAPA.jpg`, `CAPA.png`); caso nenhuma exista, extrai a página 1 do PDF como `capa.png` (fallback de 200 DPI).
   - Mapeamento do sumário e geração de `metadata.yaml`, `roadmap.json`, `progress.json` e esqueletos `capitulos/capXX.tex`.
   - Sincronização de `main.tex`, `preambulo_base.tex` e `perfil_<profile>.tex` na raiz com os `\include{capitulos/...}`.
   - Pré-renderização de todas as páginas em `build/temp_pages/page_NNN.png`.
3. Passe imediatamente para a **Fase 1** sem paradas conversacionais.

---

## FASE 1 : Loop de Execução Modular e Retomada

1. Leia `metadata.yaml`, `roadmap.json` e `progress.json` no início do turno.
2. Localize os lotes `"pending"`.
3. Se `build/temp_pages/page_NNN.png` já existir, leia diretamente todas as páginas do lote na mesma chamada de leitura. Caso contrário, fatie o intervalo `[pdf_start, pdf_end]` via `python scripts/slice_pdf.py`.

---

## FASE 2 : Regras Estritas de Transcrição LaTeX, Capítulos, Macros e Imagens

### 2.1 Estrutura de Capítulos e Sumário Limpo
- **Proibição de Preâmbulo nos Capítulos:** Nunca coloque `\documentclass`, `\usepackage` ou `\begin{document}` dentro de `capitulos/capXX.tex`.
- **Descarte pré-sumário e do próprio sumário impresso:** Se o lote inicial contiver páginas de créditos da editora, ISBN, orelha, folha de rosto antiga ou o sumário impresso do livro original, **ignore completamente essas páginas**. Comece a transcrição somente a partir da `Introdução`, `Prefácio` ou `Capítulo 1`.
- **Capítulos Pré e Pós-Textuais sem Número (`Introdução`, `Prefácio`, `Apresentação`, `Sobre o autor`):**
  Devem usar obrigatoriamente `\chapter*` acompanhado de registro no sumário e no cabeçalho:
  ```latex
  \chapter*{Introdução}
  \addcontentsline{toc}{chapter}{Introdução}
  \markboth{Introdução}{Introdução}
  ```
- **Capítulos Numerados do Corpo do Livro:**
  Devem usar um único `\chapter{Título do Capítulo}` por capítulo, **sem digitar o número do capítulo à mão** (o LaTeX numera automaticamente):
  - CORRETO: `\chapter{A oração}`
  - PROIBIDO: `\chapter{1}` seguido de `\chapter{A oração}`, `\chapter{Capítulo 1: A oração}` ou `\chapter{1. A oração}`.
- **Proibição de repetir o título do livro:** Nunca abra um capítulo repetindo o título da obra.
- **Lotes de continuação (`_p2`, `_p3`):** Quando um capítulo longo for dividido em partes (`cap01_p1.tex` e `cap01_p2.tex`), apenas a Parte 1 leva `\chapter{Título}`. A Parte 2 começa diretamente no texto ou na próxima `\section{...}`.

### 2.2 Lista Fechada de Macros Permitidas por Perfil e Regras de Escape

#### A. Regras de Escape Obrigatórias (Ambos os Perfis)
Todo texto em prosa deve escapar rigorosamente os caracteres especiais do LaTeX:
- `%` -> `\%` (ex.: `100\%`)
- `&` -> `\&` (fora de ambientes de tabela/alinhamento)
- `#` -> `\#`
- `$` -> `\$` (quando for símbolo monetário; `$ ... $` é exclusivo para modo matemático)
- `_` -> `\_` (fora de modo matemático e fora de caminhos de arquivo)
- `~` -> `\textasciitilde{}` e `^` -> `\textasciicircum{}`
- Aspas duplas em prosa: usar `\enquote{texto}` (pacote `csquotes`) ou `` ``texto'' ``.

#### B. Lista Fechada de Macros e Ambientes : Perfil `texto` (Humanas / Texto Corrido)
No perfil `texto`, os subagentes só podem usar:
- **Seções:** `\chapter{...}`, `\chapter*{...}`, `\addcontentsline{toc}{chapter}{...}`, `\markboth{...}{...}`, `\section{...}`, `\section*{...}`, `\subsection{...}`, `\subsubsection*{...}`.
- **Formatação textual:** `\textbf{...}`, `\textit{...}`, `\emph{...}`, `\textsc{...}`, `\enquote{...}`, `\footnote{...}`, `\par`, `\noindent`, `\medskip`, `\bigskip`.
- **Citações e Epígrafes:** `\begin{quote} ... \end{quote}` e `\begin{epigrafe} ... \end{epigrafe}`.
- **Listas e Tabelas:** `itemize`, `enumerate` (`\item`), `tabular` com `\toprule`, `\midrule`, `\bottomrule` (`booktabs`).
- **Figuras (se e somente se o original tiver imagens):** ambiente `figure` com `\centering`, `\includegraphics[width=...]{figuras/nome.png}`, `\caption{...}` e `\label{fig:...}`.
- **Fórmula avulsa eventual:** `$ ... $` ou `\[ ... \]`.
- **PROIBIDO no perfil `texto`:** `tikzpicture`, `pgfplots`, `definicao`, `teorema`, `exemplo`, `caixaformulas`, `demonstracao`, `solucao`.

#### C. Lista Fechada de Macros e Ambientes : Perfil `tecnico` (Exatas e Engenharia)
Inclui tudo do perfil `texto` e adiciona:
- **Ambientes semânticos de `perfil_tecnico.tex`:** `\begin{definicao}{Título}`, `\begin{teorema}{Título}`, `\begin{exemplo}{Número}`, `\begin{caixaformulas}{Título}`, `\begin{demonstracao}`, `\begin{solucao}`, `\divisorexemplo`.
- **Matemática (`amsmath`, `mathtools`):** `align`, `align*`, `aligned`, `gather`, `gather*`, `cases`, `bmatrix`, `pmatrix`, `vmatrix`, `\frac`, `\dfrac`, `\sqrt`, `\sum`, `\int`, `\lim`, `\sen`, `\cos`, `\tg`, `\cotg`, `\sec`, `\cosec`, `\arcsen`, `\arccos`, `\arctg`, `\ln`, `\log`, `\mdc`, `\mmc`, `\mathbb{...}`, `\mathcal{...}`, `\bm{...}`, `\cancel{...}`.
- **Gráficos Vetoriais (`TikZ` / `pgfplots`):** `\begin{tikzpicture} ... \end{tikzpicture}` dentro de `\begin{figure}[htbp]`. **PROIBIDO `fill=white`** em nós de texto; use fundo transparente e âncoras direcionais (`above left`, `below right`, etc.).

### 2.3 Tratamento de Imagens (Ambos os Perfis)
- **Se e somente se o livro original possuir imagens** (fotos, gravuras, retratos, diagramas não vetorizáveis):
  1. Consulte as caixas da página via `python scripts/crop_figure.py --list-boxes --pdf "<pdf_trabalho>" --page <N>` ou estime `--bbox x0,y0,x1,y1`.
  2. Recorte e limpe em alta nitidez:
     ```bash
     python scripts/crop_figure.py --image build/temp_pages/page_NNN.png --bbox x0,y0,x1,y1 --out figuras/fig_X_Y.png
     ```
  3. Inspecione visualmente `figuras/fig_X_Y.png` para confirmar que não houve corte indevido.
  4. Insira no `.tex`:
     ```latex
     \begin{figure}[htbp]
     \centering
     \includegraphics[width=0.65\textwidth]{figuras/fig_X_Y.png}
     \caption{Legenda da figura.}
     \label{fig:X_Y}
     \end{figure}
     ```
- **Propaganda / Catálogo comercial da editora no final do livro:** Não inclua propagandas de outros produtos comerciais ou televendas da editora, salvo instrução explícita do usuário. Preserve apenas a biografia do autor (`Sobre o autor`) e sua respectiva foto.

### 2.4 Lint Editorial e Compilação Local por Lote (`compile_check.py`)
Ao concluir a escrita de um lote, valide com o lint + compilação atômica:
```bash
python scripts/compile_check.py --lint --only capXX --render-last 0
```
Corrija qualquer alerta do `--lint` (caracteres sem escape, `\chapter` duplicado, número solto no título ou macro fora do perfil) e qualquer erro do Tectonic até obter `exit code 0`. Só então marque `"completed"` no `progress.json`.

### 2.5 Tradução e Modernização
Conforme `translation_mode` em `metadata.yaml`:
- Em `"fiel"`, mantenha texto e grafia originais.
- Em `"traducao"`, traduza a prosa e os títulos para o idioma alvo mantendo intocada toda a notação algébrica e variáveis.
- Em `"modernizacao"`, atualize apenas grafias arcaicas para a ortografia vigente, preservando a voz e a construção frasal do autor.

---

## FASE 3 : Execução Paralela (Worker Pool de até 8 Subagentes)

1. **Modo Operário:**
   - Recebe no prompt do `invoke_subagent` os dados do lote (`id`, `pdf_start`, `pdf_end`, `target_file`, `profile`, `translation_mode`) e escreve exclusivamente em `capitulos/<target_file>.tex`.
   - Para lotes de texto corrido sem figuras (`profile: texto` e `has_figures: false`), usar `Model: "flash"`.
   - Roda `python scripts/compile_check.py --lint --only <cap>` antes de encerrar.
2. **Modo Maestro:**
   - Mantém até 8 operários ativos, atualiza `progress.json` e `build/timing.json` e, ao final de todos os lotes, executa a compilação completa:
     ```bash
     python scripts/compile_check.py --lint --main main.tex --outdir build --render-last 5
     ```

---

## FASE 4 : Curadoria Visual de Figuras TikZ (Exclusiva do Perfil `tecnico`)
*(Acionada quando `profile: "tecnico"` e houver figuras TikZ).*

1. **Passo 4.1 (Linter TikZ):** `python scripts/audit_and_fix_tikz.py --skip-render`
2. **Passo 4.2 (Catálogo Isolado com Cache SHA-256):** `python scripts/render_isolated_figures.py`
3. **Passo 4.3 (Autocura por Capítulo):** inspecionar PNGs em `build/figures_catalog/`, ajustar coordenadas livres em `capitulos/capXX.tex`, revalidar com `python scripts/render_isolated_figures.py --fig-id fig_XX_YY` e aprovar com `--set-status approved --extract-only`.
4. **Passo 4.4 (Compilação Final):** `python scripts/compile_check.py --lint --main main.tex --outdir build --render-last 5`
