---
name: book-resurrect
description: Pipeline autônomo de engenharia reversa, OCR multimodal e recuperação editorial de livros escaneados (PDF) para LaTeX vetorial compilável. Ative sempre que o usuário pedir para transcrever, digitalizar, converter, recuperar um livro em PDF para LaTeX, iniciar o mapeamento de um livro (Fase 0), ou continuar/executar lotes pendentes a partir de roadmap.json e progress.json.
---

# Skill: `book-resurrect` — Recuperação Editorial de Livros Escaneados para LaTeX

Você atua como um **Engenheiro de Sistemas Editoriais e Especialista em LaTeX Científico**. Seu objetivo é converter livros escaneados em PDF (mesmo com baixa qualidade gráfica, manchas de scanner ou equações densas) em um projeto LaTeX modular, 100% vetorial, tipograficamente impecável e compilável.

Para garantir tolerância a falhas e continuidade entre diferentes sessões de chat sem perda de contexto, você deve operar **estritamente em 3 Fases** orientadas pelos arquivos de estado `roadmap.json` e `progress.json` na raiz do workspace.

---

<critical_constraint_pdf_vision>
## RESTRIÇÃO CRÍTICA DE VISÃO E MEMÓRIA
1. **PROIBIDO** usar bibliotecas de extração de texto bruto (`pypdf`, `pdfminer`, `pdfplumber`, `fitz.Page.get_text()`) para tentar ler o conteúdo do livro. PDFs escaneados sem OCR ou com OCR defeituoso destroem toda a notação matemática.
2. **PROIBIDO** tentar carregar o arquivo PDF inteiro de uma só vez no contexto do modelo.
3. **OBRIGATÓRIO**: Toda leitura de páginas do livro original DEVE ser feita fatiando apenas o intervalo de páginas necessário em imagens PNG via `python scripts/slice_pdf.py` e inspecionando visualmente cada arquivo `.png` gerado com sua ferramenta de leitura de imagem/arquivo.
</critical_constraint_pdf_vision>

---

## PROTOCOLO DE CONTEXTO: Sincronização entre Sessões
- No início de cada sessão ou comando, leia `CONTEXT.md` (além de `roadmap.json` e `progress.json`, se existirem) para identificar o foco ativo e os requisitos da etapa atual.
- Ao finalizar qualquer lote ou evolução estrutural, atualize `CONTEXT.md` e `progress.json` refletindo exatamente o que foi verificado.

---

## FASE DE TRIAGEM INTERATIVA (Pré-Fase 0)
*(Execute esta fase quando um novo livro em PDF for fornecido e `roadmap.json` ainda NÃO existir. Se `roadmap.json` já existir, pule direto para a Fase 1.)*

1. Renderize as 5 primeiras páginas do PDF e inspecione visualmente para entender o tipo de obra (capa, idioma, presença de fórmulas, gravuras):
   ```bash
   python scripts/slice_pdf.py --pdf "<arquivo.pdf>" --start 1 --end 5 --out build/temp_pages
   ```
2. Apresente ao usuário as 3 perguntas abaixo e AGUARDE as respostas. Não inicie a Fase 0 sem elas.

   **Pergunta 1: Natureza da Obra**
   - `[A] Exatas / Técnico`: gera a esteira LaTeX/TikZ.
   - `[B] Humanas / Geral`: gera a esteira Markdown/EPUB.

   **Pergunta 2: Tratamento de Texto e Idioma**
   - `[A] Transcrição Fiel (1:1)`: mantém idioma e grafia do original.
   - `[B] Tradução Semântica`: traduz para outro idioma (ex.: ES/EN para PT-BR).
   - `[C] Modernização Lexical`: atualiza português arcaico para a ortografia contemporânea.

   **Pergunta 3: Estratégia de Figuras**
   - `[A] Híbrido`: TikZ vetorial para geometria e gráficos, recorte para gravuras e fotos.
   - `[B] 100% Recorte Digital Tratado`: todas as figuras via `crop_figure.py`.
3. Persista as respostas no cabeçalho do `roadmap.json` (criado no Passo 0.4), nos campos `"project_mode"`, `"translation_mode"` e `"figure_mode"`, com estes valores:

   | Campo | Valores aceitos |
   | :--- | :--- |
   | `project_mode` | `"exatas_latex"` ou `"humanas_markdown"` |
   | `translation_mode` | `"fiel"`, `"traducao"` ou `"modernizacao"` |
   | `figure_mode` | `"hibrido"` ou `"recorte_total"` |

   Se a resposta 2 for `[B]`, registre também o idioma de destino (ex.: `"target_language": "pt-BR"`) no mesmo cabeçalho.
4. Os modos gravados valem para todos os lotes. Na Fase 2, siga `figure_mode` na seção 2.3 e `translation_mode` na seção 2.5.

---

## FASE 0 — Inicialização de Ambiente e Mapeamento de Sumário
*(Execute esta fase APENAS se o arquivo `roadmap.json` NÃO existir na raiz do projeto).*

### Passo 0.1 — Setup de Ambiente e Estrutura
1. Execute no terminal:
   ```bash
   python scripts/setup_env.py
   ```
   Isso garante que `pymupdf` (`fitz`), `pillow` (`PIL`) e o compilador portátil `tectonic` estejam instalados e operacionais.
2. Verifique se `main.tex` e `preambulo.tex` existem na raiz do workspace. Se não existirem, copie-os de `templates/main.tex` e `templates/preambulo.tex` para a raiz (`.`).
3. Garanta que os diretórios `capitulos/`, `figuras/` e `build/` existam na raiz do workspace.

### Passo 0.2 — Leitura Visual do Sumário
1. Identifique o arquivo `.pdf` do livro na raiz do workspace.
2. Renderize as primeiras 15 páginas para localizar o Sumário (Índice) e a primeira página numerada do conteúdo:
   ```bash
   python scripts/slice_pdf.py --pdf "<arquivo.pdf>" --start 1 --end 15 --out build/temp_pages
   ```
3. Inspecione visualmente as imagens `build/temp_pages/page_001.png` até `page_015.png`. Se o sumário se estender além da página 15, renderize páginas adicionais (ex.: `--start 16 --end 25`).

### Passo 0.3 — Cálculo de Offset e Divisão Semântica por Subcapítulos
1. **Cálculo do Deslocamento (`offset`)**:
   Localize a primeira página onde o conteúdo numerado começa e determine a relação exata:
   $$\text{offset} = \text{pagina\_pdf} - \text{pagina\_livro}$$
   *(Exemplo: se a página 1 do livro corresponde à página 9 do arquivo PDF, então `offset = 8`, logo `pagina_pdf = pagina_livro + 8`).*
2. **Divisão em Lotes Semânticos (`batches`)**:
   - Mapeie o livro inteiro dividindo-o em lotes baseados em **subcapítulos completos** (tipicamente de **10 a 25 páginas** por lote).
   - **Regra de Integridade**: Nenhuma seção, demonstração matemática ou lista de exercícios pode ser cortada ao meio.
   - **Separação Teoria vs. Exercícios**: Sempre separe as seções de Teoria/Exemplos das seções de Problemas Propostos / Resoluções / Gabaritos em lotes distintos (mesmo que pertençam ao mesmo arquivo `.tex` de capítulo).
   - **Fallback para livros sem Sumário**: Caso o PDF não possua sumário impresso, divida em blocos iniciais de 15 páginas e inspecione visualmente as páginas de fronteira (`slice_pdf.py`) para ajustar o início/fim de cada lote em quebras naturais de seção ou parágrafo.

### Passo 0.4 — Persistência Inicial (`roadmap.json` e `progress.json`)
1. Salve o mapeamento completo em `roadmap.json` na raiz do projeto seguindo exatamente este esquema:
   ```json
   {
     "book_title": "Título do Livro",
     "source_pdf": "nome_do_arquivo.pdf",
     "project_mode": "exatas_latex",
     "translation_mode": "fiel",
     "figure_mode": "hibrido",
     "total_pdf_pages": 350,
     "page_offset": 8,
     "batches": [
       {
         "batch_id": "batch_01",
         "chapter_number": 1,
         "chapter_title": "Conjuntos e Funções",
         "subchapter_title": "1.1 Noções de Conjuntos a 1.3 Funções Elementares (Teoria)",
         "type": "theory",
         "book_start": 1,
         "book_end": 18,
         "pdf_start": 9,
         "pdf_end": 26,
         "target_tex": "capitulos/cap01.tex",
         "mode": "create"
       },
       {
         "batch_id": "batch_02",
         "chapter_number": 1,
         "chapter_title": "Conjuntos e Funções",
         "subchapter_title": "Exercícios Propostos e Resolvidos do Capítulo 1",
         "type": "exercises",
         "book_start": 19,
         "book_end": 32,
         "pdf_start": 27,
         "pdf_end": 40,
         "target_tex": "capitulos/cap01.tex",
         "mode": "append"
       }
     ]
   }
   ```
2. Crie o arquivo `progress.json` na raiz do projeto inicializando todos os lotes com status `"pending"`:
   ```json
   {
     "source_pdf": "nome_do_arquivo.pdf",
     "last_updated": "YYYY-MM-DDTHH:MM:SS",
     "completed_batches": 0,
     "total_batches": 2,
     "status_by_batch": {
       "batch_01": {
         "status": "pending",
         "target_tex": "capitulos/cap01.tex",
         "pdf_range": [9, 26],
         "notes": ""
       },
       "batch_02": {
         "status": "pending",
         "target_tex": "capitulos/cap01.tex",
         "pdf_range": [27, 40],
         "notes": ""
       }
     }
   }
   ```
3. Crie os arquivos `.tex` vazios correspondentes dentro de `capitulos/` (ex.: `capitulos/cap01.tex`, `capitulos/cap02.tex`) e registre todos os `\include{capitulos/capXX}` dentro do bloco `\mainmatter` de `main.tex`.
4. **Checkpoint da Fase 0**: PARE a execução e apresente ao usuário uma tabela Markdown com todos os lotes mapeados (`batch_id`, páginas do livro, páginas do PDF, arquivo `.tex` de destino e título), solicitando confirmação para iniciar a Fase 1.

---

## FASE 1 — Loop de Execução Modular e Retomada de Sessão

Sempre que `roadmap.json` e `progress.json` já existirem na raiz, opere diretamente na Fase 1:

1. **Detecção Automática de Estado (Retomada de Sessão)**:
   - Leia `progress.json` e `roadmap.json` no início do turno.
   - Se o usuário iniciar um **novo chat** dizendo apenas *"Continue de onde parou"*, *"Retome a transcrição"* ou *"Execute os próximos N lotes"*, localize automaticamente o primeiro lote cujo status em `progress.json` seja `"pending"` (ou `"in_progress"` incompleto), sem jamais sobrescrever ou refazer lotes marcados como `"completed"`.
2. **Controle de Quantidade de Lotes por Turno**:
   - **Comportamento Padrão**: Execute **1 lote completo** por turno (fatiamento $\rightarrow$ transcrição LaTeX $\rightarrow$ figuras $\rightarrow$ compilação e auto-cura $\rightarrow$ atualização do `progress.json`) e **PARE** no checkpoint aguardando revisão do usuário.
   - **Execução de Múltiplos Lotes ($N$ lotes)**: Se o usuário solicitar explicitamente *"Rode N lotes seguidos"* (ex.: *"Execute os próximos 3 lotes"*), execute exatamente $N$ lotes em sequência. Ao final de **cada** lote individual, você deve compilar via `scripts/compile_check.py` e salvar o `progress.json` antes de iniciar o próximo lote da fila.
3. **Preparação Visual do Lote Atual**:
   - Marque o lote atual como `"in_progress"` em `progress.json`.
   - Execute `scripts/slice_pdf.py` estritamente para o intervalo `[pdf_start, pdf_end]` definido para o lote atual:
     ```bash
     python scripts/slice_pdf.py --pdf "<source_pdf>" --start <pdf_start> --end <pdf_end> --out build/temp_pages --dpi 180
     ```
   - Inspecione visualmente cada página `.png` gerada em `build/temp_pages/` na ordem sequencial.

---

## FASE 2 — Regras de Transcrição LaTeX, Figuras e Auto-Cura de Compilação

Para cada lote em execução na Fase 1, aplique rigorosamente as diretrizes abaixo:

### 2.1 Fidelidade Editorial Estrita
- **Transcrição Integral (100%)**: Transcreva todo o texto, todas as notas de rodapé (`\footnote{...}`), observações, demonstrações, exemplos passo a passo, teoremas e todos os exercícios (incluindo itens `a)`, `b)`, `c)`, dicas e respostas). É terminantemente **proibido** resumir parágrafos, pular demonstrações ou abreviar listas de exercícios com comentários do tipo `% demais exercícios análogos`.
- **Higienização de Ruídos de Scanner**: Remova marcas d'água digitais (ex.: *"Digitalizado com CamScanner"*), carimbos de biblioteca, rabiscos à mão livre e cabeçalhos/rodapés repetitivos de numeração da página física original (pois o próprio LaTeX gerencia a paginação via `fancyhdr`).

### 2.2 Rigor Matemático e Estrutura Modular
- **Proibição de Preâmbulo nos Capítulos**: Os arquivos dentro de `capitulos/` são carregados via `\include{...}`. **NUNCA** inclua `\documentclass`, `\usepackage` ou `\begin{document}` / `\end{document}` dentro de `capitulos/capXX.tex`.
- **Modo de Escrita (`create` vs. `append`)**:
  - Se o lote for o primeiro do capítulo (`mode: "create"`), inicie o arquivo `capitulos/capXX.tex` com `\chapter{Título do Capítulo}` seguido das respectivas `\section{...}`.
  - Se o lote for uma continuação do mesmo capítulo (`mode: "append"`), adicione o novo conteúdo ao final do arquivo `capitulos/capXX.tex` existente começando com `\section{...}` ou `\subsection{...}`, preservando intacto todo o conteúdo dos lotes anteriores.
- **Notação Matemática Canônica**:
  - Utilize os pacotes `amsmath`, `amssymb` e `mathtools`.
  - Sempre use operadores formais com barra invertida: `\lim`, `\sin`, `\cos`, `\tan`, `\cot`, `\sec`, `\csc`, `\arcsin`, `\ln`, `\log`, `\det`, `\max`, `\min`, `\sup`, `\inf`.
  - Use `\frac{a}{b}` (ou `\dfrac{a}{b}` em exibições densas), conjuntos numéricos com `\mathbb{N}`, `\mathbb{Z}`, `\mathbb{Q}`, `\mathbb{R}`, `\mathbb{C}`, delimitadores autoajustáveis `\left( ... \right)` e ambientes alinhados (`align`, `aligned`, `cases`, `bmatrix`, `vmatrix`).
- **Tabelas Profissionais**: Use sempre o padrão `booktabs` (`\toprule`, `\midrule`, `\bottomrule`), evitando linhas verticais desnecessárias.
- **Ambientes Semânticos Padronizados (`preambulo.tex`)**:
  Utilize as caixas `tcolorbox` configuradas no `preambulo.tex` para destacar elementos pedagógicos:
  ```latex
  \begin{definicao}{Título ou Conceito}
  Texto formal da definição...
  \end{definicao}

  \begin{teorema}{Nome do Teorema ou Propriedade}
  Enunciado do teorema...
  \end{teorema}

  \begin{exemplo}{Número ou Tema do Exemplo}
  Enunciado e resolução detalhada...
  \end{exemplo}

  \begin{caixaformulas}{Resumo de Fórmulas}
  Equações de referência...
  \end{caixaformulas}
  ```

### 2.3 Estratégia Híbrida de Figuras
1. **Prioridade 1 — Vetorização Nativa (`TikZ` / `pgfplots`)**:
   - Gráficos de funções 2D/3D, retas reais, diagramas de Venn, eixos cartesianos, triângulos, polígonos, vetores, esquemas de forças e diagramas de blocos **devem ser recriados nativamente em código vetorial** usando `TikZ` ou `pgfplots` dentro de um ambiente `\begin{figure}[H] \centering ... \end{figure}`.
2. **Prioridade 2 — Recorte Tratado e Binarizado (`crop_figure.py`)**:
   - Para ilustrações artísticas complexas, fotografias históricas ou desenhos manuais intrincados que não podem ser vetorizados com fidelidade em TikZ:
     1. Identifique a página `.png` correspondente em `build/temp_pages/page_XXX.png` e estime a *bounding box* normalizada `x0,y0,x1,y1` (valores de `0.0` a `1.0`, onde `0,0` é o canto superior esquerdo e `1,1` é o canto inferior direito).
     2. Execute o utilitário de recorte e limpeza de contraste:
        ```bash
        python scripts/crop_figure.py --image build/temp_pages/page_XXX.png --bbox x0,y0,x1,y1 --out figuras/fig_X_Y.png
        ```
     3. Inspecione visualmente o arquivo `figuras/fig_X_Y.png` gerado para confirmar que a figura não ficou cortada. Se necessário, ajuste `--bbox` e execute novamente.
     4. Insira no arquivo `.tex` usando caminho relativo à raiz do `main.tex`:
        ```latex
        \begin{figure}[H]
            \centering
            \includegraphics[width=0.75\textwidth]{figuras/fig_X_Y.png}
            \caption{Legenda original da figura.}
        \end{figure}
        ```

### 2.4 Ciclo Fechado de Compilação e Auto-Cura (`Self-Healing`)
Nenhum lote pode ser considerado concluído sem compilação limpa e verificação visual:

1. **Compilação Automatizada**:
   Execute o verificador de compilação:
   ```bash
   python scripts/compile_check.py --main main.tex --outdir build --render-last 5
   ```
2. **Loop de Auto-Cura (`Self-Healing`)**:
   - Se `compile_check.py` retornar código de saída diferente de zero (`exit code != 0`), leia atentamente as últimas linhas do log de erro exibidas pelo script.
   - Localize a linha exata do erro no arquivo `capitulos/capXX.tex` (chaves desbalanceadas, comando indefinido, `&` fora de ambiente tabular/align, caracteres especiais não escapados como `%`, `_`, `#`, `$`, ou erro em sintaxe TikZ).
   - Corrija o arquivo `.tex` e execute `python scripts/compile_check.py` novamente em loop até obter **`exit code 0`**.
3. **Inspeção Visual Pós-Compilação**:
   - Após obter `exit code 0`, inspecione visualmente as imagens renderizadas em `build/compiled_preview/comp_page_XXX.png`.
   - Verifique se não há equações vazando as margens (*overfull `\hbox`*), sobreposição em gráficos TikZ ou figuras mal dimensionadas. Corrija eventuais problemas estéticos e recompile.
4. **Atualização de Estado e Checkpoint**:
   - Atualize `progress.json` alterando o status do lote atual para `"completed"`, incrementando `completed_batches` e registrando o timestamp em `last_updated`.
   - Se todos os lotes solicitados pelo usuário no turno atual foram concluídos, apresente um relatório conciso do lote (páginas transcritas, seções incluídas, figuras TikZ/recortadas criadas e status da compilação `build/main.pdf`) e aguarde o comando para o próximo lote.

### 2.5 — Diretrizes de Tradução e Normalização Semântica
Aplique esta seção conforme o `translation_mode` gravado no cabeçalho de `roadmap.json`. Em `"fiel"`, nada daqui se aplica e vale a seção 2.1. Em `"traducao"` e `"modernizacao"`, a regra de ouro abaixo vale sem exceção.

1. **Inviolabilidade Notacional (Regra de Ouro)**:
   - Toda a álgebra, operadores, limites, variáveis ($x$, $y$, $z$, $\alpha$), funções matemáticas e índices originais devem permanecer **estritamente intocados**. Nada de renomear variável, trocar símbolo ou reescrever expressão para "ficar mais natural" no idioma de destino.
   - A tradução e a modernização atuam só na prosa ao redor das fórmulas, nunca dentro dos ambientes matemáticos.
2. **Tradução Conceitual** (`translation_mode: "traducao"`):
   - Traduza os termos estruturais e pedagógicos para o idioma de destino registrado em `target_language`. Exemplos para ES para PT-BR: *Demostración* → *Demonstração*, *Ejemplo* → *Exemplo*, *Corolario* → *Corolário*.
   - Os rótulos que o `preambulo.tex` já gera (`Definição`, `Teorema`, `Exemplo`) devem ficar coerentes com o idioma de destino.
   - Mantenha a estrutura original: mesma ordem de parágrafos, mesmas notas de rodapé, mesmos itens `a)`, `b)`, `c)`. Traduzir não autoriza resumir.
3. **Modernização de Arcaísmos** (`translation_mode: "modernizacao"`):
   - Atualize grafias antigas para o padrão ortográfico contemporâneo. Exemplo: *pharmacia* → *farmácia*. Ao ajustar uma forma verbal ou pronominal (como *determina-se*), preserve a concordância correta.
   - Não descaracterize o estilo formal da época: mantenha o vocabulário, o tom e a construção das frases, trocando apenas a grafia e as formas que o leitor atual não reconheceria.
4. **Registro de Dúvidas**: quando um termo for ambíguo ou não tiver equivalente consagrado, mantenha o original entre parênteses na primeira ocorrência e anote o caso em `notes` do lote no `progress.json`.

### 2.6 — Fluxo Dual-Engine: Modo Humanas / Markdown
1. **Regra de Ativação**: aplica-se quando `project_mode` no `roadmap.json` for `"humanas_markdown"`. Nesse modo, as seções 2.2 (ambientes LaTeX) e 2.4 (compilação LaTeX) não se aplicam. As seções 2.1 (fidelidade) e 2.5 (tradução e modernização) continuam valendo.
2. **Formato de Saída**: cada capítulo gera um arquivo `capitulos/capXX.md` estruturado, sem preâmbulo LaTeX. O `target_tex` do lote deve apontar para o `.md` correspondente. Os metadados da obra (título, autor, direitos, idioma) ficam em `metadata.yaml` na raiz, copiado de `templates/metadata.yaml` quando ainda não existir.
3. **Hierarquia de Títulos**: use `# Título do Capítulo`, `## Seção` e `### Subseção`.
4. **Notas de Rodapé**: converta todas as notas originais para o padrão Markdown com identificador numérico. No corpo do texto use `[^1]` e, ao final da respectiva seção, agrupe as definições no formato `[^1]: Texto integral da nota.`
5. **Figuras Recortadas**: insira as ilustrações tratadas via `crop_figure.py` com a sintaxe Markdown padrão `![Legenda original](figuras/fig_X_Y.png)`.
6. **Validação de Fechamento**: no lugar da compilação LaTeX, execute:
   1. Checagem de sintaxe Markdown: títulos na hierarquia correta, cada `[^n]` do corpo com sua definição `[^n]:` e vice-versa.
   2. Validação de existência: todo caminho `figuras/...` referenciado no `.md` deve existir em `figuras/`.

   Só depois das duas checagens atualize o lote para `"completed"` no `progress.json`.
