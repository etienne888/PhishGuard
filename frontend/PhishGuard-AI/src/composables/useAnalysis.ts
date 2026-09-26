import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { translate as t } from '@/i18n'
import { useAnalysisStore } from '@/stores/analysis'

export function useAnalysis() {
    const analysisStore = useAnalysisStore()
    const { currentText, result, gate, queued, isAnalyzing, isClaiming, error } = storeToRefs(analysisStore)

    return {
        currentText,
        result,
        gate,
        queued,
        isAnalyzing,
        isClaiming,
        error,
        // Sample messages shown in the visitor's language (one scam, one fake bank email, one genuine)
        examples: computed(() => [
            { id: 1, icon: 'smartphone' as const, label: t('analysis.example1.label'), text: t('analysis.example1.text') },
            { id: 2, icon: 'mail' as const, label: t('analysis.example2.label'), text: t('analysis.example2.text') },
            { id: 3, icon: 'shieldCheck' as const, label: t('ux.example3.label'), text: t('ux.example3.text') },
        ]),
        analyze: analysisStore.analyze,
        analyzeFile: analysisStore.analyzeFile,
        flushQueue: analysisStore.flushQueue,
        cancelQueue: analysisStore.cancelQueue,
        claim: analysisStore.claim,
        pendingClaim: analysisStore.pendingClaim,
        open: analysisStore.open,
        sendFeedback: analysisStore.sendFeedback,
        reset: analysisStore.reset,
        report: analysisStore.report,
    }
}
