import { defineStore } from 'pinia'

export const useToastStore = defineStore('toast', {
  state: () => ({
    visible: false,
    message: '',
    actionLabel: null as string | null,
    actionTo: null as string | null,
    timer: null as ReturnType<typeof setTimeout> | null,
  }),
  actions: {
    show(message: string, action?: { label: string; to: string }) {
      this.message = message
      this.actionLabel = action?.label ?? null
      this.actionTo = action?.to ?? null
      this.visible = true
      if (this.timer) clearTimeout(this.timer)
      this.timer = setTimeout(() => {
        this.visible = false
      }, 3000)
    },
    hide() {
      this.visible = false
      if (this.timer) clearTimeout(this.timer)
    },
  },
})
