import { defineStore } from 'pinia'

interface CartItem {
  productId: number
  quantity: number
}

function loadCart(): CartItem[] {
  try {
    const raw = localStorage.getItem('storefront_cart')
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export const useCartStore = defineStore('cart', {
  state: () => ({
    items: loadCart() as CartItem[],
  }),
  getters: {
    totalQuantity: (state) => state.items.reduce((sum, item) => sum + item.quantity, 0),
    quantityOf: (state) => (productId: number) =>
      state.items.find((item) => item.productId === productId)?.quantity ?? 0,
  },
  actions: {
    persist() {
      localStorage.setItem('storefront_cart', JSON.stringify(this.items))
    },
    addItem(productId: number, quantity: number) {
      const existing = this.items.find((item) => item.productId === productId)
      if (existing) {
        existing.quantity += quantity
      } else {
        this.items.push({ productId, quantity })
      }
      this.persist()
    },
    setQuantity(productId: number, quantity: number) {
      const existing = this.items.find((item) => item.productId === productId)
      if (!existing) return
      if (quantity <= 0) {
        this.removeItem(productId)
        return
      }
      existing.quantity = quantity
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
