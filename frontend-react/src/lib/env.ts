import { z } from "zod"

const envSchema = z.object({
  VITE_API_BASE_URL: z.string().url().default("http://localhost:8000"),
  VITE_APP_NAME: z.string().min(1).default("简历深度面试平台"),
})

export const env = envSchema.parse(import.meta.env)
