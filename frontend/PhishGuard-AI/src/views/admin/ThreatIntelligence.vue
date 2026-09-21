    <template>
    <div class="space-y-6">

        <!-- ==================== HEADER ==================== -->
        <div class="flex items-start justify-between gap-4 flex-wrap">
        <div>
            <h1 class="text-2xl font-bold text-slate-800 dark:text-slate-100">
            🧠 {{ t('admin.threats.title') }}
            </h1>
            <p class="text-sm text-slate-500">
            Renseignement sur les menaces en direct · Mise à jour automatique
            </p>
        </div>

        <div class="flex items-center gap-2 flex-wrap">
            <!-- Live status pill -->
            <span
            class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-semibold"
            :class="isAutoRefresh
                ? 'bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-500/10 dark:border-emerald-500/30 dark:text-emerald-300'
                : 'bg-slate-100 border-slate-200 text-slate-500 dark:bg-slate-800 dark:border-slate-700'"
            >
            <span class="relative flex h-2 w-2">
                <span v-if="isAutoRefresh" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75" />
                <span class="relative inline-flex h-2 w-2 rounded-full" :class="isAutoRefresh ? 'bg-emerald-500' : 'bg-slate-400'" />
            </span>
            {{ isAutoRefresh ? 'LIVE' : 'En pause' }}
            </span>

            <button
            @click="refresh"
            :disabled="isLoading"
            class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs font-medium hover:border-slate-300 transition disabled:opacity-50"
            >
            <svg :class="['w-3.5 h-3.5', isLoading ? 'animate-spin' : '']" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Actualiser
            </button>

            <button
            @click="isAutoRefresh = !isAutoRefresh"
            class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs font-medium hover:border-slate-300 transition"
            >
            {{ isAutoRefresh ? '⏸ Pause auto' : '▶ Reprendre auto' }}
            </button>

            <button
            @click="showForm = true"
            class="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-500 text-white text-sm font-medium rounded-lg shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition"
            >
            <i class="fas fa-plus mr-1.5"></i> {{ t('landing.categories.title') }}
            </button>
        </div>
        </div>

        <!-- ==================== STATUS BAR ==================== -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 p-4">
            <div class="flex items-center justify-between">
            <span class="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">IOCs suivis</span>
            <span class="text-xs text-slate-400">{{ feedStatuses.length }} sources</span>
            </div>
            <div class="mt-1 text-2xl font-bold tabular-nums text-slate-800 dark:text-slate-100">{{ iocs.length }}</div>
        </div>
        <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 p-4">
            <div class="flex items-center justify-between">
            <span class="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">Campagnes actives</span>
            <span class="text-xs text-red-600 font-semibold">{{ activeCampaigns }}</span>
            </div>
            <div class="mt-1 text-2xl font-bold tabular-nums text-slate-800 dark:text-slate-100">{{ campaigns.length }}</div>
        </div>
        <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 p-4">
            <div class="flex items-center justify-between">
            <span class="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">Critiques</span>
            <span class="text-xs text-red-500">⚠</span>
            </div>
            <div class="mt-1 text-2xl font-bold tabular-nums text-red-600">{{ criticalCount }}</div>
        </div>
        <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 p-4">
            <div class="flex items-center justify-between">
            <span class="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">Dernière sync.</span>
            <span class="text-xs text-slate-400">auto</span>
            </div>
            <div class="mt-1 text-sm font-mono tabular-nums text-slate-700 dark:text-slate-200">{{ lastSyncedLabel }}</div>
        </div>
        </div>

        <!-- ==================== TABS ==================== -->
        <div class="border-b border-slate-200 dark:border-slate-800">
        <div class="flex gap-6 overflow-x-auto">
            <button
            v-for="tabDef in tabDefs"
            :key="tabDef.id"
            @click="tab = tabDef.id"
            class="pb-3 text-sm font-medium border-b-2 transition whitespace-nowrap"
            :class="tab === tabDef.id
                ? 'border-blue-500 text-slate-900 dark:text-slate-100'
                : 'border-transparent text-slate-500 hover:text-slate-700'"
            >
            {{ tabDef.label }}
            <span v-if="tabDef.count !== undefined" class="ml-1.5 text-[11px] tabular-nums text-slate-400">
                {{ tabDef.count }}
            </span>
            </button>
        </div>
        </div>

        <!-- ==================== CATEGORIES TAB (unchanged CRUD) ==================== -->
        <div v-if="tab === 'categories'" class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm overflow-hidden">
        <div class="overflow-x-auto">
            <table class="w-full text-sm">
            <thead class="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800">
                <tr>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Nom</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Description</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Sévérité</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Région</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Actif</th>
                <th class="text-center px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Actions</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                <tr v-for="category in categories" :key="category.id" class="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition">
                <td class="px-4 py-3 text-sm font-medium text-slate-800 dark:text-slate-200">{{ category.name }}</td>
                <td class="px-4 py-3 text-xs text-slate-500 max-w-xs truncate">{{ category.description }}</td>
                <td class="px-4 py-3">
                    <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="severityBadge(category.severity)">{{ category.severity }}</span>
                </td>
                <td class="px-4 py-3 text-xs text-slate-500">{{ category.region }}</td>
                <td class="px-4 py-3">
                    <span class="text-xs" :class="category.active ? 'text-emerald-600' : 'text-slate-400'">{{ category.active ? '● Actif' : '○ Inactif' }}</span>
                </td>
                <td class="px-4 py-3">
                    <div class="flex items-center justify-center gap-1">
                    <button @click="editCategory(category)" class="p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-500/10 text-blue-600 transition" title="Modifier">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 5H6a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-5m-1.414-9.414a2 2 0 1 1 2.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                    </button>
                    <button class="p-1.5 rounded hover:bg-red-50 text-red-600 transition" title="Supprimer">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 7l-.867 12.142A2 2 0 0 1 16.138 21H7.862a2 2 0 0 1-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v3M4 7h16" /></svg>
                    </button>
                    </div>
                </td>
                </tr>
            </tbody>
            </table>
        </div>
        </div>

        <!-- ==================== IOCs TAB ==================== -->
        <div v-else-if="tab === 'iocs'" class="space-y-4">

        <!-- Filters -->
        <div class="flex flex-wrap gap-2 items-center">
            <input
            v-model="iocSearch"
            type="text"
            placeholder="Rechercher IOC (domaine, URL, IP, hash…)"
            class="flex-1 min-w-[200px] px-3 py-2 text-sm border border-slate-200 dark:border-slate-800 dark:bg-slate-900 rounded-lg outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500"
            />
            <select v-model="iocTypeFilter" class="px-3 py-2 text-sm border border-slate-200 dark:border-slate-800 dark:bg-slate-900 rounded-lg outline-none">
            <option value="">Tous les types</option>
            <option value="domain">Domain</option>
            <option value="url">URL</option>
            <option value="ip">IP</option>
            <option value="hash">Hash</option>
            <option value="email">Email</option>
            </select>
            <select v-model="iocSeverityFilter" class="px-3 py-2 text-sm border border-slate-200 dark:border-slate-800 dark:bg-slate-900 rounded-lg outline-none">
            <option value="">Toutes sévérités</option>
            <option value="critical">Critique</option>
            <option value="high">Élevée</option>
            <option value="medium">Moyenne</option>
            <option value="low">Faible</option>
            </select>
            <select v-model="iocSourceFilter" class="px-3 py-2 text-sm border border-slate-200 dark:border-slate-800 dark:bg-slate-900 rounded-lg outline-none">
            <option value="">Toutes sources</option>
            <option v-for="f in feedStatuses" :key="f.source" :value="f.source">{{ f.source }}</option>
            </select>
            <button
            @click="openExportMenu = !openExportMenu"
            class="px-3 py-2 text-sm font-medium rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300 transition"
            >
            ⬇ Exporter
            </button>
            <div v-if="openExportMenu" class="relative">
            <div class="absolute right-0 top-0 z-20 mt-10 w-40 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg shadow-xl overflow-hidden">
                <button @click="doExport('json')" class="w-full text-left px-3 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-800">JSON</button>
                <button @click="doExport('csv')"  class="w-full text-left px-3 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-800">CSV</button>
                <button @click="doExport('stix')" class="w-full text-left px-3 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-800">STIX 2.1</button>
            </div>
            </div>
        </div>

        <!-- Grid -->
        <div v-if="filteredIOCs.length > 0" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            <button
            v-for="ioc in filteredIOCs"
            :key="ioc.id"
            @click="selectedIOC = selectedIOC?.id === ioc.id ? null : ioc"
            class="text-left bg-white dark:bg-slate-900 rounded-xl border p-4 transition"
            :class="selectedIOC?.id === ioc.id
                ? 'border-blue-400 dark:border-blue-500 ring-2 ring-blue-500/20'
                : 'border-slate-100 dark:border-slate-800 hover:border-slate-300'"
            >
            <div class="flex items-start justify-between gap-2">
                <span class="text-[10px] uppercase font-semibold tracking-wider px-2 py-0.5 rounded-full" :class="iocTypeClass(ioc.type)">
                {{ ioc.type }}
                </span>
                <div class="flex items-center gap-1">
                <span
                    class="text-[10px] font-semibold px-1.5 py-0.5 rounded"
                    :class="severityPill(ioc.severity)"
                >{{ ioc.severity.toUpperCase() }}</span>
                <span
                    class="text-[10px] font-semibold px-1.5 py-0.5 rounded"
                    :class="ioc.confidence >= 90 ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'"
                >{{ ioc.confidence }}%</span>
                </div>
            </div>

            <p class="mt-2 text-xs font-mono text-slate-700 dark:text-slate-300 break-all">{{ ioc.value }}</p>

            <div class="mt-2 flex flex-wrap gap-1">
                <span v-for="tag in ioc.tags.slice(0, 3)" :key="tag" class="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                {{ tag }}
                </span>
            </div>

            <div class="mt-2 flex items-center justify-between text-[11px] text-slate-500">
                <span>{{ ioc.source }}</span>
                <span>{{ timeAgo(ioc.lastSeen) }}</span>
            </div>
            </button>
        </div>

        <div v-else class="text-center py-12 text-slate-400 text-sm">
            Aucun IOC ne correspond aux filtres.
        </div>

        <!-- ==================== IOC DETAIL PANEL (CAT) ==================== -->
        <Transition name="fade">
            <div v-if="selectedIOC" class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 space-y-4">
            <div class="flex items-start justify-between gap-4">
                <div>
                <div class="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">CAT · Category Analysis Tool</div>
                <h3 class="mt-1 text-lg font-bold text-slate-800 dark:text-slate-100 break-all">{{ selectedIOC.value }}</h3>
                <div class="flex items-center gap-2 mt-1">
                    <span class="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full" :class="iocTypeClass(selectedIOC.type)">{{ selectedIOC.type }}</span>
                    <span class="text-[10px] font-semibold px-2 py-0.5 rounded" :class="severityPill(selectedIOC.severity)">{{ selectedIOC.severity }}</span>
                    <span class="text-[11px] text-slate-500">confiance {{ selectedIOC.confidence }}%</span>
                </div>
                </div>
                <button @click="selectedIOC = null" class="text-slate-400 hover:text-slate-600">✕</button>
            </div>

            <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div class="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40">
                <div class="text-[11px] text-slate-500">Source</div>
                <div class="text-sm font-semibold text-slate-700 dark:text-slate-200">{{ selectedIOC.source }}</div>
                </div>
                <div class="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40">
                <div class="text-[11px] text-slate-500">Pays</div>
                <div class="text-sm font-semibold text-slate-700 dark:text-slate-200">{{ selectedIOC.country || '—' }}</div>
                </div>
                <div class="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40">
                <div class="text-[11px] text-slate-500">Première vue</div>
                <div class="text-sm font-semibold text-slate-700 dark:text-slate-200">{{ formatDate(selectedIOC.firstSeen) }}</div>
                </div>
                <div class="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40">
                <div class="text-[11px] text-slate-500">Dernière vue</div>
                <div class="text-sm font-semibold text-slate-700 dark:text-slate-200">{{ formatDate(selectedIOC.lastSeen) }}</div>
                </div>
            </div>

            <div>
                <p class="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Classification CAT</p>
                <div class="flex flex-wrap gap-2">
                <span v-for="c in classifyIOC(selectedIOC)" :key="c.label" class="text-xs px-2.5 py-1 rounded-full border" :class="c.tone">
                    {{ c.label }}
                </span>
                </div>
            </div>

            <div v-if="selectedIOC.tags.length" class="pt-3 border-t border-slate-100 dark:border-slate-800">
                <p class="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Tags</p>
                <div class="flex flex-wrap gap-1.5">
                <span v-for="tag in selectedIOC.tags" :key="tag" class="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">{{ tag }}</span>
                </div>
            </div>

            <div v-if="selectedIOC.references.length" class="pt-3 border-t border-slate-100 dark:border-slate-800">
                <p class="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Références externes</p>
                <ul class="space-y-1">
                <li v-for="ref in selectedIOC.references" :key="ref">
                    <a :href="ref" target="_blank" rel="noopener" class="text-xs text-blue-600 hover:underline break-all">{{ ref }}</a>
                </li>
                </ul>
            </div>

            <div class="flex flex-wrap gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
                <button class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-gradient-to-r from-blue-600 to-cyan-500 text-white">🚫 Bloquer ce domaine</button>
                <button class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200">🔔 Créer une alerte</button>
                <button class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200">📋 Copier</button>
                <button class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200">📤 Signaler au CIRT-CM</button>
            </div>
            </div>
        </Transition>
        </div>

        <!-- ==================== CAMPAIGNS TAB ==================== -->
        <div v-else-if="tab === 'campaigns'" class="space-y-3">
        <div v-for="c in campaigns" :key="c.id" class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 p-5">
            <div class="flex items-start justify-between gap-4">
            <div class="min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                <h3 class="text-base font-bold text-slate-800 dark:text-slate-100">{{ c.name }}</h3>
                <span class="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full" :class="severityPill(c.severity)">{{ c.severity }}</span>
                <span class="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full"
                    :class="c.status === 'active'
                    ? 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-300'
                    : c.status === 'monitoring'
                    ? 'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300'
                    : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300'"
                >{{ c.status }}</span>
                </div>
                <p class="text-xs text-slate-500 mt-1">{{ c.category }}</p>
                <p class="text-sm text-slate-600 dark:text-slate-300 mt-3">{{ c.description }}</p>
            </div>
            <div class="text-right flex-shrink-0">
                <div class="text-2xl font-bold text-red-600 tabular-nums">{{ c.iocCount }}</div>
                <div class="text-[11px] text-slate-500 uppercase tracking-wider">IOCs liés</div>
            </div>
            </div>

            <div class="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div><div class="text-slate-500">Marques ciblées</div><div class="font-semibold text-slate-700 dark:text-slate-200">{{ c.targetedBrands.join(', ') }}</div></div>
            <div><div class="text-slate-500">Première vue</div><div class="font-semibold text-slate-700 dark:text-slate-200">{{ formatDate(c.firstSeen) }}</div></div>
            <div><div class="text-slate-500">Dernière vue</div><div class="font-semibold text-slate-700 dark:text-slate-200">{{ formatDate(c.lastSeen) }}</div></div>
            <div><div class="text-slate-500">Statut</div><div class="font-semibold text-slate-700 dark:text-slate-200">{{ c.status }}</div></div>
            </div>
        </div>
        <div v-if="campaigns.length === 0" class="text-center py-12 text-slate-400 text-sm">
            Aucune campagne détectée.
        </div>
        </div>

        <!-- ==================== LIVE FEEDS TAB ==================== -->
        <div v-else-if="tab === 'feeds'" class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 overflow-hidden">
        <table class="w-full text-sm">
            <thead class="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800">
            <tr>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Source</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Statut</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Dernière sync.</th>
                <th class="text-right px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">IOCs</th>
                <th class="text-right px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Latence</th>
            </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            <tr v-for="f in feedStatuses" :key="f.source" class="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                <td class="px-4 py-3 text-sm font-semibold text-slate-800 dark:text-slate-200">{{ f.source }}</td>
                <td class="px-4 py-3">
                <span class="inline-flex items-center gap-1.5 text-xs">
                    <span class="relative flex h-2 w-2">
                    <span v-if="f.status === 'online'" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75" />
                    <span class="relative inline-flex h-2 w-2 rounded-full"
                        :class="f.status === 'online' ? 'bg-emerald-500' : f.status === 'degraded' ? 'bg-amber-500' : 'bg-red-500'" />
                    </span>
                    <span :class="f.status === 'online' ? 'text-emerald-600' : f.status === 'degraded' ? 'text-amber-600' : 'text-red-600'">
                    {{ f.status }}
                    </span>
                </span>
                </td>
                <td class="px-4 py-3 text-xs text-slate-500">{{ timeAgo(f.lastSync) }}</td>
                <td class="px-4 py-3 text-right text-xs font-semibold tabular-nums">{{ f.iocCount.toLocaleString('fr-FR') }}</td>
                <td class="px-4 py-3 text-right text-xs tabular-nums text-slate-500">{{ f.latencyMs }} ms</td>
            </tr>
            </tbody>
        </table>
        </div>

        <!-- ==================== GEOGRAPHY TAB ==================== -->
        <div v-else-if="tab === 'geography'" class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 p-6">
        <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-4">🌍 Origine des menaces</h3>
        <div class="space-y-3">
            <div v-for="g in geography" :key="g.code" class="flex items-center gap-3">
            <span class="w-32 text-xs text-slate-600 dark:text-slate-300 truncate">{{ g.country }}</span>
            <div class="flex-1 h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                <div class="h-full rounded-full bg-gradient-to-r from-blue-600 to-cyan-500 transition-all duration-700" :style="{ width: g.pct + '%' }" />
            </div>
            <span class="w-16 text-right text-xs font-semibold text-slate-700 dark:text-slate-200 tabular-nums">{{ g.pct }}%</span>
            <span class="w-12 text-right text-[11px] text-slate-400 tabular-nums">({{ g.iocCount }})</span>
            </div>
        </div>
        <p class="mt-4 text-[11px] text-slate-500">ⓘ Attribution géographique basée sur les IP sources observées. Ne représente pas nécessairement la localisation des attaquants.</p>
        </div>

        <!-- ==================== CREATE/EDIT MODAL (unchanged) ==================== -->
        <div v-if="showForm" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
        <div class="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full p-6 shadow-2xl">
            <div class="flex items-center justify-between mb-4">
            <h3 class="text-xl font-bold text-slate-800 dark:text-slate-100">{{ editingId ? 'Modifier' : 'Nouvelle' }} catégorie</h3>
            <button @click="showForm = false" class="text-slate-400 hover:text-slate-600 transition">✕</button>
            </div>
            <form class="space-y-4" @submit.prevent="saveCategory">
            <div>
                <label class="text-xs font-medium text-slate-600 block mb-1">Nom *</label>
                <input v-model="formData.name" type="text" required class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500" />
            </div>
            <div>
                <label class="text-xs font-medium text-slate-600 block mb-1">Description</label>
                <textarea v-model="formData.description" rows="2" class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800 rounded-lg text-sm outline-none resize-none"></textarea>
            </div>
            <div class="grid grid-cols-2 gap-3">
                <div>
                <label class="text-xs font-medium text-slate-600 block mb-1">Sévérité *</label>
                <select v-model="formData.severity" class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800 rounded-lg text-sm outline-none">
                    <option>Critique</option><option>Élevée</option><option>Moyenne</option><option>Faible</option>
                </select>
                </div>
                <div>
                <label class="text-xs font-medium text-slate-600 block mb-1">Région</label>
                <select v-model="formData.region" class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800 rounded-lg text-sm outline-none">
                    <option>Cameroun</option><option>Afrique de l'Ouest</option><option>Afrique Centrale</option><option>International</option>
                </select>
                </div>
            </div>
            <div class="flex items-center gap-2">
                <input type="checkbox" v-model="formData.active" class="rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
                <label class="text-sm text-slate-600">Actif</label>
            </div>
            <div class="flex gap-2 pt-2">
                <button type="submit" class="flex-1 py-2 bg-gradient-to-r from-blue-600 to-cyan-500 text-white text-sm font-medium rounded-lg shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition">{{ editingId ? 'Mettre à jour' : 'Créer' }}</button>
                <button type="button" @click="showForm = false" class="flex-1 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-sm font-medium rounded-lg transition">Annuler</button>
            </div>
            </form>
        </div>
        </div>
    </div>
    </template>

    <script setup lang="ts">
    import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
    import { useI18n } from '@/i18n'
    import {
    threatIntelService,
    type IOC,
    type Campaign,
    type FeedStatus,
    type GeographyRow,
    type Severity,
    } from '@/services/threatIntel.service'

    const { t } = useI18n()

    // ---------------------------------------------------------------------------
    // Existing state (unchanged)
    // ---------------------------------------------------------------------------
    interface ThreatCategory {
    id: number
    name: string
    description: string
    severity: string
    region: string
    active: boolean
    }

    const categories = ref<ThreatCategory[]>([
    { id: 1, name: 'Phishing Mobile Money', description: 'Tentatives de phishing ciblant MTN/Orange Money', severity: 'Critique', region: 'Cameroun', active: true },
    { id: 2, name: 'Ingénierie sociale', description: 'Manipulation psychologique', severity: 'Élevée', region: 'Cameroun', active: true },
    { id: 3, name: 'SIM swapping', description: 'Transfert frauduleux de numéro', severity: 'Élevée', region: 'Afrique de l\'Ouest', active: true },
    { id: 4, name: 'Deepfake / IA', description: 'Contenus générés par IA', severity: 'Moyenne', region: 'International', active: false },
    ])

    const showForm = ref(false)
    const editingId = ref<number | null>(null)
    const formData = ref({ name: '', description: '', severity: 'Moyenne', region: 'Cameroun', active: true })

    const editCategory = (category: ThreatCategory) => {
    editingId.value = category.id
    formData.value = { ...category }
    showForm.value = true
    }

    const saveCategory = () => {
    if (editingId.value) {
        const index = categories.value.findIndex(c => c.id === editingId.value)
        if (index !== -1) categories.value[index] = { ...formData.value, id: editingId.value }
    } else {
        categories.value.push({ ...formData.value, id: Math.max(...categories.value.map(c => c.id)) + 1 })
    }
    showForm.value = false
    editingId.value = null
    formData.value = { name: '', description: '', severity: 'Moyenne', region: 'Cameroun', active: true }
    }

    const severityBadge = (s: string) =>
    s === 'Critique' ? 'bg-red-100 text-red-700' :
    s === 'Élevée' ? 'bg-orange-100 text-orange-700' :
    s === 'Moyenne' ? 'bg-yellow-100 text-yellow-700' : 'bg-blue-100 text-blue-700'

    const iocTypeClass = (t: string) =>
    t === 'domain' ? 'bg-blue-100 text-blue-700' :
    t === 'url' ? 'bg-purple-100 text-purple-700' :
    t === 'ip' ? 'bg-cyan-100 text-cyan-700' : 'bg-slate-100 text-slate-600'

    // ---------------------------------------------------------------------------
    // New state: live feeds, IOCs, campaigns
    // ---------------------------------------------------------------------------

    const tab = ref<'categories' | 'iocs' | 'campaigns' | 'feeds' | 'geography'>('iocs')

    const iocs = ref<IOC[]>([])
    const campaigns = ref<Campaign[]>([])
    const feedStatuses = ref<FeedStatus[]>([])
    const geography = ref<GeographyRow[]>([])

    const isLoading = ref(false)
    const lastFetched = ref<string | null>(null)

    const isAutoRefresh = ref(true)
    const REFRESH_MS = 30_000
    let timer: number | null = null

    // Filters
    const iocSearch = ref('')
    const iocTypeFilter = ref('')
    const iocSeverityFilter = ref('')
    const iocSourceFilter = ref('')
    const selectedIOC = ref<IOC | null>(null)
    const openExportMenu = ref(false)

    // Derived
    const filteredIOCs = computed(() => {
    const q = iocSearch.value.trim().toLowerCase()
    return iocs.value
        .filter(i => !q || i.value.toLowerCase().includes(q) || i.tags.some(t => t.includes(q)))
        .filter(i => !iocTypeFilter.value || i.type === iocTypeFilter.value)
        .filter(i => !iocSeverityFilter.value || i.severity === iocSeverityFilter.value)
        .filter(i => !iocSourceFilter.value || i.source === iocSourceFilter.value)
    })

    const criticalCount = computed(() => iocs.value.filter(i => i.severity === 'critical').length)
    const activeCampaigns = computed(() => campaigns.value.filter(c => c.status === 'active').length)
    const lastSyncedLabel = computed(() =>
    lastFetched.value ? timeAgo(lastFetched.value) : 'jamais',
    )

    const tabDefs = computed(() => [
    { id: 'categories' as const, label: 'Catégories', count: categories.value.length },
    { id: 'iocs' as const,       label: 'IOCs',       count: iocs.value.length },
    { id: 'campaigns' as const,  label: 'Campagnes',  count: campaigns.value.length },
    { id: 'feeds' as const,      label: 'Flux live',  count: feedStatuses.value.length },
    { id: 'geography' as const,  label: 'Géographie', count: geography.value.length },
    ])

    // ---------------------------------------------------------------------------
    // Fetch loop
    // ---------------------------------------------------------------------------

    async function refresh() {
    if (isLoading.value) return
    isLoading.value = true
    try {
        const snapshot = await threatIntelService.fetchSnapshot()
        iocs.value = snapshot.iocs
        campaigns.value = snapshot.campaigns
        feedStatuses.value = snapshot.feeds
        geography.value = snapshot.geography
        lastFetched.value = snapshot.fetchedAt
    } catch (err) {
        console.error('threat-intel refresh failed', err)
    } finally {
        isLoading.value = false
    }
    }

    function startAutoRefresh() {
    stopAutoRefresh()
    if (!isAutoRefresh.value) return
    timer = window.setInterval(refresh, REFRESH_MS)
    }

    function stopAutoRefresh() {
    if (timer !== null) {
        window.clearInterval(timer)
        timer = null
    }
    }

    onMounted(async () => {
    await refresh()
    startAutoRefresh()
    })

    onBeforeUnmount(stopAutoRefresh)

    // Restart timer when the toggle flips
    import { watch } from 'vue'
    watch(isAutoRefresh, (on) => { on ? startAutoRefresh() : stopAutoRefresh() })

    // ---------------------------------------------------------------------------
    // Helpers
    // ---------------------------------------------------------------------------

    function timeAgo(iso: string): string {
    const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
    if (diff < 60) return 'à l\'instant'
    if (diff < 3600) return `il y a ${Math.floor(diff / 60)} min`
    if (diff < 86400) return `il y a ${Math.floor(diff / 3600)} h`
    return `il y a ${Math.floor(diff / 86400)} j`
    }

    function formatDate(iso: string): string {
    return new Date(iso).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' })
    }

    function severityPill(s: Severity): string {
    return s === 'critical' ? 'bg-red-100 text-red-700'
        : s === 'high' ? 'bg-orange-100 text-orange-700'
        : s === 'medium' ? 'bg-amber-100 text-amber-700'
        : s === 'low' ? 'bg-emerald-100 text-emerald-700'
        : 'bg-slate-100 text-slate-600'
    }

    /**
     * CAT: local classification heuristic.
     * Produces human-readable labels describing what this IOC likely is.
     */
    function classifyIOC(ioc: IOC): Array<{ label: string; tone: string }> {
    const out: Array<{ label: string; tone: string }> = []
    const v = ioc.value.toLowerCase()

    if (ioc.tags.includes('mobile-money') || /mtn|orange|momo/.test(v))
        out.push({ label: 'Mobile Money', tone: 'bg-purple-100 text-purple-700 border-purple-200' })
    if (ioc.tags.includes('impersonation'))
        out.push({ label: 'Usurpation de marque', tone: 'bg-red-100 text-red-700 border-red-200' })
    if (ioc.tags.includes('credential') || /login|verify|account|password/.test(v))
        out.push({ label: 'Vol d\'identifiants', tone: 'bg-orange-100 text-orange-700 border-orange-200' })
    if (v.endsWith('.tk') || v.endsWith('.ga') || v.endsWith('.cf') || v.endsWith('.ml'))
        out.push({ label: 'TLD à risque', tone: 'bg-amber-100 text-amber-700 border-amber-200' })
    if (ioc.type === 'ip')
        out.push({ label: 'Infrastructure réseau', tone: 'bg-cyan-100 text-cyan-700 border-cyan-200' })
    if (ioc.type === 'hash')
        out.push({ label: 'Artefact binaire', tone: 'bg-slate-100 text-slate-700 border-slate-200' })
    if (out.length === 0)
        out.push({ label: 'Non catégorisé', tone: 'bg-slate-100 text-slate-600 border-slate-200' })

    return out
    }

    // ---------------------------------------------------------------------------
    // Export
    // ---------------------------------------------------------------------------

    async function doExport(format: 'json' | 'csv' | 'stix') {
    openExportMenu.value = false
    try {
        const blob = await threatIntelService.exportIOCs(filteredIOCs.value, format)
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `phishguard-iocs-${Date.now()}.${format === 'csv' ? 'csv' : 'json'}`
        a.click()
        URL.revokeObjectURL(url)
    } catch (err) {
        console.error('export failed', err)
    }
    }
    </script>

    <style scoped>
    .fade-enter-active, .fade-leave-active { transition: opacity .25s ease; }
    .fade-enter-from, .fade-leave-to { opacity: 0; }
    </style>