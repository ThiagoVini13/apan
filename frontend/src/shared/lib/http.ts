import ky, { isHTTPError, isNetworkError, isTimeoutError, type Options } from 'ky'
import { CSRF_HEADERS, refreshAccessToken, tokenStore } from './auth-token'
import { env } from './env'

export type FieldError = { field: string; code: string }

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly fieldErrors: FieldError[]
  readonly requestId: string | null

  constructor(
    status: number,
    code: string,
    fieldErrors: FieldError[] = [],
    requestId: string | null = null,
  ) {
    super(code)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.fieldErrors = fieldErrors
    this.requestId = requestId
  }
}

type ProblemBody = { code?: string; fieldErrors?: FieldError[]; requestId?: string }

export type SearchParams = Record<string, string | number | boolean | null | undefined>

type RequestOptions = {
  searchParams?: SearchParams
  json?: unknown
  skipAuthRefresh?: boolean
}

const client = ky.create({
  prefix: env.apiPrefix,
  baseUrl: globalThis.location?.origin,
  credentials: 'same-origin',
  timeout: 30_000,
  retry: { limit: 1, methods: ['get'], statusCodes: [408, 502, 503, 504] },
})

function cleanParams(params: SearchParams | undefined): Record<string, string> | undefined {
  if (!params) return undefined
  const entries = Object.entries(params).filter(
    (entry): entry is [string, string | number | boolean] =>
      entry[1] !== undefined && entry[1] !== null && entry[1] !== '',
  )
  return Object.fromEntries(entries.map(([key, value]) => [key, String(value)]))
}

function toApiError(error: unknown): ApiError {
  if (isHTTPError(error)) {
    const body = (
      typeof error.data === 'object' && error.data !== null ? error.data : {}
    ) as ProblemBody
    return new ApiError(
      error.response.status,
      body.code ?? 'http_error',
      body.fieldErrors ?? [],
      body.requestId ?? null,
    )
  }
  if (isNetworkError(error) || isTimeoutError(error)) return new ApiError(0, 'network_error')
  return new ApiError(0, 'unknown_error')
}

let unauthorizedHandler: () => void = () => {}

export function onUnauthorized(handler: () => void) {
  unauthorizedHandler = handler
}

async function send(
  method: string,
  path: string,
  options: RequestOptions = {},
  isRetry = false,
): Promise<Response> {
  const token = tokenStore.get()
  const kyOptions: Options = {
    method,
    searchParams: cleanParams(options.searchParams),
    json: options.json,
    headers: { ...CSRF_HEADERS, ...(token ? { Authorization: `Bearer ${token}` } : {}) },
  }
  try {
    return await client(path, kyOptions)
  } catch (error) {
    const isUnauthorized = isHTTPError(error) && error.response.status === 401
    if (isUnauthorized && !options.skipAuthRefresh && !isRetry && (await refreshAccessToken())) {
      return send(method, path, options, true)
    }
    if (isUnauthorized && !options.skipAuthRefresh) {
      tokenStore.set(null)
      unauthorizedHandler()
    }
    throw toApiError(error)
  }
}

async function json<T>(method: string, path: string, options?: RequestOptions): Promise<T> {
  const response = await send(method, path, options)
  if (response.status === 204 || response.status === 202) return undefined as T
  return (await response.json()) as T
}

export const http = {
  get: <T>(path: string, searchParams?: SearchParams) => json<T>('get', path, { searchParams }),
  post: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'json'>) =>
    json<T>('post', path, { ...options, json: body }),
  put: <T>(path: string, body: unknown) => json<T>('put', path, { json: body }),
  patch: <T>(path: string, body: unknown) => json<T>('patch', path, { json: body }),
  delete: (path: string) => json<void>('delete', path),
  blob: async (path: string, searchParams?: SearchParams) => {
    const response = await send('get', path, { searchParams })
    return response.blob()
  },
}
