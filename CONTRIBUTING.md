# 🤝 Contribuindo para a Price Tracker API

Obrigado por querer contribuir com a **Price Tracker API**! Este documento orienta o processo de desenvolvimento para manter o projeto organizado e altamente sustentável.

---

## 🛠️ Setup de Desenvolvimento

### 1. Clonar e Inicializar o Ambiente
Recomendamos o uso direto do Docker para evitar ter que instalar o PostgreSQL e o Redis na sua máquina local:

```bash
# Clone o repositório
git clone https://github.com/felipevenas/api-price-tracker.git
cd api-price-tracker

# Inicialize o banco de dados e os containers de forma automática
python run.py start
```

### 2. Acessando os logs e monitoramento
Enquanto desenvolve novas features, mantenha o terminal de logs ativos para diagnosticar exceptions e retornos:
```bash
python run.py logs
```

---

## 🛤️ Estrutura de Branches

Adotamos a abordagem de **Trunk-Based Development**. As branches de funcionalidades devem ser criadas a partir de `main`, serem de curta duração e mescladas rapidamente de volta à `main` após aprovação em Pull Request.

Os nomes de branches devem ser escritos **em português** e seguir o padrão de nomenclatura:
- `funcionalidade/nome-da-feature`: Para novas implementações.
- `correcao/nome-do-bug`: Para correções de falhas de código ou segurança.
- `documentacao/nome-do-arquivo`: Para atualizações em manuais ou markdown.
- `melhoria/ajuste-infra`: Para refatorações e melhorias de setup.

**Exemplo:** `funcionalidade/scraper-amazon` ou `correcao/ajuste-timezone`.

---

## ✍️ Convenções de Commit

Nossos commits são escritos **em português** com os prefixos estruturados para clareza no histórico do Git:

| Prefixo | Uso | Exemplo |
|---|---|---|
| `feat:` | Nova funcionalidade para o usuário | `feat: adiciona scraper para o e-commerce Amazon` |
| `fix:` | Correção de bug no código | `fix: resolve falha ao obter centavos no Mercado Livre` |
| `chore:` | Tarefas de build, dependências ou configurações | `chore: atualiza pacotes no requirements.txt` |
| `docs:` | Atualizações na documentação ou README | `docs: detalha fluxo de execução no manual de setup` |
| `style:` | Formatação de código ou ajustes em logs (sem mudar comportamento) | `style: ajusta quebras de linha nos arquivos de model` |
| `refactor:` | Refatoração interna de código para melhor legibilidade/performance | `refactor: otimiza query de produtos vencidos no repository` |

---

## 🧪 Rodando Testes

Antes de submeter qualquer código, verifique se os testes unitários continuam passando com sucesso:

```bash
# Executa a suíte de testes de forma direta
pytest
```

Se precisar criar novos cenários de testes, adicione-os na pasta `tests/` com o prefixo `test_`.

---

## 📦 Banco de Dados e Migrações (Alembic)

Sempre que alterar os modelos do banco de dados (arquivos `model.py` sob a pasta `domain/`), você deve gerar uma migração correspondente do Alembic:

```bash
# 1. Crie a migração (dentro do container ou localmente)
docker-compose exec web alembic revision --autogenerate -m "sua_descricao_em_portugues"

# 2. Aplique a migração no banco de dados local
docker-compose exec web alembic upgrade head
```

Verifique se a migração foi gerada corretamente na pasta `alembic/versions/` e adicione-a ao commit.
