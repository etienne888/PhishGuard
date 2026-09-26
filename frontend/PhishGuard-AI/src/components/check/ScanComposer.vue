<script setup lang="ts">
/** Where the user gives us the message: type/paste, a screenshot (read on the device) or an .eml file. */
import { computed, ref } from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import type { IconName } from '@/components/ui/icons'
import { useOcr } from '@/composables/useOcr'
import { useI18n } from '@/i18n'

const draft = defineModel<string>({ default: '' })
const props = defineProps<{ busy: boolean; examples?: Array<{ id: number; icon: IconName; label: string; text: string }> }>()
const emit = defineEmits<{ submit: []; file: [file: File]; example: [text: string] }>()

const { t } = useI18n()
const ocr = useOcr()
const emlInput = ref<HTMLInputElement | null>(null)
const imageInput = ref<HTMLInputElement | null>(null)
const ocrError = ref<string | null>(null)
const canPaste = typeof navigator !== 'undefined' && !!navigator.clipboard?.readText
const MAX = 20000

const count = computed(() => draft.value.length)
const disabled = computed(() => props.busy || ocr.busy.value)

async function pasteFromClipboard() {
  try {
    const text = await navigator.clipboard.readText()
    if (text) draft.value = text.slice(0, MAX)
  } catch { /* permission refused: the user can still paste with the keyboard */ }
}

async function onImage(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  ocrError.value = null
  try {
    const text = await ocr.readImage(file)
    if (text.length < 10) ocrError.value = t('ux.composer.ocrEmpty')
    else draft.value = text.slice(0, MAX)
  } catch {
    ocrError.value = t('ux.composer.ocrFailed')
  }
}

function onEml(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (file) emit('file', file)
}

function onKey(event: KeyboardEvent) {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') emit('submit')
}
</script>

<template>
  <div class="composer">
    <label for="scan-input" class="sr-only">{{ t('landing.analyzer.label') }}</label>
    <div class="field">
      <textarea id="scan-input" v-model="draft" :maxlength="MAX" rows="6" :disabled="ocr.busy.value"
                :placeholder="t('ux.composer.placeholder')" @keydown="onKey"></textarea>

      <div v-if="ocr.busy.value" class="ocr-overlay" role="status">
        <AppIcon name="scan" :size="22" class="text-blue-600" />
        <span class="text-sm font-medium text-slate-700 dark:text-slate-200">{{ t('ux.composer.reading', { p: ocr.progress.value }) }}</span>
        <div class="h-1.5 w-40 overflow-hidden rounded-full bg-slate-200"><div class="h-full bg-blue-500 transition-all" :style="{ width: ocr.progress.value + '%' }"></div></div>
      </div>

      <div class="field-bar">
        <div class="flex flex-wrap gap-1.5">
          <button v-if="canPaste" type="button" class="mini" :disabled="disabled" @click="pasteFromClipboard">
            <AppIcon name="clipboard" :size="15" /> <span>{{ t('ux.composer.paste') }}</span>
          </button>
          <button type="button" class="mini" :disabled="disabled" :title="t('ux.composer.screenshotHint')" @click="imageInput?.click()">
            <AppIcon name="camera" :size="15" /> <span>{{ t('ux.composer.screenshot') }}</span>
          </button>
          <button type="button" class="mini" :disabled="disabled" :title="t('analysis.emlTitle')" @click="emlInput?.click()">
            <AppIcon name="paperclip" :size="15" /> <span>{{ t('ux.composer.eml') }}</span>
          </button>
          <button v-if="draft" type="button" class="mini" :disabled="disabled" @click="draft = ''">
            <AppIcon name="x" :size="15" /> <span>{{ t('landing.analyzer.clear') }}</span>
          </button>
        </div>
        <span class="text-[11px] tabular-nums text-slate-400">{{ count.toLocaleString() }} / {{ MAX.toLocaleString() }}</span>
      </div>
      <input ref="imageInput" type="file" accept="image/*" class="hidden" @change="onImage" />
      <input ref="emlInput" type="file" accept=".eml,message/rfc822" class="hidden" @change="onEml" />
    </div>
    <p v-if="ocrError" class="mt-2 flex items-center gap-1.5 text-sm text-amber-600"><AppIcon name="info" :size="15" /> {{ ocrError }}</p>

    <div class="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <button type="button" class="go" :disabled="disabled || !draft.trim()" @click="emit('submit')">
        <span v-if="busy" class="h-4 w-4 animate-spin rounded-full border-2 border-white/50 border-t-white"></span>
        <AppIcon v-else name="shieldCheck" :size="19" />
        {{ busy ? t('landing.analyzer.analyzing') : t('ux.composer.check') }}
      </button>
      <ul class="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
        <li class="flex items-center gap-1.5"><AppIcon name="cpu" :size="14" class="text-blue-500" /> {{ t('ux.composer.engines') }}</li>
        <li class="flex items-center gap-1.5"><AppIcon name="lock" :size="14" class="text-emerald-500" /> {{ t('ux.composer.private') }}</li>
        <li class="hidden items-center gap-1.5 sm:flex"><AppIcon name="zap" :size="14" class="text-amber-500" /> Ctrl + Enter</li>
      </ul>
    </div>

    <div v-if="examples?.length" class="mt-5">
      <p class="mb-2 text-xs font-medium text-slate-500">{{ t('landing.analyzer.tryWith') }}</p>
      <div class="grid gap-2 sm:grid-cols-3">
        <button v-for="ex in examples" :key="ex.id" type="button" class="example" :disabled="disabled" @click="emit('example', ex.text)">
          <span class="example-icon"><AppIcon :name="ex.icon" :size="16" /></span>
          <span class="text-left text-xs font-medium text-slate-700 dark:text-slate-200">{{ ex.label }}</span>
          <AppIcon name="arrowRight" :size="14" class="ml-auto text-slate-400" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.field {
  position: relative;
  border-radius: 1.25rem;
  background: white;
  border: 1px solid rgba(148, 163, 184, 0.35);
  box-shadow: 0 1px 0 rgba(15, 23, 42, 0.02), 0 12px 30px -18px rgba(37, 99, 235, 0.25);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.field:focus-within { border-color: #3b82f6; box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.12), 0 12px 30px -18px rgba(37, 99, 235, 0.35); }
:global(.dark) .field { background: #0b1224; border-color: #1e293b; }
textarea {
  display: block;
  width: 100%;
  resize: vertical;
  min-height: 9rem;
  padding: 1rem 1.1rem 0.5rem;
  border: 0;
  outline: none;
  background: transparent;
  font-size: 0.95rem;
  line-height: 1.6;
  color: #1e293b;
}
textarea::placeholder { color: #94a3b8; }
.field-bar { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; padding: 0.5rem 0.6rem 0.6rem; border-top: 1px dashed rgba(148, 163, 184, 0.3); }
.mini {
  display: inline-flex; align-items: center; gap: 0.35rem;
  padding: 0.4rem 0.65rem; border-radius: 0.7rem;
  font-size: 0.76rem; font-weight: 600; color: #475569;
  background: rgba(148, 163, 184, 0.1);
  transition: all 0.15s ease;
}
.mini:hover:not(:disabled) { color: #2563eb; background: rgba(37, 99, 235, 0.1); }
.mini:disabled { opacity: 0.5; }
:global(.dark) .mini { color: #cbd5e1; }
@media (max-width: 420px) { .mini span { display: none; } }
.ocr-overlay {
  position: absolute; inset: 0; z-index: 2;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.5rem;
  border-radius: 1.25rem; background: rgba(255, 255, 255, 0.88); backdrop-filter: blur(3px);
}
:global(.dark) .ocr-overlay { background: rgba(2, 6, 23, 0.85); }
.go {
  display: inline-flex; align-items: center; justify-content: center; gap: 0.55rem;
  padding: 0.85rem 1.6rem; border-radius: 1rem;
  font-weight: 700; font-size: 0.95rem; color: white;
  background: linear-gradient(135deg, #2563eb, #06b6d4);
  box-shadow: 0 14px 28px -14px rgba(37, 99, 235, 0.8);
  transition: transform 0.15s ease, box-shadow 0.2s ease, opacity 0.2s ease;
}
.go:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 18px 32px -14px rgba(37, 99, 235, 0.9); }
.go:disabled { opacity: 0.55; cursor: not-allowed; }
.example {
  display: flex; align-items: center; gap: 0.6rem;
  padding: 0.6rem 0.75rem; border-radius: 0.95rem;
  background: rgba(148, 163, 184, 0.08); border: 1px solid rgba(148, 163, 184, 0.2);
  transition: all 0.15s ease;
}
.example:hover:not(:disabled) { border-color: rgba(37, 99, 235, 0.4); background: rgba(37, 99, 235, 0.05); }
.example-icon { display: grid; place-items: center; width: 1.9rem; height: 1.9rem; border-radius: 0.65rem; color: #2563eb; background: rgba(37, 99, 235, 0.1); flex-shrink: 0; }
</style>
