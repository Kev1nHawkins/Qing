import { reactive } from 'vue'
import type { Creation } from '@/types'

export const posterCreationSession = reactive({
  selectedTemplateCode: '',
  choices: {} as Record<string, string>,
  creation: null as Creation | null,
  generating: false,
  feedback: '',
  feedbackKind: 'info' as 'info' | 'success' | 'error',
})

export const freeImageCreationSession = reactive({
  prompt: '',
  aspectRatio: 'PORTRAIT' as 'SQUARE' | 'PORTRAIT' | 'LANDSCAPE',
  creation: null as Creation | null,
  generating: false,
  feedback: '',
})
