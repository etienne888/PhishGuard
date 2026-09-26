<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import PageHeader from '@/components/admin/ui/PageHeader.vue'
import Panel from '@/components/admin/ui/Panel.vue'
import Pill from '@/components/admin/ui/Pill.vue'
import Sparkline from '@/components/admin/ui/Sparkline.vue'
import StatTile from '@/components/admin/ui/StatTile.vue'
import { socService, type BlockedDomain, type FeedStatus, type IntelSummary, type Ioc } from '@/services/soc.service'
import { useNotificationsStore } from '@/stores/notifications'
import { formatDate, timeAgo } from '@/utils/risk'
import { useI18n } from '@/i18n'

/**
 * Threat intelligence from real data: indicators (domains, URLs, sender domains, impersonated
 * brands) extracted from every dangerous message, cross-checked against the OpenPhish community
 * feed and the PhishGuard blocklist, plus the targeted brands and threat categories.
 */
const { t } = useI18n()
const toast = useNotificationsStore()

type Tab = 'iocs' | 'brands' | 'blocklist' | 'feed'
const TABS: Array<{ id: Tab; icon: string }> = [{ id: 'iocs', icon: '🧬' }, { id: 'brands', icon: '🎯' }, { id: 'blocklist', icon: '🚫' }, { id: 'feed', icon: '🌐' }]
const tab = ref<Tab>('iocs')
const days = ref(30)
const iocs = ref<Ioc[]>([])
const feed = ref<FeedStatus | null>(null)
const summary = ref<IntelSummary | null>(null)
const blocklist = ref<BlockedDomain[]>([])
const scanned = ref(0)
const loading = ref(false)
const typeFilter = ref<Ioc['type'] | ''>('')
const q = ref('')
const onlyActive = ref(false)
const selected = ref<Ioc | null>(null)
const newBlock = ref({ domain: '', reason: '' })

async function load() {
  loading.value = true
  try {
    const [ioc, sum, bl] = await Promise.all([socService.listIocs(days.value), socService.getIntelSummary(days.value), socService.listBlocklist()])
    iocs.value = ioc.items
    feed.value = ioc.feed
    scanned.value = ioc.analyses_scanned
    summary.value = sum
    blocklist.value = bl.items
  } finally { loading.value = false }
}
watch(days, load)
onMounted(load)

const filtered = computed(() => {
  const needle = q.value.trim().toLowerCase()
  return iocs.value.filter((i) => (!typeFilter.value || i.type === typeFilter.value) && (!onlyActive.value || i.active)
    && (!needle || i.value.toLowerCase().includes(needle)))
})
const stats = computed(() => ({
  total: iocs.value.length,
  domains: iocs.value.filter((i) => i.type === 'domain').length,
  active: iocs.value.filter((i) => i.active).length,
  confirmed: iocs.value.filter((i) => i.openphish).length,
  blocked: blocklist.value.filter((b) => b.is_active).length,
}))

const SEV_TONE = { critical: 'red', high: 'orange', medium: 'amber' } as const
const TYPE_ICON: Record<Ioc['type'], string> = { domain: '🌐', url: '🔗', sender: '✉️', brand: '🏷️' }

async function blockIoc(ioc: Ioc) {
  const domain = ioc.type === 'url' ? new URL(ioc.value.includes('://') ? ioc.value : `http://${ioc.value}`).hostname : ioc.value
  try {
    await socService.block(domain, t('intel2.blockReason', { hits: ioc.hits }))
    toast.push(t('inc.toast.blocked', { domain }), 'success')
    await load()
  } catch { /* shown */ }
}
async function addBlock() {
  try {
    await socService.block(newBlock.value.domain, newBlock.value.reason)
    newBlock.value = { domain: '', reason: '' }
    toast.push(t('intel2.blockAdded'), 'success')
    blocklist.value = (await socService.listBlocklist()).items
  } catch { /* shown */ }
}
async function unblock(row: BlockedDomain) {
  if (!confirm(t('intel2.confirmUnblock', { domain: row.domain }))) return
  try {
    await socService.unblock(row.id)
    blocklist.value = blocklist.value.filter((b) => b.id !== row.id)
  } catch { /* sudo prompt */ }
}
async function refreshFeed() {
  const r = await socService.refreshFeed()
  toast.push(r.ok ? t('intel2.feedRefreshed', { n: r.size }) : t('intel2.feedDown'), r.ok ? 'success' : 'error')
  await load()
}
function exportIocs() {
  const header = 'type,value,hits,max_score,confidence,users,openphish,blocked,first_seen,last_seen\n'
  const rows = filtered.value.map((i) => [i.type, `"${i.value.replace(/"/g, '""')}"`, i.hits, i.max_score, i.confidence, i.users, i.openphish, i.blocked, i.first_seen, i.last_seen].join(','))
  const blob = new Blob([header + rows.join('\n')], { type: 'text/csv' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `phishguard-iocs-${days.value}d.csv`
  a.click()
  URL.revokeObjectURL(a.href)
}
const maxBrand = computed(() => Math.max(1, ...(summary.value?.brands.map((b) => b.count) ?? [1])))
const maxCategory = computed(() => Math.max(1, ...(summary.value?.categories.map((b) => b.count) ?? [1])))
</script>

<template>
  <div class="space-y-6">
    <PageHeader :title="t('admin.page.threatIntel')" :subtitle="t('intel2.subtitle')" icon="🧠" live>
      <select v-model.number="days" class="input w-auto">
        <option :value="7">{{ t('map.days', { n: 7 }) }}</option><option :value="30">{{ t('map.days', { n: 30 }) }}</option>
        <option :value="90">{{ t('map.days', { n: 90 }) }}</option><option :value="365">{{ t('map.days', { n: 365 }) }}</option>
      </select>
      <button class="btn-ghost" :disabled="loading" @click="load">↻ {{ t('common.refresh') }}</button>
      <button class="btn-primary" @click="exportIocs">⬇ {{ t('intel2.export') }}</button>
    </PageHeader>

    <section class="grid grid-cols-2 gap-3 md:grid-cols-5">
      <StatTile :label="t('intel2.kpi.iocs')" :value="stats.total" icon="🧬" :hint="t('intel2.kpi.scanned', { n: scanned })" />
      <StatTile :label="t('intel2.kpi.domains')" :value="stats.domains" icon="🌐" tone="blue" />
      <StatTile :label="t('intel2.kpi.active')" :value="stats.active" icon="🔴" tone="red" :hint="t('intel2.kpi.activeHint')" />
      <StatTile :label="t('intel2.kpi.confirmed')" :value="stats.confirmed" icon="🌍" tone="violet" hint="OpenPhish" />
      <StatTile :label="t('intel2.kpi.blocked')" :value="stats.blocked" icon="🚫" tone="green" clickable @click="tab = 'blocklist'" />
    </section>

    <Panel v-if="summary" :title="t('intel2.trend', { n: summary.dangerous_messages })" :hint="t('intel2.trendHint')">
      <Sparkline :values="summary.daily.map((d) => d.count)" color="#ef4444" :height="56" :label="t('intel2.trend', { n: summary.dangerous_messages })" />
      <div class="mt-1 flex justify-between text-[10px] text-slate-400"><span>{{ summary.daily[0]?.date }}</span><span>{{ summary.daily.at(-1)?.date }}</span></div>
    </Panel>

    <div class="inline-flex rounded-2xl bg-slate-100 p-1 dark:bg-slate-800/80">
      <button v-for="item in TABS" :key="item.id" class="rounded-xl px-4 py-2 text-sm font-semibold transition"
              :class="tab === item.id ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-900 dark:text-white' : 'text-slate-500 dark:text-slate-400'" @click="tab = item.id">
        {{ item.icon }} {{ t(`intel2.tab.${item.id}`) }}
      </button>
    </div>

    <!-- IOCs -->
    <template v-if="tab === 'iocs'">
      <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
        <input v-model="q" type="search" class="input sm:w-72" :placeholder="t('intelx.searchIoc')" />
        <div class="flex flex-wrap gap-1.5">
          <button class="chip" :class="{ active: !typeFilter }" @click="typeFilter = ''">{{ t('common.all') }}</button>
          <button v-for="ty in (['domain', 'url', 'sender', 'brand'] as const)" :key="ty" class="chip" :class="{ active: typeFilter === ty }" @click="typeFilter = ty">{{ TYPE_ICON[ty] }} {{ t(`intel2.type.${ty}`) }}</button>
        </div>
        <label class="flex items-center gap-2 text-xs text-slate-500 sm:ml-auto"><input v-model="onlyActive" type="checkbox" /> {{ t('intel2.onlyActive') }}</label>
      </div>

      <Panel flush>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-slate-50 text-left text-[11px] uppercase tracking-wide text-slate-500 dark:bg-slate-800/50">
              <tr><th class="px-5 py-3">{{ t('intel2.col.indicator') }}</th><th class="px-3">{{ t('intelx.col.severity') }}</th><th class="px-3 text-right">{{ t('map.col.hits') }}</th>
                <th class="hidden px-3 text-right md:table-cell">{{ t('inc.users') }}</th><th class="hidden px-3 lg:table-cell">{{ t('intelx.lastSeen') }}</th><th class="px-3">{{ t('intel2.col.intel') }}</th><th class="px-5"></th></tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
              <tr v-if="!filtered.length"><td colspan="7" class="px-5 py-10 text-center text-slate-400">{{ loading ? t('common.loading') : t('intelx.noIoc') }}</td></tr>
              <tr v-for="i in filtered" :key="i.id" class="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/40" @click="selected = i">
                <td class="max-w-sm px-5 py-2.5">
                  <p class="truncate font-mono text-xs text-slate-800 dark:text-slate-100"><span class="mr-1">{{ TYPE_ICON[i.type] }}</span>{{ i.value }}</p>
                  <p class="text-[11px] text-slate-400">{{ t(`intel2.type.${i.type}`) }}<span v-if="i.country"> · {{ i.country }}</span></p>
                </td>
                <td class="px-3"><Pill :tone="SEV_TONE[i.severity]" dot :pulse="i.active">{{ t(`level.${i.severity}`) }} · {{ i.confidence }}%</Pill></td>
                <td class="px-3 text-right font-semibold tabular-nums">{{ i.hits }}</td>
                <td class="hidden px-3 text-right tabular-nums md:table-cell">{{ i.users }}</td>
                <td class="hidden px-3 text-xs text-slate-500 lg:table-cell">{{ timeAgo(i.last_seen) }}</td>
                <td class="px-3">
                  <div class="flex gap-1">
                    <Pill v-if="i.openphish" tone="violet">OpenPhish</Pill>
                    <Pill v-if="i.blocked" tone="red">🚫</Pill>
                    <Pill v-if="!i.active" tone="slate">{{ t('intel2.dormant') }}</Pill>
                  </div>
                </td>
                <td class="px-5 text-right" @click.stop>
                  <button v-if="!i.blocked && i.type !== 'brand'" class="text-xs font-semibold text-red-600 hover:underline" @click="blockIoc(i)">🚫 {{ t('intel2.block') }}</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Panel>
    </template>

    <!-- Brands & categories -->
    <div v-else-if="tab === 'brands'" class="grid gap-6 lg:grid-cols-2">
      <Panel :title="`🎯 ${t('overview.brands')}`" :hint="t('intel2.brandsHint')">
        <p v-if="!summary?.brands.length" class="text-sm text-slate-400">{{ t('overview.noBrands') }}</p>
        <ul class="space-y-3">
          <li v-for="b in summary?.brands ?? []" :key="b.name">
            <div class="flex justify-between text-sm"><span class="font-medium">{{ b.name }}</span><b class="tabular-nums">{{ b.count }}</b></div>
            <div class="mt-1 h-2 rounded-full bg-slate-100 dark:bg-slate-800"><div class="h-full rounded-full bg-gradient-to-r from-red-500 to-orange-400" :style="{ width: `${b.count / maxBrand * 100}%` }"></div></div>
          </li>
        </ul>
      </Panel>
      <Panel :title="`🧪 ${t('intel2.categories')}`" :hint="t('intel2.categoriesHint')">
        <p v-if="!summary?.categories.length" class="text-sm text-slate-400">{{ t('common.empty') }}</p>
        <ul class="space-y-3">
          <li v-for="c in summary?.categories ?? []" :key="c.name">
            <div class="flex justify-between text-sm"><span class="font-medium">{{ t(`intel2.cat.${c.name}`) }}</span><b class="tabular-nums">{{ c.count }}</b></div>
            <div class="mt-1 h-2 rounded-full bg-slate-100 dark:bg-slate-800"><div class="h-full rounded-full bg-gradient-to-r from-violet-500 to-blue-500" :style="{ width: `${c.count / maxCategory * 100}%` }"></div></div>
          </li>
        </ul>
      </Panel>
    </div>

    <!-- Blocklist -->
    <template v-else-if="tab === 'blocklist'">
      <Panel :title="t('intel2.addBlock')" :hint="t('intel2.addBlockHint')">
        <form class="flex flex-col gap-2 sm:flex-row" @submit.prevent="addBlock">
          <input v-model="newBlock.domain" class="input sm:w-64" required :placeholder="t('intel2.domainPlaceholder')" />
          <input v-model="newBlock.reason" class="input flex-1" :placeholder="t('intel2.reasonPlaceholder')" />
          <button class="btn-primary">🚫 {{ t('intel2.block') }}</button>
        </form>
      </Panel>
      <Panel flush>
        <table class="w-full text-sm">
          <thead class="bg-slate-50 text-left text-[11px] uppercase tracking-wide text-slate-500 dark:bg-slate-800/50">
            <tr><th class="px-5 py-3">{{ t('map.col.domain') }}</th><th class="px-3">{{ t('intel2.col.reason') }}</th><th class="hidden px-3 md:table-cell">{{ t('intel2.col.by') }}</th><th class="px-3">{{ t('audit.col.timestamp') }}</th><th class="px-5"></th></tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            <tr v-if="!blocklist.length"><td colspan="5" class="px-5 py-10 text-center text-slate-400">{{ t('intel2.noBlocks') }}</td></tr>
            <tr v-for="b in blocklist" :key="b.id">
              <td class="px-5 py-2.5 font-mono text-xs text-red-600">{{ b.domain }}</td>
              <td class="px-3 text-xs text-slate-600 dark:text-slate-300">{{ b.reason ?? '—' }}</td>
              <td class="hidden px-3 text-xs text-slate-500 md:table-cell">{{ b.created_by ?? t('inc.source.auto') }}</td>
              <td class="px-3 text-xs text-slate-500">{{ formatDate(b.created_at) }}</td>
              <td class="px-5 text-right"><button class="text-xs font-semibold text-slate-500 hover:text-red-600" @click="unblock(b)">{{ t('intel2.unblock') }} 🔐</button></td>
            </tr>
          </tbody>
        </table>
      </Panel>
    </template>

    <!-- External feed -->
    <Panel v-else :title="`🌐 OpenPhish`" :hint="t('intel2.feedHint')">
      <template #actions>
        <Pill :tone="summary?.feed.ok ? 'green' : 'red'" dot :pulse="summary?.feed.ok">{{ summary?.feed.ok ? t('intelx.feedStatus.online') : t('intelx.feedStatus.offline') }}</Pill>
        <button class="btn-ghost" @click="refreshFeed">↻ {{ t('intel2.refreshFeed') }}</button>
      </template>
      <dl class="grid gap-3 text-sm sm:grid-cols-3">
        <div><dt class="text-xs text-slate-400">{{ t('intel2.feedSize') }}</dt><dd class="text-2xl font-bold tabular-nums">{{ summary?.feed.size ?? 0 }}</dd></div>
        <div><dt class="text-xs text-slate-400">{{ t('intel2.feedFetched') }}</dt><dd class="font-semibold">{{ summary?.feed.fetched_at ? timeAgo(summary.feed.fetched_at) : '—' }}</dd></div>
        <div><dt class="text-xs text-slate-400">{{ t('intel2.feedMatches') }}</dt><dd class="text-2xl font-bold tabular-nums text-violet-600">{{ stats.confirmed }}</dd></div>
      </dl>
      <p class="mt-4 text-xs font-semibold uppercase tracking-wide text-slate-400">{{ t('intel2.feedSample') }}</p>
      <ul class="mt-2 space-y-1">
        <li v-for="u in summary?.feed.sample ?? []" :key="u" class="truncate rounded-lg bg-slate-50 px-3 py-1.5 font-mono text-[11px] text-slate-600 dark:bg-slate-800 dark:text-slate-300">{{ u }}</li>
      </ul>
      <p class="mt-3 text-[11px] text-slate-400">⚠️ {{ t('intel2.feedWarning') }}</p>
    </Panel>

    <!-- IOC detail -->
    <Teleport to="body">
      <div v-if="selected" class="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4 backdrop-blur-sm" @click.self="selected = null">
        <div class="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-400">{{ TYPE_ICON[selected.type] }} {{ t(`intel2.type.${selected.type}`) }}</p>
              <p class="mt-1 break-all font-mono text-sm font-semibold text-slate-900 dark:text-white">{{ selected.value }}</p>
            </div>
            <button class="text-slate-400" @click="selected = null">✕</button>
          </div>
          <dl class="mt-4 grid grid-cols-2 gap-3 text-sm">
            <div><dt class="text-xs text-slate-400">{{ t('intelx.col.severity') }}</dt><dd><Pill :tone="SEV_TONE[selected.severity]">{{ t(`level.${selected.severity}`) }}</Pill></dd></div>
            <div><dt class="text-xs text-slate-400">{{ t('intel2.confidence') }}</dt><dd class="font-bold">{{ selected.confidence }} %</dd></div>
            <div><dt class="text-xs text-slate-400">{{ t('map.col.hits') }}</dt><dd class="font-bold">{{ selected.hits }}</dd></div>
            <div><dt class="text-xs text-slate-400">{{ t('inc.maxScore') }}</dt><dd class="font-bold text-red-600">{{ selected.max_score }}</dd></div>
            <div><dt class="text-xs text-slate-400">{{ t('intelx.firstSeen') }}</dt><dd>{{ formatDate(selected.first_seen) }}</dd></div>
            <div><dt class="text-xs text-slate-400">{{ t('intelx.lastSeen') }}</dt><dd>{{ formatDate(selected.last_seen) }}</dd></div>
            <div><dt class="text-xs text-slate-400">{{ t('intelx.country') }}</dt><dd>{{ selected.country ?? '—' }}</dd></div>
            <div><dt class="text-xs text-slate-400">ISP</dt><dd class="truncate">{{ selected.isp ?? '—' }}</dd></div>
          </dl>
          <p class="mt-4 text-xs text-slate-500">{{ t('intel2.linked', { ids: selected.analysis_ids.slice(0, 10).map((id) => `#${id}`).join(', ') }) }}</p>
          <div class="mt-5 flex flex-wrap justify-end gap-2">
            <a v-if="selected.type !== 'brand'" :href="`https://www.virustotal.com/gui/search/${encodeURIComponent(selected.value)}`" target="_blank" rel="noopener noreferrer" class="btn-ghost">VirusTotal ↗</a>
            <a v-if="selected.type === 'domain'" :href="`https://urlscan.io/domain/${selected.value}`" target="_blank" rel="noopener noreferrer" class="btn-ghost">urlscan.io ↗</a>
            <button v-if="!selected.blocked && selected.type !== 'brand'" class="btn-primary" @click="blockIoc(selected); selected = null">🚫 {{ t('intel2.block') }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.input { border-radius: 0.75rem; border: 1px solid #e2e8f0; background: white; padding: 0.5rem 0.85rem; font-size: 0.85rem; outline: none; }
:global(.dark) .input { background: #0f172a; border-color: #334155; color: #f1f5f9; }
.btn-primary { border-radius: 0.75rem; background: #0f172a; padding: 0.5rem 1rem; font-size: 0.85rem; font-weight: 600; color: white; white-space: nowrap; }
:global(.dark) .btn-primary { background: #22d3ee; color: #0f172a; }
.btn-ghost { border-radius: 0.75rem; border: 1px solid #e2e8f0; padding: 0.5rem 1rem; font-size: 0.85rem; font-weight: 500; white-space: nowrap; }
:global(.dark) .btn-ghost { border-color: #334155; color: #e2e8f0; }
.chip { border-radius: 9999px; border: 1px solid #e2e8f0; padding: 0.35rem 0.8rem; font-size: 0.78rem; font-weight: 600; color: #475569; }
.chip.active { background: #0f172a; border-color: #0f172a; color: white; }
:global(.dark) .chip { border-color: #334155; color: #cbd5e1; }
:global(.dark) .chip.active { background: #22d3ee; border-color: #22d3ee; color: #0f172a; }
</style>
