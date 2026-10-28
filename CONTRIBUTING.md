# Guia de Contribuicao: book-resurrect

Agradecemos o interesse em contribuir com o framework **book-resurrect**. Este documento estabelece as diretrizes de desenvolvimento, arquitetura editorial e integridade etica para colaboracoes tecnicas e restauracoes de obras.

---

## 1. Principios Fundamentais do Projeto

1. **Fidelidade Editorial Estrita:** Toda transcricao deve ser integral (100%), incluindo demonstracoes, observacoes, notas de rodape e todas as alternativas de exercicios. E terminantemente proibido resumir paragrafos ou omitir demonstracoes.
2. **Inviolabilidade Notacional:** Toda algebra, limites, variaveis, funcoes matematicas e indices originais devem permanecer estritamente intocados. Nada de renomear variaveis ou alterar a notacao para "ficar mais moderna".
3. **Trava Etica de Errata:** Contribuidores e agentes sao proibidos de alterar deduces matematicas ou gralhas historicas silenciosamente. Qualquer divergencia contra o scan original deve ser documentada em `ERRATA.md`.

---

## 2. Estrutura Modular dos Capitulos

Os arquivos de conteudo sao armazenados na pasta `capitulos/` e carregados via `\include{...}` pelo arquivo mestre `main.tex`:

- **Proibicao de Preambulos Internos:** Arquivos `capitulos/capXX.tex` nunca devem conter `\documentclass`, `\usepackage`, `\begin{document}` ou `\end{document}`.
- **Hierarquia:**
  - O primeiro lote de um capitulo deve iniciar com `\chapter{Titulo do Capitulo}`.
  - Subcapitulos seguintes no mesmo arquivo utilizam `\section{...}` e `\subsection{...}`.
- **Modo Markdown (Dual-Engine):** No modo `humanas_markdown`, os capitulos sao salvos como `capitulos/capXX.md`, utilizando `# Capitulo`, `## Secao` e notas de rodape no padrao `[^1]`.

---

## 3. Diretrizes Tipograficas Obrigatorias (Design System SBM/Springer)

Para assegurar qualidade grafica uniforme, respeite rigorosamente as seguintes convencoes:

### Listas de Exercicios e Letras
- **PROIBIDO** o uso de ambientes `tabular` para diagramar listas de exercicios.
- Utilize exclusivamente o pacote `tasks` (configurado no `preambulo.tex`) ou `multicol` com `enumerate`:
  ```latex
  \begin{tasks}(2)
      \task $x^2 - 4 = 0$
      \task $x^2 + 1 = 0$
  \end{tasks}
  ```

### Caixas Semanticas (`tcolorbox`)
- Utilize caixas minimalistas com barra lateral de 2.5pt definidas em `preambulo.tex`:
  - `\begin{definicao}{Conceito} ... \end{definicao}` (Azul Cobalto)
  - `\begin{teorema}{Nome} ... \end{teorema}` (Rubi / Vinho)
  - `\begin{proposicao}{Nome} ... \end{proposicao}`
  - `\begin{lema}{Nome} ... \end{lema}`
  - `\begin{caixaformulas}{Titulo} ... \end{caixaformulas}`
- **PROIBIDO** englobar multiplos exemplos, tabelas extensas ou graficos TikZ dentro de caixas `tcolorbox`.

### Exemplos e Resoluces
- Exemplos devem ser sempre formatados em texto corrido atraves do ambiente `\begin{exemplo}{Titulo}`:
  ```latex
  \begin{exemplo}{Calculo do Limite}
  Enunciado detalhado do problema...
  \end{exemplo}
  \begin{solucao}
  Passo a passo da resolucao com delimitador de encerramento automatico.
  \end{solucao}
  ```

### Tabelas Matematicas
- Tabelas matematicas e tabelas-verdade devem usar o estilo respiravel `booktabs` (`\toprule`, `\midrule`, `\bottomrule`), evitando grades completas claustrofobicas em todas as celulas.

### Graficos e Figuras
- Graficos cartesianos, funcoes 2D/3D e diagramas geometricos devem ser reconstruidos nativamente em codigo vetorial **TikZ** ou **pgfplots**.
- Em rotulos sobre curvas ou retas, utilize sempre `fill=white, inner sep=1.5pt` no no do TikZ para evitar colisoes visuais.
- Fotos e ilustracoes manuais que nao podem ser vetorizadas devem ser tratadas via `scripts/crop_figure.py` e salvas em `figuras/`.

---

## 4. Gestao de Errata Humana-no-Loop (`ERRATA.md`)

Quando encontrar uma inconsistencia no livro original escaneado (erro aritmetico, gralha de impressao ou salto logico):

1. Registre o caso em `ERRATA.md` informando:
   - Capitulo e pagina fisica do scan original.
   - Trecho exato no livro original.
   - Divergencia identificada e proposta de correcao.
2. Adote uma das tres posturas padronizadas:
   - `[M] Manter`: mantem a versao historica original intacta.
   - `[C] Corrigir no texto`: aplica a correcao diretamente no arquivo `.tex`.
   - `[N] Nota de Rodape`: preserva o texto original no corpo da pagina e insere `\footnote{Nota de revisao: ...}`.

---

## 5. Ambiente de Desenvolvimento e Verificacao

Antes de submeter alteracoes nos scripts ou templates:

1. Instale as dependencias oficiais:
   ```bash
   pip install -r requirements.txt
   ```
2. Valide o ambiente com o inicializador:
   ```bash
   python scripts/setup_env.py
   ```
3. Teste a compilacao do template com o Tectonic:
   ```bash
   python scripts/compile_check.py --main templates/main.tex --outdir build
   ```
4. Assegure que os scripts Python passem na checagem de sintaxe sem avisos:
   ```bash
   python -m py_compile scripts/*.py
   ```

---

## 6. Padrao de Commits

Seguimos a convencao **Conventional Commits** para manter o historico limpo e rastreavel:

- `feat:` novas funcionalidades ou adicoes na skill/scripts.
- `fix:` correcoes de bugs em scripts ou templates.
- `docs:` melhorias ou criacao de documentacao.
- `refactor:` alteracoes estruturais de codigo sem mudanca de comportamento.
- `style:` ajustes tipograficos ou de formatacao sem alteracao funcional.

Exemplo de mensagem:
```text
feat: adicionar suporte a divisao de folhas duplas no setup
```

Nao adicione trailers ou assinaturas de ferramentas automatizadas nas mensagens de commit.
