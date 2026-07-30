<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  modelValue: boolean
  src: string
  alt?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const scale = ref(1)
const translateX = ref(0)
const translateY = ref(0)
const dragging = ref(false)
let lastX = 0
let lastY = 0

const MIN_SCALE = 1
const MAX_SCALE = 4

function reset() {
  scale.value = 1
  translateX.value = 0
  translateY.value = 0
}

function close() {
  emit('update:modelValue', false)
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') close()
}

watch(
  () => props.modelValue,
  (visible) => {
    if (!visible) {
      reset()
      window.removeEventListener('keydown', onKeydown)
    } else {
      window.addEventListener('keydown', onKeydown)
    }
  },
)

function clampScale(value: number) {
  return Math.min(MAX_SCALE, Math.max(MIN_SCALE, value))
}

function onWheel(event: WheelEvent) {
  const next = clampScale(scale.value + (event.deltaY < 0 ? 0.3 : -0.3))
  scale.value = next
  if (next === MIN_SCALE) {
    translateX.value = 0
    translateY.value = 0
  }
}

function onImageClick() {
  if (scale.value > 1) {
    reset()
  } else {
    scale.value = 2.5
  }
}

function onMouseDown(event: MouseEvent) {
  if (scale.value <= 1) return
  dragging.value = true
  lastX = event.clientX
  lastY = event.clientY
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
}

function onMouseMove(event: MouseEvent) {
  if (!dragging.value) return
  translateX.value += (event.clientX - lastX) / scale.value
  translateY.value += (event.clientY - lastY) / scale.value
  lastX = event.clientX
  lastY = event.clientY
}

function onMouseUp() {
  dragging.value = false
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
      tabindex="-1"
      @click.self="close"
      @wheel.prevent="onWheel"
    >
      <button
        class="absolute right-4 top-4 text-3xl leading-none text-white hover:text-gray-300"
        aria-label="關閉"
        @click="close"
      >
        ×
      </button>
      <img
        :src="src"
        :alt="alt"
        class="max-h-[90vh] max-w-[90vw] select-none rounded transition-transform duration-150"
        :style="{
          transform: `scale(${scale}) translate(${translateX}px, ${translateY}px)`,
          cursor: scale > 1 ? 'grab' : 'zoom-in',
        }"
        draggable="false"
        @click.stop="onImageClick"
        @mousedown.stop="onMouseDown"
      />
    </div>
  </Teleport>
</template>
