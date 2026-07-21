# 🏷️ Price Tracker API | Monitoramento Resiliente de Preços de Produtos

> API de alta performance desenvolvida em FastAPI e Python, estruturada sob princípios rígidos de Clean Architecture, Domain-Driven Design (DDD) e SOLID. Conta com automações e Web Scraping resiliente (Selenium Chrome Standalone) para extração de preços periódicos de e-commerces (Mercado Livre), enfileiramento via Celery/Redis, logs estruturados para observabilidade e segurança JWT profissional.

![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.3-3781B8?logo=celery&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?logo=redis&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15.0-4169E1?logo=postgresql&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.18-43B02A?logo=selenium&logoColor=white)
![Workflow](https://img.shields.io/badge/Workflow-Trunk--Based-2ea44f)
![License](https://img.shields.io/badge/license-Propriet%C3%A1ria-red)

---

## 📖 Propósito

A **Price Tracker API** foi planejada para resolver o problema de monitoramento manual de preços de produtos. Ela permite que usuários registrem as URLs de produtos de e-commerces de interesse (com foco inicial no Mercado Livre) e definam preços-alvo. Periodicamente, tarefas assíncronas em background utilizam instâncias limpas e otimizadas do Selenium WebDriver para extrair os preços diretamente das páginas web, registrando históricos detalhados de variações de preços, auditorias de sistema e enviando alertas (logs do sistema) de forma isolada, resiliente e escalável.

---

## 🌟 Funcionalidades Focadas na Robustez

- **Clean Architecture & DDD**: Separação clara de responsabilidades com camadas dedicadas de domínio, serviços, esquemas, controllers e infraestrutura física de execução.
- **Web Scraping Resiliente com Selenium**: Scrapers baseados em interfaces comuns e padrão Factory. Implementação do Mercado Livre com bypass de detecção de bots (suporte a execução em modo headful simulado dentro do Xvfb do Docker Grid e patches do CDP para a flag `navigator.webdriver`).
- **Enfileiramento Celery + Redis**: Separação assíncrona da execução e consultas de rede. O FastAPI despacha tarefas de I/O na fila do Redis de forma instantânea sem bloquear as requisições HTTP do usuário.
- **Agendamento com Celery Beat**: Tarefa agendadora que roda de forma periódica localizando registros expirados de monitoramento de acordo com o intervalo escolhido do usuário e alimentando o enfileirador de forma concorrente.
- **Autenticação Profissional JWT**: Segurança via OAuth2 com assinaturas criptográficas HS256, hash de senhas de usuários com bcrypt e barreiras de proteção de rotas privadas.
- **Logs estruturados e Observabilidade**: Sistema de logs com injeção automática de `correlation_id` (nas chamadas FastAPI) e `task_id` (nas tarefas do Celery) gerenciados por ContextVars assíncronos.
- **Script Utilitário de DX**: Inclui um script centralizador `run.py` para controlar todas as ações do ecossistema do Docker Compose e migrações do banco com um único comando.

---

## 📁 Estrutura do Projeto

```
api-price-tracker/
├── alembic/                      # Scripts e histórico de migrações do banco de dados
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   └── routes.py         # Registrador central de rotas unificadas v1
│   │   └── deps.py               # Injeção de dependências (get_db, get_current_user)
│   ├── core/
│   │   ├── config.py             # Carregamento de variáveis de ambiente (.env)
│   │   ├── security.py           # Utilitários de Hash, bcrypt e JWT
│   │   └── response.py           # Padronização de saídas JSON da API
│   ├── db/
│   │   ├── base_class.py         # Base declarativa SQLAlchemy com tabelas dinâmicas
│   │   └── session.py            # Sessionmaker assíncrono (asyncpg) utilizando NullPool
│   ├── domain/                   # Camadas divididas por domínios de negócio (DDD)
│   │   ├── auth/                 # Rotas e controladores de Login e Token
│   │   ├── user/                 # Modelos, Repositories e Services do Usuário
│   │   ├── product/              # Monitoramento de Produtos (CRUD, Services)
│   │   ├── price_history/        # Histórico de preços consultados com sucesso ou falha
│   │   └── audit_log/            # Rastreabilidade total e logs físicos de auditoria
│   ├── helpers/                  # Validadores de URLs e higienizadores de strings de preços
│   ├── infra/                    # Serviços externos e componentes de infraestrutura
│   │   ├── logging/
│   │   │   └── logger.py         # Logging estruturado centralizado com ContextVars
│   │   ├── queue/
│   │   │   ├── celery_app.py     # Inicialização e carregamento do Celery App
│   │   │   ├── celery_config.py  # Fila e agendamento periódico do Celery Beat
│   │   │   └── tasks.py          # Definições de tarefas assíncronas do worker
│   │   └── scrapers/             # Mecanismo de scraping com Selenium
│   │       ├── base_scraper.py   # Classe base com otimização e patches anti-bot
│   │       ├── factory.py        # Fábrica de instâncias dos scrapers concretos
│   │       └── mercado_livre.py  # Raspagem específica de anúncios e catálogo
│   └── main.py                   # Ponto de entrada do FastAPI e Middlewares
├── tests/                        # Suite de testes automatizados com pytest
├── docker-compose.yml            # Orquestração do ambiente PostgreSQL, Redis e Selenium
├── Dockerfile                    # Dockerfile baseado em Python Slim
├── requirements.txt              # Arquivo de dependências do Python
└── run.py                        # Script CLI/Interativo unificado de DX
```

---

## 🏷️ Stack Tecnológica

### Core & Framework
| Tecnologia | Versão | Propósito |
|---|---|---|
| FastAPI | 0.110.x | Framework web assíncrono de alto desempenho para APIs |
| Pydantic v2 | 2.x | Validação robusta de dados e schemas |
| SQLAlchemy | 2.0.x | ORM mapeador de objetos relacionais com suporte a asyncio |
| Alembic | 1.13.x | Histórico de migrações e controle de alterações no banco de dados |
| bcrypt | 4.x | Criptografia de senhas de usuários |
| PyJWT | 2.x | Criação e decodificação de tokens JWT criptografados |

### Banco de Dados, Filas & Infraestrutura
| Componente | Descrição |
|---|---|
| PostgreSQL 15 | Persistência de dados relacionais utilizando tipos robustos (UUID, JSONB) |
| Redis 7 | Message broker de alta velocidade para controle de filas do Celery |
| Celery & Beat | Agendamento distribuído e execução assíncrona de I/O em background |
| Selenium Chrome | Container Standalone Chrome isolado para scraping com noVNC (porta 7900) |
| Docker Compose | Orquestração simplificada de serviços e isolamento de ambientes |

---

## 🚀 Instalação e Execução

### Pré-requisitos
- Python **3.10** ou superior instalado localmente (apenas se for testar helpers locais)
- **Docker** e **Docker Compose** instalados e em execução

### Setup Local Simples (DX)

```bash
# 1. Clonar o repositório
git clone https://github.com/seu-usuario/api-price-tracker.git
cd api-price-tracker

# 2. Iniciar a aplicação e o banco (Docker + Alembic Migrations + Status)
python run.py start
```

Após a execução, o projeto estará ativo. URLs úteis locais:
- **FastAPI Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **pgAdmin 4:** [http://localhost:8080](http://localhost:8080) (Login: `admin@admin.com` / Senha: `admin`)
- **Selenium noVNC Screen:** [http://localhost:7900](http://localhost:7900) (Senha: `secret` - para assistir ao Chrome raspando em tempo real)

---

## 🤝 Contribuição — fluxo Trunk-Based

Este projeto adota o modelo de **Trunk-Based Development**. Feature branches devem ser curtas e mescladas na branch `main` após aprovação em Pull Request.

### Convenções de Commit
| Prefixo | Uso | SemVer |
|---|---|---|
| `feat:` | Nova funcionalidade | MINOR |
| `fix:` | Correção de bug | PATCH |
| `chore:` | Ajuste de build, dependências ou configurações | - |
| `docs:` | Atualizações na documentação | - |
| `style:` | Ajustes visuais de logs, layout ou formatação | - |
| `refactor:` | Refatoração interna de código | - |

---

## 📄 Licença

Software proprietário — todos os direitos reservados.
**&copy; 2026 Price Tracker API**
