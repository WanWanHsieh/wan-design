<script setup lang="ts">
defineProps<{
  basePrice: number
  effectivePrice: number
  isOnSale: boolean
  size?: 'sm' | 'lg'
}>()
</script>

<template>
  <span class="inline-flex flex-wrap items-baseline gap-1.5">
    <span v-if="isOnSale" class="text-taupe/60 line-through" :class="size === 'lg' ? 'text-sm' : 'text-xs'">
      NT$ {{ basePrice }}
    </span>
    <span
      class="font-semibold"
      :class="[isOnSale ? 'text-red-600' : 'text-terracotta-dark', size === 'lg' ? 'text-xl' : '']"
    >
      NT$ {{ effectivePrice }}
    </span>
    <span
      v-if="isOnSale"
      class="rounded-full bg-red-500 px-1.5 py-0.5 text-[10px] font-medium text-white"
    >
      特價
    </span>
  </span>
</template>
