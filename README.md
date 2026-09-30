# APAN

Monorepo com backend em FastAPI (Python) e frontend em React + TypeScript.

## Estrutura

```
apan-backend/
├── backend/                  # FastAPI — Python 3.12+
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py
│   ├── .dockerignore
│   ├── pyproject.toml
│   └── run.py
├── frontend/                 # React + TypeScript (Vite)
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── main.tsx
│   │   └── index.css
│   ├── .dockerignore
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
├── docker/
│   ├── Dockerfile.backend      # Multi-stage — Python slim
│   ├── Dockerfile.frontend     # Multi-stage — Node builder + Nginx
│   ├── nginx.conf              # Reverse proxy + SPA routing
│   ├── docker-compose.yml      # Produção
│   └── docker-compose.dev.yml  # Desenvolvimento com hot reload
├── .env.example                # Template de variáveis de ambiente
└── .gitignore
```

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
O Nginx faz proxy de `/api/*` → backend automaticamente.

### Desenvolvimento com hot reload

```bash
docker compose -f docker/docker-compose.dev.yml up --build
```

| Serviço  | URL                         | Descrição                    |
|----------|-----------------------------|------------------------------|
| Frontend | http://localhost:5173       | Vite dev server (hot reload) |
| Backend  | http://localhost:8000       | FastAPI + uvicorn --reload   |
| API Docs | http://localhost:8000/docs  | Swagger UI automático        |

---

## 💻 Desenvolvimento local (sem Docker)

### Backend (FastAPI)

**Pré-requisitos:** Python 3.12+

```bash
cd backend

# Criar e ativar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Instalar dependências
pip install fastapi "uvicorn[standard]" pydantic

# Iniciar servidor com hot reload
python run.py
```

API disponível em: http://localhost:8000  
Docs: http://localhost:8000/docs

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
