<script setup lang="ts">
import { useToastStore } from '../stores/toast'

const toast = useToastStore()
</script>

<template>
  <Teleport to="body">
    <transition name="toast-fade">
      <div
        v-if="toast.visible"
        class="fixed bottom-6 left-1/2 z-50 flex -translate-x-1/2 items-center gap-3 whitespace-nowrap rounded-full bg-brown px-5 py-3 text-sm text-white shadow-lg"
      >
        <span>{{ toast.message }}</span>
        <RouterLink
          v-if="toast.actionLabel && toast.actionTo"
          :to="toast.actionTo"
          class="font-medium text-terracotta-light hover:underline"
          @click="toast.hide()"
        >
          {{ toast.actionLabel }} →
        </RouterLink>
      </div>
    </transition>
  </Teleport>
</template>

<style scoped>
.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: opacity 0.2s ease;
}
.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
}
</style>
