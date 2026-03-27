import { onBeforeUnmount } from 'vue'

export function useAnimationLoop(callback: (timestamp: number) => void) {
  let frameId = 0
  let active = true

  const loop = (timestamp: number) => {
    if (!active) {
      return
    }
    callback(timestamp)
    frameId = window.requestAnimationFrame(loop)
  }

  frameId = window.requestAnimationFrame(loop)

  onBeforeUnmount(() => {
    active = false
    window.cancelAnimationFrame(frameId)
  })
}
