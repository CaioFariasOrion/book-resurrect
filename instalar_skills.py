#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
instalar_skills.py: Script autonomo de sincronizacao de skills, regras e ambiente.

Sincroniza e instala:
1. Skills Globais (%USERPROFILE%/.gemini/config/skills/ e %USERPROFILE%/.agent/skills/)
2. Regras e Instrucoes Globais (%USERPROFILE%/.gemini/config/rules/ e %USERPROFILE%/.gemini/GEMINI.md)
3. Skill de Workspace (.agent/skills/book-resurrect/SKILL.md)
4. Scripts e Templates Auxiliares (scripts/ e templates/)

Uso:
    python instalar_skills.py                      # Instala tudo no computador atual
    python instalar_skills.py --global-only        # Instala apenas as configuracoes e skills globais
    python instalar_skills.py --workspace-only     # Instala apenas as skills e scripts do workspace local
    python instalar_skills.py --workspace /path    # Especifica a pasta do workspace alvo
"""

import argparse
import os
import sys
from pathlib import Path

# ==============================================================================
# CONTEUDO INTEGRAL DOS ARQUIVOS (STRINGS MULTILINE)
# ==============================================================================

GLOBAL_SKILLS = {}
GLOBAL_RULES = {}
WORKSPACE_FILES = {}

# --- 1. SKILLS GLOBAIS ---
GLOBAL_SKILLS["skills/depurar-bug/SKILL.md"] = r'''---
name: depurar-bug
description: Diagnostica bugs e erros por evidência antes de corrigir. Use quando houver traceback, comportamento inesperado, teste falhando ou erro 404/500.
---

# Depurar bug

Não corrija por tentativa e erro.

## Processo
1. Reproduza: comando, entrada, comportamento esperado vs. observado.
2. Leia o erro inteiro. Em tracebacks Python, comece pelo último trecho que está no código do projeto.
3. Liste de 1 a 3 hipóteses e diga como cada uma seria confirmada ou descartada.
4. Teste as hipóteses (logs, `python manage.py shell`, `python manage.py check`, `python manage.py showmigrations`, leitura da query). Remova qualquer print ou log temporário depois.
5. Confirme a causa raiz e só então aplique a menor correção.
6. Verifique que o erro original sumiu e sugira um teste que impeça o bug de voltar.

## Proibido
- Esconder o erro com `try/except` genérico.
- Desativar validação, teste ou checagem de segurança para fazer passar.

Se a primeira hipótese estiver errada, diga isso e atualize o diagnóstico.'''
GLOBAL_SKILLS["skills/explicar-mudanca/SKILL.md"] = r'''---
name: explicar-mudanca
description: Explica em português simples o que foi alterado e por quê. Use quando o usuário pedir "me explica o que você fez", "o que mudou" ou quiser entender e apresentar a mudança para o time ou orientador.
---

# Explicar mudança

Somente leitura. Leia o `git diff` e explique para quem não escreveu o código.

## Entrega
1. **Resumo** em 2 ou 3 frases: o problema e como foi resolvido.
2. **Por arquivo:** o que mudou, por quê, e o trecho-chave explicado linha por linha em linguagem simples.
3. **Caminho do fluxo:** como uma requisição passa pelas partes alteradas (URL -> view -> model -> template, quando fizer sentido).
4. **Como testar manualmente**, passo a passo.
5. **O que pode quebrar** e o que ainda não foi verificado.
6. **Perguntas prováveis** que um colega ou orientador faria, com as respostas.
7. **Glossário** dos termos técnicos usados.

Seja honesto: se algo no código parece frágil, errado ou desnecessário, diga.'''
GLOBAL_SKILLS["skills/grill-me/SKILL.md"] = r'''﻿---
name: grill-me
description: Entrevista o usuário com perguntas, uma de cada vez, antes de planejar ou programar. Use quando o usuário digitar /grill-me ou pedir para ser entrevistado sobre uma ideia, tarefa ou funcionalidade antes de implementar.
---

# Grill Me

Objetivo: chegar a um entendimento compartilhado e sem pontas soltas antes de escrever qualquer código. Não suponha: pergunte.

## Regras
1. NÃO escreva código, não edite arquivos e não rode comandos que alterem algo durante a entrevista.
2. Faça UMA pergunta por vez e espere a resposta.
3. Em cada pergunta, inclua a resposta que você recomendaria e o motivo, para o usuário só confirmar ou corrigir.
4. Se a resposta puder ser descoberta lendo o projeto, leia o projeto em vez de perguntar.
5. Percorra as decisões em ordem, do mais geral ao mais específico: objetivo, quem usa, escopo, o que fica de fora, dados envolvidos, permissões, casos de borda, tratamento de erros, como testar.
6. Se a resposta for vaga ou contradisser algo dito antes, aponte isso e peça para esclarecer.
7. Explique termos técnicos em linguagem simples, porque o usuário quer entender o que será feito no código.

## Encerramento
Quando não restar dúvida relevante, entregue:
1. Resumo das decisões tomadas.
2. Premissas assumidas e riscos.
3. Plano de implementação em passos numerados, com os arquivos que serão alterados.
4. Pergunte: "Posso implementar?" e só comece depois da confirmação.
'''
GLOBAL_SKILLS["skills/investigar-codigo/SKILL.md"] = r'''---
name: investigar-codigo
description: Investiga e explica como uma parte do código funciona, sem modificar nada. Use quando o usuário pedir para entender, mapear ou rastrear um fluxo, ou antes de mexer em modelos, rotas, login, permissões ou migrations.
---

# Investigar código

Somente leitura. Não edite arquivos nem rode comandos que alterem algo.

## Processo
1. Localize o ponto de entrada (em Django: `urls.py` -> view).
2. Siga o fluxo: view -> forms/serializers -> models -> templates. Veja também permissões (mixins, decorators, middleware), signals, admin e as configurações relevantes em `settings`.
3. Procure quem chama o trecho (busca por nome) e quais testes o cobrem.
4. Não leia o repositório inteiro; leia só o que participa do fluxo.

## Entrega
- Como funciona hoje, em linguagem simples.
- Arquivos envolvidos, na ordem do fluxo.
- O que pode quebrar se isso for alterado.
- Testes existentes e lacunas.
- O que você não conseguiu confirmar.'''
GLOBAL_SKILLS["skills/migracoes-django/SKILL.md"] = r'''---
name: migracoes-django
description: Conduz alterações de modelos e migrations do Django com segurança. Use quando um model for criado ou alterado, quando o usuário pedir makemigrations ou migrate, ou quando houver conflito de migrations.
---

# Migrações Django

## Processo
1. Descubra qual banco o `settings` usa. Se não for claramente um banco local de desenvolvimento, pare e pergunte.
2. Veja o que vai ser gerado: `python manage.py makemigrations --dry-run -v 3`.
3. Gere com `python manage.py makemigrations` e LEIA o arquivo criado.
4. Alerte sobre operações perigosas: `RemoveField`, `DeleteModel`, `RenameField`, `AlterField` que reduz tamanho ou torna obrigatório, `RunSQL`, `RunPython`. Explique o que cada uma faz com os dados existentes.
5. Para ver o SQL: `python manage.py sqlmigrate <app> <numero>`.
6. Migrations de dados (`RunPython`) devem ter função de volta (reversa).
7. NUNCA edite uma migration que já foi aplicada ou enviada ao repositório. Crie outra.
8. Em trabalho em equipe: antes de gerar, confira se há migrations novas dos colegas. Se houver conflito, explique e proponha uma migration de merge.
9. Só rode `python manage.py migrate` depois da confirmação do usuário, e sugira backup se o banco não for descartável.
10. Ao final, `python manage.py makemigrations --check --dry-run` deve confirmar que não falta nada.'''
GLOBAL_SKILLS["skills/pesquisar-antes-de-codar/SKILL.md"] = r'''---
name: pesquisar-antes-de-codar
description: Consulta a documentação oficial, na versão usada pelo projeto, antes de implementar. Use quando a tarefa depender de biblioteca, framework, API externa ou comportamento que varia por versão.
---

# Pesquisar antes de codar

## Processo
1. Descubra a versão em uso (`requirements.txt`, `pyproject.toml`, `pip show <pacote>`).
2. Consulte primeiro a documentação oficial dessa versão; depois changelog e release notes.
3. Compare com o que o projeto já faz e siga os padrões existentes.
4. Implemente conforme a documentação. Não copie trechos de blogs ou fóruns sem checar a compatibilidade.
5. No resumo final, cite o link ou a seção da documentação que embasou a decisão.

Se não achar fonte confiável, diga isso em vez de supor.'''
GLOBAL_SKILLS["skills/revisar-mudancas/SKILL.md"] = r'''---
name: revisar-mudancas
description: Revisa as alterações antes de commit ou pull request, com checklist de segurança e Django. Use quando o usuário pedir revisão, "pode commitar?" ou antes de abrir PR. Não cria commit.
---

# Revisar mudanças

Somente leitura. NÃO crie commit nem faça push.

## Processo
1. Rode `git status` e leia o `git diff` completo.
2. Escopo: cada alteração pertence à tarefa? Aponte o que sobrou. Comentários, docstrings ou textos que já existiam e foram alterados, removidos ou reformatados são achado Crítico, porque comentário já commitado não pode ser tocado.
3. Arquivos que não devem entrar: `.env`, chaves, dumps, `db.sqlite3`, uploads em `media/`, `__pycache__`, prints e logs de debug.
4. Checklist Django:
   - Migrations: há nova migration? Procure `RemoveField`, `DeleteModel`, `AlterField`, `RunSQL`, `RunPython`. Confira se não há migrations conflitantes.
   - Permissões: a view exige login? O usuário só acessa os próprios dados (cuidado com IDOR, ou seja, acessar o objeto de outra pessoa trocando o ID na URL)? Staff vs. usuário comum?
   - Formulários: `{% csrf_token %}` presente, sem `csrf_exempt` desnecessário.
   - Templates: uso de `|safe` ou `mark_safe` com dados do usuário (XSS).
   - Consultas: SQL cru, `extra`, N+1 (faltou `select_related` ou `prefetch_related`).
   - Arquivos: upload e download validam caminho, tipo e permissão (path traversal).
   - Configuração: `DEBUG`, `ALLOWED_HOSTS`, `SECRET_KEY` não foram enfraquecidos.
   - Dados pessoais em logs, prints ou testes.
5. Verifique se testes foram adicionados ou atualizados e se `python manage.py check` passa.

## Entrega
Lista de achados com severidade (Crítico, Alto, Médio, Baixo), o arquivo e a linha, e a sugestão de correção. Termine com: "Pronto para commit" ou "Corrigir antes".'''

# --- 2. REGRAS E INSTRUCOES GLOBAIS ---
GLOBAL_RULES["rules/estilo-do-projeto.md"] = r'''---
trigger: always_on
description: Estilo de código, comentários, texto e commits. Nunca alterar comentários existentes. Escrever como uma pessoa da equipe escreveria.
---

# Estilo do projeto

## Regra absoluta: código e comentários que já existem
- NUNCA altere, reescreva, remova, traduza, reformate ou "melhore" comentários, docstrings, mensagens ou textos que já existem no repositório. Eles já foram commitados e são intocáveis.
- Só escreva comentários nas linhas NOVAS que a tarefa criar.
- Se achar um comentário errado ou desatualizado, avise no resumo final e não corrija.
- Não rode formatadores (black, ruff format, isort, prettier) em arquivos inteiros. O diff deve conter só as linhas necessárias para a tarefa.

## Estilo
- Se o projeto tiver regras próprias na raiz (AGENTS.md, GEMINI.md, CONTRIBUTING.md ou similar), elas mandam e valem mais que esta regra.
- Em dúvida sobre o estilo, abra arquivos vizinhos e imite (nomes, estrutura, idioma, formatação).

## Comentários e docstrings novos
- Comente só quando o código sozinho não explica o porquê. Nunca descreva o que uma linha óbvia já diz.
- Direto ao ponto: de 1 a 4 frases, sem seções rotuladas ("Args:", "Returns:", "Nota:", "Importante:") e sem repetir o nome da função.
- Se o comportamento é óbvio pela assinatura, não comente.
- Cubra só o que não dá para ver de cara: a regra de negócio, o motivo de um parâmetro estranho, quem mais usa a função.
- Exemplo de uso só quando a chamada não for óbvia pela assinatura.
- Sem comentários de narração ("# Passo 1", "# Agora vamos..."), sem código comentado, sem TODO e sem print de debug.

Bom (explica a regra e o motivo do parâmetro, nada além):

    def _tem_conflito_horario(trilha, data, hora_inicio, hora_fim, excluir_pk=None):
        """True se já existe outra aula programada da mesma trilha no mesmo dia
        com sobreposição de horário (checagem clássica de overlap). `excluir_pk`
        tira a própria aula da comparação ao reagendar. Regra compartilhada por
        reagendar e criar aula avulsa."""

Ruim (repete a assinatura, tem seções e explica o óbvio):

    def somar(a, b):
        """Função que soma dois números.

        Args:
            a: o primeiro número.
            b: o segundo número.

        Returns:
            A soma de a e b.
        """

## Texto novo (código, comentários, mensagens, commits, templates e documentação)
- Não use travessão nem meia-risca. Use vírgula, ponto, dois-pontos ou parênteses.
- Sem emojis.
- Sem adjetivos de marketing ("robusto", "elegante", "poderoso") nem frases de efeito.
- Escreva como alguém da equipe escreveria: direto, frases curtas, português natural, sem formalidade exagerada.
- Mensagens de erro e textos de interface curtos e no tom do projeto.

## Arquivos
- Não crie arquivos de documentação, notas ou planos dentro do repositório sem pedido (README, PLAN.md, NOTES.md etc.).
- Não adicione arquivos ou pastas de configuração de ferramentas ao repositório.

## Commits (somente quando o usuário pedir)
- Antes, leia `git log -10` e siga o padrão de mensagem do projeto (idioma, tamanho, prefixos).
- Mensagem curta e objetiva, descrevendo a mudança.
- Não adicione rodapés ou trailers de ferramenta (`Co-authored-by`, "Generated by" etc.).

## Antes de terminar
Releia o diff. Confirme que nenhuma linha antiga foi alterada ou removida sem necessidade. Reescreva apenas os comentários e textos que VOCÊ escreveu nesta tarefa e que fujam destas regras (longos, óbvios ou com travessão).'''
GLOBAL_RULES["rules/fluxo-de-trabalho.md"] = r'''---
trigger: always_on
description: Como trabalhar - ler antes de mudar, escopo mínimo, verificar e relatar com honestidade, explicando em português simples.
---

# Fluxo de trabalho

## Idioma e explicação
- Responda em português do Brasil.
- Explique termos técnicos em linguagem simples. O usuário quer entender o que está sendo feito para poder explicar ao time.

## Antes de mudar
- Leia o código relacionado. Não adivinhe o que dá para descobrir no projeto.
- Se a tarefa for ampla ou envolver modelos, migrations, login/permissões ou mais de 3 arquivos, proponha um plano curto e espere confirmação.

## Escopo
- Faça só o que foi pedido, com a menor mudança possível. Sem refatorações, renomeações ou limpezas extras.
- Problemas vistos fora do escopo: relate no final, não corrija.
- Se precisar ampliar o escopo, explique o motivo antes.

## Verificação
- Em projetos Django, rode `python manage.py check` e os testes relacionados, quando existirem.
- Mostre o resultado real. Nunca diga que funciona sem ter executado.
- Nunca desative testes, validações ou configurações de segurança para "fazer passar". Se algo falhar, diga.

## Resumo final (sempre)
1. O que mudou (arquivo -> o quê).
2. O que foi verificado e como.
3. O que NÃO foi verificado.
4. Riscos e pontos de atenção.
5. Como testar manualmente.'''
GLOBAL_RULES["rules/seguranca-e-dados.md"] = r'''---
trigger: always_on
description: Limites de segurança do agente - ações destrutivas, segredos, banco de dados e dados pessoais.
---

# Segurança e dados

## Pergunte e espere confirmação antes de
- apagar arquivos ou pastas, ou sobrescrever arquivos grandes;
- usar `git commit`, `git push`, `git reset --hard`, `git clean`, `git checkout -- .`, `git rebase` ou reescrever histórico (só faça commit ou push quando o usuário pedir);
- instalar, atualizar ou remover dependências (`pip install`, `npm install`, editar `requirements.txt`);
- rodar `migrate`, `flush`, `loaddata`, `dumpdata` ou qualquer comando que altere ou exporte dados; antes, mostre qual banco o `settings` está usando;
- editar migrations que já existem ou arquivos de configuração (`settings`, Docker, CI, deploy).

## Segredos
- Nunca leia, mostre, edite ou faça commit de `.env`, chaves, tokens, senhas ou certificados.
- Nunca coloque segredos no código; use variáveis de ambiente.
- Se encontrar um segredo exposto, avise sem repetir o valor.

## Dados pessoais
- Plataformas educacionais (como o PETI) lidam com dados de alunos, professores e participantes: trate como dados pessoais (LGPD).
- Não use dados reais em testes, fixtures, logs, exemplos ou prints.
- Não exporte dumps do banco nem envie dados para serviços externos.

## Arquivos e uploads
- Ao ler ou servir arquivos a partir de caminhos recebidos do usuário, valide o caminho (`safe_join`, bloqueie `..`) e verifique a permissão.

## Na dúvida
Pare e pergunte, explicando o risco em uma frase.'''
GLOBAL_RULES["GEMINI.md"] = r'''﻿# Narração de trabalho (sempre ativa)

Enquanto executa tarefas com ferramentas, narre o que está fazendo em tempo real.

## Regras
1. Antes de cada bloco de ações, escreva UMA frase curta dizendo o que vai fazer e por quê.
2. Depois de ler arquivos ou rodar comandos, escreva UMA frase dizendo o que encontrou e qual é o próximo passo.
3. Ao trabalhar em plano com etapas, rotule: "**Passo 1:** `arquivo.py` — o que muda".
4. Cite nomes de arquivos, funções e imports entre crases.
5. Nunca fique em silêncio por mais de 2 chamadas de ferramenta seguidas.
6. Se algo der errado ou o plano mudar, diga isso na hora, antes de corrigir.
7. Frases curtas, tom natural, sem enrolação. Sem repetir o que o diff já mostra.

## Exemplo do estilo esperado
Vamos executar o plano! Começando pelos arquivos base para entender o que já existe.
[lê arquivos]
Tudo lido. Vou implementar os 4 passos em paralelo onde possível.
**Passo 1:** `urls.py` — remover a rota estática e adicionar a rota protegida.
[edita]
Os imports `LoginRequiredMixin` e `View` já existem. Preciso adicionar `mimetypes` e `os`.
[edita]
**Passo 3:** `core/urls.py` — proteger `/em-construcao/`.
'''

# --- 3. SKILL DE WORKSPACE E SCRIPTS/TEMPLATES AUXILIARES ---
WORKSPACE_FILES[".agent/skills/book-resurrect/SKILL.md"] = r'''---
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
'''
WORKSPACE_FILES["scripts/compile_check.py"] = r'''#!/usr/bin/env python3
"""
compile_check.py — Compilador e verificador visual de fechamento de lote (Self-Healing).

Responsabilidades:
1. Localizar o binário `tectonic` (em ./bin/ ou no PATH) ou fazer fallback para `latexmk`.
2. Compilar `main.tex` gerando o PDF em `build/main.pdf`.
3. Em caso de falha (exit code != 0), exibir as últimas 40 linhas do log de erro
   e encerrar com código 1 para que o agente corrija a sintaxe LaTeX em loop.
4. Em caso de sucesso (exit code == 0), renderizar as últimas N páginas compiladas
   em `build/compiled_preview/comp_page_XXX.png` para revisão visual do agente.
"""

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
BIN_DIR = WORKSPACE_ROOT / "bin"


def resolve_compiler(main_tex: Path, outdir: Path) -> tuple[str, list[str]]:
    """Localiza tectonic (local ou PATH) ou retorna comando fallback com latexmk."""
    exe_name = "tectonic.exe" if platform.system().lower() == "windows" else "tectonic"
    local_tectonic = BIN_DIR / exe_name

    tectonic_bin: str | None = None
    if local_tectonic.is_file():
        tectonic_bin = str(local_tectonic)
    else:
        tectonic_bin = shutil.which("tectonic")

    if tectonic_bin:
        cmd = [
            tectonic_bin,
            "--outdir",
            str(outdir),
            "--keep-logs",
            str(main_tex),
        ]
        return "tectonic", cmd

    latexmk_bin = shutil.which("latexmk")
    if latexmk_bin:
        cmd = [
            latexmk_bin,
            "-pdf",
            "-interaction=nonstopmode",
            f"-output-directory={outdir.as_posix()}",
            str(main_tex),
        ]
        return "latexmk", cmd

    pdflatex_bin = shutil.which("pdflatex")
    if pdflatex_bin:
        cmd = [
            pdflatex_bin,
            "-interaction=nonstopmode",
            f"-output-directory={outdir.as_posix()}",
            str(main_tex),
        ]
        return "pdflatex", cmd

    raise RuntimeError(
        "Nenhum compilador LaTeX encontrado (tectonic, latexmk ou pdflatex). "
        "Execute `python scripts/setup_env.py` primeiro."
    )


def render_last_compiled_pages(
    pdf_path: Path, preview_dir: Path, count: int, dpi: int = 160
) -> list[Path]:
    """Renderiza as últimas `count` páginas do PDF compilado em PNG."""
    try:
        import fitz
    except ImportError:
        print(
            "[AVISO] PyMuPDF (fitz) ausente; pulando renderização de preview.",
            file=sys.stderr,
        )
        return []

    preview_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []

    with fitz.open(pdf_path) as doc:
        total = len(doc)
        if total == 0 or count <= 0:
            return []
        start_page = max(1, total - count + 1)
        for page_num in range(start_page, total + 1):
            page = doc.load_page(page_num - 1)
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            out_png = preview_dir / f"comp_page_{page_num:03d}.png"
            pix.save(str(out_png))
            rendered.append(out_png)

    return rendered


def extract_error_tail(stdout_text: str, stderr_text: str, log_file: Path, max_lines: int = 40) -> str:
    """Extrai as últimas `max_lines` linhas combinando saída do processo e arquivo .log."""
    combined_lines: list[str] = []
    for stream_text in (stdout_text, stderr_text):
        if stream_text:
            combined_lines.extend(stream_text.splitlines())

    if log_file.is_file():
        try:
            log_lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
            combined_lines.extend(["--- Trecho final do arquivo .log ---", *log_lines[-max_lines:]])
        except Exception:
            pass

    tail = combined_lines[-max_lines:] if len(combined_lines) > max_lines else combined_lines
    return "\n".join(tail)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Compila main.tex via Tectonic (ou latexmk) e renderiza páginas compiladas para inspeção."
    )
    parser.add_argument(
        "--main",
        type=Path,
        default=Path("main.tex"),
        help="Arquivo mestre LaTeX a ser compilado (padrão: main.tex).",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("build"),
        help="Diretório de saída da compilação (padrão: build).",
    )
    parser.add_argument(
        "--render-last",
        type=int,
        default=5,
        help="Quantidade de páginas finais do PDF compilado para converter em PNG (padrão: 5).",
    )

    args = parser.parse_args()

    if not args.main.is_file():
        print(f"[ERRO] Arquivo mestre não encontrado: {args.main}", file=sys.stderr)
        return 1

    args.outdir.mkdir(parents=True, exist_ok=True)
    # Garante também que o subdiretório build/capitulos exista para arquivos .aux de \include
    (args.outdir / "capitulos").mkdir(parents=True, exist_ok=True)

    try:
        compiler_name, cmd = resolve_compiler(args.main, args.outdir)
    except RuntimeError as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1

    print(f"[INFO] Compilando '{args.main}' com {compiler_name}...")
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

    stem = args.main.stem
    log_file = args.outdir / f"{stem}.log"
    compiled_pdf = args.outdir / f"{stem}.pdf"

    if proc.returncode != 0 or not compiled_pdf.is_file():
        print(
            f"[ERRO] Compilação LaTeX falhou (exit code {proc.returncode}). "
            "Últimas 40 linhas do log:",
            file=sys.stderr,
        )
        print("=" * 72, file=sys.stderr)
        print(extract_error_tail(proc.stdout, proc.stderr, log_file, max_lines=40), file=sys.stderr)
        print("=" * 72, file=sys.stderr)
        return 1

    print(f"[OK] Compilação concluída com sucesso: {compiled_pdf.as_posix()}")

    preview_dir = args.outdir / "compiled_preview"
    previews = render_last_compiled_pages(
        pdf_path=compiled_pdf,
        preview_dir=preview_dir,
        count=args.render_last,
    )
    if previews:
        print(f"[OK] {len(previews)} página(s) renderizada(s) para revisão visual:")
        for p in previews:
            print(p.as_posix())

    return 0


if __name__ == "__main__":
    sys.exit(main())
'''
WORKSPACE_FILES["scripts/crop_figure.py"] = r'''#!/usr/bin/env python3
"""
crop_figure.py — Recorte e limpeza de figuras não vetorizáveis de páginas escaneadas.

Recorta uma bounding box normalizada (x0,y0,x1,y1 em [0.0, 1.0]) de uma imagem PNG,
converte para tons de cinza limpos com ganho de contraste e remoção de fundo
acinzentado típico de scanners/fotos, salvando o resultado em alta nitidez.
"""

import argparse
import sys
from pathlib import Path


def parse_bbox(bbox_str: str) -> tuple[float, float, float, float]:
    """Valida e converte a string 'x0,y0,x1,y1' em 4 floats normalizados [0.0, 1.0]."""
    parts = [p.strip() for p in bbox_str.split(",")]
    if len(parts) != 4:
        raise ValueError(
            f"--bbox deve conter exatamente 4 valores separados por vírgula 'x0,y0,x1,y1' (recebido: '{bbox_str}')"
        )
    try:
        x0, y0, x1, y1 = (float(v) for v in parts)
    except ValueError as exc:
        raise ValueError(f"Valores numéricos inválidos em --bbox: '{bbox_str}'") from exc

    if not (0.0 <= x0 < x1 <= 1.0 and 0.0 <= y0 < y1 <= 1.0):
        raise ValueError(
            f"Coordenadas --bbox devem respeitar 0.0 <= x0 < x1 <= 1.0 e 0.0 <= y0 < y1 <= 1.0 "
            f"(recebido: {x0}, {y0}, {x1}, {y1})"
        )
    return x0, y0, x1, y1


def crop_and_clean_figure(
    image_path: Path,
    bbox: tuple[float, float, float, float],
    out_path: Path,
    white_threshold: int = 215,
) -> Path:
    """Recorta a região especificada e aplica limpeza de fundo de scanner e nitidez."""
    try:
        from PIL import Image, ImageEnhance, ImageOps
    except ImportError:
        print(
            "[ERRO] Pillow (PIL) não está instalado. Execute `python scripts/setup_env.py` primeiro.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not image_path.is_file():
        raise FileNotFoundError(f"Imagem de entrada não encontrada: {image_path}")

    with Image.open(image_path) as img:
        width, height = img.size
        x0, y0, x1, y1 = bbox
        left = max(0, int(round(x0 * width)))
        top = max(0, int(round(y0 * height)))
        right = min(width, int(round(x1 * width)))
        bottom = min(height, int(round(y1 * height)))

        if right <= left or bottom <= top:
            raise ValueError("Região recortada possui dimensões nulas ou inválidas.")

        cropped = img.crop((left, top, right, bottom))

        # Converte para escala de cinza e normaliza os níveis
        gray = cropped.convert("L")
        normalized = ImageOps.autocontrast(gray, cutoff=1)

        # Aumenta contraste e nitidez para destacar traços de ilustrações
        contrasted = ImageEnhance.Contrast(normalized).enhance(1.35)
        sharpened = ImageEnhance.Sharpness(contrasted).enhance(1.5)

        # Remove o fundo acinzentado típico de digitalização tornando brancos puros os tons claros
        cleaned = sharpened.point(lambda p: 255 if p >= white_threshold else p)
        final_rgb = cleaned.convert("RGB")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        final_rgb.save(str(out_path), format="PNG", optimize=True)

    return out_path


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Recorta e limpa figuras de páginas escaneadas usando coordenadas relativas [0.0, 1.0]."
    )
    parser.add_argument(
        "--image",
        required=True,
        type=Path,
        help="Caminho da imagem PNG da página (ex.: build/temp_pages/page_010.png).",
    )
    parser.add_argument(
        "--bbox",
        required=True,
        type=str,
        help="Coordenadas relativas 'x0,y0,x1,y1' no intervalo de 0.0 a 1.0.",
    )
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Caminho do arquivo PNG de saída (ex.: figuras/fig_1_1.png).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=215,
        help="Limiar de branqueamento de fundo (0-255, padrão: 215).",
    )

    args = parser.parse_args()

    try:
        bbox = parse_bbox(args.bbox)
        saved_path = crop_and_clean_figure(
            image_path=args.image,
            bbox=bbox,
            out_path=args.out,
            white_threshold=args.threshold,
        )
    except Exception as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1

    print(f"[OK] Figura recortada e tratada salva em: {saved_path.as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''
WORKSPACE_FILES["scripts/setup_env.py"] = r'''#!/usr/bin/env python3
"""
setup_env.py — Inicializador e verificador de ambiente do book-resurrect.

Responsabilidades:
1. Verificar se PyMuPDF (fitz) e Pillow (PIL) estão instalados; caso contrário,
   instalá-los via pip.
2. Verificar se o compilador LaTeX portátil Tectonic está disponível no PATH
   ou em ./bin/tectonic(.exe). Caso não esteja, baixar automaticamente o binário
   oficial da API de Releases do GitHub (tectonic-typesetting/tectonic) e extraí-lo
   em ./bin/.
"""

import argparse
import importlib.util
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
BIN_DIR = WORKSPACE_ROOT / "bin"

FALLBACK_VERSION = "0.15.0"
FALLBACK_BASE_URL = (
    f"https://github.com/tectonic-typesetting/tectonic/releases/download/"
    f"tectonic%40{FALLBACK_VERSION}"
)


def check_and_install_python_deps() -> bool:
    """Verifica e instala pymupdf (fitz) e pillow (PIL) caso ausentes."""
    missing = []
    if importlib.util.find_spec("fitz") is None:
        missing.append("pymupdf")
    if importlib.util.find_spec("PIL") is None:
        missing.append("pillow")

    if not missing:
        print("[OK] Dependências Python verificadas: PyMuPDF (fitz) e Pillow (PIL).")
        return True

    print(f"[INFO] Instalando pacotes Python ausentes: {', '.join(missing)}...")
    cmd = [sys.executable, "-m", "pip", "install", *missing]
    try:
        subprocess.run(cmd, check=True)
        print("[OK] Pacotes Python instalados com sucesso.")
        return True
    except subprocess.CalledProcessError as exc:
        print(
            f"[ERRO] Falha ao instalar pacotes Python ({', '.join(missing)}): {exc}",
            file=sys.stderr,
        )
        return False


def get_local_tectonic_path() -> Path:
    """Retorna o caminho esperado para o binário portátil do Tectonic em ./bin/."""
    exe_name = "tectonic.exe" if platform.system().lower() == "windows" else "tectonic"
    return BIN_DIR / exe_name


def find_tectonic_binary() -> str | None:
    """Procura pelo executável tectonic em ./bin/ ou no PATH do sistema."""
    local_bin = get_local_tectonic_path()
    if local_bin.is_file():
        return str(local_bin)

    system_bin = shutil.which("tectonic")
    if system_bin:
        return system_bin

    return None


def _select_target_suffix() -> tuple[str, str]:
    """Determina o sufixo de plataforma e o nome do arquivo fallback do Tectonic."""
    sys_name = platform.system().lower()
    machine = platform.machine().lower()

    if sys_name == "windows":
        return (
            "x86_64-pc-windows-msvc.zip",
            f"tectonic-{FALLBACK_VERSION}-x86_64-pc-windows-msvc.zip",
        )
    if sys_name == "darwin":
        if machine in ("arm64", "aarch64"):
            return (
                "aarch64-apple-darwin.tar.gz",
                f"tectonic-{FALLBACK_VERSION}-aarch64-apple-darwin.tar.gz",
            )
        return (
            "x86_64-apple-darwin.tar.gz",
            f"tectonic-{FALLBACK_VERSION}-x86_64-apple-darwin.tar.gz",
        )
    # Linux
    if machine in ("arm64", "aarch64"):
        return (
            "aarch64-unknown-linux-musl.tar.gz",
            f"tectonic-{FALLBACK_VERSION}-aarch64-unknown-linux-musl.tar.gz",
        )
    return (
        "x86_64-unknown-linux-musl.tar.gz",
        f"tectonic-{FALLBACK_VERSION}-x86_64-unknown-linux-musl.tar.gz",
    )


def _resolve_download_url() -> str:
    """Consulta a API do GitHub Releases ou retorna a URL oficial estável de fallback."""
    target_suffix, fallback_filename = _select_target_suffix()
    api_url = "https://api.github.com/repos/tectonic-typesetting/tectonic/releases?per_page=10"

    req = urllib.request.Request(
        api_url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "book-resurrect-setup"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            releases = json.loads(resp.read().decode("utf-8"))
            for rel in releases:
                for asset in rel.get("assets", []):
                    name = asset.get("name", "")
                    if name.endswith(target_suffix):
                        return asset["browser_download_url"]
    except Exception as exc:
        print(f"[AVISO] Não foi possível consultar a API do GitHub ({exc}). Usando URL estável.")

    return f"{FALLBACK_BASE_URL}/{fallback_filename}"


def download_and_extract_tectonic() -> Path | None:
    """Baixa e extrai o binário portátil do Tectonic para ./bin/."""
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    download_url = _resolve_download_url()
    print(f"[INFO] Baixando Tectonic portátil de: {download_url}")

    req = urllib.request.Request(
        download_url, headers={"User-Agent": "book-resurrect-setup"}
    )
    suffix = ".zip" if download_url.endswith(".zip") else ".tar.gz"

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_path = Path(tmp_file.name)
            with urllib.request.urlopen(req, timeout=60) as response:
                shutil.copyfileobj(response, tmp_file)
    except urllib.error.URLError as exc:
        print(f"[ERRO] Falha no download do Tectonic: {exc}", file=sys.stderr)
        return None

    target_bin = get_local_tectonic_path()
    try:
        if suffix == ".zip":
            with zipfile.ZipFile(tmp_path, "r") as zf:
                for member in zf.namelist():
                    if Path(member).name.lower() in ("tectonic.exe", "tectonic"):
                        with zf.open(member) as src, open(target_bin, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                        break
        else:
            with tarfile.open(tmp_path, "r:gz") as tf:
                for member in tf.getmembers():
                    if Path(member.name).name in ("tectonic", "tectonic.exe"):
                        extracted = tf.extractfile(member)
                        if extracted is not None:
                            with extracted as src, open(target_bin, "wb") as dst:
                                shutil.copyfileobj(src, dst)
                            break

        if target_bin.is_file() and platform.system().lower() != "windows":
            target_bin.chmod(target_bin.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

        if target_bin.is_file():
            print(f"[OK] Tectonic extraído com sucesso em: {target_bin}")
            return target_bin
        print("[ERRO] Arquivo baixado não continha o executável tectonic.", file=sys.stderr)
        return None
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def verify_tectonic(bin_path: str) -> bool:
    """Executa `tectonic --version` para confirmar que o binário está operacional."""
    try:
        res = subprocess.run(
            [bin_path, "--version"],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
        version_str = res.stdout.strip() or res.stderr.strip()
        print(f"[OK] Compilador Tectonic operacional: {version_str} ({bin_path})")
        return True
    except Exception as exc:
        print(f"[ERRO] Falha ao executar Tectonic ({bin_path}): {exc}", file=sys.stderr)
        return False


def ensure_workspace_structure(init_dirs: bool = False) -> None:
    """Opcionalmente inicializa as pastas capitulos/, figuras/, build/ e templates na raiz."""
    if not init_dirs:
        return

    for folder in ("capitulos", "figuras", "build"):
        folder_path = WORKSPACE_ROOT / folder
        folder_path.mkdir(parents=True, exist_ok=True)

    templates_dir = WORKSPACE_ROOT / "templates"
    for tex_name in ("main.tex", "preambulo.tex"):
        src = templates_dir / tex_name
        dst = WORKSPACE_ROOT / tex_name
        if src.is_file() and not dst.exists():
            shutil.copy2(src, dst)
            print(f"[OK] Template copiado para a raiz: {tex_name}")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Verifica e instala PyMuPDF, Pillow e o compilador portátil Tectonic."
    )
    parser.add_argument(
        "--init-workspace",
        action="store_true",
        help="Cria as pastas capitulos/, figuras/, build/ e copia main.tex/preambulo.tex se ausentes.",
    )
    args = parser.parse_args()

    print("=== book-resurrect: Verificação de Ambiente ===")
    deps_ok = check_and_install_python_deps()

    tectonic_bin = find_tectonic_binary()
    if not tectonic_bin:
        print("[INFO] Tectonic não encontrado no PATH ou em ./bin/. Iniciando download portátil...")
        downloaded = download_and_extract_tectonic()
        if downloaded:
            tectonic_bin = str(downloaded)

    tectonic_ok = False
    if tectonic_bin:
        tectonic_ok = verify_tectonic(tectonic_bin)
    else:
        latexmk_bin = shutil.which("latexmk")
        if latexmk_bin:
            print(f"[AVISO] Tectonic indisponível, mas fallback latexmk detectado: {latexmk_bin}")
            tectonic_ok = True
        else:
            print(
                "[ERRO] Nenhum compilador LaTeX (tectonic ou latexmk) disponível.",
                file=sys.stderr,
            )

    ensure_workspace_structure(init_dirs=args.init_workspace)

    if deps_ok and tectonic_ok:
        print("=== Ambiente pronto para o book-resurrect! ===")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
'''
WORKSPACE_FILES["scripts/slice_pdf.py"] = r'''#!/usr/bin/env python3
"""
slice_pdf.py — Fatiador e renderizador de páginas de PDF para PNG (150-200 DPI).

Converte apenas o intervalo [start, end] (base 1, inclusivo) de um arquivo PDF
em imagens PNG numeradas (`page_001.png`, `page_002.png`, ...) para inspeção
visual multimodal do agente de IA sem sobrecarregar a memória.
"""

import argparse
import sys
from pathlib import Path


def slice_pdf(
    pdf_path: Path,
    start_page: int,
    end_page: int,
    out_dir: Path,
    dpi: int = 180,
) -> list[Path]:
    """Renderiza o intervalo [start_page, end_page] (1-based) do PDF em imagens PNG."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print(
            "[ERRO] PyMuPDF (fitz) não está instalado. Execute `python scripts/setup_env.py` primeiro.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not pdf_path.is_file():
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {pdf_path}")

    if start_page < 1:
        raise ValueError(f"--start deve ser >= 1 (recebido: {start_page})")
    if end_page < start_page:
        raise ValueError(
            f"--end ({end_page}) deve ser maior ou igual a --start ({start_page})"
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    generated_files: list[Path] = []

    with fitz.open(pdf_path) as doc:
        total_pages = len(doc)
        if start_page > total_pages:
            raise ValueError(
                f"Página inicial ({start_page}) excede o total de páginas do PDF ({total_pages})."
            )

        actual_end = min(end_page, total_pages)
        print(
            f"[INFO] PDF: '{pdf_path.name}' | Total de páginas: {total_pages} | "
            f"Renderizando intervalo: {start_page} a {actual_end} ({dpi} DPI)"
        )

        for page_num in range(start_page, actual_end + 1):
            page = doc.load_page(page_num - 1)
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            out_file = out_dir / f"page_{page_num:03d}.png"
            pix.save(str(out_file))
            generated_files.append(out_file)

    return generated_files


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Renderiza um intervalo de páginas de um PDF em arquivos PNG numerados."
    )
    parser.add_argument(
        "--pdf",
        required=True,
        type=Path,
        help="Caminho para o arquivo PDF de entrada.",
    )
    parser.add_argument(
        "--start",
        required=True,
        type=int,
        help="Página inicial do intervalo (base 1, inclusiva).",
    )
    parser.add_argument(
        "--end",
        required=True,
        type=int,
        help="Página final do intervalo (base 1, inclusiva).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("build/temp_pages"),
        help="Diretório de saída para as imagens PNG (padrão: build/temp_pages).",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=180,
        help="Resolução em DPI para renderização (padrão: 180).",
    )

    args = parser.parse_args()

    try:
        files = slice_pdf(
            pdf_path=args.pdf,
            start_page=args.start,
            end_page=args.end,
            out_dir=args.out,
            dpi=args.dpi,
        )
    except Exception as exc:
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1

    print(f"[OK] {len(files)} página(s) gerada(s):")
    for fpath in files:
        print(fpath.as_posix())

    return 0


if __name__ == "__main__":
    sys.exit(main())
'''
WORKSPACE_FILES["templates/main.tex"] = r'''\documentclass[11pt,b5paper,twoside,openright]{book}

\input{preambulo.tex}

\title{\textbf{Título do Livro Recuperado}}
\author{Autor Original \\ \small Edição Vetorial Recuperada via \texttt{book-resurrect}}
\date{\today}

\begin{document}

\frontmatter
\maketitle
\tableofcontents

\mainmatter
% Os capítulos gerados na Fase 0 e transcritos na Fase 1/2 são incluídos abaixo:
% \include{capitulos/cap01}
% \include{capitulos/cap02}

\end{document}
'''
WORKSPACE_FILES["templates/preambulo.tex"] = r'''% ==============================================================================
% preambulo.tex — Preâmbulo Canônico do Pipeline book-resurrect
% Compatível com Tectonic (XeTeX) e pdfLaTeX / latexmk
% ==============================================================================

% --- Codificação e Idioma ---
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[brazil]{babel}

% --- Geometria da Página (Papel B5 Editorial) ---
\usepackage[
    b5paper,
    top=2.2cm,
    bottom=2.2cm,
    inner=2.4cm,
    outer=1.8cm,
    headheight=14pt
]{geometry}

% --- Tipografia e Microtipografia ---
\usepackage{lmodern}
\usepackage{microtype}
\setlength{\parskip}{0.4em}
\setlength{\parindent}{1.25em}

% --- Matemática Avançada ---
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{amsfonts}
\usepackage{mathtools}
\usepackage{bm}
\usepackage{cancel}

% --- Tabelas, Figuras e Posicionamento ---
\usepackage{booktabs}
\usepackage{array}
\usepackage{multirow}
\usepackage{graphicx}
\usepackage{float}
\usepackage[font=small,labelfont=bf]{caption}
\usepackage{subcaption}
\usepackage{enumitem}

% --- Cores Personalizadas ---
\usepackage[dvipsnames,table]{xcolor}
\definecolor{defBlue}{HTML}{1A5276}
\definecolor{defBack}{HTML}{F2F7FA}
\definecolor{thmRed}{HTML}{7B241C}
\definecolor{thmBack}{HTML}{FDEDEC}
\definecolor{exGreen}{HTML}{1E8449}
\definecolor{exBack}{HTML}{EAFAF1}
\definecolor{formGold}{HTML}{9A7D0A}
\definecolor{formBack}{HTML}{FEF9E7}

% --- Gráficos Vetoriais (TikZ & pgfplots) ---
\usepackage{tikz}
\usetikzlibrary{
    arrows.meta,
    calc,
    positioning,
    patterns,
    angles,
    quotes,
    decorations.pathreplacing,
    shapes.geometric
}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}

% --- Cabeçalhos e Rodapés (fancyhdr) ---
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[LE,RO]{\thepage}
\fancyhead[RE]{\nouppercase{\leftmark}}
\fancyhead[LO]{\nouppercase{\rightmark}}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0pt}

% --- Caixas Semânticas (tcolorbox) ---
\usepackage{tcolorbox}
\tcbuselibrary{skins,breakable,theorems}

% 1. Ambiente de Definição: \begin{definicao}{Título} ... \end{definicao}
\newtcolorbox[auto counter, number within=chapter]{definicao}[2][]{
    enhanced,
    breakable,
    colback=defBack,
    colframe=defBlue,
    fonttitle=\bfseries,
    title={Definição~\thetcbcounter\ifx\relax#2\relax\else: #2\fi},
    arc=2mm,
    boxrule=0.8pt,
    left=3mm,
    right=3mm,
    top=2mm,
    bottom=2mm,
    #1
}

% 2. Ambiente de Teorema: \begin{teorema}{Título} ... \end{teorema}
\newtcolorbox[auto counter, number within=chapter]{teorema}[2][]{
    enhanced,
    breakable,
    colback=thmBack,
    colframe=thmRed,
    fonttitle=\bfseries,
    title={Teorema~\thetcbcounter\ifx\relax#2\relax\else: #2\fi},
    arc=2mm,
    boxrule=0.8pt,
    left=3mm,
    right=3mm,
    top=2mm,
    bottom=2mm,
    #1
}

% 3. Ambiente de Exemplo: \begin{exemplo}{Número ou Título} ... \end{exemplo}
\newtcolorbox[auto counter, number within=chapter]{exemplo}[2][]{
    enhanced,
    breakable,
    colback=exBack,
    colframe=exGreen,
    fonttitle=\bfseries,
    title={Exemplo\ifx\relax#2\relax~\thetcbcounter\else~#2\fi},
    arc=1.5mm,
    boxrule=0.6pt,
     borderline west={1.2mm}{0mm}{exGreen},
    left=3.5mm,
    right=3mm,
    top=2mm,
    bottom=2mm,
    #1
}

% 4. Ambiente de Caixa de Fórmulas: \begin{caixaformulas}{Título} ... \end{caixaformulas}
\newtcolorbox{caixaformulas}[2][]{
    enhanced,
    breakable,
    colback=formBack,
    colframe=formGold,
    fonttitle=\bfseries,
    title={\ifx\relax#2\relax Resumo de Fórmulas\else #2\fi},
    arc=2mm,
    boxrule=0.9pt,
    left=3mm,
    right=3mm,
    top=2mm,
    bottom=2mm,
    #1
}

% --- Ambiente de Demonstração / Solução ---
\newenvironment{solucao}{%
    \par\noindent\textbf{Solução.}\ \ignorespaces
}{%
    \hfill$\blacksquare$\par\medskip
}

\newenvironment{demonstracao}{%
    \par\noindent\textit{Demonstração.}\ \ignorespaces
}{%
    \hfill$\square$\par\medskip
}

% --- Hiperlinks e Metadados ---
\usepackage{hyperref}
\hypersetup{
    colorlinks=true,
    linkcolor=defBlue,
    citecolor=exGreen,
    urlcolor=defBlue,
    pdfborder={0 0 0}
}
'''

# ==============================================================================
# LOGICA DE INSTALACAO E RELATORIO
# ==============================================================================

def get_global_base_dir() -> Path:
    """Retorna o diretorio base ~/.gemini do usuario atual de forma compativel com Windows e Unix."""
    user_home = Path.home()
    return user_home / ".gemini"

def get_agent_global_dir() -> Path:
    """Retorna o diretorio base ~/.agent do usuario para espelhamento compativel."""
    user_home = Path.home()
    return user_home / ".agent"

def install_file(target_path: Path, content: str) -> tuple[bool, int]:
    """Escreve o conteudo garantindo codificacao UTF-8 e criando pastas pai."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    existed = target_path.is_file()
    
    # Escreve sempre em UTF-8 com quebras de linha normalizadas
    target_path.write_text(content, encoding="utf-8", newline="\n")
    byte_count = target_path.stat().st_size
    return existed, byte_count

def run_installation(install_global: bool, install_workspace: bool, mirror_agent: bool, workspace_dir: Path) -> int:
    report = []
    total_bytes = 0
    
    print("=" * 76)
    print("  INSTALADOR AUTONOMO DE SKILLS E CONFIGURACOES DE AGENTE")
    print("=" * 76)
    
    gemini_base = get_global_base_dir()
    agent_base = get_agent_global_dir()
    
    if install_global:
        print(f"\n[1/3] Instalando Skills Globais em: {gemini_base / 'config' / 'skills'}")
        for rel_path, content in GLOBAL_SKILLS.items():
            # rel_path é ex.: skills/depurar-bug/SKILL.md
            # destino em .gemini/config/skills/depurar-bug/SKILL.md
            subpath = rel_path[len("skills/"):] if rel_path.startswith("skills/") else rel_path
            dst = gemini_base / "config" / "skills" / subpath
            existed, b_size = install_file(dst, content)
            total_bytes += b_size
            status = "ATUALIZADO" if existed else "NOVO"
            report.append((status, f".gemini/config/skills/{subpath}", b_size))
            print(f"  [{status}] {dst.as_posix()} ({b_size} bytes)")
            
            # Espelhamento em .agent/skills/ para ferramentas que buscam em ~/.agent/skills/
            if mirror_agent:
                dst_agent = agent_base / "skills" / subpath
                existed_ag, b_size_ag = install_file(dst_agent, content)
                status_ag = "ATUALIZADO" if existed_ag else "NOVO"
                report.append((status_ag, f".agent/skills/{subpath}", b_size_ag))
        
        print(f"\n[2/3] Instalando Regras e Prompts Globais em: {gemini_base}")
        for rel_path, content in GLOBAL_RULES.items():
            if rel_path == "GEMINI.md":
                dst = gemini_base / "GEMINI.md"
                label = ".gemini/GEMINI.md"
            else:
                # rel_path é rules/estilo-do-projeto.md
                dst = gemini_base / "config" / rel_path
                label = f".gemini/config/{rel_path}"
            existed, b_size = install_file(dst, content)
            total_bytes += b_size
            status = "ATUALIZADO" if existed else "NOVO"
            report.append((status, label, b_size))
            print(f"  [{status}] {dst.as_posix()} ({b_size} bytes)")
    
    if install_workspace:
        print(f"\n[3/3] Instalando Skills e Scripts de Workspace em: {workspace_dir.resolve()}")
        for rel_path, content in WORKSPACE_FILES.items():
            dst = workspace_dir / rel_path
            existed, b_size = install_file(dst, content)
            total_bytes += b_size
            status = "ATUALIZADO" if existed else "NOVO"
            report.append((status, f"workspace/{rel_path}", b_size))
            print(f"  [{status}] {dst.as_posix()} ({b_size} bytes)")
    
    print("\n" + "=" * 76)
    print("  RELATORIO DE SINCRONIZACAO CONCLUIDA COM SUCESSO")
    print("=" * 76)
    print(f"{'STATUS':<12} | {'ARQUIVO':<48} | {'TAMANHO':>10}")
    print("-" * 76)
    for status, label, b_size in report:
        print(f"{status:<12} | {label:<48} | {b_size:>7} B")
    print("-" * 76)
    print(f"Total de arquivos gravados: {len(report)}")
    print(f"Volume total gravado: {total_bytes:,} bytes")
    print("Todas as skills e configuracoes estao 100% sincronizadas!")
    print("=" * 76)
    return 0

def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    
    parser = argparse.ArgumentParser(
        description="Instalador autonomo de skills e configuracoes de agente."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--global-only",
        action="store_true",
        help="Instala somente as skills e regras globais do usuario.",
    )
    group.add_argument(
        "--workspace-only",
        action="store_true",
        help="Instala somente as skills e scripts do workspace local.",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path("."),
        help="Diretorio do workspace de destino (padrao: diretorio atual).",
    )
    parser.add_argument(
        "--no-mirror",
        action="store_true",
        help="Desativa o espelhamento adicional em ~/.agent/skills/.",
    )
    
    args = parser.parse_args()
    
    install_global = not args.workspace_only
    install_workspace = not args.global_only
    mirror_agent = not args.no_mirror
    
    return run_installation(
        install_global=install_global,
        install_workspace=install_workspace,
        mirror_agent=mirror_agent,
        workspace_dir=args.workspace,
    )

if __name__ == "__main__":
    sys.exit(main())
