<script setup lang="ts">
interface KpiCardProps {
  label: string
  value: string
}

defineProps<KpiCardProps>()
</script>

<template>
  <div class="flex min-h-[136px] min-w-0 flex-col justify-between rounded-control border border-border-subtle bg-canvas px-4 py-4">
    <p class="max-w-[11ch] text-xs uppercase tracking-normal text-subtle">{{ label }}</p>
    <div class="min-h-[52px] overflow-hidden">
      <p class="whitespace-nowrap text-[2rem] leading-none font-semibold tracking-tight tabular-nums text-strong">
        {{ value }}
      </p>
    </div>
  </div>
</template>
