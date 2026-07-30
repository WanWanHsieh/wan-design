import { computed, type Ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { Category } from '../types'

interface QueryKeys {
  cat: string
  sub: string
}

export function useCategoryNav(categories: Ref<Category[]>, queryKeys: QueryKeys = { cat: 'cat', sub: 'sub' }) {
  const route = useRoute()
  const router = useRouter()

  const topCategories = computed(() => categories.value.filter((c) => c.parent_id === null))

  const showingAll = computed(() => route.query[queryKeys.cat] === 'all')

  const selectedTop = computed(() => {
    const slug = route.query[queryKeys.cat]
    if (!slug || slug === 'all') return null
    return topCategories.value.find((c) => c.slug === slug) ?? null
  })

  const childCategories = computed(() => {
    if (!selectedTop.value) return []
    return categories.value.filter((c) => c.parent_id === selectedTop.value!.id)
  })

  const selectedSub = computed(() => {
    const slug = route.query[queryKeys.sub]
    if (!slug) return null
    return childCategories.value.find((c) => c.slug === slug) ?? null
  })

  // null = no category chosen yet (show top-level browsing), otherwise a list of category ids in scope
  const categoryIdsInScope = computed<number[] | null>(() => {
    if (showingAll.value) return null
    if (selectedSub.value) return [selectedSub.value.id]
    if (selectedTop.value) return [selectedTop.value.id, ...childCategories.value.map((c) => c.id)]
    return null
  })

  function selectTop(slug: string) {
    router.push({ query: { ...route.query, [queryKeys.cat]: slug, [queryKeys.sub]: undefined } })
  }

  function selectAll() {
    router.push({ query: { ...route.query, [queryKeys.cat]: 'all', [queryKeys.sub]: undefined } })
  }

  function selectSub(slug: string | null) {
    router.push({ query: { ...route.query, [queryKeys.sub]: slug ?? undefined } })
  }

  function reset() {
    router.push({ query: { ...route.query, [queryKeys.cat]: undefined, [queryKeys.sub]: undefined } })
  }

  return {
    topCategories,
    selectedTop,
    childCategories,
    selectedSub,
    showingAll,
    categoryIdsInScope,
    selectTop,
    selectAll,
    selectSub,
    reset,
  }
}
