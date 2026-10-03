# APAN Frequência Escolar — Guia de Arquitetura do Backend (FastAPI + PostgreSQL)

> Use este documento como prompt/contexto fixo (CLAUDE.md, AGENTS.md, regras do Cursor/Copilot ou colado no início de qualquer conversa com IA) e como referência de code review para toda a equipe de backend.
> Regra de ouro: **se algo não está coberto aqui, siga o padrão do módulo `students`, que é o módulo de referência.**
> Este guia é o par do guia de frontend (`ARQUITETURA_APAN.md`). As duas pontas devem permanecer alinhadas (seção 17).

## 0. Princípios inegociáveis

1. **Segurança por padrão.** Autorização em toda rota, validação de toda entrada, nenhum dado pessoal em log. Em conflito entre segurança e conveniência, a segurança vence.
2. **Todo o código é em inglês.** Identificadores, arquivos, pastas, rotas, campos JSON, códigos de erro, mensagens de commit e testes. O backend **não** produz texto para o usuário final: devolve **códigos de erro estáveis** e o frontend os traduz para pt-BR. (Única exceção a confirmar: templates de e-mail transacional, seção 19.)
3. **Camadas explícitas:** router → service → repository → model. Regra de negócio só no service; SQL só no repository; HTTP só no router.
4. **O banco também protege os dados:** constraints (`UNIQUE`, `CHECK`, `FOREIGN KEY`), tipos corretos e índices. Não confiar só na aplicação.
5. **Tudo versionado e reproduzível:** schema por migrations, dependências por lockfile, ambiente por container.
6. **Sem comentários desnecessários.** O código se explica por nomes e tipos; comentar apenas o porquê não óbvio.

---

## 1. Contexto e escopo

API REST para o sistema de controle de frequência escolar (consumida pela SPA React).

- **Módulos funcionais:** autenticação (login), usuários, anos letivos e calendário, disciplinas, turmas, vínculo turma–disciplina–professor, alunos e responsáveis, matrículas, chamadas (roll calls), relatórios/exportação, dashboard, auditoria.
- **Perfis:** `admin` (gestão completa) e `teacher` (apenas as próprias turmas). O modelo de papéis deve permitir novos perfis (ex.: `coordinator`) sem refatoração.
- **Regras de negócio chave:**
  - Frequência mínima legal de **75%** (constante única `MIN_ATTENDANCE_RATE`).
  - Idade mínima de matrícula: 3 anos; menor de 18 anos exige ao menos um responsável.
  - Chamada única por `(class, subject, lesson_date)`; salvar é **idempotente** (upsert).
  - Chamada só aceita alunos com matrícula ativa na turma na data da aula.
  - Professor só registra chamada de turma/disciplina a que está vinculado e dentro da janela de edição configurável; `admin` edita sempre.
  - Dias letivos de relatório descontam feriados/recessos do calendário escolar.
- **Dados de menores de idade:** tratamento sujeito à **LGPD** (seção 11).

---

## 2. Stack (não adicionar libs fora desta lista sem aprovação)

| Necessidade | Escolha |
|---|---|
| Linguagem | **Python 3.13** (mínimo 3.12), type hints em todo o código |
| Gerenciador de pacotes/ambiente | **uv** (`pyproject.toml` + `uv.lock`) |
| Framework web | **FastAPI** (async) sobre **Uvicorn** |
| Validação / serialização | **Pydantic v2** + **pydantic-settings** |
| Banco de dados | **PostgreSQL 17+** |
| ORM | **SQLAlchemy 2.0** (estilo 2.0, `Mapped[]`, async) |
| Driver | **asyncpg** |
| Migrations | **Alembic** |
| Hash de senha | **pwdlib** com **Argon2id** |
| Tokens | **PyJWT** (algoritmo fixo; nunca `python-jose`) |
| Rate limiting / cache curto | **Redis** + **slowapi** (ou `limits`) |
| Logs | **structlog** (JSON) |
| Observabilidade | **OpenTelemetry**, **prometheus-fastapi-instrumentator**, **Sentry** |
| IDs | **UUIDv7** (`uuid-utils`) |
| Exportação XLSX/CSV | **XlsxWriter** / `csv` com resposta em streaming |
| CLI administrativa | **Typer** |
| Lint / format | **Ruff** (`E,F,I,UP,B,S,ASYNC,SIM,RUF`) |
| Tipos | **mypy** em modo `strict` (ou pyright strict) |
| Testes | **pytest**, **pytest-asyncio**, **httpx** (`ASGITransport`), **testcontainers** (Postgres real), **polyfactory** |
| Segurança de dependências | **pip-audit** + Dependabot/Renovate |
| Arquitetura | **import-linter** (impõe as regras de dependência) |
| Contêiner | **Docker** multi-stage + **docker-compose** (dev) |

**Não usar:** SQLite em testes, ORM síncrono, SQL com f-strings, `python-jose`, `passlib` (abandonado), Pydantic v1, `Base.metadata.create_all()` em produção, lógica de negócio em router, retorno direto de objetos ORM nas rotas, `print()`.

---

## 3. Arquitetura

**Monólito modular em camadas.** Um deploy, módulos com fronteiras claras (cada módulo poderia virar serviço no futuro sem reescrita).

```
HTTP request
   │
   ▼
router.py        valida entrada (Pydantic), injeta dependências, chama o service, devolve schema
   │
   ▼
service.py       regra de negócio, autorização de objeto, transação (commit), auditoria
   │
   ▼
repository.py    único lugar com SQL/SQLAlchemy; aplica escopo de acesso nas queries
   │
   ▼
models.py        mapeamento ORM (tabelas)
```

### Regras de dependência (impostas por import-linter)

1. `router` → `service` → `repository` → `models`. Nunca no sentido inverso nem pulando camadas.
2. Routers **nunca** importam repositories ou models. Services **nunca** importam `fastapi` (exceto tipos neutros), `Request` ou `Response`.
3. Um módulo **nunca** importa `repository` ou `models` de outro módulo. A comunicação entre módulos acontece pela interface pública do outro módulo (`service` exposto em `__init__.py`). Relacionamentos entre tabelas usam FK/`relationship` com string, sem import circular.
4. `core/` não importa de `modules/`. `modules/*` pode importar de `core/`.
5. Regra de negócio **pura** (cálculos, validações de domínio) vai em `domain.py` do módulo, sem I/O, testada de forma unitária.
6. Schemas Pydantic (API) e models SQLAlchemy (banco) são **separados**. O ORM nunca vaza para a resposta.

---

## 4. Estrutura de pastas

```
backend/
├── pyproject.toml
├── uv.lock
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── .env.example
├── migrations/
│   ├── env.py
│   └── versions/
├── src/apan/
│   ├── main.py
│   ├── cli.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   ├── errors.py
│   │   ├── error_handlers.py
│   │   ├── logging.py
│   │   ├── middleware.py
│   │   ├── rate_limit.py
│   │   ├── pagination.py
│   │   ├── schemas.py
│   │   ├── models.py
│   │   ├── dependencies.py
│   │   └── constants.py
│   └── modules/
│       ├── auth/
│       ├── users/
│       ├── school_years/
│       ├── subjects/
│       ├── classes/
│       ├── students/
│       │   ├── router.py
│       │   ├── service.py
│       │   ├── repository.py
│       │   ├── models.py
│       │   ├── schemas.py
│       │   ├── domain.py
│       │   ├── dependencies.py
│       │   ├── errors.py
│       │   └── __init__.py
│       ├── enrollments/
│       ├── roll_calls/
│       ├── reports/
│       ├── dashboard/
│       ├── audit/
│       └── health/
└── tests/
    ├── conftest.py
    ├── factories/
    ├── unit/
    ├── integration/
    └── security/
```

- `main.py` expõe um **app factory** (`create_app()`); nada de lógica em escopo de módulo.
- Cada módulo registra seu router em `main.py` sob o prefixo `/api/v1`.

---

## 5. Modelo de domínio e banco de dados

### 5.1 Tabelas

| Tabela | Colunas principais | Observações |
|---|---|---|
| `users` | `id`, `email` (citext, único), `password_hash`, `full_name`, `role`, `is_active`, `must_change_password`, `failed_login_count`, `locked_until`, `last_login_at` | Papéis: `admin`, `teacher` |
| `refresh_tokens` | `id`, `user_id`, `family_id`, `token_hash`, `expires_at`, `revoked_at`, `replaced_by_id`, `ip`, `user_agent` | Rotação com detecção de reuso |
| `password_reset_tokens` | `id`, `user_id`, `token_hash`, `expires_at`, `used_at` | Uso único |
| `school_years` | `id`, `name`, `starts_on`, `ends_on`, `is_current` | Único registro `is_current` (índice parcial) |
| `terms` | `id`, `school_year_id`, `name`, `starts_on`, `ends_on` | Bimestres/trimestres |
| `calendar_days` | `id`, `school_year_id`, `day`, `kind`, `description` | `holiday`, `recess`, `non_school_day`, `extra_school_day` |
| `subjects` | `id`, `name`, `code` | `code` único |
| `school_classes` | `id`, `school_year_id`, `name`, `grade`, `shift`, `room`, `capacity`, `is_active` | Único `(school_year_id, name, shift)` |
| `class_subject_teachers` | `id`, `class_id`, `subject_id`, `teacher_id` | Único `(class_id, subject_id)`; `teacher_id` deve ter papel `teacher` |
| `students` | `id`, `enrollment_number` (único), `full_name`, `birth_date`, `archived_at` | Dados mínimos (LGPD) |
| `guardians` | `id`, `student_id`, `full_name`, `phone`, `relationship`, `is_primary` | Um `is_primary` por aluno |
| `enrollments` | `id`, `student_id`, `class_id`, `status`, `starts_on`, `ends_on` | `active`, `transferred`, `cancelled`, `completed`; **uma matrícula ativa por aluno por ano letivo** |
| `roll_calls` | `id`, `class_id`, `subject_id`, `lesson_date`, `taken_by_id`, `notes` | Único `(class_id, subject_id, lesson_date)` |
| `attendance_records` | `roll_call_id`, `student_id`, `status` | PK composta; `present` ou `absent` |
| `audit_logs` | `id`, `actor_id`, `action`, `entity_type`, `entity_id`, `metadata` (jsonb), `ip`, `user_agent`, `created_at` | **Append-only** (sem `UPDATE`/`DELETE` para a role da aplicação) |

Fase 2 (não implementar agora, mas não bloquear no modelo): justificativa de faltas, MFA (TOTP), múltiplas unidades/escolas.

### 5.2 Convenções de banco

- **Chaves primárias:** UUIDv7 gerado na aplicação (ordenável por tempo, sem expor contagem). Nunca inteiros sequenciais expostos na API.
- **Datas:** `timestamptz` sempre em UTC para instantes (`created_at`, `updated_at`, `expires_at`); tipo `date` para datas de calendário (`lesson_date`, `birth_date`).
- **Enums:** `VARCHAR` + `CHECK` (via `Enum(..., native_enum=False)` do SQLAlchemy). Evitar `ENUM` nativo do Postgres (alteração dolorosa em migrations).
- **E-mail:** extensão `citext` (comparação sem diferenciar caixa) com índice único.
- **Busca por nome:** extensões `unaccent` + `pg_trgm` com índice GIN nos campos buscáveis.
- **Nomes:** tabelas e colunas em `snake_case`, tabelas no plural, FKs `<entity>_id`.
- **Naming convention** do `MetaData` definida uma vez (`ix`, `uq`, `ck`, `fk`, `pk`) para migrations determinísticas.
- **Constraints obrigatórias:** `NOT NULL` por padrão, `FOREIGN KEY ... ON DELETE RESTRICT`, `CHECK` para regras simples (capacidade > 0, `ends_on >= starts_on`), índices únicos parciais para regras condicionais.
- **Exclusão:** dados de aluno usam arquivamento (`archived_at`) e política de retenção (LGPD); nada de `DELETE` físico de histórico de frequência.
- **Concorrência otimista:** coluna `version` (`version_id_col` do SQLAlchemy) nas entidades editáveis por mais de uma pessoa; conflito vira `409 Conflict`.
- **Índices:** criar para toda coluna usada em `WHERE`/`JOIN`/`ORDER BY` frequente (ex.: `roll_calls(class_id, lesson_date)`, `attendance_records(student_id)`); validar com `EXPLAIN ANALYZE` nas queries de relatório.
- **Relatórios:** agregações feitas **em SQL** (`COUNT(*) FILTER (WHERE ...)`), nunca somando em Python. Views materializadas só se medido necessário.

### 5.3 Base e mixins

```python
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid_utils.compat import uuid7

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class IdMixin:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

---

## 6. Autenticação e autorização

### 6.1 Fluxo de login

| Endpoint | Função |
|---|---|
| `POST /api/v1/auth/login` | Valida credenciais; devolve `accessToken` e define o refresh token em cookie |
| `POST /api/v1/auth/refresh` | Troca o refresh token (rotação) por novo par |
| `POST /api/v1/auth/logout` | Revoga a família de refresh tokens e limpa o cookie |
| `GET /api/v1/auth/me` | Usuário autenticado e permissões |
| `POST /api/v1/auth/password/change` | Troca de senha autenticada (revoga demais sessões) |
| `POST /api/v1/auth/password/forgot` | Solicita redefinição; **sempre** responde `202` |
| `POST /api/v1/auth/password/reset` | Redefine com token de uso único |

**Tokens**
- **Access token:** JWT de **15 minutos**, algoritmo fixo (EdDSA/ES256 preferido; HS256 apenas com segredo forte), claims `sub`, `role`, `iat`, `exp`, `jti`, `iss`, `aud`. Enviado em `Authorization: Bearer`; o frontend o mantém **somente em memória**.
- **Refresh token:** valor opaco aleatório de 256 bits, armazenado no banco **apenas como hash (SHA-256)**. Cookie `HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth`. Validade deslizante de 7 dias com teto absoluto de 30.
- **Rotação com detecção de reuso:** cada refresh invalida o token usado e emite outro na mesma `family_id`; reapresentar um token já usado revoga **toda a família** e registra evento de auditoria.
- A cada requisição autenticada o usuário é carregado do banco por PK: desativação de conta e troca de papel valem **imediatamente**.
- **CSRF:** endpoints que usam o cookie (`refresh`, `logout`) exigem cabeçalho customizado e validam `Origin`. O deploy deve manter SPA e API no **mesmo site** (mesmo domínio registrável ou proxy reverso com `/api`), para `SameSite=Strict` funcionar.

**Endurecimento do login**
- Resposta única e genérica para falha (`invalid_credentials`); sem enumeração de usuário. Quando o e-mail não existe, ainda executar uma verificação de hash fictícia para igualar o tempo de resposta.
- Rate limit por IP **e** por conta; bloqueio progressivo (`failed_login_count`, `locked_until`) com retorno `account_locked`.
- Senhas: Argon2id (parâmetros revisados periodicamente, **re-hash automático** no login quando desatualizados), mínimo de 10 caracteres, máximo de 128, rejeição de senhas comuns/vazadas, sem regras de composição arbitrárias.
- Redefinição: token de uso único, 30 minutos de validade, guardado como hash; ao redefinir, **revogar todos os refresh tokens** do usuário.
- Usuários criados por `admin` recebem convite/redefinição e `must_change_password = true`. O primeiro `admin` nasce por CLI (`apan create-admin`), nunca por migration ou seed com senha fixa.
- Todo evento de login (sucesso, falha, bloqueio, reuso de token) vai para `audit_logs`.

### 6.2 Autorização (RBAC + escopo por objeto)

| Recurso | `admin` | `teacher` |
|---|---|---|
| Usuários | CRUD, ativar/desativar | Ler/atualizar o próprio perfil, trocar a própria senha |
| Anos letivos, calendário, disciplinas | CRUD | Leitura |
| Turmas | CRUD | Leitura apenas das turmas vinculadas |
| Vínculos turma–disciplina–professor | CRUD | Leitura dos próprios |
| Alunos, responsáveis | CRUD | Leitura dos alunos das turmas vinculadas |
| Matrículas | CRUD | Leitura |
| Chamadas | Ler/escrever em qualquer turma | Ler/escrever nas turmas/disciplinas vinculadas, dentro da janela de edição |
| Relatórios e exportação | Todas as turmas | Somente as próprias turmas |
| Auditoria | Leitura | Sem acesso |

Regras:
1. **Autenticação obrigatória por padrão.** O `APIRouter` raiz exige usuário autenticado; rotas públicas são exceções explícitas (`login`, `refresh`, `forgot`, `reset`, `health`).
2. **Autorização de papel** por dependência: `Depends(require_roles(Role.ADMIN))`.
3. **Autorização de objeto (anti-IDOR/BOLA):** o service calcula um `AccessScope` a partir do usuário (admin = irrestrito; teacher = `class_ids` permitidos) e o **repository aplica o escopo na própria query**. Recurso fora do escopo responde `404`, não `403`.
4. Políticas ficam em `policies.py` do módulo (funções puras, testáveis). Nenhuma checagem de permissão em router.
5. Todo endpoint tem teste de autorização cobrindo **papel × recurso** (seção 14).

---

## 7. Convenções da API

- **Prefixo e versão:** `/api/v1`. Mudança incompatível cria `/api/v2`; nunca quebrar `v1`.
- **Recursos (inglês, plural, kebab-case):** `/students`, `/classes`, `/school-years`, `/subjects`, `/enrollments`, `/roll-calls`, `/users`, `/reports`, `/audit-logs`.
- **Verbos HTTP:** `GET` leitura, `POST` criação (201 + `Location`), `PUT` substituição/upsert idempotente, `PATCH` atualização parcial, `DELETE` remoção/arquivamento (204).
- **JSON em `camelCase`**, Python em `snake_case`: `alias_generator=to_camel` no schema base. Parâmetros de query seguem o mesmo padrão via modelos de query do FastAPI (`classId`, `studentId`, `from`, `to`).
- **Schemas separados por intenção:** `XCreate`, `XUpdate`, `XRead`, `XFilters`. Entrada com `extra="forbid"` (anti mass-assignment). Resposta com `response_model` explícito; campos sensíveis (`passwordHash`, tokens) **nunca** existem em schema de saída.
- **Paginação:** listas retornam `{ items, total, page, pageSize }` (`page` ≥ 1, `pageSize` ≤ 100, padrão 20). Listas muito grandes (auditoria, registros de frequência) usam paginação por cursor (keyset).
- **Filtro e ordenação:** filtros por query params tipados; `sort=name` ou `sort=-createdAt` com **lista branca** de campos ordenáveis.
- **Erros no formato RFC 9457 (`application/problem+json`):**

```json
{
  "type": "about:blank",
  "title": "Validation error",
  "status": 422,
  "code": "validation_error",
  "detail": "One or more fields are invalid.",
  "instance": "/api/v1/students",
  "fieldErrors": [
    { "field": "birthDate", "code": "date_in_future" }
  ]
}
```

- `code` é **estável, em inglês e `snake_case`** (`student_not_found`, `invalid_credentials`, `account_locked`, `roll_call_locked`, `class_capacity_exceeded`...). É o contrato que o frontend traduz. `detail` é só para desenvolvedores e nunca vai para a tela.
- **Status:** 400 (requisição inválida), 401 (não autenticado), 403 (autenticado sem papel), 404 (inexistente **ou fora do escopo**), 409 (conflito/versão/duplicidade), 422 (validação), 429 (rate limit). Nunca expor stack trace.
- **Idempotência:** `PUT /roll-calls` com `(classId, subjectId, lessonDate)` faz upsert e é seguro para reenvio (essencial com internet instável).
- **Concorrência:** entidades com `version` aceitam `If-Match`/campo `version` e respondem `409 version_conflict`.
- **Exportação:** `GET /reports/attendance/export?format=xlsx|csv` em resposta de streaming com `Content-Disposition` seguro; exportação é evento auditado.
- **OpenAPI** é fonte de verdade: tags, `operation_id` estáveis, exemplos e respostas de erro documentadas. `/docs` e `/openapi.json` desativados ou protegidos em produção.

### Endpoints por módulo

```
auth          POST /auth/login | /auth/refresh | /auth/logout | /auth/password/*   GET /auth/me
users         GET,POST /users   GET,PATCH /users/{id}   POST /users/{id}/deactivate | /activate
school-years  GET,POST /school-years   GET,PATCH,DELETE /school-years/{id}
              GET,POST /school-years/{id}/terms | /school-years/{id}/calendar-days
subjects      GET,POST /subjects   GET,PATCH,DELETE /subjects/{id}
classes       GET,POST /classes   GET,PATCH /classes/{id}   POST /classes/{id}/archive
              GET,PUT /classes/{id}/subject-teachers
              GET /classes/{id}/students
students      GET,POST /students   GET,PATCH /students/{id}   POST /students/{id}/archive
              GET,POST /students/{id}/guardians   PATCH,DELETE /students/{id}/guardians/{gid}
enrollments   GET,POST /enrollments   POST /enrollments/{id}/transfer | /cancel
roll-calls    GET /roll-calls?classId&subjectId&date   PUT /roll-calls   GET /roll-calls/{id}
dashboard     GET /dashboard/today
reports       GET /reports/attendance/summary | /by-class | /low-attendance | /export
audit-logs    GET /audit-logs
health        GET /health/live | /health/ready
```

---

## 8. Padrões de código por camada

### 8.1 Configuração (`core/config.py`)

- `pydantic-settings` com `SecretStr` para segredos, validado **na inicialização** (falha rápida). Sem valores padrão inseguros em produção. Nenhum `os.environ` fora deste arquivo.
- Segredos vêm de variáveis de ambiente ou gerenciador de segredos; `.env.example` documenta todas as chaves sem valores reais.

### 8.2 Schemas (`schemas.py`)

```python
from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ApiInput(ApiModel):
    model_config = ConfigDict(extra="forbid")


class StudentCreate(ApiInput):
    full_name: str = Field(min_length=3, max_length=150)
    birth_date: date
    class_id: UUID


class StudentRead(ApiModel):
    id: UUID
    enrollment_number: str
    full_name: str
    birth_date: date
```

### 8.3 Model (`models.py`)

```python
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apan.core.models import Base, IdMixin, TimestampMixin


class Student(IdMixin, TimestampMixin, Base):
    __tablename__ = "students"
    __table_args__ = (
        CheckConstraint("birth_date <= CURRENT_DATE", name="birth_date_not_future"),
    )

    enrollment_number: Mapped[str] = mapped_column(String(20), unique=True)
    full_name: Mapped[str] = mapped_column(String(150))
    birth_date: Mapped[date] = mapped_column(Date)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    guardians: Mapped[list["Guardian"]] = relationship(lazy="raise")
```

- Relacionamentos com `lazy="raise"`: **carregamento explícito** (`selectinload`/`joinedload`) no repository. Evita N+1 e I/O escondido em contexto async.

### 8.4 Repository (`repository.py`)

```python
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.security import AccessScope
from apan.modules.students.models import Student
from apan.modules.students.schemas import StudentFilters


class StudentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, student_id: UUID, scope: AccessScope) -> Student | None:
        stmt = select(Student).where(Student.id == student_id)
        stmt = self._apply_scope(stmt, scope)
        return await self._session.scalar(stmt)

    async def list(
        self, filters: StudentFilters, scope: AccessScope
    ) -> tuple[Sequence[Student], int]:
        stmt = self._apply_scope(select(Student), scope)
        if filters.q:
            stmt = stmt.where(func.unaccent(Student.full_name).ilike(f"%{filters.q}%"))
        total = await self._session.scalar(select(func.count()).select_from(stmt.subquery()))
        stmt = stmt.order_by(Student.full_name).limit(filters.page_size).offset(filters.offset)
        return (await self._session.scalars(stmt)).all(), total or 0
```

- Somente SQLAlchemy Core/ORM com **parâmetros vinculados**. SQL textual (`text()`) é exceção revisada, sempre com bind params.
- O repository **não** faz `commit`; usa `flush` quando precisar do id.
- O escopo de acesso (`AccessScope`) é obrigatório em toda leitura de dado protegido.

### 8.5 Service (`service.py`)

```python
class StudentService:
    def __init__(
        self,
        repository: StudentRepository,
        audit: AuditService,
        uow: UnitOfWork,
    ) -> None:
        self._repository = repository
        self._audit = audit
        self._uow = uow

    async def update(
        self, actor: CurrentUser, student_id: UUID, data: StudentUpdate
    ) -> Student:
        ensure_can_manage_students(actor)
        student = await self._repository.get(student_id, actor.scope)
        if student is None:
            raise StudentNotFoundError()
        student.apply(data)
        await self._audit.record(actor, "student.updated", "student", student.id)
        await self._uow.commit()
        return student
```

- O service é dono da **transação**: o `commit` acontece aqui, uma vez por caso de uso, nunca no router nem no encerramento de dependência.
- Erros de negócio são exceções tipadas (`AppError` e subclasses), nunca `HTTPException` dentro do service.
- Operações multi-etapa (salvar chamada + registros + auditoria) são atômicas na mesma transação.
- Upsert em massa com `INSERT ... ON CONFLICT DO UPDATE`.

### 8.6 Router (`router.py`)

```python
router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=Page[StudentRead])
async def list_students(
    filters: Annotated[StudentFilters, Query()],
    service: StudentServiceDep,
    actor: CurrentUserDep,
) -> Page[StudentRead]:
    items, total = await service.list(actor, filters)
    return Page.of(items, total, filters)


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
async def create_student(
    data: StudentCreate,
    service: StudentServiceDep,
    actor: Annotated[CurrentUser, Depends(require_roles(Role.ADMIN))],
) -> Student:
    return await service.create(actor, data)
```

- Router fino: valida, injeta, delega, devolve. Sem `if` de regra de negócio, sem SQL, sem `commit`.
- Dependências tipadas com `Annotated` e aliases (`CurrentUserDep`, `SessionDep`, `StudentServiceDep`).
- Todas as rotas são `async def` e **nunca** chamam código bloqueante (I/O síncrono, hash de senha, geração de XLSX): usar `anyio.to_thread` / `run_in_threadpool` quando inevitável.

### 8.7 Erros (`core/errors.py`)

```python
class AppError(Exception):
    status_code: int = 400
    code: str = "app_error"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class StudentNotFoundError(NotFoundError):
    code = "student_not_found"
```

- Handlers globais convertem `AppError`, `RequestValidationError` e exceções inesperadas em `application/problem+json`. Erros inesperados retornam `500` genérico com `requestId`; detalhes só em log.

---

## 9. Migrations (Alembic)

- **Toda mudança de schema passa por migration.** Proibido `create_all()` e alterações manuais no banco.
- Nome do arquivo: `YYYYMMDD_HHMM_<slug>.py` (via `file_template`), mensagem em inglês e imperativa.
- `alembic revision --autogenerate` é **ponto de partida**: o autor revisa e corrige o SQL gerado (renomeações, índices, constraints, `server_default`).
- **Uma migration por PR/mudança lógica**; nunca editar migration já aplicada em ambiente compartilhado.
- **Compatibilidade para zero-downtime (expand → migrate → contract):** adicionar coluna nullable/com default → backfill → só então tornar `NOT NULL` ou remover a antiga em release posterior. Índices grandes com `CREATE INDEX CONCURRENTLY`.
- Toda migration traz `downgrade()` funcional, exceto as destrutivas explicitamente marcadas como irreversíveis.
- Extensões (`citext`, `unaccent`, `pg_trgm`) criadas na primeira migration.
- Migrations rodam em **etapa de release separada** (job), nunca na inicialização da aplicação, e com uma **role de banco própria** (com DDL). A aplicação usa uma role sem DDL.
- **Seed:** dados de referência vêm de comando CLI idempotente (`apan seed`); dados de teste/demonstração apenas fora de produção. Nenhuma credencial em migration.
- CI: `alembic upgrade head` em banco limpo, `alembic downgrade -1` + `upgrade head` e `alembic check` (detecta divergência entre models e migrations).

---

## 10. Segurança (checklist OWASP ASVS / API Top 10)

**Entrada e saída**
- Toda entrada validada por Pydantic (tipos estritos, limites de tamanho, `extra="forbid"`).
- Limite de tamanho de corpo e de upload; `pageSize` com teto; ordenação com lista branca.
- Respostas sempre via `response_model` explícito.

**Autenticação e sessão** — seção 6.

**Autorização** — escopo por objeto na query; testes de papel × recurso; `404` para fora do escopo.

**Transporte e navegador**
- TLS obrigatório; `Strict-Transport-Security` e headers de segurança (`X-Content-Type-Options`, `Referrer-Policy`, `Cache-Control: no-store` em respostas autenticadas) via middleware/proxy.
- **CORS** com lista explícita de origens; nunca `*` com credenciais.
- `TrustedHostMiddleware` com hosts permitidos.

**Dados**
- Somente consultas parametrizadas; zero SQL por concatenação.
- Conexão ao banco com TLS; role da aplicação com **privilégios mínimos** (sem DDL, sem `DELETE` em `audit_logs`).
- Segredos fora do repositório; rotação documentada; nada de segredo em log, imagem Docker ou erro.
- Backups criptografados e restauração testada.

**Abuso**
- Rate limiting global e reforçado em `login`, `refresh`, `forgot`, exportação e busca (Redis em produção).
- Timeouts em chamadas externas e em queries (`statement_timeout`).

**Cadeia de suprimentos**
- `uv.lock` versionado; `pip-audit` e Dependabot/Renovate no CI; imagens base fixadas por digest e escaneadas.
- Ruff com regras `S` (bandit) como erro.

**Contêiner**
- Multi-stage, usuário **não-root**, sistema de arquivos somente leitura quando possível, sem ferramentas de build na imagem final.

**Logs e auditoria**
- Logs estruturados (JSON) com `requestId`; **nunca** logar senha, token, cabeçalho `Authorization`, CPF, telefone ou nome completo; mascarar quando indispensável.
- `audit_logs` para: login/falhas, mudanças de senha/papel, CRUD de aluno e turma, registro/edição de chamada, exportações.

---

## 11. LGPD (dados de crianças e adolescentes)

- **Minimização:** coletar apenas o necessário. Não armazenar CPF/RG/saúde sem decisão formal; se necessário, criptografar a coluna.
- **Finalidade e base legal** documentadas por tabela com dado pessoal.
- **Acesso restrito e rastreável:** professor só vê alunos das suas turmas; leitura de ficha de aluno por `admin` gera auditoria.
- **Retenção:** política definida (ex.: anos após conclusão) com job de anonimização/eliminação; arquivamento em vez de `DELETE` durante a retenção.
- **Direitos do titular/responsável:** rotina para exportar e corrigir dados; processo de eliminação documentado.
- **Ambientes não produtivos** nunca usam dados reais; fixtures sintéticas.
- **Incidentes:** logs e auditoria suficientes para investigar vazamento; contato do encarregado (DPO) documentado fora do código.

---

## 12. Observabilidade

- **Logs:** structlog em JSON; `requestId` gerado/propagado (`X-Request-ID`) e presente em todo log e resposta de erro.
- **Métricas:** Prometheus (latência, taxa de erro, requisições por rota, pool de conexões do banco).
- **Tracing:** OpenTelemetry (FastAPI, SQLAlchemy, Redis, HTTP client).
- **Erros:** Sentry com scrub de dados pessoais.
- **Health:** `/health/live` (processo vivo) e `/health/ready` (banco e Redis alcançáveis); sem autenticação e sem detalhes internos.

---

## 13. Configuração, execução e deploy

- **12-factor:** configuração por variáveis de ambiente validadas; mesma imagem em todos os ambientes.
- **Docker:** multi-stage com `uv`; `docker-compose.yml` de desenvolvimento com Postgres, Redis e Mailpit.
- **Servidor:** Uvicorn com múltiplos workers atrás de proxy reverso/load balancer com TLS.
- **Pool de conexões:** dimensionado por (`workers × pool_size`) ≤ `max_connections` do Postgres; `pool_pre_ping=True`; timeouts configurados. Em alta escala, PgBouncer.
- **Fuso horário:** banco e aplicação em UTC; conversão para `America/Sao_Paulo`/`America/Manaus` é responsabilidade da apresentação.
- **Release:** pipeline → build → testes → imagem → job de migration → deploy → smoke test (`/health/ready`).
- **Tarefas assíncronas (fase 2):** só adicionar fila (Celery + Redis) se exportações/relatórios ficarem pesados; na v1, usar resposta em streaming.
- Comandos padronizados no `Makefile`: `make dev`, `make lint`, `make typecheck`, `make test`, `make migrate`, `make revision m="..."`.

---

## 14. Testes

| Tipo | O que cobrir |
|---|---|
| Unitário (`tests/unit`) | `domain.py` e `policies.py`: cálculo de frequência, idade, janela de edição, regras de matrícula |
| Integração (`tests/integration`) | Endpoints com `httpx.AsyncClient` + **PostgreSQL real** (testcontainers) |
| Segurança (`tests/security`) | **Matriz papel × endpoint**, IDOR (professor acessando turma alheia), rate limit, reuso de refresh token, mass assignment, enumeração de usuário |
| Migrations | `upgrade head`, `downgrade`/`upgrade` e `alembic check` |
| Contrato | OpenAPI exportado é versionado e comparado no CI (mudança incompatível quebra o build) |

- **Nunca SQLite.** Mesmo motor, extensões e constraints de produção.
- Isolamento: transação com savepoint revertida ao fim de cada teste, ou banco por worker.
- Dados com `polyfactory`/factories em `tests/factories`; sem fixtures gigantes.
- Descrições de teste em inglês (`test_teacher_cannot_read_student_from_unassigned_class`).
- Cobertura mínima de 85% em `service` e `domain`; **100% dos endpoints** com teste de autorização.
- Todo bug corrigido ganha teste de regressão.

---

## 15. Qualidade, Git e PR

- **Commits e PRs em inglês**, Conventional Commits (`feat(roll-calls): make roll call save idempotent`).
- **Branches:** `feat/<scope>-<description>`, `fix/...`. PRs pequenos.
- **pre-commit:** Ruff (lint + format), mypy, `uv lock --check`.
- **CI:** lint, typecheck, import-linter, testes com Postgres/Redis, `pip-audit`, `alembic check`, build da imagem.

### Checklist de PR

**Segurança (bloqueante)**
- [ ] Toda rota nova exige autenticação e tem autorização de papel **e** de objeto
- [ ] Escopo de acesso aplicado na query; recurso fora do escopo retorna 404
- [ ] Schemas de entrada com `extra="forbid"`; resposta com `response_model` sem campos sensíveis
- [ ] Nenhum SQL por concatenação; nenhum dado pessoal/segredo em log
- [ ] Rate limit em endpoints sensíveis; ação sensível auditada
- [ ] Teste de autorização (papel × recurso) e de IDOR incluído

**Banco**
- [ ] Migration revisada, reversível e compatível com zero-downtime
- [ ] Constraints, FKs e índices necessários criados
- [ ] Sem N+1 (`lazy="raise"` + carregamento explícito); agregações em SQL

**Código**
- [ ] Todo o código em inglês; nenhum texto de usuário no backend, apenas `code` estável
- [ ] Camadas respeitadas (import-linter verde); commit só no service
- [ ] Sem comentários desnecessários, sem código comentado, sem `print`
- [ ] Tipos completos (mypy strict), sem `Any` sem justificativa
- [ ] OpenAPI atualizado e tipos do frontend regenerados
- [ ] Testes unitários e de integração para a regra nova

---

## 16. Como criar um novo módulo (passo a passo)

1. Criar `modules/<name>/` (snake_case, inglês) com `router.py`, `service.py`, `repository.py`, `models.py`, `schemas.py`, `domain.py`, `policies.py`, `errors.py`, `dependencies.py`, `__init__.py`.
2. Modelar a tabela (constraints e índices inclusos) e gerar/revisar a **migration**.
3. Escrever `domain.py` e `policies.py` (puros) com testes unitários.
4. Escrever `schemas.py` (`Create`, `Update`, `Read`, `Filters`).
5. Implementar `repository.py` (com `AccessScope`), depois `service.py` (transação, auditoria, erros tipados).
6. Implementar `router.py` e registrar em `main.py`.
7. Declarar os `code` de erro novos e documentar no OpenAPI.
8. Testes de integração, de autorização (papel × recurso) e de IDOR.
9. Exportar o OpenAPI e regenerar os tipos do frontend.
10. Conferir o checklist de PR.

---

## 17. Alinhamento com o frontend

- **Contrato único:** o OpenAPI do backend gera os tipos do frontend (`openapi-typescript`). O backend não muda campo sem regenerar e versionar o contrato.
- **IDs são UUID (`string`)** em toda a API. O guia de frontend deve usar `id: string` (não `number`).
- **JSON em `camelCase`**, valores de enum em inglês (`present`, `absent`, `morning`, `afternoon`, `evening`, `admin`, `teacher`); o frontend traduz para pt-BR com seus `labels.ts`.
- **Mensagens de erro:** o frontend mapeia `code` → texto em pt-BR; `fieldErrors[].field` casa com os nomes dos campos do formulário.
- **Rotas do frontend e da API usam o mesmo vocabulário:** `students`, `classes`, `roll-calls`, `reports`.
- **Autenticação:** access token em memória + refresh por cookie `HttpOnly`; o cliente HTTP do frontend renova o token ao receber `401` e reenvia a requisição uma vez.
- **Datas:** a API envia `date` como `YYYY-MM-DD` e instantes como ISO-8601 em UTC.

---

## 18. Instruções para assistentes de IA

Ao gerar ou modificar código neste repositório:

1. **Siga este documento à risca** e use o módulo `students` como modelo.
2. **Todo o código em inglês.** O backend não escreve texto de interface: devolva `code` estável, o frontend traduz.
3. **Respeite as camadas:** router → service → repository → model. Sem SQL no service, sem regra no router, sem commit fora do service.
4. **Segurança primeiro:** autenticação e autorização (papel **e** escopo por objeto) em toda rota, `extra="forbid"` na entrada, `response_model` explícito, SQL sempre parametrizado, nenhum dado pessoal em log. Em dúvida, negue acesso e peça confirmação.
5. **Nunca** retorne objetos ORM nem exponha hash, token ou campo interno.
6. **Todo schema de banco muda por migration** revisada e reversível; inclua constraints e índices.
7. **Sem comentários desnecessários.** Comente apenas o porquê não óbvio.
8. Use SQLAlchemy 2.0 async (`Mapped[]`, `select()`), Pydantic v2 e FastAPI com `Annotated`; sem APIs legadas.
9. Não introduza bibliotecas novas; se achar necessário, pare e proponha com justificativa.
10. Entregue código **completo e tipado** (mypy strict), com testes (unitário, integração e autorização), sem placeholders.
11. Ao criar ou alterar endpoint, atualize o OpenAPI e liste os impactos no frontend.
12. Não faça refatorações fora do escopo pedido; aponte-as como sugestão ao final.

---

## 19. Decisões em aberto (confirmar antes de implementar)

1. **Multi-unidade/escola:** o protótipo menciona "unidade". Se houver mais de uma escola, adicionar `school_id` desde o início (escopo de acesso e índices dependem disso).
2. **E-mail transacional:** o texto de e-mails (convite, redefinição de senha) é voltado ao usuário e precisaria estar em pt-BR em templates do backend. Confirmar se essa exceção à regra "backend sem texto em português" é aceita.
3. **Faltas justificadas** e seu efeito no cálculo dos 75%: definir regra de negócio com a coordenação.
4. **Janela de edição da chamada** para professores (quantos dias) e quem pode reabrir.
5. **MFA** para `admin` (TOTP) já na v1 ou na fase 2.
6. **Provedor de e-mail** e **hospedagem** (define gerenciador de segredos, proxy e estratégia de backup).
7. **Retenção de dados** (prazo LGPD) e política de anonimização.
