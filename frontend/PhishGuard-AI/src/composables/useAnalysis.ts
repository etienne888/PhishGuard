import { storeToRefs } from 'pinia'
import { useAnalysisStore } from '@/stores/analysis'

export function useAnalysis() {
    const analysisStore = useAnalysisStore()
    const { currentText, result, isAnalyzing, error } = storeToRefs(analysisStore)

    return {
        currentText,
        result,
        isAnalyzing,
        error,
        examples: [
            {
                id: 1,
                label: 'SMS bancaire',
                text: 'Votre compte bancaire a été suspendu. Cliquez ici pour vérifier votre identité et éviter la fermeture.'
            },
            {
                id: 2,
                label: 'Mail urgent',
                text: 'Votre compte Microsoft expirera dans 24 heures. Connectez-vous immédiatement pour sécuriser votre accès.'
            }
        ],
        analyze: analysisStore.analyze,
        reset: analysisStore.reset,
        report: analysisStore.report,
    }
}
