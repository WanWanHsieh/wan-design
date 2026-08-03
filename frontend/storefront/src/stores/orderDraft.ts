import { defineStore } from 'pinia'

interface OrderDraftItem {
  productId: number
  quantity: number
}

function loadDraft(): OrderDraftItem[] {
  try {
    const raw = localStorage.getItem('storefront_order_draft')
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export const useOrderDraftStore = defineStore('orderDraft', {
  state: () => ({
    items: loadDraft() as OrderDraftItem[],
  }),
  getters: {
    totalQuantity: (state) => state.items.reduce((sum, item) => sum + item.quantity, 0),
    quantityOf: (state) => (productId: number) =>
      state.items.find((item) => item.productId === productId)?.quantity ?? 0,
  },
  actions: {
    persist() {
      localStorage.setItem('storefront_order_draft', JSON.stringify(this.items))
    },
    addItem(productId: number, quantity: number = 1) {
      const existing = this.items.find((item) => item.productId === productId)
      if (existing) {
        existing.quantity += quantity
      } else {
        this.items.push({ productId, quantity })
      }
      this.persist()
    },
    removeItem(productId: number) {
      this.items = this.items.filter((item) => item.productId !== productId)
      this.persist()
    },
    clear() {
      this.items = []
      this.persist()
    },
  },
})
