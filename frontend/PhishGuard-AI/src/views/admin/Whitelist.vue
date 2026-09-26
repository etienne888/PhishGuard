<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import PageHeader from '@/components/admin/ui/PageHeader.vue'
import Pill from '@/components/admin/ui/Pill.vue'
import StatTile from '@/components/admin/ui/StatTile.vue'
import { adminOpsService, type DomainHealth, type WhitelistCategory, type WhitelistEntry } from '@/services/admin.service'
import { ApiError } from '@/services/http'
import { useNotificationsStore } from '@/stores/notifications'
import { timeAgo } from '@/utils/risk'
import { useI18n } from '@/i18n'

/**
 * Official Cameroonian institutions. The engine trusts their domains and flags look-alikes;
 * each domain's live health (DNS, HTTPS, certificate expiry, latency) is checked on demand.
 */
const { t } = useI18n()
const toast = useNotificationsStore()

const CATEGORIES: WhitelistCategory[] = ['mobile_money', 'banking', 'telecom', 'government', 'other']
const CATEGORY_ICONS: Record<WhitelistCategory, string> = { mobile_money: '📱', banking: '🏦', telecom: '📡', government: '🏛️', other: '•' }

const items = ref<WhitelistEntry[]>([])
const loading = ref(false)
const checking = ref<Set<number>>(new Set())
const checkingAll = ref(false)
const q = ref('')
const category = ref<WhitelistCategory | ''>('')
const brokenLogos = ref<Set<number>>(new Set())
let timer: number | undefined

async function load() {
  loading.value = true
  try { items.value = (await adminOpsService.listWhitelist()).items } finally { loading.value = false }
}
onMounted(() => { void load(); timer = window.setInterval(load, 60_000) })
onBeforeUnmount(() => window.clearInterval(timer))

const filtered = computed(() => {
  const needle = q.value.trim().toLowerCase()
  return items.value.filter((i) => (!category.value || i.category === category.value)
    && (!needle || `${i.domain} ${i.institution}`.toLowerCase().includes(needle)))
})
const stats = computed(() => ({
  total: items.value.length,
  active: items.value.filter((i) => i.is_active).length,
  online: items.value.filter((i) => i.health?.status === 'online').length,
  issues: items.value.filter((i) => i.health && i.health.status !== 'online').length,
  unchecked: items.value.filter((i) => !i.health).length,
}))

const HEALTH_TONE: Record<DomainHealth['status'], 'green' | 'amber' | 'red' | 'orange'> = {
  online: 'green', expiring: 'amber', invalid_certificate: 'red', no_https: 'orange', offline: 'red',
}

function replace(updated: WhitelistEntry) {
  items.value = items.value.map((i) => (i.id === updated.id ? updated : i))
}

async function check(entry: WhitelistEntry) {
  checking.value = new Set([...checking.value, entry.id])
  try { replace(await adminOpsService.checkWhitelist(entry.id)) } finally {
    checking.value = new Set([...checking.value].filter((id) => id !== entry.id))
  }
}
async function checkAll() {
  checkingAll.value = true
  try {
    items.value = (await adminOpsService.checkAllWhitelist()).items
    toast.push(t('wl.checkedAll', { n: items.value.length }), 'success')
  } finally { checkingAll.value = false }
}
async function toggle(entry: WhitelistEntry) {
  replace(await adminOpsService.updateWhitelist(entry.id, { is_active: !entry.is_active }))
}
async function remove(entry: WhitelistEntry) {
  if (!confirm(t('whitelist.confirmRemove', { domain: entry.domain, institution: entry.institution }))) return
  try {
    await adminOpsService.deleteWhitelist(entry.id)
    items.value = items.value.filter((i) => i.id !== entry.id)
    toast.push(t('whitelist.removed'), 'success')
  } catch { /* sudo prompt or toast */ }
}

// ---------- Add / edit modal ----------
const editing = ref<WhitelistEntry | null>(null)
const modalOpen = ref(false)
const form = ref({ domain: '', institution: '', category: 'banking' as WhitelistCategory, website: '', logo_url: '', support_contact: '' })
const saving = ref(false)
const previewLogo = computed(() => form.value.logo_url || (form.value.domain ? `https://www.google.com/s2/favicons?domain=${form.value.domain}&sz=128` : ''))

function openModal(entry?: WhitelistEntry) {
  editing.value = entry ?? null
  form.value = entry
    ? { domain: entry.domain, institution: entry.institution, category: entry.category,
        website: entry.website === `https://${entry.domain}` ? '' : entry.website, logo_url: entry.custom_logo ? entry.logo_url : '', support_contact: entry.support_contact ?? '' }
    : { domain: '', institution: '', category: 'banking', website: '', logo_url: '', support_contact: '' }
  modalOpen.value = true
}

async function save() {
  saving.value = true
  const payload = { ...form.value, website: form.value.website || null, logo_url: form.value.logo_url || null,
                    support_contact: form.value.support_contact || null }
  try {
    if (editing.value) {
      replace(await adminOpsService.updateWhitelist(editing.value.id, payload))
      toast.push(t('wl.updated', { domain: form.value.domain }), 'success')
    } else {
      const created = await adminOpsService.createWhitelist(payload)
      items.value = [created, ...items.value]
      toast.push(t('whitelist.added', { domain: created.domain }), 'success')
      void check(created)
    }
    modalOpen.value = false
  } catch (e) {
    if (!(e instanceof ApiError)) toast.push(t('whitelist.addFailed'), 'error')
  } finally {
    saving.value = false
  }
}

const initials = (name: string) => name.split(/\s+/).map((p) => p[0]).join('').slice(0, 2).toUpperCase()
</script>

<template>
  <div class="space-y-6">
    <PageHeader :title="t('whitelist.title')" :subtitle="t('wl.subtitle')" icon="🏛️" live>
      <button class="btn-ghost" :disabled="checkingAll" @click="checkAll">{{ checkingAll ? t('wl.checking') : `🩺 ${t('wl.checkAll')}` }}</button>
      <button class="btn-primary" @click="openModal()">+ {{ t('wl.add') }}</button>
    </PageHeader>

    <section class="grid grid-cols-2 gap-3 md:grid-cols-5">
      <StatTile :label="t('wl.kpi.total')" :value="stats.total" icon="🏛️" />
      <StatTile :label="t('wl.kpi.active')" :value="stats.active" icon="✅" tone="green" />
      <StatTile :label="t('wl.kpi.online')" :value="stats.online" icon="🟢" tone="green" />
      <StatTile :label="t('wl.kpi.issues')" :value="stats.issues" icon="⚠️" :tone="stats.issues ? 'red' : 'slate'" />
      <StatTile :label="t('wl.kpi.unchecked')" :value="stats.unchecked" icon="❔" />
    </section>

    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div class="flex flex-wrap gap-1.5">
        <button class="chip" :class="{ active: !category }" @click="category = ''">{{ t('common.all') }}</button>
        <button v-for="c in CATEGORIES" :key="c" class="chip" :class="{ active: category === c }" @click="category = c">{{ CATEGORY_ICONS[c] }} {{ t(`whitelist.cat.${c}`) }}</button>
      </div>
      <input v-model="q" type="search" :placeholder="t('whitelist.search')" class="input sm:w-72" />
    </div>

    <p v-if="!loading && !filtered.length" class="rounded-2xl border border-dashed border-slate-300 p-10 text-center text-sm text-slate-400 dark:border-slate-700">{{ t('whitelist.empty') }}</p>

    <!-- Institution cards -->
    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <article v-for="e in filtered" :key="e.id"
               class="group relative flex flex-col overflow-hidden rounded-2xl border bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg dark:bg-slate-900"
               :class="e.is_active ? 'border-slate-200 dark:border-slate-800' : 'border-dashed border-slate-300 opacity-70 dark:border-slate-700'">
        <div class="h-1" :class="e.health ? { online: 'bg-emerald-500', expiring: 'bg-amber-500', invalid_certificate: 'bg-red-500', no_https: 'bg-orange-500', offline: 'bg-red-500' }[e.health.status] : 'bg-slate-200 dark:bg-slate-700'"></div>
        <div class="flex items-start gap-4 p-5">
          <div class="grid h-14 w-14 flex-shrink-0 place-items-center overflow-hidden rounded-2xl bg-white shadow ring-1 ring-slate-200 dark:ring-slate-700">
            <img v-if="!brokenLogos.has(e.id)" :src="e.logo_url" :alt="e.institution" class="h-10 w-10 object-contain"
                 @error="brokenLogos = new Set([...brokenLogos, e.id])" />
            <span v-else class="text-sm font-bold text-slate-500">{{ initials(e.institution) }}</span>
          </div>
          <div class="min-w-0 flex-1">
            <p class="truncate font-semibold text-slate-900 dark:text-white">{{ e.institution }}</p>
            <a :href="e.website" target="_blank" rel="noopener noreferrer" class="truncate font-mono text-xs text-blue-600 hover:underline dark:text-cyan-400">{{ e.domain }} ↗</a>
            <div class="mt-2 flex flex-wrap gap-1">
              <Pill>{{ CATEGORY_ICONS[e.category] }} {{ t(`whitelist.cat.${e.category}`) }}</Pill>
              <Pill v-if="e.health" :tone="HEALTH_TONE[e.health.status]" dot :pulse="e.health.status === 'online'">{{ t(`wl.health.${e.health.status}`) }}</Pill>
              <Pill v-else>{{ t('wl.health.unknown') }}</Pill>
            </div>
          </div>
        </div>

        <dl class="grid grid-cols-3 gap-px border-y border-slate-100 bg-slate-100 text-center text-xs dark:border-slate-800 dark:bg-slate-800">
          <div class="bg-white p-2 dark:bg-slate-900"><dt class="text-slate-400">HTTPS</dt><dd class="font-semibold">{{ e.health ? (e.health.https ? '✓' : '✕') : '—' }}</dd></div>
          <div class="bg-white p-2 dark:bg-slate-900"><dt class="text-slate-400">{{ t('wl.cert') }}</dt>
            <dd class="font-semibold" :class="(e.health?.ssl_days_left ?? 99) < 21 ? 'text-amber-600' : ''">{{ e.health?.ssl_days_left != null && e.health.ssl_days_left >= 0 ? t('wl.days', { n: e.health.ssl_days_left }) : '—' }}</dd></div>
          <div class="bg-white p-2 dark:bg-slate-900"><dt class="text-slate-400">{{ t('intelx.latency') }}</dt><dd class="font-semibold">{{ e.health?.latency_ms != null ? `${e.health.latency_ms} ms` : '—' }}</dd></div>
        </dl>

        <div class="flex items-center justify-between gap-2 px-5 py-3">
          <span class="text-[11px] text-slate-400">{{ e.last_checked_at ? t('wl.checked', { when: timeAgo(e.last_checked_at) }) : t('wl.neverChecked') }}</span>
          <div class="flex gap-1">
            <button class="icon-btn" :title="t('wl.check')" :disabled="checking.has(e.id)" @click="check(e)"><span :class="{ 'animate-spin': checking.has(e.id) }">↻</span></button>
            <button class="icon-btn" :title="t('common.edit')" @click="openModal(e)">✎</button>
            <button class="icon-btn" :title="e.is_active ? t('whitelist.clickDisable') : t('whitelist.clickEnable')" @click="toggle(e)">{{ e.is_active ? '⏸' : '▶' }}</button>
            <button class="icon-btn text-red-500" :title="t('common.delete')" @click="remove(e)">🗑</button>
          </div>
        </div>
      </article>
    </div>

    <!-- Add / edit modal -->
    <Teleport to="body">
      <div v-if="modalOpen" class="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4 backdrop-blur-sm" @click.self="modalOpen = false">
        <form class="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900" @submit.prevent="save">
          <div class="flex items-center gap-4">
            <div class="grid h-16 w-16 place-items-center overflow-hidden rounded-2xl bg-slate-50 ring-1 ring-slate-200 dark:bg-slate-800 dark:ring-slate-700">
              <img v-if="previewLogo" :src="previewLogo" alt="" class="h-11 w-11 object-contain" />
              <span v-else class="text-2xl">🏛️</span>
            </div>
            <div>
              <h2 class="text-lg font-bold text-slate-900 dark:text-white">{{ editing ? t('wl.editTitle') : t('wl.addTitle') }}</h2>
              <p class="text-xs text-slate-500">{{ t('wl.modalHint') }}</p>
            </div>
          </div>
          <div class="mt-5 grid gap-3 sm:grid-cols-2">
            <label class="field sm:col-span-2"><span>{{ t('wl.form.institution') }}</span><input v-model="form.institution" required placeholder="Afriland First Bank" /></label>
            <label class="field"><span>{{ t('map.col.domain') }}</span><input v-model="form.domain" required placeholder="afrilandfirstbank.com" /></label>
            <label class="field"><span>{{ t('wl.form.category') }}</span>
              <select v-model="form.category"><option v-for="c in CATEGORIES" :key="c" :value="c">{{ CATEGORY_ICONS[c] }} {{ t(`whitelist.cat.${c}`) }}</option></select></label>
            <label class="field sm:col-span-2"><span>{{ t('wl.form.website') }} <em>({{ t('common.optional') }})</em></span><input v-model="form.website" placeholder="https://www.afrilandfirstbank.com" /></label>
            <label class="field sm:col-span-2"><span>{{ t('wl.support') }} <em>({{ t('common.optional') }})</em></span><input v-model="form.support_contact" maxlength="160" :placeholder="t('wl.supportHint')" /></label>
            <label class="field sm:col-span-2"><span>{{ t('wl.form.logo') }} <em>({{ t('wl.form.logoHint') }})</em></span><input v-model="form.logo_url" placeholder="https://…/logo.png" /></label>
          </div>
          <div class="mt-6 flex justify-end gap-2">
            <button type="button" class="btn-ghost" @click="modalOpen = false">{{ t('common.cancel') }}</button>
            <button class="btn-primary" :disabled="saving">{{ saving ? t('settings.saving') : editing ? t('common.save') : t('common.add') }}</button>
          </div>
        </form>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.input { border-radius: 0.75rem; border: 1px solid #e2e8f0; background: white; padding: 0.55rem 0.85rem; font-size: 0.875rem; outline: none; }
:global(.dark) .input { background: #0f172a; border-color: #334155; color: #f1f5f9; }
.btn-primary { border-radius: 0.75rem; background: #0f172a; padding: 0.55rem 1.1rem; font-size: 0.875rem; font-weight: 600; color: white; }
.btn-primary:disabled { opacity: 0.5; }
:global(.dark) .btn-primary { background: #22d3ee; color: #0f172a; }
.btn-ghost { border-radius: 0.75rem; border: 1px solid #e2e8f0; padding: 0.55rem 1rem; font-size: 0.875rem; font-weight: 500; }
:global(.dark) .btn-ghost { border-color: #334155; color: #e2e8f0; }
.chip { border-radius: 9999px; border: 1px solid #e2e8f0; padding: 0.35rem 0.8rem; font-size: 0.78rem; font-weight: 600; color: #475569; }
.chip.active { background: #0f172a; border-color: #0f172a; color: white; }
:global(.dark) .chip { border-color: #334155; color: #cbd5e1; }
:global(.dark) .chip.active { background: #22d3ee; border-color: #22d3ee; color: #0f172a; }
.icon-btn { display: inline-grid; place-items: center; width: 2rem; height: 2rem; border-radius: 0.6rem; color: #64748b; transition: background 0.15s; }
.icon-btn:hover { background: #f1f5f9; }
:global(.dark) .icon-btn:hover { background: #1e293b; }
.field { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.8rem; font-weight: 500; color: #475569; }
.field em { font-style: normal; font-weight: 400; color: #94a3b8; }
.field input, .field select { border-radius: 0.75rem; border: 1px solid #e2e8f0; background: #f8fafc; padding: 0.6rem 0.85rem; font-size: 0.875rem; color: #0f172a; outline: none; }
.field input:focus { border-color: #60a5fa; background: white; }
:global(.dark) .field { color: #cbd5e1; }
:global(.dark) .field input, :global(.dark) .field select { background: #0f172a; border-color: #334155; color: #f1f5f9; }
</style>
