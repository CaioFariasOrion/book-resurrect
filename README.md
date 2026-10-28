# book-resurrect: Pipeline Editorial de Recuperação e Tradução de Livros

O **book-resurrect** é um framework editorial e skill universal para agentes de inteligência artificial (Antigravity, Cursor, Claude Code, Windsurf e GitHub Copilot). Seu propósito vai além da digitalização convencional: ele foi concebido para derrubar as barreiras de tempo, idioma e degradação física que mantêm o conhecimento científico e cultural isolado em páginas impressas.

Independente da época em que a obra foi concebida, do nível de desgaste do papel, de manchas de digitalização ou da complexidade do conteúdo, o pipeline é capaz de recuperar, modernizar e verter livros legados para qualquer idioma contemporâneo. O resultado é entregue em formatos digitais abertos e sustentáveis, compiláveis diretamente em PDF no padrão tipográfico acadêmico B5 (baseado nas diretrizes da SBM e Springer) ou em Markdown semântico para leitura em dispositivos modernos e leitores de EPUB.

Na versão **v2.1**, o ecossistema consolida triagem em três blocos, esteira paralela com pool de subagentes concorrentes, revisão editorial desacoplada com auditoria ética em `ERRATA.md` e empacotamento com abertura editorial padronizada e despacho automático para a raiz.

---

## 1. Transposição Universal de Conhecimento

O conhecimento humano acumulado ao longo dos séculos com frequência fica retido em edições esgotadas, cópias físicas degradadas ou restrito ao idioma de sua publicação original. O pipeline editorial do **book-resurrect** dissolve essas limitações por meio de três modalidades estruturadas de transposição:

- **Transcrição Fiel (1:1):** Direcionada à salvaguarda patrimonial e edições de referência crítica. O texto, a pontuação, o desenvolvimento do raciocínio e o estilo original são transcritos com fidelidade absoluta, transpondo imagens rasterizadas em código tipográfico puro e gráficos vetoriais paramétricos.
- **Modernização Lexical e Ortográfica:** Voltada para obras históricas cujo acesso didático é dificultado por normas ortográficas arcaicas ou grafias pré-reforma (como arcaísmos do português dos séculos XIX e XX). O motor atualiza o vocabulário e a ortografia para a norma culta contemporânea sob regras explícitas, preservando rigorosamente o estilo formal, a voz original e a cadência do autor.
- **Tradução Técnica Universal:** Permite transpor tratados e manuais técnicos de qualquer idioma original (como árabe, russo, alemão, francês, latim ou inglês) diretamente para o português contemporâneo ou qualquer outro idioma de destino. O processo segue o princípio da **Inviolabilidade Notacional**: toda a álgebra, matrizes, operadores lógicos, variáveis e limites matemáticos permanecem 100% intocados sob trava sintática (`<translation_syntax_lock>`), traduzindo apenas a prosa didática e os conceitos estruturais ao redor das equações.
- **Independência de Formato (Dual-Engine):** O pipeline aceita qualquer material escaneado e direciona a obra para o motor ideal:
  1. *Exatas (LaTeX e TikZ):* Gera código TeX modular em B5, reconstruindo diagramas geométricos e gráficos de funções como vetores nativos.
  2. *Humanas (Markdown e EPUB):* Gera arquivos `.md` semânticos com notas de rodapé padronizadas e metadados estruturados, prontos para compilação em EPUB e PDF via Pandoc.

---

## 2. Destaques da Arquitetura v2.1

- **Visão Multimodal Fatiada:** Não utiliza extratores de texto bruto quebrados (como pypdf ou pdfminer). O agente fatia o PDF em PNGs de 180 DPI por lote via `slice_pdf.py` e realiza a leitura visual direta.
- **Detecção e Divisão de Folha Dupla:** Identifica escaneamentos abertos em folha dupla (booklet) via `split_double_pages.py`, fatiando-os verticalmente em páginas simples ordenadas.
- **Triagem Interativa em 3 Blocos:** Classifica a obra antes da geração do estado (`roadmap.json` e `progress.json`):
  1. *Propósito:* Resgate Fiel, Modernização Didática ou Tradução Técnica.
  2. *Natureza:* Exatas (LaTeX/TikZ) ou Humanas (Markdown/EPUB).
  3. *Figuras:* Híbrido inteligente (código TikZ e recorte) ou Recorte total.
- **Design System SBM/Springer:** Preâmbulo acadêmico padronizado em B5 com microtipografia (`microtype`), pacotes `tasks`, `multicol`, `tabularx`, caixas com fio de 2.5pt (`definicao`, `teorema`, `proposicao`, `lema`, `caixaformulas`), exemplos em texto corrido e tabelas no padrão `booktabs`.
- **Fase 4 Desacoplada (Revisão e Errata):** Auditoria acionada sob demanda via `@book-resurrect revisar`:
  1. *Camada 1 (Auto-Cura de Layout):* Varre `build/main.log`, localiza transbordamentos de margem (`Overfull \hbox`), reconfigura tabelas e insere respiro opaco (`fill=white, inner sep=1.5pt`) em rótulos de gráficos TikZ.
  2. *Camada 2 (Errata Humana-no-Loop):* Proíbe a IA de alterar raciocínios matemáticos ou o texto do autor silenciosamente. Divergências são catalogadas em `ERRATA.md` com escolhas padronizadas (`[M] Manter`, `[C] Corrigir no texto`, `[N] Nota de Rodapé`).
  3. *Camada 3 (Empacotamento):* Insere a capa sangrada na Página 1, Folha de Rosto na Página 2, Ficha Técnica/Manifesto institucional com a logo da fênix na Página 3, Sumário na Página 4 e copia o PDF final para `./<Titulo>_<Autor>.pdf`.
- **Modo Autônomo Zero-Touch (Fase 3):** Suporta esteira paralela com pool de até 3 subagentes concorrentes operando em arquivos `.tex` isolados, com consolidação pelo Modo Maestro.

---

## 3. Estrutura do Repositório

```text
.
├── .agent/
│   └── skills/
│       └── book-resurrect/
│           └── SKILL.md             # Protocolo canônico completo da Skill (Fases 0 a 4)
├── .cursor/rules/                   # Adaptador de regras para Cursor IDE
├── .github/                         # Adaptador para GitHub Copilot
├── CLAUDE.md                        # Adaptador para Claude Code CLI
├── .windsurfrules                   # Adaptador para Windsurf IDE
├── assets/
│   └── logo-blue.png                # Logo oficial da Book Resurrect para a Ficha Técnica
├── scripts/
│   ├── init_book.py                 # Provisionador de pastas isoladas para novos livros
│   ├── setup_env.py                 # Instalador e verificador de ambiente e Tectonic
│   ├── split_double_pages.py         # Divisão vertical de folhas duplas em formato paisagem
│   ├── slice_pdf.py                 # Renderizador de intervalos de páginas do PDF em PNG
│   ├── crop_figure.py               # Recorte e limpeza binarizada de figuras manuais
│   └── compile_check.py             # Compilador Tectonic, self-healing e despacho do PDF
├── templates/
│   ├── main.tex                     # Estrutura mestra com abertura editorial internacional
│   ├── preambulo.tex                # Preâmbulo canônico SBM/Springer v2.1
│   └── metadata.yaml                # Metadados para compilação EPUB via Pandoc
├── requirements.txt                 # Dependências Python oficiais (pymupdf, Pillow, pypdf)
├── CONTRIBUTING.md                  # Guia de contribuição e padrões técnicos
└── README.md                        # Documentação técnica do projeto
```

---

## 4. Instalação e Requisitos

### Requisitos do Sistema
- Python 3.10 ou superior.
- Git instalado.
- Conexão com a internet no primeiro uso para download do compilador portátil Tectonic e pacotes TeX.

### Instalação das Dependências Python
```bash
pip install -r requirements.txt
```

### Configuração Inicial do Ambiente
Execute o verificador oficial para certificar os módulos Python e baixar o executável do Tectonic em `./bin/`:
```bash
python scripts/setup_env.py
```

### Instalação Global da Skill no Antigravity / Gemini
Para disponibilizar a skill em qualquer projeto no computador:
```powershell
# Criar diretório e copiar SKILL.md
New-Item -ItemType Directory -Force "$env:USERPROFILE\.gemini\config\skills\book-resurrect"
Copy-Item ".agent\skills\book-resurrect\SKILL.md" "$env:USERPROFILE\.gemini\config\skills\book-resurrect\SKILL.md"

# Criar junção para acesso central dos scripts pelo motor
New-Item -ItemType Junction -Force -Path "$env:USERPROFILE\.gemini\book-resurrect-engine" -Target (Get-Location).Path
```

---

## 5. Guia de Uso Passo a Passo

### Passo 1: Provisionar a Pasta de um Novo Livro
Mantenha o repositório da skill limpo. Sempre provisione uma pasta exclusiva para cada obra:
```bash
python scripts/init_book.py --pdf "caminho/do/livro_escaneado.pdf" --dest "../pasta-do-novo-livro"
```
O script copia os templates, scripts, adaptadores, a logo em `assets/`, o arquivo PDF e gera o `CONTEXT.md`. Se desejar incluir capa, coloque `capa.png` ou `capa.jpg` na raiz da pasta criada.

### Passo 2: Executar a Triagem e a Fase 0
Abra a pasta do novo livro no editor e envie o comando:
```text
@book-resurrect @livro.pdf
```
O agente executará:
1. `split_double_pages.py` para inspecionar geometria de folha dupla.
2. Abertura da Triagem Interativa em 3 Blocos.
3. Leitura visual do sumário e cálculo de offset (`offset = pagina_pdf - pagina_livro`).
4. Criação de `roadmap.json` e `progress.json` com os lotes de 10 a 25 páginas.
5. Criação dos arquivos modulares em `capitulos/capXX.tex`.

### Passo 3: Execução dos Lotes (Fases 1 a 3)
- **Modo Passo a Passo:** Peça ao agente *"Execute o próximo lote pendente"*. Ele transcreverá as páginas, criará as figuras TikZ ou recortes em `figuras/`, validará chaves e compilará via `compile_check.py`.
- **Modo Autônomo (Zero-Touch):** Envie *@book-resurrect recupere este livro*. O Maestro disparará o pool de subagentes concorrentes até esgotar a fila e consolidará o documento.

### Passo 4: Revisão Editorial e Fechamento (Fase 4)
Após a transcrição de todos os capítulos, abra uma nova sessão de chat limpa na pasta do livro e envie:
```text
@book-resurrect revisar
```
O agente executará a auditoria de layout (resolvendo `Overfull \hbox`), catalogará divergências históricas em `ERRATA.md` com perguntas padronizadas e compilará o PDF final.

---

## 6. Abertura Editorial Padronizada (Página a Página)

Os livros compilados pelo pipeline seguem a estrutura de abertura internacional:

1. **Página 1 (Capa Sangrada):** Se existir `capa.png` ou `capa.jpg` na raiz, o LaTeX projeta a imagem em sangria total B5 (`\paperwidth` por `\paperheight`) via TikZ overlay sem bordas brancas.
2. **Página 2 (Folha de Rosto):** Título da obra, autor e o selo rodapé *"Edição Vetorial Recuperada via Book Resurrect"*, centralizados e limpos.
3. **Página 3 (Verso da Folha de Rosto: Ficha Técnica e Manifesto):** Sem numeração de página (`\thispagestyle{empty}`), com a logo da fênix azul centralizada (`width=2.2cm`), manifesto de preservação científica no padrão SBM/Springer, nota de acesso aberto educacional e o link oficial:
   `https://github.com/CaioFariasOrion/book-resurrect`
4. **Página 4 (Sumário):** Início imediato de `\tableofcontents` com controle de quebra de página para eliminar qualquer folha em branco intermediária.

---

## 7. Utilitários de Linha de Comando (`scripts/`)

- `setup_env.py`: verifica `pymupdf`, `Pillow`, `pypdf` e provisiona `tectonic.exe` em `./bin/`.
- `split_double_pages.py <arquivo.pdf>`: divide folhas duplas em formato paisagem em páginas simples verticais.
- `slice_pdf.py --pdf <arquivo.pdf> --start X --end Y --out <pasta>`: renderiza páginas em PNG (180 DPI).
- `crop_figure.py --image <png> --bbox x0,y0,x1,y1 --out <destino.png>`: recorta e limpa figuras manuais.
- `compile_check.py --main main.tex --outdir build`: compila com Tectonic, gera preview das últimas páginas e despacha o PDF nomeado para a raiz.
- `init_book.py --pdf <arquivo.pdf> --dest <pasta>`: inicializa uma pasta de livro completa e isolada.

---

## 8. Licença e Propósito Educacional

Este projeto é desenvolvido para fins educacionais, científicos e de preservação de obras históricas sob modelo de acesso aberto. Todos os direitos morais dos autores originais são integralmente preservados.
