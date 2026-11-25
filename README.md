# APAN

Monorepo com backend em FastAPI (Python) e frontend em React + TypeScript.

## Estrutura

```
apan/
├── backend/                  # FastAPI — Python 3.13, PostgreSQL, Redis
│   ├── src/apan/
│   │   ├── main.py           # create_app() (app factory)
│   │   ├── core/             # config, banco, erros RFC 9457, logs, middleware, paginação
│   │   └── modules/          # um pacote por módulo (router → service → repository → models)
│   ├── migrations/           # Alembic
│   ├── tests/                # unit/ e integration/ (testcontainers)
│   ├── alembic.ini
│   ├── Makefile
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/                 # React + TypeScript (Vite)
├── docker/
│   ├── Dockerfile.backend      # Multi-stage com uv (targets dev e runtime)
│   ├── Dockerfile.frontend     # Node builder + Nginx
│   ├── nginx.conf              # SPA + proxy de /api → backend
│   ├── docker-compose.yml      # Produção: db, redis, migrate, backend, frontend
│   └── docker-compose.dev.yml  # Desenvolvimento: + Mailpit, hot reload
├── docs/arquitetura/         # Guias de arquitetura (backend e frontend)
└── .env.example
```

> Os módulos `roll-calls` e `dashboard` ainda usam dados em memória (`core/store.py`)
> e serão migrados para o PostgreSQL no PR de chamadas. Alunos, turmas, disciplinas,
> anos letivos e matrículas já estão no banco e exigem login.

---

## 🐳 Docker (recomendado)

### Configuração inicial

```bash
# Copie e preencha as variáveis de ambiente
cp .env.example .env
```

### Produção

```bash
docker compose -f docker/docker-compose.yml up --build

# Em background
docker compose -f docker/docker-compose.yml up --build -d
```

O app estará disponível em **http://localhost** (porta 80).  
O Nginx faz proxy de `/api/*` → backend. O serviço `migrate` aplica as migrations antes de a API subir.

> Com `APP_ENV=production`, a API exige `SECRET_KEY` forte (≥ 32 caracteres) e `POSTGRES_PASSWORD` diferente do padrão, e desativa `/docs`.

### Desenvolvimento com hot reload

```bash
docker compose -f docker/docker-compose.dev.yml up --build
```

| Serviço  | URL                         | Descrição                    |
|----------|-----------------------------|------------------------------|
| Frontend | http://localhost:5173       | Vite dev server (hot reload) |
| Backend  | http://localhost:8000       | FastAPI + uvicorn --reload   |
| API Docs | http://localhost:8000/docs  | Swagger UI automático        |
| Mailpit  | http://localhost:8025       | Caixa de e-mails de teste    |

---

## 💻 Desenvolvimento local (sem Docker)

### Backend (FastAPI)

**Pré-requisitos:** [uv](https://docs.astral.sh/uv/) e Docker (para Postgres/Redis e para os testes de integração).

```bash
# Postgres e Redis do compose de desenvolvimento (publicados em localhost)
docker compose -f docker/docker-compose.dev.yml up -d db redis

cd backend
uv sync                 # cria .venv com Python 3.13 e dependências
uv run alembic upgrade head
uv run uvicorn --factory apan.main:create_app --reload --reload-dir src
```

API: http://localhost:8000 · Docs: http://localhost:8000/docs · Health: `/api/v1/health/live` e `/api/v1/health/ready`

| Comando (`make` ou o equivalente `uv run ...`) | O que faz |
|---|---|
| `make lint` | Ruff (lint + format check) e import-linter |
| `make typecheck` | mypy strict |
| `make test` / `make test-unit` | pytest (integração sobe Postgres e Redis via testcontainers) |
| `make migrate` | `alembic upgrade head` |
| `make revision m="..."` | nova migration com autogenerate |

### Primeiro acesso (criar o administrador)

O primeiro `admin` é criado pela linha de comando (nunca por migration ou seed):

```bash
# Docker (produção ou desenvolvimento)
docker exec -it apan-backend apan create-admin        # ou apan-backend-dev
# Local
cd backend && uv run apan create-admin
```

Os demais usuários são criados pelo admin em `POST /api/v1/users`. A pessoa recebe
um e-mail de convite com o link para definir a senha (em desenvolvimento, os e-mails
ficam no Mailpit: http://localhost:8025).

### Dados de demonstração (desenvolvimento)

Depois de criar o admin, `apan seed-demo` cria um ano letivo com bimestres e feriados,
3 disciplinas, 3 turmas, 15 alunos fictícios com responsáveis e a conta
`professora.demo@example.com` (vinculada a duas das turmas). O comando pede a senha da
professora e não roda com `APP_ENV=production`.

```bash
docker exec -it apan-backend-dev apan seed-demo
```

### Quem pode o quê (cadastros)

| Recurso | Admin | Professor |
|---|---|---|
| Anos letivos, bimestres, calendário, disciplinas | Tudo | Leitura |
| Turmas e vínculo turma–disciplina–professor | Tudo | Leitura das próprias turmas |
| Alunos e responsáveis | Tudo | Cadastrar nas próprias turmas; ver e editar os alunos delas |
| Arquivar aluno, matricular, transferir, cancelar | Sim | Não (só leitura das matrículas das próprias turmas) |

Recursos fora do escopo do professor respondem `404`.

### Autenticação (resumo)

| Endpoint | Função |
|---|---|
| `POST /api/v1/auth/login` | Devolve `accessToken` (15 min) e grava o refresh token em cookie `HttpOnly` |
| `POST /api/v1/auth/refresh` | Troca o refresh token por um novo (rotação; reuso derruba a sessão) |
| `POST /api/v1/auth/logout` | Encerra a sessão |
| `GET /api/v1/auth/me` | Usuário logado e permissões |
| `POST /api/v1/auth/password/change` \| `/forgot` \| `/reset` | Troca, pedido e redefinição de senha |

`refresh` e `logout` exigem o cabeçalho `X-Requested-With: XMLHttpRequest` e uma
`Origin` listada em `CORS_ORIGINS`.

### Frontend (React + TypeScript)

**Pré-requisitos:** Node.js 18+

```bash
cd frontend

# Instalar dependências
npm install

# Iniciar servidor de desenvolvimento
npm run dev
```

Frontend disponível em: http://localhost:5173

> O Vite faz proxy de `/api/*` → `http://localhost:8000` em dev, então não há problemas de CORS.
