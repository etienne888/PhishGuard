<script setup lang="ts">
/** The analysed message with its risky parts marked, plus a legend explaining each colour. */
import { computed } from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import type { IconName } from '@/components/ui/icons'
import { highlight, type MarkKind } from '@/utils/highlight'
import { useI18n } from '@/i18n'
import type { AnalysisUrl } from '@/types'

const props = defineProps<{ text: string; urls?: AnalysisUrl[] }>()
const { t } = useI18n()

const segments = computed(() => highlight(props.text, props.urls ?? []))

const LEGEND: Record<MarkKind, { icon: IconName }> = {
  'danger-link': { icon: 'ban' },
  link: { icon: 'link' },
  'official-link': { icon: 'checkCircle' },
  secret: { icon: 'key' },
  urgency: { icon: 'clock' },
  money: { icon: 'sparkles' },
  phone: { icon: 'phone' },
}

const found = computed(() => {
  const kinds = new Set(segments.value.map((s) => s.kind).filter(Boolean) as MarkKind[])
  return (Object.keys(LEGEND) as MarkKind[]).filter((k) => kinds.has(k))
})
</script>

<template>
  <div>
    <div v-if="found.length" class="mb-3 flex flex-wrap gap-1.5">
      <span v-for="kind in found" :key="kind" class="legend" :class="`m-${kind}`">
        <AppIcon :name="LEGEND[kind].icon" :size="13" /> {{ t(`ux.mark.${kind}`) }}
      </span>
    </div>
    <p class="message"><template v-for="(seg, i) in segments" :key="i"><mark v-if="seg.kind" :class="`m-${seg.kind}`" :title="t(`ux.markHint.${seg.kind}`)">{{ seg.text }}</mark><template v-else>{{ seg.text }}</template></template></p>
    <p v-if="!found.length" class="mt-2 text-xs text-slate-500">{{ t('ux.mark.none') }}</p>
  </div>
</template>

<style scoped>
.message {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.9rem;
  line-height: 1.75;
  color: #334155;
  padding: 1rem 1.1rem;
  border-radius: 1rem;
  background: rgba(248, 250, 252, 0.9);
  border: 1px dashed rgba(148, 163, 184, 0.45);
  max-height: 18rem;
  overflow-y: auto;
}
:global(.dark) .message { background: rgba(2, 6, 23, 0.6); color: #cbd5e1; }
mark {
  border-radius: 0.35rem;
  padding: 0.05rem 0.25rem;
  cursor: help;
  color: inherit;
  box-decoration-break: clone;
  -webkit-box-decoration-break: clone;
}
.legend {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.2rem 0.55rem;
  border-radius: 9999px;
  font-size: 0.7rem;
  font-weight: 600;
}
.m-danger-link { background: rgba(239, 68, 68, 0.16); color: #b91c1c; text-decoration: line-through wavy rgba(239, 68, 68, 0.6); }
.legend.m-danger-link { text-decoration: none; }
.m-link { background: rgba(245, 158, 11, 0.16); color: #b45309; }
.m-official-link { background: rgba(16, 185, 129, 0.15); color: #047857; }
.m-secret { background: rgba(168, 85, 247, 0.15); color: #7e22ce; }
.m-urgency { background: rgba(249, 115, 22, 0.16); color: #c2410c; }
.m-money { background: rgba(236, 72, 153, 0.13); color: #be185d; }
.m-phone { background: rgba(59, 130, 246, 0.14); color: #1d4ed8; }
:global(.dark) mark, :global(.dark) .legend { filter: brightness(1.5); }
</style>
