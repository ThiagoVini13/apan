import { z } from 'zod'

const EnvSchema = z.object({
  VITE_API_PREFIX: z.string().startsWith('/').default('/api/v1'),
})

const parsed = EnvSchema.parse(import.meta.env)

export const env = {
  apiPrefix: parsed.VITE_API_PREFIX,
}
