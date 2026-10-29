# CLAUDE.md: Adaptador Claude Code para `book-resurrect`

Para transcrever, recuperar ou continuar lotes de um livro em PDF, leia e siga integralmente [`.agent/skills/book-resurrect/SKILL.md`](.agent/skills/book-resurrect/SKILL.md). Ele é a única fonte de verdade.

## Resumo
1. Pipeline 100% LaTeX (Tectonic) com saída exclusiva em PDF e dois perfis de preâmbulo em `metadata.yaml`: `tecnico` ou `texto`.
2. O livro começa após o sumário original (descarte créditos/ISBN/orelha anteriores e nunca transcreva o sumário impresso).
3. Sem `roadmap.json`: Triagem Interativa (`ask_question`) e depois `python scripts/init_book_fase0.py ... --pre-render`.
4. Validação obrigatória de lote: `python scripts/compile_check.py --lint --only capXX --render-last 0`.
