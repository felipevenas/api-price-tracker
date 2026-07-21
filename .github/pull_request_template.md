# Descrição do Pull Request

Por favor, inclua um resumo das alterações feitas e quais problemas ou funcionalidades foram abordados.

---

## Tipo de Alteração

- [ ] 🚀 Nova funcionalidade (feature)
- [ ] 🐞 Correção de bug (bug fix)
- [ ] 🔧 Refatoração de código (sem alteração de funcionalidade)
- [ ] 📝 Documentação (docs)
- [ ] 🎨 Estilo / Design / Logs (logs, formatação, etc.)
- [ ] ⚙️ Ajuste de infraestrutura (Docker, CI/CD, dependências, etc.)

## Como foi testado?

Por favor, descreva os testes executados para verificar suas alterações e como reproduzi-los.

- [ ] **Testes de Unidade:** Rodou `pytest` localmente e todos os testes passaram.
- [ ] **Stack Docker Compose:** Subiu os containers via `python run.py start` ou `docker-compose up -d` e os serviços (web, worker, beat, chrome, db, redis) estão saudáveis.
- [ ] **Logs de Diagnóstico:** Verificou os logs com `python run.py logs` e não há exceptions de banco ou scraping.
- [ ] **Alembic Migrations:** Gerada e testada nova migração de banco via `alembic upgrade head` (se aplicável).
- [ ] Outros testes executados:

## Evidência Visual / Logs

*Se aplicável, cole capturas do terminal, logs significativos de sucesso ou capturas de tela do Swagger/pgAdmin.*

## Checklist

- [ ] Meu código segue as diretrizes de estilo do projeto.
- [ ] Eu fiz uma auto-revisão do meu próprio código.
- [ ] Comentei partes do meu código que podem ser complexas ou difíceis de entender.
- [ ] Atualizei o arquivo `CHANGELOG.md` com as minhas modificações na versão correspondente.
- [ ] Minhas alterações não geraram novos warnings ou erros nos logs do Docker.
