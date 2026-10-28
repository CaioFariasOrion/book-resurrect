# book-resurrect: Pipeline Editorial de Recuperacao de Livros para LaTeX e Markdown

O **book-resurrect** e um framework editorial e skill universal para agentes de inteligencia artificial (Antigravity, Cursor, Claude Code, Windsurf e GitHub Copilot). Seu objetivo e converter livros escaneados em PDF (mesmo com baixa qualidade, manchas de scanner ou notacao matematica densa) em projetos modulares, vetoriais e compilaveis.

Na versao **v2.1**, o ecossistema consolida o Design System academico no formato editorial B5 (baseado nos padroes da SBM e Springer), provisionamento isolado por obra, revisao editorial desacoplada com trava etica em `ERRATA.md` e empacotamento com injecao automatica de capa e despacho semantico para a raiz.

---

## 1. Destaques da Arquitetura v2.1

- **Visao Multimodal Fatiada:** Nao utiliza extratores de texto bruto quebrados (como pypdf ou pdfminer). O agente fatia o PDF em PNGs de 180 DPI por lote via `slice_pdf.py` e realiza a leitura visual direta.
- **Deteccao e Divisao de Folha Dupla:** Identifica escaneamentos abertos em folha dupla (booklet) via `split_double_pages.py`, fatiando-os verticalmente em paginas simples ordenadas.
- **Triagem Interativa em 3 Blocos:** Classifica a obra antes da geracao do estado (`roadmap.json` e `progress.json`):
  1. *Proposito:* Resgate Fiel, Modernizacao Didatica ou Traducao Tecnica.
  2. *Natureza:* Exatas (LaTeX/TikZ) ou Humanas (Markdown/EPUB).
  3. *Figuras:* Hibrido inteligente (código TikZ e recorte) ou Recorte total.
- **Design System SBM/Springer:** Preambulo academico padronizado em B5 com microtipografia (`microtype`), pacotes `tasks`, `multicol`, `tabularx`, caixas com fio de 2.5pt (`definicao`, `teorema`, `proposicao`, `lema`, `caixaformulas`), exemplos em texto corrido e tabelas no padrao `booktabs`.
- **Fase 4 Desacoplada (Revisao e Errata):** Auditoria acionada sob demanda via `@book-resurrect revisar`:
  1. *Camada 1 (Auto-Cura de Layout):* Varre `build/main.log`, localiza transbordamentos de margem (`Overfull \hbox`), reconfigura tabelas e insere respiro opaco (`fill=white, inner sep=1.5pt`) em rotulos de graficos TikZ.
  2. *Camada 2 (Errata Humana-no-Loop):* Proibe a IA de alterar raciocinios matematicos ou o texto do autor silenciosamente. Divergencias sao catalogadas em `ERRATA.md` com escolhas padronizadas (`[M] Manter`, `[C] Corrigir no texto`, `[N] Nota de Rodape`).
  3. *Camada 3 (Empacotamento):* Insere a capa sangrada na Pagina 1, Folha de Rosto na Pagina 2, Ficha Tecnica/Manifesto institucional com a logo da fenix na Pagina 3, Sumario na Pagina 4 e copia o PDF final para `./<Titulo>_<Autor>.pdf`.
- **Modo Autonomo Zero-Touch (Fase 3):** Suporta esteira paralela com pool de ate 3 subagentes concorrentes operando em arquivos `.tex` isolados, com consolidacao pelo Modo Maestro.

---

## 2. Estrutura do Repositorio

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
│   └── logo-blue.png                # Logo oficial da Book Resurrect para a Ficha Tecnica
├── scripts/
│   ├── init_book.py                 # Provisionador de pastas isoladas para novos livros
│   ├── setup_env.py                 # Instalador e verificador de ambiente e Tectonic
│   ├── split_double_pages.py         # Divisao vertical de folhas duplas em formato paisagem
│   ├── slice_pdf.py                 # Renderizador de intervalos de paginas do PDF em PNG
│   ├── crop_figure.py               # Recorte e limpeza binarizada de figuras manuais
│   └── compile_check.py             # Compilador Tectonic, self-healing e despacho do PDF
├── templates/
│   ├── main.tex                     # Estrutura mestra com abertura editorial internacional
│   ├── preambulo.tex                # Preambulo canônico SBM/Springer v2.1
│   └── metadata.yaml                # Metadados para compilacao EPUB via Pandoc
├── requirements.txt                 # Dependencias Python oficiais (pymupdf, Pillow, pypdf)
├── CONTRIBUTING.md                  # Guia de contribuicao e padroes tecnicos
└── README.md                        # Documentacao tecnica do projeto
```

---

## 3. Instalacao e Requisitos

### Requisitos do Sistema
- Python 3.10 ou superior.
- Git instalado.
- Conexao com a internet no primeiro uso para download do compilador portatil Tectonic e pacotes TeX.

### Instalacao das Dependencias Python
```bash
pip install -r requirements.txt
```

### Configuracao Inicial do Ambiente
Execute o verificador oficial para certificar os modulos Python e baixar o executavel do Tectonic em `./bin/`:
```bash
python scripts/setup_env.py
```

### Instalacao Global da Skill no Antigravity / Gemini
Para disponibilizar a skill em qualquer projeto no computador:
```powershell
# Criar diretorio e copiar SKILL.md
New-Item -ItemType Directory -Force "$env:USERPROFILE\.gemini\config\skills\book-resurrect"
Copy-Item ".agent\skills\book-resurrect\SKILL.md" "$env:USERPROFILE\.gemini\config\skills\book-resurrect\SKILL.md"

# Criar juncao para acesso central dos scripts pelo motor
New-Item -ItemType Junction -Force -Path "$env:USERPROFILE\.gemini\book-resurrect-engine" -Target (Get-Location).Path
```

---

## 4. Guia de Uso Passo a Passo

### Passo 1: Provisionar a Pasta de um Novo Livro
Mantenha o repositorio da skill limpo. Sempre provisione uma pasta exclusiva para cada obra:
```bash
python scripts/init_book.py --pdf "caminho/do/livro_escaneado.pdf" --dest "../pasta-do-novo-livro"
```
O script copia os templates, scripts, adaptadores, a logo em `assets/`, o arquivo PDF e gera o `CONTEXT.md`. Se desejar incluir capa, coloque `capa.png` ou `capa.jpg` na raiz da pasta criada.

### Passo 2: Executar a Triagem e a Fase 0
Abra a pasta do novo livro no editor e envie o comando:
```text
@book-resurrect @livro.pdf
```
O agente executara:
1. `split_double_pages.py` para inspecionar geometria de folha dupla.
2. Abertura da Triagem Interativa em 3 Blocos.
3. Leitura visual do sumario e calculo de offset (`offset = pagina_pdf - pagina_livro`).
4. Criacao de `roadmap.json` e `progress.json` com os lotes de 10 a 25 paginas.
5. Criacao dos arquivos modulares em `capitulos/capXX.tex`.

### Passo 3: Execucao dos Lotes (Fases 1 a 3)
- **Modo Passo a Passo:** Peça ao agente *"Execute o proximo lote pendente"*. Ele transcrevera as paginas, criara as figuras TikZ ou recortes em `figuras/`, validara chaves e compilara via `compile_check.py`.
- **Modo Autonomo (Zero-Touch):** Envie *@book-resurrect recupere este livro*. O Maestro disparara o pool de subagentes concorrentes ate esgotar a fila e consolidara o documento.

### Passo 4: Revisao Editorial e Fechamento (Fase 4)
Apos a transcricao de todos os capitulos, abra uma nova sessao de chat limpa na pasta do livro e envie:
```text
@book-resurrect revisar
```
O agente executara a auditoria de layout (resolvendo `Overfull \hbox`), catalogara divergencias historicas em `ERRATA.md` com perguntas padronizadas e compilara o PDF final.

---

## 5. Abertura Editorial Padronizada (Página a Página)

Os livros compilados pelo pipeline seguem a estrutura de abertura internacional:

1. **Pagina 1 (Capa Sangrada):** Se existir `capa.png` ou `capa.jpg` na raiz, o LaTeX projeta a imagem em sangria total B5 (`\paperwidth` por `\paperheight`) via TikZ overlay sem bordas brancas.
2. **Pagina 2 (Folha de Rosto):** Titulo da obra, autor e o selo rodapé *"Edicao Vetorial Recuperada via Book Resurrect"*, centralizados e limpos.
3. **Pagina 3 (Verso da Folha de Rosto: Ficha Tecnica e Manifesto):** Sem numeracao de pagina (`\thispagestyle{empty}`), com a logo da fenix azul centralizada (`width=2.2cm`), manifesto de preservacao cientifica no padrao SBM/Springer, nota de acesso aberto educacional e o link oficial:
   `https://github.com/CaioFariasOrion/book-resurrect`
4. **Pagina 4 (Sumario):** Início imediato de `\tableofcontents` com controle de quebra de pagina para eliminar qualquer folha em branco intermediaria.

---

## 6. Utilitarios de Linha de Comando (`scripts/`)

- `setup_env.py`: verifica `pymupdf`, `Pillow`, `pypdf` e provisiona `tectonic.exe` em `./bin/`.
- `split_double_pages.py <arquivo.pdf>`: divide folhas duplas em formato paisagem em paginas simples verticais.
- `slice_pdf.py --pdf <arquivo.pdf> --start X --end Y --out <pasta>`: renderiza paginas em PNG (180 DPI).
- `crop_figure.py --image <png> --bbox x0,y0,x1,y1 --out <destino.png>`: recorta e limpa figuras manuais.
- `compile_check.py --main main.tex --outdir build`: compila com Tectonic, gera preview das ultimas paginas e despacha o PDF nomeado para a raiz.
- `init_book.py --pdf <arquivo.pdf> --dest <pasta>`: inicializa uma pasta de livro completa e isolada.

---

## 7. Licenca e Proposito Educacional

Este projeto e desenvolvido para fins educacionais, cientificos e de preservacao de obras historicas sob modelo de acesso aberto. Todos os direitos morais dos autores originais sao integralmente preservados.
