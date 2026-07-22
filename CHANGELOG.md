# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [0.2.0] - 21-07-2026

### Alterações

#### 🔧 Refatorado
- **Padronização de Nomenclatura CRUD & Refatoração para Abordagem 1 (Clean Architecture)**:
  - Eliminação de serviços anêmicos (`service.py`) em favor de UseCases focados em ações de aplicação.
  - Implementação de UseCases isolados por domínio em `app/domain/user/usecase.py`, `app/domain/auth/usecase.py` e `app/domain/product/usecase.py` que dependem e orquestram Repositories diretamente.
  - Padronização da nomenclatura dos métodos nos repositórios (`get_by_user`, `get_by_product`, `get_expired_for_checking`).
  - Aplicação de Injeção de Dependências (DI) via `Depends` no topo de cada arquivo de rotas (`routes.py`) e em `app/api/deps.py`.

## [0.1.0] - 20-07-2026

### Alterações

#### 🚀 Adicionado
- **Estrutura Arquitetural de Base (Clean Architecture + DDD)**:
  - Inicialização da estrutura de pastas separando camadas de Domínio (User, Product, Price History, Audit Log), API (Endpoints, Middleware e dependências) e Infraestrutura (Fila, Logging e Scrapers).
  - Implementação da classe base declarativa do SQLAlchemy com mapeamento dinâmico de nomes de tabelas.
- **Domínio User & Autenticação Profissional**:
  - Modelagem da tabela `user` com chaves primárias UUID e índices.
  - Implementação de hashes de senhas seguros via `bcrypt` e geração/validação de tokens JWT.
  - Criação de rotas `/auth/register` (cadastro de novos usuários) e `/auth/login` (autenticação com Swagger).
  - Criação de rota protegida `/users/me` para consulta e edição de dados cadastrais com dependência `get_current_user`.
- **Domínio Product & Histórico de Preços**:
  - Modelagem e criação da tabela `product_monitored` com intervalo de checagem customizado e controle de status ativo/inativo.
  - Criação da tabela `price_history` para rastreamento de variações de preços com suporte a gravação de erros.
  - Implementação do `ProductService` e `ProductRepository` orquestrando o CRUD e as operações de banco.
- **Logs de Auditoria e Rastreabilidade**:
  - Modelagem da tabela `audit_log` utilizando o tipo `JSONB` do Postgres para gravação de metadados dinâmicos de auditoria.
  - Implementação de registros físicos de auditoria para ações críticas (criação, edição e exclusão de produtos monitorados, além de logins).
- **Mecanismo de Scraping com Selenium Grid**:
  - Criação da infraestrutura base de scrapers com suporte ao Selenium Grid do Docker (`chrome:4444`).
  - Implementação do scraper robusto do Mercado Livre (`MercadoLivreScraper`) tratando layouts de anúncios individuais e catálogo com esperas explícitas (`WebDriverWait`).
  - Implementação de patches de bypass anti-bot (desativação do `navigator.webdriver` via CDP e desativação do modo headless em ambiente docker permitindo renderização headful virtual).
  - Implementação de Helpers auxiliares: `price_cleaner` (resiliente para conversão de valores monetários de e-commerce para float) e `url_parser` (extração e validação de domínios).
- **Observabilidade Estruturada (Logger)**:
  - Configuração do sistema de logging integrado com `ContextVars` assíncronos.
  - Injeção dinâmica de identificadores de contexto unificados nos logs: `REQ-xxxx` (para requisições HTTP via Middleware FastAPI) e `TSK-xxxx` (para tarefas em segundo plano do Celery).
- **Enfileiramento e Agendamento (Celery + Redis + Beat)**:
  - Setup do Celery configurado com Redis como Broker e Backend.
  - Criação da tarefa periódica `orchestrate_price_checks` (Celery Beat) para verificar produtos com checagem vencida a cada 1 minuto.
  - Criação do worker task `check_product_price_task` para carregar o Selenium, realizar o scraping de forma assíncrona, atualizar o banco de dados e persistir a variação do preço.
- **Script Utilitário de DX**:
  - Criação do script interativo `run.py` na raiz para iniciar a stack, reconstruir imagens, aplicar migrações do Alembic, e exibir logs e status em tempo real com facilidade.
- **Suite de Testes com Pytest**:
  - Configuração de testes unitários com pytest validando as utilidades de limpeza de strings de preços e validadores de URLs.
