# Guia de Contribuição: book-resurrect

Agradecemos o interesse em contribuir com o framework **book-resurrect**. Este documento estabelece as diretrizes de desenvolvimento, arquitetura editorial e integridade ética para colaborações técnicas e restaurações de obras.

---

## 1. Princípios Fundamentais do Projeto

1. **Fidelidade Editorial Estrita:** Toda transcrição deve ser integral (100%), incluindo demonstrações, observações, notas de rodapé e todas as alternativas de exercícios. É terminantemente proibido resumir parágrafos ou omitir demonstrações.
2. **Inviolabilidade Notacional:** Toda álgebra, limites, variáveis, funções matemáticas e índices originais devem permanecer estritamente intocados. Nada de renomear variáveis ou alterar a notação para "ficar mais moderna".
3. **Trava Ética de Errata:** Contribuidores e agentes são proibidos de alterar deduções matemáticas ou gralhas históricas silenciosamente. Qualquer divergência contra o scan original deve ser documentada em `ERRATA.md`.

---

## 2. Estrutura Modular dos Capítulos

Os arquivos de conteúdo são armazenados na pasta `capitulos/` e carregados via `\include{...}` pelo arquivo mestre `main.tex`:

- **Proibição de Preâmbulos Internos:** Arquivos `capitulos/capXX.tex` nunca devem conter `\documentclass`, `\usepackage`, `\begin{document}` ou `\end{document}`.
- **Hierarquia:**
  - O primeiro lote de um capítulo deve iniciar com `\chapter{Título do Capítulo}`.
  - Subcapítulos seguintes no mesmo arquivo utilizam `\section{...}` e `\subsection{...}`.
- **Modo Markdown (Dual-Engine):** No modo `humanas_markdown`, os capítulos são salvos como `capitulos/capXX.md`, utilizando `# Capítulo`, `## Seção` e notas de rodapé no padrão `[^1]`.

---

## 3. Diretrizes Tipográficas Obrigatórias (Design System SBM/Springer)

Para assegurar qualidade gráfica uniforme, respeite rigorosamente as seguintes convenções:

### Listas de Exercícios e Letras
- **PROIBIDO** o uso de ambientes `tabular` para diagramar listas de exercícios.
- Utilize exclusivamente o pacote `tasks` (configurado no `preambulo.tex`) ou `multicol` com `enumerate`:
  ```latex
  \begin{tasks}(2)
      \task $x^2 - 4 = 0$
      \task $x^2 + 1 = 0$
  \end{tasks}
  ```

### Caixas Semânticas (`tcolorbox`)
- Utilize caixas minimalistas com barra lateral de 2.5pt definidas em `preambulo.tex`:
  - `\begin{definicao}{Conceito} ... \end{definicao}` (Azul Cobalto)
  - `\begin{teorema}{Nome} ... \end{teorema}` (Rubi / Vinho)
  - `\begin{proposicao}{Nome} ... \end{proposicao}`
  - `\begin{lema}{Nome} ... \end{lema}`
  - `\begin{caixaformulas}{Título} ... \end{caixaformulas}`
- **PROIBIDO** englobar múltiplos exemplos, tabelas extensas ou gráficos TikZ dentro de caixas `tcolorbox`.

### Exemplos e Resoluções
- Exemplos devem ser sempre formatados em texto corrido através do ambiente `\begin{exemplo}{Título}`:
  ```latex
  \begin{exemplo}{Cálculo do Limite}
  Enunciado detalhado do problema...
  \end{exemplo}
  \begin{solucao}
  Passo a passo da resolução com delimitador de encerramento automático.
  \end{solucao}
  ```

### Tabelas Matemáticas
- Tabelas matemáticas e tabelas-verdade devem usar o estilo respirável `booktabs` (`\toprule`, `\midrule`, `\bottomrule`), evitando grades completas claustrofóbicas em todas as células.

### Gráficos e Figuras
- Gráficos cartesianos, funções 2D/3D e diagramas geométricos devem ser reconstruídos nativamente em código vetorial **TikZ** ou **pgfplots**.
- Em rótulos sobre curvas ou retas, utilize sempre `fill=white, inner sep=1.5pt` no nó do TikZ para evitar colisões visuais.
- Fotos e ilustrações manuais que não podem ser vetorizadas devem ser tratadas via `scripts/crop_figure.py` e salvas em `figuras/`.

---

## 4. Gestão de Errata Humana-no-Loop (`ERRATA.md`)

Quando encontrar uma inconsistência no livro original escaneado (erro aritmético, gralha de impressão ou salto lógico):

1. Registre o caso em `ERRATA.md` informando:
   - Capítulo e página física do scan original.
   - Trecho exato no livro original.
   - Divergência identificada e proposta de correção.
2. Adote uma das três posturas padronizadas:
   - `[M] Manter`: mantém a versão histórica original intacta.
   - `[C] Corrigir no texto`: aplica a correção diretamente no arquivo `.tex`.
   - `[N] Nota de Rodapé`: preserva o texto original no corpo da página e insere `\footnote{Nota de revisão: ...}`.

---

## 5. Ambiente de Desenvolvimento e Verificação

Antes de submeter alterações nos scripts ou templates:

1. Instale as dependências oficiais:
   ```bash
   pip install -r requirements.txt
   ```
2. Valide o ambiente com o inicializador:
   ```bash
   python scripts/setup_env.py
   ```
3. Teste a compilação do template com o Tectonic:
   ```bash
   python scripts/compile_check.py --main templates/main.tex --outdir build
   ```
4. Assegure que os scripts Python passem na checagem de sintaxe sem avisos:
   ```bash
   python -m py_compile scripts/*.py
   ```

---

## 6. Padrão de Commits

Seguimos a convenção **Conventional Commits** para manter o histórico limpo e rastreável:

- `feat:` novas funcionalidades ou adições na skill/scripts.
- `fix:` correções de bugs em scripts ou templates.
- `docs:` melhorias ou criação de documentação.
- `refactor:` alterações estruturais de código sem mudança de comportamento.
- `style:` ajustes tipográficos ou de formatação sem alteração funcional.

Exemplo de mensagem:
```text
feat: adicionar suporte a divisão de folhas duplas no setup
```

Não adicione trailers ou assinaturas de ferramentas automatizadas nas mensagens de commit.
