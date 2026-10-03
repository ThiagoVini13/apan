# APAN Frequência Escolar — Guia de Arquitetura e Padrões

> Use este documento como prompt/contexto fixo (CLAUDE.md, AGENTS.md, regras do Cursor/Copilot ou colado no início de qualquer conversa com IA) e como referência de code review para toda a equipe.
> Regra de ouro: **se algo não está coberto aqui, siga o padrão da feature `students`, que é a feature de referência.**

## 0. Princípios inegociáveis

1. **Acessibilidade vem primeiro (WCAG 2.1 AA).** Em conflito entre acessibilidade e visual, prazo ou conveniência, a acessibilidade vence. Detalhes na seção 8.
2. **Todo o código é em inglês.** Identificadores, arquivos, pastas, tipos, rotas, campos da API, mensagens de commit e descrições de testes. **Somente o texto exibido ao usuário (frontend) é em português (pt-BR).** Detalhes na seção 5.
3. **Tema claro e escuro em toda a interface**, via tokens de design. Nada de cor fixa nos componentes. Detalhes na seção 7.
4. **Sem comentários desnecessários.** O código deve se explicar por nomes claros. Detalhes na seção 6.

---

## 1. Contexto do produto

Sistema web de controle de frequência escolar.

- **Telas:** Início (dashboard), Chamada (roll call), Alunos (students), Relatórios (reports).
- **Perfis:** `teacher` (vê só as próprias turmas) e `admin` (vê todas).
- **Entidades:** `SchoolClass` (turma), `Student` (aluno), `RollCall` (chamada de uma turma em uma data), `Report` (agregados).
- **Regras de negócio chave:**
  - Mínimo legal de presença: **75%** (constante única `MIN_ATTENDANCE_RATE = 75`).
  - Aluno menor de 18 anos exige nome do responsável (`guardianName`).
  - Idade mínima de matrícula: 3 anos. Data de nascimento não pode ser futura.
  - Telefone: DDD + número (10 ou 11 dígitos), com máscara.
  - A chamada só pode ser salva com **todos** os alunos marcados (modo `segmented`) ou com padrão "presente" (modo `switch`).
  - Período de relatório: `to` ≥ `from`.
- **Prioridades:** acessibilidade, uso em celular e desktop, tolerância a internet ruim em sala de aula.

---

## 2. Stack (não adicionar libs fora desta lista sem aprovação)

| Necessidade | Lib |
|---|---|
| Build / dev server | **Vite** |
| UI | **React 18+** com **TypeScript estrito** (`strict: true`, sem `any`) |
| Rotas | **React Router v6/v7** (data router, `createBrowserRouter`) |
| Dados do servidor, cache, mutations | **TanStack Query v5** |
| Formulários | **React Hook Form** + **Zod** (`@hookform/resolvers/zod`) |
| Estado global de UI | **Zustand** (somente UI/preferências, nunca dados do servidor) |
| Estilo | **Tailwind CSS** + **Radix UI primitives** (padrão shadcn/ui) |
| HTTP | **ky** (wrapper único em `shared/lib/http.ts`) |
| Datas | **date-fns** com locale `pt-BR` |
| Gráficos | **Recharts** (ou SVG próprio para donut/barras simples) |
| Testes | **Vitest** + **Testing Library** + **MSW** + **vitest-axe** |
| Lint / format | **ESLint** (typescript-eslint, react-hooks, jsx-a11y strict, import) + **Prettier** |
| Tipos da API | **openapi-typescript** (se houver OpenAPI) ou schemas Zod em `api/` |

**Não usar:** Redux, MobX, Context API para dados do servidor, `useEffect` para buscar dados, `fetch`/`axios` direto nos componentes, CSS-in-JS, bibliotecas de componentes pesadas (MUI/Ant), moment.js.

---

## 3. Estrutura de pastas

Organização **por feature**, não por tipo de arquivo.

```
src/
├── app/
│   ├── providers.tsx
│   ├── router.tsx
│   ├── query-client.ts
│   └── layouts/
│       ├── AppShell.tsx
│       ├── Sidebar.tsx
│       ├── BottomNav.tsx
│       └── ThemeToggle.tsx
├── features/
│   ├── auth/
│   ├── dashboard/
│   ├── classes/
│   ├── students/
│   │   ├── api/
│   │   │   ├── students.api.ts
│   │   │   ├── students.keys.ts
│   │   │   └── students.queries.ts
│   │   ├── components/
│   │   │   ├── StudentsTable.tsx
│   │   │   ├── StudentCard.tsx
│   │   │   ├── StudentsFilters.tsx
│   │   │   └── StudentFormDialog.tsx
│   │   ├── schemas/student.schema.ts
│   │   ├── lib/
│   │   ├── pages/StudentsPage.tsx
│   │   ├── labels.ts
│   │   ├── types.ts
│   │   └── index.ts
│   ├── roll-call/
│   └── reports/
├── shared/
│   ├── ui/
│   │   ├── Button.tsx  Field.tsx  Select.tsx  Dialog.tsx
│   │   ├── StatusPill.tsx  EmptyState.tsx  Toast.tsx  VisuallyHidden.tsx
│   ├── hooks/
│   ├── lib/
│   │   ├── http.ts
│   │   ├── format.ts
│   │   ├── date.ts
│   │   ├── labels.ts
│   │   └── constants.ts
│   └── types/
├── stores/
│   ├── theme.store.ts
│   └── preferences.store.ts
├── test/
├── main.tsx
└── index.css
```

### Regras de dependência (impostas por ESLint `import/no-restricted-paths`)

1. `features/*` pode importar de `shared/*`, `stores/*` e de si mesma.
2. `features/A` **nunca** importa de `features/B`. Se duas features precisam do mesmo código, ele sobe para `shared/`. Exceção única: importar de `features/B/index.ts` (API pública), apenas para tipos e hooks de leitura, e com justificativa no PR.
3. `shared/*` **nunca** importa de `features/*` nem de `app/*`.
4. `app/*` pode importar de tudo (é a camada de composição).
5. Importar de dentro de outra feature (`features/students/components/X`) é proibido: use apenas o `index.ts`.
6. Usar alias `@/` para `src/`. Imports relativos só dentro da mesma feature.

---

## 4. Padrões de código por tipo de arquivo

### 4.1 Camada de API (`*.api.ts`)

Funções puras, tipadas, sem React. Um único lugar que conhece URLs.

```ts
import { http } from '@/shared/lib/http';
import type { Student, StudentInput, StudentsFilters } from '../types';

export const studentsApi = {
  list: (filters: StudentsFilters) =>
    http.get('students', { searchParams: filters }).json<Student[]>(),
  get: (id: number) => http.get(`students/${id}`).json<Student>(),
  create: (data: StudentInput) => http.post('students', { json: data }).json<Student>(),
  update: (id: number, data: StudentInput) =>
    http.put(`students/${id}`, { json: data }).json<Student>(),
};
```

- Respostas validadas com Zod quando a API não tiver tipos gerados.
- Erros HTTP são normalizados em `ApiError` dentro de `http.ts` (nunca tratar `Response` nos componentes).

### 4.2 Query keys (`*.keys.ts`)

Factory hierárquica por feature. **Proibido** montar arrays de key inline.

```ts
export const studentsKeys = {
  all: ['students'] as const,
  lists: () => [...studentsKeys.all, 'list'] as const,
  list: (filters: StudentsFilters) => [...studentsKeys.lists(), filters] as const,
  details: () => [...studentsKeys.all, 'detail'] as const,
  detail: (id: number) => [...studentsKeys.details(), id] as const,
};
```

### 4.3 Queries e mutations (`*.queries.ts`)

- Um hook por operação: `useStudents`, `useStudent`, `useSaveStudent`.
- Componentes **nunca** chamam `useQuery`/`useMutation` direto: sempre via hook da feature.
- `queryOptions()` para reuso (prefetch em loaders, `useQueries`).
- Defaults no `QueryClient`: `staleTime` de 30s, `retry: 1`, `refetchOnWindowFocus: false`. Sobrescrever por hook quando fizer sentido (ex.: `classes` com `staleTime` de 10 min).
- Listas filtráveis usam `placeholderData: keepPreviousData`.
- Queries dependentes usam `enabled`.
- Mutations: `onSuccess` invalida **por key factory**; erro de negócio (422) é mapeado no formulário, erro genérico cai no handler global.

```ts
export function useSaveStudent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id?: number; data: StudentInput }) =>
      id ? studentsApi.update(id, data) : studentsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: studentsKeys.all });
      queryClient.invalidateQueries({ queryKey: classesKeys.all });
    },
  });
}
```

**Invalidações obrigatórias do domínio:**
- salvar chamada → invalida `dashboard`, `roll-calls`, `reports`, `students` (a frequência individual muda);
- salvar aluno → invalida `students` e `classes` (contagem).

### 4.4 Schemas (`*.schema.ts`)

- O schema Zod é a **fonte da verdade** das regras de validação **e** dos tipos do formulário (`z.infer`).
- Mensagens de erro em pt-BR no próprio schema (são texto de interface).
- Regras entre campos usam `superRefine` (ex.: responsável obrigatório para menores).
- Funções auxiliares (calcular idade, máscara) ficam em `lib/` ou `shared/lib/` e têm teste unitário.

### 4.5 Páginas (`pages/*Page.tsx`)

- Finas: leem `searchParams`, chamam hooks, compõem componentes. Sem regra de negócio, sem JSX gigante.
- Exportação **default** apenas em páginas (necessário para `lazy`). Todo o resto usa export nomeado.
- **Filtros e período vivem na URL** (`useSearchParams`), não em `useState`.
- Cada página trata os 4 estados explicitamente: **loading** (skeleton), **erro** (mensagem + "Tentar novamente"), **vazio** (`EmptyState`) e **sucesso**.
- Cada página define um `<title>` único e descritivo e move o foco para o `<h1>` ou `<main>` ao navegar.

### 4.6 Componentes

- Function components com `export function Name()`. Um componente por arquivo, arquivo com o nome do componente (PascalCase).
- Props tipadas com `type NameProps = {...}` no próprio arquivo; sem `React.FC`.
- Componentes de `shared/ui` são **burros**: sem fetch, sem conhecimento de domínio, aceitam `className` e repassam props nativas (`ComponentPropsWithoutRef`).
- Componentes de feature podem conhecer o domínio, mas não fazem request: recebem dados por props ou usam hooks da feature.
- Composição > configuração: preferir `children`/slots a props booleanas em excesso.
- Variantes com `cva`; classes combinadas com `cn()` (clsx + tailwind-merge).
- Listas sempre com `key` estável (id do dado, nunca índice).
- Memoização (`useMemo`, `useCallback`, `memo`) só com problema medido.

### 4.7 Formulários

- Sempre React Hook Form + `zodResolver`, com `mode: 'onTouched'`.
- Todo campo usa o componente `Field` de `shared/ui`, que garante label visível, `aria-invalid`, `aria-describedby`, `autoComplete` adequado e mensagem de erro com ícone + texto.
- Ao submeter com erro: foco no primeiro campo inválido e mensagem-resumo anunciada (`role="alert"`).
- O botão de envio mostra `isPending` e fica desabilitado durante a mutation.
- Modais de formulário são **rotas filhas** (`/students/new`, `/students/:id/edit`) para suportar o botão voltar e link direto.

### 4.8 Estado

| Tipo de estado | Onde vive |
|---|---|
| Dados do servidor | TanStack Query (nunca copiar para Zustand/useState) |
| Filtros, período, turma selecionada | URL (`searchParams`) |
| Rascunho de chamada (marcações, anotações) | Estado local da `RollCallPage` (`useReducer`), enviado no "Salvar" |
| Tema (`light` / `dark` / `system`) | `theme.store.ts` |
| Preferências (`rollCallMode`, `showAvatars`) | `preferences.store.ts` (Zustand + `persist`) |
| Sessão/perfil | Query `useSession` + `RequireRole` |
| Estado efêmero de componente | `useState` local |

- Alterações não salvas na chamada: `useBlocker` (React Router) com confirmação.
- Toasts: um único `Toaster` em `app/providers.tsx`, acionado por `notify.success/warn/error`.

### 4.9 Rotas

```
/                                              Dashboard
/roll-call/:classId?date=YYYY-MM-DD            Roll call
/students?q=&classId=&shift=                   Students list
/students/new                                  Dialog: new student
/students/:id/edit                             Dialog: edit student
/reports?from=&to=&classId=&studentId=         Reports
```

- Páginas carregadas com `lazy()` + `Suspense` no nível do router.
- Proteção por perfil com `<RequireRole roles={['admin']}>`; o **backend é a autoridade**, o front só esconde.
- O filtro "teacher vê só as próprias turmas" é feito **pela API**, nunca no cliente.

---

## 5. Idioma e convenções de nomes

### 5.1 O que é inglês e o que é português

| Em **inglês** | Em **português (pt-BR)** |
|---|---|
| Identificadores, funções, hooks, tipos, enums | Texto visível na tela (títulos, labels, botões, placeholders) |
| Nomes de arquivos e pastas | Mensagens de validação dos schemas Zod |
| Rotas/URLs e query params | `aria-label`, `aria-describedby` e demais textos para leitores de tela |
| Campos e códigos de erro da API | Mensagens de toast, erro e estado vazio |
| Valores de enum (`'present'`, `'morning'`, `'teacher'`) | `<title>` das páginas |
| Mensagens de commit, títulos de PR, nomes de branch | Locale de formatação (`pt-BR`) e `<html lang="pt-BR">` |
| Descrições de testes (`describe`/`it`) | |

- **Valores de domínio nunca são exibidos diretamente.** Cada enum tem um mapa de rótulos em pt-BR (`labels.ts`):

```ts
export const shiftLabels: Record<Shift, string> = {
  morning: 'Manhã',
  afternoon: 'Tarde',
  evening: 'Noite',
};
```

- Textos repetidos em mais de um lugar vão para um `messages.ts` da feature.
- Termos do domínio: `SchoolClass` (turma; `Class` é palavra reservada), `Student`, `RollCall`, `Attendance`, `AttendanceStatus = 'present' | 'absent'`, `Shift`, `Subject`, `enrollmentNumber`, `guardianName`, `guardianPhone`.

### 5.2 Padrões de nomes

| Item | Padrão | Exemplo |
|---|---|---|
| Componentes, tipos, schemas Zod | PascalCase | `StudentFormDialog`, `StudentSchema` |
| Hooks | `use` + PascalCase | `useStudents`, `useSaveRollCall` |
| Funções, variáveis | camelCase | `calculateAge` |
| Constantes | UPPER_SNAKE_CASE | `MIN_ATTENDANCE_RATE` |
| Arquivos de componente | PascalCase | `StudentsTable.tsx` |
| Arquivos não-componente | kebab-case com sufixo de papel | `students.api.ts`, `student.schema.ts`, `theme.store.ts` |
| Pastas | kebab-case | `features/roll-call` |
| Testes | ao lado do arquivo | `StudentsTable.test.tsx`, `age.test.ts` |
| Handlers | `handleX` (definição) / `onX` (prop) | `handleSubmit`, `onSelect` |
| Booleanos | prefixo `is/has/can/should` | `isPending`, `hasFilters` |

---

## 6. Comentários

- **Padrão: nenhum comentário.** Nomes claros, funções pequenas e tipos expressivos substituem comentários.
- Comentar **apenas o porquê**, nunca o o quê: workaround de bug de lib/navegador (com link), regra de negócio não óbvia, decisão de performance medida.
- Proibido: comentário que repete o código, código comentado, `// TODO` sem link para ticket, banners/separadores de seção, comentários de changelog (o histórico é do Git).
- JSDoc apenas em API pública de `shared/` quando os tipos não bastam para explicar o uso.
- Se um comentário parece necessário, primeiro tente renomear ou extrair uma função.

---

## 7. Estilo, design system e tema claro/escuro

### 7.1 Tokens

- Toda cor é um **token semântico** definido como variável CSS e mapeado no tema do Tailwind. Componentes usam classes semânticas (`bg-surface`, `text-fg`, `text-fg-muted`, `border-line`, `bg-primary`, `text-primary-fg`).
- **Proibido:** hex/rgb solto em componente, cores nomeadas do Tailwind (`bg-blue-600`) e variantes `dark:` espalhadas pelos componentes. Trocar de tema deve ser apenas trocar os valores dos tokens.
- Tokens que existem em pares (fundo + texto sobre ele) são garantidos juntos: `success` / `success-fg`, `danger` / `danger-fg`, `warning` / `warning-fg`, `primary` / `primary-fg`.
- Existem tokens **separados para preenchimento e para texto/link** (`primary` vs `primary-text`), porque uma cor que passa como fundo de botão pode falhar como texto sobre superfície escura.

Valores iniciais (devem ser **validados com verificador de contraste** antes de uso e ajustados se necessário):

| Token | Claro | Escuro |
|---|---|---|
| `bg` | `#F4F6F9` | `#0F141B` |
| `surface` | `#FFFFFF` | `#171D26` |
| `line` | `#E2E6EC` | `#2A3340` |
| `line-strong` (bordas de input) | `#8A94A3` | `#6B7686` |
| `fg` | `#14181F` | `#E8ECF2` |
| `fg-muted` | `#4B5563` | `#A3ADBB` |
| `primary` (preenchimento) | `#1A56DB` | `#2F6FED` |
| `primary-fg` | `#FFFFFF` | `#FFFFFF` |
| `primary-text` (links/ícones) | `#1A56DB` | `#8AB4FF` |
| `success` / `success-bg` | `#057A55` / `#E6F4EC` | `#4ADE9B` / `#0F2A20` |
| `danger` / `danger-bg` | `#C81E1E` / `#FDECEC` | `#FF8A8A` / `#301616` |
| `warning` / `warning-bg` | `#B84300` / `#FDF0E6` | `#FFB27A` / `#33210F` |
| `focus-ring` | `#1A56DB` | `#8AB4FF` |

```css
:root {
  color-scheme: light;
  --bg: #f4f6f9;
  --surface: #ffffff;
  --fg: #14181f;
}

.dark {
  color-scheme: dark;
  --bg: #0f141b;
  --surface: #171d26;
  --fg: #e8ecf2;
}
```

### 7.2 Mecânica do tema

- Três opções: **claro, escuro e sistema** (padrão: `system`, respeitando `prefers-color-scheme`).
- Tailwind com `darkMode: 'class'`; a classe `dark` fica no `<html>`.
- `theme.store.ts` persiste a escolha, aplica a classe e escuta mudanças de `prefers-color-scheme` enquanto estiver em `system`.
- **Sem flash de tema errado:** um script inline no `index.html` aplica a classe antes da primeira renderização.

```html
<script>
  (function () {
    try {
      var stored = localStorage.getItem('apan-theme');
      var prefersDark = matchMedia('(prefers-color-scheme: dark)').matches;
      var isDark = stored === 'dark' || ((!stored || stored === 'system') && prefersDark);
      document.documentElement.classList.toggle('dark', isDark);
    } catch (e) {}
  })();
</script>
```

- `ThemeToggle` no header é um grupo de rádio nativo com três opções e rótulos visíveis em pt-BR ("Claro", "Escuro", "Sistema"), totalmente operável por teclado.
- Gráficos, SVGs e ícones usam `currentColor` ou variáveis CSS, nunca cores fixas.
- Imagens/ilustrações precisam ser verificadas nos dois temas.
- **Todo componente novo é revisado nos dois temas** (e o PR deve conter print ou verificação de ambos).

### 7.3 Layout e demais regras

- Fonte: **Public Sans** (400/500/600/700), tamanhos em `rem`.
- **Mobile-first** com breakpoints do Tailwind. Sidebar a partir de `lg`, `BottomNav` abaixo; tabela de alunos a partir de `lg`, cards abaixo. Usar classes responsivas (`hidden lg:block`), **não** `window.innerWidth` em JS.
- Alvos de toque **≥ 44×44px** em todo elemento interativo.
- Números com `tabular-nums`.
- Animações curtas e sempre desativadas sob `prefers-reduced-motion: reduce`.

---

## 8. Acessibilidade — prioridade máxima (WCAG 2.1 AA)

Acessibilidade é requisito de aceite, não melhoria futura. Um PR que quebra qualquer item abaixo **não é aprovado**.

### 8.1 Perceptível

- **Contraste (1.4.3):** texto ≥ 4,5:1 (≥ 3:1 para texto grande) **nos dois temas**.
- **Contraste não textual (1.4.11):** bordas de inputs, ícones informativos, indicadores de foco e gráficos ≥ 3:1 contra o fundo adjacente.
- **Cor não é o único meio (1.4.1):** todo estado tem ícone + texto (presente ✓, ausente ✕, alerta !, campo inválido com mensagem). Nenhum estado pode depender só de cor.
- **Redimensionamento (1.4.4) e reflow (1.4.10):** tudo funciona com zoom de 200% e em 320px de largura, sem rolagem horizontal (exceto tabelas largas em contêiner com rolagem rotulada).
- **Espaçamento de texto (1.4.12):** layout não quebra com line-height 1,5 e espaçamento aumentado; nunca fixar `height` em contêiner de texto.
- **Texto alternativo (1.1.1):** ícones decorativos com `aria-hidden="true"`; imagens informativas com `alt` descritivo; ícone-botão com `aria-label` em pt-BR.
- **Estrutura (1.3.1):** HTML semântico (`header`, `nav`, `main`, `section`, `table`, `button`, `label`), hierarquia de títulos sem pular níveis, um único `<h1>` por página.
- **Finalidade dos campos (1.3.5):** `autoComplete` correto (`name`, `bday`, `tel`...).
- **Idioma (3.1.1):** `<html lang="pt-BR">`.
- **Movimento:** respeitar `prefers-reduced-motion`; nada pisca.

### 8.2 Operável

- **Teclado (2.1.1):** 100% operável sem mouse; sem armadilhas de foco; ordem de foco = ordem visual (2.4.3).
- **Foco visível (2.4.7):** `focus-visible:ring` com token `focus-ring`, ≥ 3:1, nunca removido com `outline: none` sem substituto.
- **Foco não obscurecido (2.4.11):** o rodapé fixo da chamada e a barra inferior mobile não podem cobrir o elemento focado (`scroll-padding-bottom` correspondente).
- **Pular blocos (2.4.1):** skip link "Pular para o conteúdo" como primeiro elemento focável; `<main id="main" tabIndex={-1}>`.
- **Títulos de página (2.4.2):** `<title>` único por rota, atualizado na navegação.
- **Propósito dos links/botões (2.4.4):** nomes acessíveis claros e únicos no contexto (ex.: "Editar Ana Beatriz Souza", não só "Editar").
- **Tamanho do alvo (2.5.8):** mínimo adotado de **44px**, acima do exigido pelo AA.
- **Foco ao navegar:** a cada troca de rota o foco vai para `<main>` ou `<h1>`; ao abrir/fechar diálogo o foco é preso e devolvido (Radix Dialog), `Esc` fecha.
- **Gestos:** nenhuma ação depende de gesto complexo, arrastar ou hover; tooltips também aparecem no foco.

### 8.3 Compreensível

- **Rótulos e instruções (3.3.2):** todo input tem `<label>` visível associado; obrigatoriedade indicada em texto ("Campos com * são obrigatórios").
- **Identificação e sugestão de erro (3.3.1, 3.3.3):** erro em texto, junto ao campo, com ícone, via `aria-invalid` + `aria-describedby`, dizendo **o que corrigir**; foco no primeiro campo inválido ao submeter.
- **Prevenção de erro (3.3.4):** ações que alteram dados importantes confirmam ou permitem revisar; alterações não salvas na chamada pedem confirmação ao sair.
- **Consistência (3.2.3, 3.2.4):** navegação e componentes iguais em todas as telas; nenhuma mudança de contexto automática ao focar/alterar um campo.

### 8.4 Robusto

- **Nome, função, valor (4.1.2):** preferir elementos nativos; ARIA só quando não houver equivalente nativo.
  - botões de seleção: `aria-pressed`;
  - interruptores: `role="switch"` + `aria-checked`;
  - nav atual: `aria-current="page"`;
  - tabelas: marcação nativa de `table`/`th scope`, ou roles `table/row/cell` completos.
- **Mensagens de status (4.1.3):** toasts, contadores de resultado e totais da chamada em região `role="status"` / `aria-live="polite"`; erros críticos com `role="alert"`.
- **Modo de alto contraste do SO (`forced-colors`):** estados não podem depender apenas de `background-color`; usar bordas e ícones.

### 8.5 Como garantir

- `eslint-plugin-jsx-a11y` em modo `strict` (erro, não aviso).
- Testes de componente e de página com `vitest-axe` (`toHaveNoViolations`) **nos dois temas**.
- Queries de teste por `getByRole` / `getByLabelText` (se não dá para consultar por role, a semântica está errada).
- Fase 2: Playwright + `@axe-core/playwright` no caminho crítico.
- Checklist manual em todo PR de UI: navegar só com teclado, zoom 200%, tema claro e escuro, e ao menos uma verificação com leitor de tela (NVDA ou VoiceOver) em fluxos novos.

---

## 9. Formatação e textos

- Datas e números passam por `shared/lib/format.ts` (nunca `toLocaleString` solto nos componentes).
- Datas na API em ISO `YYYY-MM-DD` (tipo `string`, sem `Date` para datas sem hora, evitando bug de fuso).
- Percentual em `pt-BR`: 1 casa nos relatórios (`87,5%`), 0 casas em listas.
- Busca textual ignora acentos e caixa (`normalize('NFD')`).
- Textos de interface: claros, em linguagem simples, com mensagens de erro que dizem como resolver.

---

## 10. Tratamento de erros e carregamento

- `http.ts` converte falhas em `ApiError { status, code, message, fieldErrors? }`.
- 401 → redireciona para login; 403 → tela "sem permissão"; 422 → `fieldErrors` mapeados no RHF (`setError`); demais → toast de erro + estado de erro na página.
- `ErrorBoundary` por rota (`errorElement`) para erros inesperados de render.
- Nunca `console.log` em código commitado.
- Skeletons no lugar de spinners para listas e cards, com `aria-busy` na região em carregamento.

---

## 11. Testes

| Tipo | Ferramenta | O que cobrir |
|---|---|---|
| Unitário | Vitest | Funções puras: idade, máscara de telefone, dias letivos, schemas Zod |
| Componente | Testing Library + vitest-axe | Interações por `getByRole`; loading/erro/vazio; sem violações axe nos dois temas |
| Integração de feature | RTL + MSW | Fluxos: cadastrar aluno, salvar chamada, filtrar relatório |
| E2E (fase 2) | Playwright + axe | Caminho crítico: login → chamada → relatório |

- Descrições de teste em inglês (`it('shows an error when the end date is before the start date')`); textos consultados na tela em pt-BR.
- Mock de rede **somente com MSW** (handlers em `src/test/handlers`), nunca mockando `ky`/hooks.
- `renderWithProviders` em `src/test` (QueryClient novo por teste, `retry: false`, opção de tema).
- Todo bug corrigido ganha teste de regressão.

---

## 12. Qualidade, Git e PR

- **Commits e PRs em inglês:** Conventional Commits (`feat(students): add guardian field`, `fix(roll-call): keep focus on save error`).
- **Branches:** `feat/<scope>-<description>`, `fix/...`. PRs pequenos e focados em uma feature.
- **Husky + lint-staged:** ESLint, Prettier e `tsc --noEmit` antes do commit.
- **CI:** lint, typecheck, testes (incluindo axe) e build precisam passar para merge.
- Variáveis de ambiente: sempre `VITE_*`, validadas com Zod em `shared/lib/env.ts`; nunca segredos no front.

### Checklist de PR

**Acessibilidade (bloqueante)**
- [ ] Operável só com teclado, foco visível e na ordem certa
- [ ] Contraste AA nos dois temas (texto 4,5:1; não textual 3:1)
- [ ] Nenhum estado depende só de cor
- [ ] Labels, erros, `aria-*` e `live regions` corretos; sem violações axe
- [ ] Alvos ≥ 44px; funciona com zoom 200% e em 320px
- [ ] `prefers-reduced-motion` respeitado; `<title>` e foco na navegação corretos

**Tema**
- [ ] Só tokens semânticos; nenhuma cor fixa nem `dark:` solto
- [ ] Verificado em claro e escuro

**Código**
- [ ] Todo o código em inglês; apenas texto de UI em pt-BR (via `labels.ts`/schemas)
- [ ] Sem comentários desnecessários, sem código comentado, sem `console.log`
- [ ] Respeita as regras de dependência entre pastas (seção 3)
- [ ] Sem `any`, sem `@ts-ignore` sem justificativa
- [ ] Dados do servidor só via TanStack Query, com keys da factory e invalidações corretas
- [ ] Filtros/período na URL
- [ ] Estados loading, erro, vazio e sucesso tratados
- [ ] Formulário com RHF + Zod, foco no primeiro erro
- [ ] Testes para regra de negócio nova e para o fluxo principal

---

## 13. Como criar uma nova feature (passo a passo)

1. Criar `features/<name>/` (kebab-case, inglês) com `api/`, `components/`, `pages/`, `schemas/`, `types.ts`, `labels.ts`, `index.ts`.
2. Definir **tipos** e **schema Zod** primeiro.
3. Escrever `*.api.ts` e `*.keys.ts`; depois os hooks em `*.queries.ts`.
4. Adicionar handlers MSW e testes dos hooks.
5. Construir componentes de apresentação com tokens de tema e semântica acessível; depois a página que compõe tudo.
6. Registrar a rota (lazy) em `app/router.tsx` e o item de navegação.
7. Definir quais outras keys precisam ser invalidadas.
8. Rodar axe nos dois temas e conferir o checklist de PR.

---

## 14. Instruções para assistentes de IA

Ao gerar ou modificar código neste repositório:

1. **Siga este documento à risca** e use a feature `students` como modelo de estrutura e estilo.
2. **Todo o código em inglês** (identificadores, arquivos, rotas, tipos, testes, commits). **Somente texto visível ao usuário em pt-BR**, passando por `labels.ts`, `messages.ts` ou schemas Zod.
3. **Não escreva comentários** a menos que expliquem um porquê não óbvio. Nunca comente o que o código já diz.
4. **Acessibilidade primeiro (WCAG 2.1 AA):** HTML semântico, teclado, foco visível, labels, `aria-*` corretos, estados com ícone + texto, alvos ≥ 44px. Se houver conflito entre visual e acessibilidade, a acessibilidade vence.
5. **Suporte a tema claro e escuro em todo componente:** use somente tokens semânticos (`bg-surface`, `text-fg`, ...). Nunca hex, nunca cores nomeadas do Tailwind, nunca `dark:` para cores.
6. Antes de criar um arquivo, verifique se já existe componente/hook equivalente em `shared/`.
7. Não introduza bibliotecas novas; se achar necessário, pare e proponha com justificativa.
8. Entregue código **completo e tipado**, sem `any` e sem placeholders.
9. Respeite as regras de import entre features; em caso de dúvida, mova o código para `shared/`.
10. Ao alterar regra de negócio, atualize schema, testes e, se necessário, este documento.
11. Em dúvida entre duas abordagens, escolha a mais simples e explique o trade-off em uma frase.
12. Não faça refatorações fora do escopo pedido; aponte-as como sugestão ao final.
