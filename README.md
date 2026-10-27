# 📚 `book-resurrect` — Pipeline Autônomo de Recuperação de Livros Escaneados para LaTeX Vetorial

O **`book-resurrect`** é uma *skill* universal e repositório de automação editorial que transforma livros antigos ou escaneados em PDF (mesmo sem camada de OCR, com manchas de scanner ou repletos de equações matemáticas e gráficos) em um projeto **LaTeX modular, 100% vetorial, padronizado em formato B5 e pronto para compilação**.

Projetado com adaptadores nativos para **Antigravity**, **Cursor**, **Claude Code**, **Windsurf** e **GitHub Copilot**, o pipeline opera por meio de **visão multimodal fatiada**, **persistência de estado em JSON** (`roadmap.json` e `progress.json`) e um **ciclo fechado de auto-cura de compilação (`Self-Healing`)** usando o compilador LaTeX portátil **Tectonic**.

---

## ✨ Principais Diferenciais

- **Visão Multimodal sem Alucinação de OCR**: Proíbe a extração de texto bruto quebrado (`pypdf`/`pdfminer`) e nunca carrega o PDF inteiro na memória. O agente fatia apenas o lote atual em imagens PNG (`180 DPI`) e lê visualmente página por página.
- **Divisão Semântica por Subcapítulos**: Mapeia o Sumário calculando o deslocamento exato (`offset = pagina_pdf - pagina_livro`) e divide o livro em lotes coesos de 10 a 25 páginas, separando sempre **Teoria** de **Listas de Exercícios/Resoluções** sem cortar demonstrações ao meio.
- **Estratégia Híbrida de Figuras**:
  - Gráficos de funções, eixos cartesianos e diagramas geométricos são recriados nativamente em código vetorial **`TikZ` / `pgfplots`**.
  - Ilustrações artísticas ou desenhos manuais não vetorizáveis são recortados e limpos com ganho de contraste via `scripts/crop_figure.py`.
- **Zero Configuração Manual de LaTeX**: O script `scripts/setup_env.py` instala automaticamente `PyMuPDF` + `Pillow` e baixa o binário portátil do **Tectonic** em `./bin/`, dispensando instalações pesadas de TeX Live ou MiKTeX.
- **Persistência entre Sessões de Chat**: Todo o progresso fica salvo em `roadmap.json` e `progress.json`. Você pode fechar a IDE a qualquer momento, abrir um novo chat dias depois e pedir apenas *"Continue de onde parou"*.

---

## 🗂️ Arquitetura do Repositório

```text
.
├── .agent/
│   └── skills/
│       └── book-resurrect/
│           └── SKILL.md           # Protocolo mestre canônico da Skill (3 Fases)
├── .cursor/
│   └── rules/
│       └── book-resurrect.mdc     # Adaptador automático para Cursor IDE
├── .github/
│   └── copilot-instructions.md    # Adaptador automático para GitHub Copilot
├── CLAUDE.md                      # Adaptador automático para Claude Code (CLI)
├── .windsurfrules                 # Adaptador automático para Windsurf IDE
├── scripts/
│   ├── setup_env.py               # Instala/verifica PyMuPDF, Pillow e binário portátil do Tectonic
│   ├── slice_pdf.py               # Renderiza intervalos de páginas do PDF em PNG (150-200 DPI)
│   ├── crop_figure.py             # Recorta e binariza figuras manuais não vetorizáveis
│   └── compile_check.py           # Compila main.tex via Tectonic e renderiza páginas compiladas
├── templates/
│   ├── main.tex                   # Arquivo mestre LaTeX modular (classe book, B5)
│   └── preambulo.tex              # Pacotes matemáticos, TikZ, booktabs e caixas tcolorbox
├── .gitignore                     # Ignora build/, bin/, temp_pages/, __pycache__/
└── README.md                      # Documentação completa de uso e arquitetura
```

Quando um livro está em processo de recuperação, o agente cria automaticamente na raiz:
- `roadmap.json`: Mapa completo de subcapítulos, intervalos de páginas (`book_start`/`book_end` vs. `pdf_start`/`pdf_end`) e arquivos `.tex` de destino.
- `progress.json`: Estado de execução de cada lote (`pending`, `in_progress`, `completed`).
- `main.tex` e `preambulo.tex`: Copiados de `templates/` e atualizados com os `\include{capitulos/capXX}`.
- `capitulos/`: Arquivos `.tex` modulares de cada capítulo.
- `figuras/`: Figuras recortadas e tratadas via `crop_figure.py`.
- `build/`: Diretório de saída contendo `build/main.pdf`, logs de compilação e `build/compiled_preview/`.

---

## 🚀 Como Usar Passo a Passo

### 1. Preparação Inicial
1. Clone este repositório (ou copie sua estrutura para a pasta do seu projeto).
2. Coloque o arquivo `.pdf` escaneado do livro na raiz do workspace (ex.: `meu_livro.pdf`).

### 2. Iniciar um Livro Novo (`Fase 0` — Mapeamento e Setup)
Abra o chat do agente na sua IDE favorita (Antigravity, Cursor, Claude Code, Windsurf ou GitHub Copilot) e envie:

> **"Inicie a recuperação do livro `meu_livro.pdf` executando a Fase 0 da skill `book-resurrect`."**

O que o agente fará automaticamente na **Fase 0**:
1. Executará `python scripts/setup_env.py` para garantir `PyMuPDF`, `Pillow` e o compilador portátil `tectonic`.
2. Copiará `templates/main.tex` e `templates/preambulo.tex` para a raiz e criará `capitulos/`, `figuras/` e `build/`.
3. Renderizará as primeiras 15 páginas do PDF em `build/temp_pages/` e lerá visualmente o **Sumário**.
4. Calculará o deslocamento exato de páginas (`offset = pagina_pdf - pagina_livro`) e dividirá o livro em lotes semânticos por subcapítulos completos (separando Teoria de Exercícios).
5. Salvará `roadmap.json` e `progress.json`, criará os arquivos `.tex` vazios em `capitulos/` e apresentará a tabela completa de lotes para sua confirmação.

---

### 3. Executar Lotes de Transcrição (`Fase 1` e `Fase 2`)

#### Opção A — Executar 1 lote por vez (Comportamento Padrão com Revisão)
Para transcrever um único lote, compilar e revisar o resultado antes de prosseguir:

> **"Execute o próximo lote pendente."**

#### Opção B — Executar $N$ lotes seguidos em sequência
Se desejar que o agente avance múltiplos subcapítulos em um único turno (compilando e salvando `progress.json` ao final de cada lote):

> **"Rode 3 lotes seguidos."** *(ou a quantidade $N$ desejada)*

---

### 4. Como Continuar de Onde Parou em um Novo Chat
Quando o histórico de conversa ficar longo ou você reabrir a IDE em outro dia, basta abrir uma **nova sessão de chat** limpa e digitar:

> **"Continue de onde parou."**
> *(ou **"Continue de onde parou e execute os próximos 2 lotes."**)*

O agente lerá imediatamente `progress.json` e `roadmap.json`, identificará todos os lotes já marcados como `"completed"` sem refazê-los e retomará exatamente no primeiro lote com status `"pending"`.

---

## 🛠️ Utilitários de Linha de Comando (`scripts/`)

Você (ou o agente) também pode invocar os utilitários diretamente via terminal:

1. **Verificar/Instalar Ambiente (`setup_env.py`)**:
   ```bash
   python scripts/setup_env.py
   ```
2. **Fatiar Intervalo de Páginas do PDF em PNG (`slice_pdf.py`)**:
   ```bash
   python scripts/slice_pdf.py --pdf "meu_livro.pdf" --start 1 --end 15 --out build/temp_pages --dpi 180
   ```
3. **Recortar e Limpar Figura Manual (`crop_figure.py`)**:
   ```bash
   python scripts/crop_figure.py --image build/temp_pages/page_012.png --bbox 0.15,0.25,0.85,0.60 --out figuras/fig_1_1.png
   ```
4. **Compilar `main.tex` e Gerar Preview de Revisão (`compile_check.py`)**:
   ```bash
   python scripts/compile_check.py --main main.tex --outdir build --render-last 5
   ```

---

## 🎨 Ambientes LaTeX Disponíveis em `preambulo.tex`

O template inclui quatro caixas semânticas baseadas em `tcolorbox` (`breakable` entre páginas) prontas para uso nos capítulos:

```latex
\begin{definicao}{ Conceito ou Nome }
Enunciado formal da definição...
\end{definicao}

\begin{teorema}{ Nome do Teorema }
Enunciado matemático do teorema...
\end{teorema}

\begin{exemplo}{ 1.1 — Aplicação Direta }
Enunciado e passo a passo do exemplo...
\end{exemplo}

\begin{caixaformulas}{ Identidades Fundamentais }
Resumo de fórmulas importantes do capítulo...
\end{caixaformulas}
```
Além disso, estão disponíveis os ambientes `\begin{demonstracao} ... \end{demonstracao}` e `\begin{solucao} ... \end{solucao}`.
