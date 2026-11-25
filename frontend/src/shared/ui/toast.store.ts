import { create } from 'zustand'

export type Tone = 'success' | 'error' | 'info'
export type Toast = { id: number; tone: Tone; message: string }

type ToastState = {
  toasts: Toast[]
  push: (tone: Tone, message: string) => void
  dismiss: (id: number) => void
}

const DURATION_MS = 6000
let nextId = 1

export const useToastStore = create<ToastState>((set, get) => ({
  toasts: [],
  push: (tone, message) => {
    const id = nextId++
    set({ toasts: [...get().toasts.slice(-2), { id, tone, message }] })
    setTimeout(() => get().dismiss(id), DURATION_MS)
  },
  dismiss: (id) => set({ toasts: get().toasts.filter((toast) => toast.id !== id) }),
}))

export const notify = {
  success: (message: string) => useToastStore.getState().push('success', message),
  error: (message: string) => useToastStore.getState().push('error', message),
  info: (message: string) => useToastStore.getState().push('info', message),
}
