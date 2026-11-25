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

> Todos os módulos usam o PostgreSQL e exigem login. O frontend ainda chama a API
> antiga sem autenticação e será atualizado no próximo PR.

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

### Chamada, relatórios e exportação

| Endpoint | Função |
|---|---|
| `GET /api/v1/roll-calls/sheet?classId&subjectId&date` | Alunos matriculados na data da aula, marcações já salvas e se ainda pode editar |
| `PUT /api/v1/roll-calls` | Salva a chamada (turma + disciplina + data) com anotações de até 1000 caracteres; reenviar é seguro |
| `GET /api/v1/reports/attendance/students?from&to[&classId&subjectId&studentId]` | Presenças, faltas e % por aluno no período |
| `GET /api/v1/reports/attendance/summary` · `/by-class` · `/low-attendance` | Totais, por turma e alunos abaixo de 75% |
| `GET /api/v1/reports/attendance/export?format=xlsx\|csv&from&to` | Planilha (XLSX com abas Resumo, Por aluno, Por turma, Aulas e Registros; CSV com `;` para o Excel) |
| `GET /api/v1/dashboard/today` | Chamadas pendentes de hoje, presença recente e alunos em risco |

Regras da chamada: só em dias letivos (fins de semana e feriados do calendário ficam de
fora, dias letivos extras entram), nunca no futuro, apenas com os alunos matriculados na
data. O professor registra só as disciplinas que leciona na turma, até
`ROLL_CALL_EDIT_WINDOW_DAYS` dias depois da aula (padrão 7); o admin pode sempre.

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

**Pré-requisitos:** Node.js 22 (ou Docker, veja abaixo).

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173 (proxy de /api → http://localhost:8000)
```

| Comando | O que faz |
|---|---|
| `npm run lint` | ESLint (inclui `jsx-a11y` estrito e as regras de import entre features) |
| `npm run type-check` | TypeScript estrito |
| `npm test` | Vitest + Testing Library + MSW + axe (temas claro e escuro) |
| `npm run build` | Type-check e build de produção |
| `npm run api:types` | Regenera `src/shared/api/schema.d.ts` a partir de `backend/openapi.json` |

Sem Node instalado, rode os mesmos comandos num contêiner (o `node_modules` fica num
volume Docker):

```bash
docker run --rm -it -v "$PWD:/repo" -v apan-frontend-node-modules:/repo/frontend/node_modules   -w /repo/frontend node:22-alpine npm test
```

Quando a API mudar: `make openapi` no backend e depois `npm run api:types` no frontend.
