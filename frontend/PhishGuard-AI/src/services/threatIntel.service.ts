    // J:\PhishGuard\frontend\PhishGuard-AI\src\services\threatIntel.service.ts

    /**
     * Threat Intelligence service.
     *
     * In production, replace `USE_MOCK = true` with `false` and point
     * `API_BASE` to your Flask endpoint (e.g. /api/admin/threat-intel).
     *
     * The component NEVER calls fetch() directly — it only calls this service.
     */

    export type IOCType = 'domain' | 'url' | 'ip' | 'hash' | 'email' | 'unknown'
    export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info'
    export type FeedSource =
    | 'URLhaus'
    | 'PhishDestroy'
    | 'ThreatFox'
    | 'CIRT-CM'
    | 'Interne'
    | 'Signalement'

    export interface IOC {
    id: string
    type: IOCType
    value: string
    confidence: number
    severity: Severity
    source: FeedSource
    firstSeen: string
    lastSeen: string
    country?: string
    tags: string[]
    references: string[]
    description?: string
    }

    export interface Campaign {
    id: string
    name: string
    category: string
    severity: Severity
    iocCount: number
    targetedBrands: string[]
    firstSeen: string
    lastSeen: string
    description: string
    status: 'active' | 'mitigated' | 'monitoring'
    }

    export interface FeedStatus {
    source: FeedSource
    status: 'online' | 'degraded' | 'offline'
    lastSync: string
    iocCount: number
    latencyMs: number
    }

    export interface GeographyRow {
    country: string
    code: string
    pct: number
    iocCount: number
    }

    export interface ThreatIntelSnapshot {
    iocs: IOC[]
    campaigns: Campaign[]
    feeds: FeedStatus[]
    geography: GeographyRow[]
    fetchedAt: string
    }

    // ---------------------------------------------------------------------------
    // Configuration
    // ---------------------------------------------------------------------------

    const USE_MOCK = true // ← flip to false when backend is wired
    const API_BASE = '/api/admin/threat-intel'

    // ---------------------------------------------------------------------------
    // Public API
    // ---------------------------------------------------------------------------

    export const threatIntelService = {
    async fetchSnapshot(): Promise<ThreatIntelSnapshot> {
        if (USE_MOCK) return mockSnapshot()
        const r = await fetch(`${API_BASE}/snapshot`, { credentials: 'include' })
        if (!r.ok) throw new Error(`threat-intel fetch failed: ${r.status}`)
        return r.json()
    },

    async exportIOCs(iocs: IOC[], format: 'json' | 'csv' | 'stix'): Promise<Blob> {
        if (USE_MOCK) return localExport(iocs, format)
        const r = await fetch(`${API_BASE}/export?format=${format}`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids: iocs.map((i) => i.id) }),
        })
        if (!r.ok) throw new Error(`export failed: ${r.status}`)
        return r.blob()
    },
    }

    // ---------------------------------------------------------------------------
    // Local export (works offline)
    // ---------------------------------------------------------------------------

    function localExport(iocs: IOC[], format: 'json' | 'csv' | 'stix'): Blob {
    if (format === 'json') {
        return new Blob([JSON.stringify(iocs, null, 2)], { type: 'application/json' })
    }
    if (format === 'csv') {
        const header =
        'id,type,value,confidence,severity,source,firstSeen,lastSeen,country,tags\n'
        const rows = iocs
        .map((i) =>
            [
            i.id,
            i.type,
            i.value,
            i.confidence,
            i.severity,
            i.source,
            i.firstSeen,
            i.lastSeen,
            i.country ?? '',
            i.tags.join('|'),
            ]
            .map((v) => `"${String(v).replace(/"/g, '""')}"`)
            .join(','),
        )
        .join('\n')
        return new Blob([header + rows], { type: 'text/csv' })
    }
    // STIX-lite
    const stix = {
        type: 'bundle',
        id: `bundle--${crypto.randomUUID()}`,
        objects: iocs.map((i) => ({
        type: 'indicator',
        spec_version: '2.1',
        id: `indicator--${crypto.randomUUID()}`,
        created: i.firstSeen,
        modified: i.lastSeen,
        name: i.value,
        pattern_type: 'stix',
        pattern: `[${i.type}:value = '${i.value}']`,
        confidence: i.confidence,
        labels: i.tags,
        })),
    }
    return new Blob([JSON.stringify(stix, null, 2)], { type: 'application/json' })
    }

    // ---------------------------------------------------------------------------
    // Mock data — realistic snapshot for demo
    // ---------------------------------------------------------------------------

    function mockSnapshot(): Promise<ThreatIntelSnapshot> {
    const now = new Date()
    const minutesAgo = (m: number) =>
        new Date(now.getTime() - m * 60_000).toISOString()

    const iocs: IOC[] = [
        { id: 'ioc-001', type: 'domain', value: 'mtn-secure-cm.tk', confidence: 98, severity: 'critical', source: 'URLhaus', firstSeen: minutesAgo(180), lastSeen: minutesAgo(2), country: 'CM', tags: ['mobile-money', 'impersonation'], references: ['https://urlhaus.abuse.ch/'] },
        { id: 'ioc-002', type: 'url', value: 'http://orange-verif-cm.tk/verify', confidence: 94, severity: 'high', source: 'PhishDestroy', firstSeen: minutesAgo(360), lastSeen: minutesAgo(60), country: 'CM', tags: ['phishing', 'orange'], references: [] },
        { id: 'ioc-003', type: 'ip', value: '185.234.14.22', confidence: 88, severity: 'high', source: 'ThreatFox', firstSeen: minutesAgo(720), lastSeen: minutesAgo(240), country: 'RU', tags: ['c2', 'botnet'], references: [] },
        { id: 'ioc-004', type: 'hash', value: 'a3f5c8e21b6d4f91', confidence: 91, severity: 'critical', source: 'Interne', firstSeen: minutesAgo(900), lastSeen: minutesAgo(1440), tags: ['malware', 'docm'], references: [] },
        { id: 'ioc-005', type: 'domain', value: 'afriland-secure.ga', confidence: 96, severity: 'critical', source: 'Signalement', firstSeen: minutesAgo(1440), lastSeen: minutesAgo(1440), country: 'GA', tags: ['banking', 'impersonation'], references: [] },
        { id: 'ioc-006', type: 'url', value: 'https://camtel-promo.cm/free', confidence: 72, severity: 'medium', source: 'URLhaus', firstSeen: minutesAgo(2880), lastSeen: minutesAgo(2880), country: 'CM', tags: ['promo', 'scam'], references: [] },
        { id: 'ioc-007', type: 'domain', value: 'whatsapp-verify.xyz', confidence: 89, severity: 'high', source: 'PhishDestroy', firstSeen: minutesAgo(60), lastSeen: minutesAgo(15), country: 'US', tags: ['whatsapp', 'impersonation'], references: [] },
        { id: 'ioc-008', type: 'email', value: 'support@mtn-secure.tk', confidence: 97, severity: 'critical', source: 'CIRT-CM', firstSeen: minutesAgo(30), lastSeen: minutesAgo(5), country: 'CM', tags: ['sender', 'mtn'], references: [] },
    ]

    const campaigns: Campaign[] = [
        {
        id: 'camp-001',
        name: 'Operation Mobile Money Rewrite',
        category: 'Mobile Money',
        severity: 'critical',
        iocCount: 47,
        targetedBrands: ['MTN', 'Orange Money'],
        firstSeen: minutesAgo(2880),
        lastSeen: minutesAgo(2),
        description:
            "Campagne de phishing ciblant les utilisateurs de Mobile Money au Cameroun. Faux domaines MTN/Orange, faux messages d'alerte de blocage de compte.",
        status: 'active',
        },
        {
        id: 'camp-002',
        name: 'Fake Camtel Promo Wave',
        category: 'Promotional Scam',
        severity: 'medium',
        iocCount: 12,
        targetedBrands: ['Camtel'],
        firstSeen: minutesAgo(14400),
        lastSeen: minutesAgo(1440),
        description:
            'Offres promotionnelles fictives Camtel diffusées par WhatsApp et SMS.',
        status: 'monitoring',
        },
        {
        id: 'camp-003',
        name: 'Afriland Bank Impersonation',
        category: 'Credential Phishing',
        severity: 'critical',
        iocCount: 23,
        targetedBrands: ['Afriland First Bank'],
        firstSeen: minutesAgo(4320),
        lastSeen: minutesAgo(360),
        description:
            "Faux portails Afriland First Bank. Vol d'identifiants bancaires.",
        status: 'active',
        },
    ]

    const feeds: FeedStatus[] = [
        { source: 'URLhaus', status: 'online', lastSync: minutesAgo(2), iocCount: 8421, latencyMs: 120 },
        { source: 'PhishDestroy', status: 'online', lastSync: minutesAgo(5), iocCount: 3120, latencyMs: 210 },
        { source: 'ThreatFox', status: 'degraded', lastSync: minutesAgo(45), iocCount: 1802, latencyMs: 640 },
        { source: 'CIRT-CM', status: 'online', lastSync: minutesAgo(12), iocCount: 42, latencyMs: 320 },
        { source: 'Interne', status: 'online', lastSync: minutesAgo(1), iocCount: 341, latencyMs: 8 },
        { source: 'Signalement', status: 'online', lastSync: minutesAgo(3), iocCount: 58, latencyMs: 15 },
    ]

    // Aggregate geography from IOCs
    const countryMap: Record<string, number> = {}
    iocs.forEach((i) => {
        if (i.country) countryMap[i.country] = (countryMap[i.country] || 0) + 1
    })
    const totalGeo = Object.values(countryMap).reduce((a, b) => a + b, 0) || 1
    const geography: GeographyRow[] = Object.entries(countryMap)
        .map(([code, count]) => ({
        country: code,
        code,
        pct: Math.round((count / totalGeo) * 100),
        iocCount: count,
        }))
        .sort((a, b) => b.iocCount - a.iocCount)

    return Promise.resolve({
        iocs,
        campaigns,
        feeds,
        geography,
        fetchedAt: new Date().toISOString(),
    })
    }