# book-resurrect: Pipeline Editorial de Recuperação e Tradução de Livros em LaTeX (PDF)

O **book-resurrect** é um framework editorial e skill universal para agentes de inteligência artificial (Antigravity, Cursor, Claude Code, Windsurf e GitHub Copilot). Seu propósito é recuperar, modernizar e traduzir obras impressas digitalizadas em PDF, entregando um projeto LaTeX modular compilado em PDF pelo Tectonic no padrão tipográfico acadêmico B5 (SBM e Springer).

Todo livro processado pelo `book-resurrect` utiliza **um único pipeline em LaTeX**, **um único compilador (`compile_check.py` / Tectonic)** e **um único template mestre (`templates/main.tex` + `templates/preambulo_base.tex`)**, selecionando apenas o perfil de preâmbulo (`perfil_tecnico.tex` ou `perfil_texto.tex`) conforme a natureza da obra.

---

## 1. Modalidades de Transposição e Perfis de Preâmbulo

### Modalidades de Edição (`translation_mode`)
- **Transcrição Fiel (1:1):** O texto, a pontuação e o desenvolvimento original são transcritos integralmente, convertendo páginas escaneadas em código tipográfico LaTeX limpo.
- **Modernização Lexical e Ortográfica:** Atualiza grafias pré-reforma e arcaísmos para a norma culta vigente, preservando a voz e a construção frasal do autor.
- **Tradução Técnica Universal:** Traduz a prosa e os termos estruturais para o idioma de destino mantendo intocada toda a notação matemática, variáveis e limites.

### Perfis de Preâmbulo (`profile` em `metadata.yaml`)
1. **Perfil `tecnico` (`templates/perfil_tecnico.tex`):** Para obras de exatas, física e engenharia. Inclui ambientes semânticos (`definicao`, `teorema`, `exemplo`, `caixaformulas`, `demonstracao`, `solucao`), operadores matemáticos em português (`\sen`, `\tg`, `\mdc`, `\mmc`) e reconstrução vetorial em `TikZ` / `pgfplots` com microcompilação isolada na Fase 4.
2. **Perfil `texto` (`templates/perfil_texto.tex`):** Para obras de humanas, literatura e ensaios em texto corrido. Usa a mesma abertura canônica e o mesmo compilador Tectonic, sem ambientes de teorema e sem TikZ, preservando citações (`quote`, `epigrafe`), notas de rodapé, fórmulas avulsas e figuras recortadas em alta nitidez (`crop_figure.py`) quando presentes no original.

---

## 2. Destaques da Arquitetura

- **Fase 0 Determinística (`init_book_fase0.py`):** Em menos de 3 segundos, detecta e divide folhas duplas verticalmente via PyMuPDF, extrai a capa (`capa.png`), mapeia os lotes sem lacunas, gera `metadata.yaml`, `roadmap.json`, `progress.json` e sincroniza `main.tex`, `preambulo_base.tex` e `perfil_<profile>.tex`.
- **Descarte Estrito de Pré-Textuais Comerciais e Sumário Impresso:** Tudo o que vier antes do sumário no livro físico original (orelha, créditos da editora, ISBN, ficha catalográfica antiga) é descartado. O sumário impresso no papel nunca é transcrito; o sumário final é gerado automaticamente por `\tableofcontents` com links clicáveis.
- **Linter Editorial Integrado (`compile_check.py --lint`):** Verifica antes da compilação caracteres especiais sem escape (`%`, `&`, `#`, `_`), comandos `\chapter` duplicados, números de capítulo digitados manualmente no título e macros fora da lista permitida do perfil.
- **Worker Pool Paralelo (Fase 3):** Até 8 subagentes concorrentes escrevendo em arquivos `capitulos/capXX.tex` isolados, com validação atômica via `compile_check.py --lint --only capXX`.
- **Fase 4 Desacoplada com Cache SHA-256 (Exclusiva do Perfil `tecnico`):**
  - `scripts/audit_and_fix_tikz.py`: normaliza ambientes `figure` e remove qualquer ocorrência indevida de `fill=white` em nós TikZ (rótulos matemáticos têm fundo 100% transparente e âncoras direcionais em espaço limpo).
  - `scripts/render_isolated_figures.py`: compila cada figura TikZ isoladamente via classe `standalone` em paralelo com cache SHA-256 e gravação de `manifest.json` sob lock de arquivo.

---

## 3. Estrutura do Repositório

```text
.
├── .agent/
│   └── skills/
│       └── book-resurrect/
│           └── SKILL.md                  # Protocolo canônico completo da Skill (Fases 0 a 4)
├── .cursor/rules/                        # Adaptador para Cursor IDE
├── .github/                              # Adaptador para GitHub Copilot
├── CLAUDE.md                             # Adaptador para Claude Code CLI
├── .windsurfrules                        # Adaptador para Windsurf IDE
├── assets/
│   └── logo-blue.png                     # Logo oficial da Book Resurrect para o Manifesto Editorial
├── scripts/
│   ├── init_book.py                      # Provisionador de pastas isoladas para novos livros
│   ├── init_book_fase0.py                # Mapeador determinístico da Fase 0 (< 3s) e split de folha dupla
│   ├── setup_env.py                      # Verificador de ambiente Python e compilador portátil Tectonic
│   ├── slice_pdf.py                      # Renderizador de páginas do PDF em PNG com cache
│   ├── crop_figure.py                    # Recorte e limpeza de figuras em alta nitidez (--list-boxes)
│   ├── compile_check.py                  # Linter editorial (--lint), compilador Tectonic (--only) e despacho PDF
│   ├── render_isolated_figures.py        # Microcompilador paralelo de figuras TikZ com cache SHA-256
│   └── audit_and_fix_tikz.py             # Saneador geométrico de TikZ e gerador de galeria de revisão
├── templates/
│   ├── main.tex                          # Estrutura mestra com abertura editorial canônica (Págs. 1 a 4)
│   ├── preambulo_base.tex                # Preâmbulo base universal B5 (capa, folha de rosto, manifesto, csquotes)
│   ├── perfil_tecnico.tex                # Extensão para obras técnicas (teoremas, definições, TikZ)
│   ├── perfil_texto.tex                  # Extensão mínima para obras de humanas em texto corrido
│   ├── preambulo.tex                     # Wrapper de compatibilidade (carrega base + perfil_tecnico)
│   └── metadata.yaml                     # Metadados do projeto e seleção de perfil (tecnico ou texto)
├── instalar_skills.py                    # Sincronizador global e local da skill
├── requirements.txt                      # Dependências Python oficiais (pymupdf, Pillow)
├── CONTEXT.md                            # Quadro de bordo de arquitetura do motor
├── CONTRIBUTING.md                       # Guia de contribuição e padrões técnicos
└── README.md                             # Documentação técnica do projeto
```

---

## 4. Instalação e Configuração

```bash
pip install -r requirements.txt
python scripts/setup_env.py
python instalar_skills.py
```

---

## 5. Guia de Uso Passo a Passo

### Passo 1: Provisionar a Pasta de um Novo Livro
```bash
python scripts/init_book.py --pdf "caminho/do/livro_escaneado.pdf" --dest "../pasta-do-novo-livro"
```

### Passo 2: Triagem (`ask_question`) e Fase 0 Instantânea (`init_book_fase0.py`)
```bash
python scripts/init_book_fase0.py --pdf "livro.pdf" --profile tecnico --translation-mode fiel --figure-mode hibrido --title "Título" --author "Autor" --pre-render
```

### Passo 3: Transcrição e Validação Local (Fases 1 a 3)
```bash
python scripts/compile_check.py --lint --only cap01 --render-last 0
```

### Passo 4: Curadoria de Figuras TikZ (Perfil `tecnico`) e Fechamento Final
```bash
python scripts/audit_and_fix_tikz.py --skip-render
python scripts/render_isolated_figures.py
python scripts/compile_check.py --lint --main main.tex --outdir build --render-last 5
```

---

## 6. Abertura Editorial Canônica (Idêntica para Todos os Livros)

1. **Página 1 (Capa Sangrada):** `\inserircapa` projeta `capa.png` ou `capa.jpg` em sangria total B5 (`160mm x 230mm`).
2. **Página 2 (Folha de Rosto):** `\folhaderosto` com título, autor e a chancela *"Edição Vetorial Recuperada via Book Resurrect"*.
3. **Página 3 (Manifesto Editorial):** `\manifestoeditorial` sem numeração de página, com a logo `assets/logo-blue.png`, manifesto institucional e link oficial do repositório.
4. **Página 4 (Sumário Automático):** `\tableofcontents` gerado pelo compilador com links clicáveis.
5. **Página 5 em diante:** Conteúdo da obra (`\chapter*{Introdução}` com `\addcontentsline` para pré/pós-textuais e `\chapter{Título}` para capítulos numerados).
