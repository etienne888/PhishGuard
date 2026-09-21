    import { computed, ref } from 'vue'

    export type Locale = 'fr' | 'en' | 'pcm' | 'ewo' | 'ff'

    export const localeOptions: Array<{ code: Locale; label: string; nativeLabel: string }> = [
    { code: 'fr', label: 'French', nativeLabel: 'Français' },
    { code: 'en', label: 'English', nativeLabel: 'English' },
    { code: 'pcm', label: 'Cameroonian Pidgin', nativeLabel: 'Pidgin Camerounais' },
    { code: 'ewo', label: 'Ewondo', nativeLabel: 'Ewondo' },
    { code: 'ff', label: 'Fulfulde', nativeLabel: 'Fulfulde' },
    ]

    type TranslationKey = string
    | 'nav.analyze'
    | 'nav.education'
    | 'nav.threatIntel'
    | 'nav.about'
    | 'nav.login'
    | 'nav.register'
    | 'nav.dashboard'
    | 'nav.admin'
    | 'nav.logout'
    | 'nav.openMenu'
    | 'nav.language'
    | 'nav.lightMode'
    | 'nav.darkMode'
    | 'nav.user'
    | 'footer.description'
    | 'footer.secure'
    | 'footer.poweredAi'
    | 'footer.navigation'
    | 'footer.legalSecurity'
    | 'footer.resources'
    | 'footer.reporting'
    | 'footer.followUs'
    | 'footer.activeProtection'
    | 'footer.securedBy'
    | 'footer.home'
    | 'footer.privacy'
    | 'footer.terms'
    | 'footer.legal'
    | 'footer.cookies'
    | 'footer.education'
    | 'footer.report'

    type TranslationTable = Partial<Record<TranslationKey, string>>

    const pageTranslations: TranslationTable = {
    'landing.hero.adopted': 'Adopté par des citoyens partout au Cameroun',
    'landing.hero.title': 'Détectez le phishing',
    'landing.hero.subtitle': "avant qu'il ne soit trop tard",
    'landing.hero.description': "Collez un SMS, un email ou un message suspect pour savoir instantanément s'il s'agit d'une arnaque.",
    'landing.hero.poweredBy': "Propulsé par l'IA, pensé pour le Cameroun.",
    'landing.hero.ctaAnalyze': 'Lancer une analyse',
    'landing.hero.ctaThreats': 'Voir les menaces',
    'landing.hero.statLosses': 'FCFA perdus en 2025',
    'landing.hero.statReports': 'cas de phishing signalés',
    'landing.hero.statAccuracy': 'précision de détection',
    'landing.hero.liveAnalysis': 'Analyse en direct',
    'landing.hero.riskDetected': 'de risque détecté',
    'landing.hero.suspiciousDomain': 'Domaine suspect (.tk)',
    'landing.hero.urgency': 'Urgence détectée',
    'landing.hero.mobileMoneyFraud': 'Fraude Mobile Money',
    'landing.hero.verifiedByAi': "Vérifié par l'IA",
    'landing.hero.ruleEngine': 'Moteur à règles',
    'landing.analyzer.title': 'Collez & détectez',
    'landing.analyzer.subtitle': 'Copiez un message suspect, collez-le ci-dessous, et obtenez un score de risque instantané.',
    'landing.analyzer.label': 'Collez votre message',
    'landing.analyzer.subLabel': 'SMS, email, WhatsApp, ou tout autre texte',
    'landing.analyzer.placeholder': 'Collez un message suspect ici...\nExemple : « Cher client MTN, votre compte a été bloqué... »',
    'landing.analyzer.analyzing': 'Analyse...',
    'landing.analyzer.analyze': 'Analyser',
    'landing.analyzer.clear': 'Effacer',
    'landing.analyzer.privacy': 'Vos données ne sont pas conservées',
    'landing.analyzer.report': 'Signaler',
    'landing.analyzer.learnMore': 'En savoir plus',
    'landing.analyzer.tryWith': 'Tester avec :',
    'landing.categories.title': '12 menaces à connaître',
    'landing.categories.subtitle': "Chaque catégorie détaille le mécanisme, les signaux d'alerte, et les bons réflexes.",
    'landing.categories.threat': 'Menace n°',
    'landing.categories.mechanism': 'Mécanisme',
    'landing.categories.warningSigns': "Signaux d'alerte",
    'landing.categories.action': 'Que faire',
    'landing.categories.close': 'Fermer',
    'landing.threatIntel.title': 'Veille menaces',
    'landing.about.title': 'À propos',
    'landing.about.comment': 'Laissez un commentaire',
    'verify.title': 'Vérification email',
    'verify.loading': 'Vérification de votre adresse email...',
    'verify.success': 'Votre email est vérifié. Vous pouvez maintenant vous connecter.',
    'verify.incomplete': 'Ce lien de vérification est incomplet.',
    'verify.invalid': 'Ce lien est invalide ou a expiré.',
    'verify.login': 'Se connecter',
    'auth.close': 'Fermer',
    'auth.email': 'Email',
    'auth.password': 'Mot de passe',
    'auth.phone': 'Téléphone',
    'auth.confirmPassword': 'Confirmer le mot de passe',
    'auth.emailPlaceholder': 'vous@exemple.com',
    'auth.passwordPlaceholder': '••••••••',
    'auth.login.title': 'Content de vous revoir',
    'auth.login.subtitle': 'Connectez-vous à votre compte PhishGuard-AI',
    'auth.login.submit': 'Se connecter',
    'auth.login.remember': 'Se souvenir de moi',
    'auth.login.forgot': 'Mot de passe oublié ?',
    'auth.login.register': "S'inscrire",
    'auth.register.title': 'Créer mon compte',
    'auth.register.submit': 'Créer mon compte',
    'auth.register.login': 'Se connecter',
    'auth.mfa.title': 'Google Authenticator',
    'auth.mfa.setup': 'Configurer Google Authenticator',
    'auth.mfa.enabled': 'Activé',
    'auth.mfa.disabled': 'Désactivé',
    'auth.mfa.enable': 'Activer la protection',
    'auth.mfa.disable': 'Désactiver',
    'auth.verify.code': 'Code de vérification',
    'auth.verify.send': 'Envoyer le code',
    'auth.verify.submit': 'Vérifier le code',
    'user.dashboard.title': 'Tableau de bord',
    'user.dashboard.checkSecurity': 'Vérifier la sécurité',
    'user.dashboard.analyze': 'Analyser',
    'user.dashboard.protection': 'Statut de protection',
    'user.dashboard.securityScore': 'Score de sécurité',
    'user.dashboard.quarantine': 'Quarantaine',
    'user.dashboard.emailSecurity': 'Sécurité des e-mails',
    'user.dashboard.activeThreats': 'Menaces actives',
    'user.dashboard.statistics': 'Statistiques',
    'user.dashboard.reportHistory': 'Historique des signalements',
    'user.dashboard.about': 'À propos',
    'user.dashboard.report': 'Signaler',
    'user.dashboard.details': 'Détails',
    'user.dashboard.viewAll': 'Voir tout',
    'user.dashboard.changePassword': 'Changer le mot de passe',
    'user.security.title': 'Sécurité du compte',
    'user.security.account': 'Compte',
    'admin.overview.title': 'Security Operations Center',
    'admin.overview.status': 'TOUS LES SYSTÈMES OPÉRATIONNELS',
    'admin.overview.lastUpdate': 'Dernière mise à jour',
    'admin.overview.liveActivity': 'Activité de menaces en temps réel',
    'admin.overview.analytics': 'Analyses au fil du temps',
    'admin.overview.recentActivity': 'Activité récente',
    'admin.overview.summary': 'Synthèse exécutive',
    'admin.users.title': 'Utilisateurs',
    'admin.users.add': 'Ajouter un utilisateur',
    'admin.users.search': 'Rechercher par nom, email...',
    'admin.users.role': 'Rôle',
    'admin.users.status': 'Statut',
    'admin.users.actions': 'Actions',
    'admin.users.securityProfile': 'Profil sécurité utilisateur',
    'admin.users.close': 'Fermer',
    'admin.audit.title': 'Audit',
    'admin.audit.export': 'Exporter CSV',
    'admin.audit.search': 'Rechercher acteur, action, ressource...',
    'admin.audit.previous': 'Précédent',
    'admin.audit.next': 'Suivant',
    'admin.settings.title': 'Paramètres',
    'admin.settings.testConnection': 'Tester la connexion',
    'admin.settings.save': 'Enregistrer les modifications',
    'admin.reports.title': 'Signalements',
    'admin.reports.search': 'Rechercher expéditeur, sujet, URL...',
    'admin.threats.title': 'Threat Intelligence',
    'admin.threats.categories': 'Catégories',
    'admin.threats.iocs': 'Indicateurs de compromission',
    'admin.threats.geography': 'Géographie',
    'admin.models.title': 'AI Engine',
    'admin.models.retrain': 'Réentraîner',
    'common.cancel': 'Annuler',
    'common.save': 'Enregistrer',
    'common.close': 'Fermer',
    'common.active': 'Actif',
    'common.suspended': 'Suspendu',
    'common.enabled': 'Activé',
    'common.disabled': 'Désactivé',
    }

    const translations: Record<Locale, TranslationTable> = {
    fr: {
        ...pageTranslations,
        'nav.analyze': 'Analyser', 'nav.education': 'Éducation', 'nav.threatIntel': 'Veille', 'nav.about': 'À propos',
        'nav.login': 'Se connecter', 'nav.register': "S'inscrire", 'nav.dashboard': 'Mon tableau de bord', 'nav.admin': 'Administration',
        'nav.logout': 'Se déconnecter', 'nav.openMenu': 'Ouvrir le menu', 'nav.language': 'Langue', 'nav.lightMode': 'Activer le mode clair',
        'nav.darkMode': 'Activer le mode sombre', 'nav.user': 'Utilisateur', 'footer.description': 'Protégez-vous contre le phishing, la fraude Mobile Money et les cyberarnaques au Cameroun.',
        'footer.secure': 'Sécurisé', 'footer.poweredAi': 'IA puissante', 'footer.navigation': 'Navigation', 'footer.legalSecurity': 'Légal & Sécurité',
        'footer.resources': 'Ressources', 'footer.reporting': 'Signalement', 'footer.followUs': 'Suivez-nous', 'footer.activeProtection': 'Protection active',
        'footer.securedBy': 'Sécurisé par', 'footer.home': 'Accueil', 'footer.privacy': 'Confidentialité', 'footer.terms': 'Conditions',
        'footer.legal': 'Mentions légales', 'footer.cookies': 'Cookies', 'footer.education': 'Éducation', 'footer.report': 'Signalement',
    },
    en: {
        'nav.analyze': 'Analyze', 'nav.education': 'Education', 'nav.threatIntel': 'Threat intelligence', 'nav.about': 'About',
        'nav.login': 'Log in', 'nav.register': 'Sign up', 'nav.dashboard': 'My dashboard', 'nav.admin': 'Administration',
        'nav.logout': 'Log out', 'nav.openMenu': 'Open menu', 'nav.language': 'Language', 'nav.lightMode': 'Enable light mode',
        'nav.darkMode': 'Enable dark mode', 'nav.user': 'User', 'footer.description': 'Protect yourself from phishing, Mobile Money fraud, and cyber scams in Cameroon.',
        'footer.secure': 'Secure', 'footer.poweredAi': 'AI powered', 'footer.navigation': 'Navigation', 'footer.legalSecurity': 'Legal & security',
        'footer.resources': 'Resources', 'footer.reporting': 'Reporting', 'footer.followUs': 'Follow us', 'footer.activeProtection': 'Active protection',
        'footer.securedBy': 'Secured by', 'footer.home': 'Home', 'footer.privacy': 'Privacy', 'footer.terms': 'Terms',
        'footer.legal': 'Legal notice', 'footer.cookies': 'Cookies', 'footer.education': 'Education', 'footer.report': 'Report',
    },
    pcm: {
        'nav.analyze': 'Check am', 'nav.education': 'Learn', 'nav.threatIntel': 'Threat news', 'nav.about': 'About us',
        'nav.login': 'Login', 'nav.register': 'Sign up', 'nav.dashboard': 'My dashboard', 'nav.admin': 'Admin', 'nav.logout': 'Log out',
        'nav.openMenu': 'Open menu', 'nav.language': 'Language', 'nav.lightMode': 'Put light mode', 'nav.darkMode': 'Put dark mode', 'nav.user': 'User',
        'footer.description': 'Protect yourself from phishing, Mobile Money fraud and online scams for Cameroon.', 'footer.secure': 'Secure',
        'footer.poweredAi': 'AI power', 'footer.navigation': 'Navigation', 'footer.legalSecurity': 'Law and security', 'footer.resources': 'Resources',
        'footer.reporting': 'Report am', 'footer.followUs': 'Follow us', 'footer.activeProtection': 'Protection dey on', 'footer.securedBy': 'Secured by',
        'footer.home': 'Home', 'footer.privacy': 'Privacy', 'footer.terms': 'Terms', 'footer.legal': 'Legal notice', 'footer.cookies': 'Cookies',
        'footer.education': 'Learn', 'footer.report': 'Report am',
    },
    ewo: {
        'nav.analyze': 'Kɔghe', 'nav.education': 'Ayem', 'nav.threatIntel': 'Mvoé', 'nav.about': 'Nye', 'nav.login': 'Kɔlɔ',
        'nav.register': 'Tɔlɔ', 'nav.dashboard': 'Nnam', 'nav.admin': 'Admin', 'nav.logout': 'Kɔlɔ é', 'nav.openMenu': 'Vul menu',
        'nav.language': 'Nsem', 'nav.lightMode': 'Vul mode ya mwam', 'nav.darkMode': 'Vul mode ya zoé', 'nav.user': 'Mɔndi',
        'footer.description': 'Kɔghe phishing, mbɔgɔ Mobile Money na mvoé ya internet na Cameroon.', 'footer.secure': 'A ne mvus',
        'footer.poweredAi': 'AI a ne ngul', 'footer.navigation': 'Nnam', 'footer.legalSecurity': 'Mbet na mvus', 'footer.resources': 'Mvean',
        'footer.reporting': 'Kɔghe mvoé', 'footer.followUs': 'Kɔlɔ bia', 'footer.activeProtection': 'Mvus a ne nnam', 'footer.securedBy': 'Mvus na',
        'footer.home': 'Nnam', 'footer.privacy': 'Sɔgɔlɔ', 'footer.terms': 'Mbet', 'footer.legal': 'Mbet ya mɔndi', 'footer.cookies': 'Cookies',
        'footer.education': 'Ayem', 'footer.report': 'Kɔghe',
    },
    ff: {
        'nav.analyze': 'Ƴeewto', 'nav.education': 'Janngude', 'nav.threatIntel': 'Habaruuji', 'nav.about': 'Baɗte amen',
        'nav.login': 'Seŋo', 'nav.register': 'Winndito', 'nav.dashboard': 'Tablo am', 'nav.admin': 'Laamu', 'nav.logout': 'Yaltu',
        'nav.openMenu': 'Uddit menü', 'nav.language': 'Ɗemngal', 'nav.lightMode': 'Hurmin lewru', 'nav.darkMode': 'Hurmin jamma', 'nav.user': 'Gorko',
        'footer.description': 'Hisnu hoore maa e phishing, bonnude Mobile Money e juulɗe internet e Kamerun.', 'footer.secure': 'Hisnorde',
        'footer.poweredAi': 'AI sembe', 'footer.navigation': 'Nattugol', 'footer.legalSecurity': 'Laawol e hisnorde', 'footer.resources': 'Ɗaɓɓitaare',
        'footer.reporting': 'Jaŋtugol', 'footer.followUs': 'Yahdu e amen', 'footer.activeProtection': 'Hisnorde ina woodi', 'footer.securedBy': 'Hisnii e',
        'footer.home': 'Galle', 'footer.privacy': 'Sirrude', 'footer.terms': 'Doggol', 'footer.legal': 'Laawol', 'footer.cookies': 'Cookies',
        'footer.education': 'Janngude', 'footer.report': 'Jaŋtu',
    },
    }

    const savedLocale = typeof window !== 'undefined' ? window.localStorage.getItem('pg-locale') as Locale | null : null
    const locale = ref<Locale>(savedLocale && savedLocale in translations ? savedLocale : 'fr')
    if (typeof document !== 'undefined') {
    document.documentElement.lang = locale.value === 'pcm' ? 'en-CM' : locale.value
    }

    export function useI18n() {
    const t = (key: TranslationKey) => translations[locale.value][key] || translations.fr[key] || key
    const setLocale = (nextLocale: Locale) => {
        locale.value = nextLocale
        if (typeof window !== 'undefined') {
        window.localStorage.setItem('pg-locale', nextLocale)
        document.documentElement.lang = nextLocale === 'pcm' ? 'en-CM' : nextLocale
        }
    }

    return { locale, locales: computed(() => localeOptions), t, setLocale }
    }