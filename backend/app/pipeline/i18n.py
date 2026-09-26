"""
User-facing pipeline messages in French and English.

The scan endpoint picks the language from the request (`lang` field, then the
Accept-Language header) and passes it down; French is the default.
"""

LANGUAGES = ("fr", "en")
DEFAULT_LANG = "fr"

MESSAGES = {
    "fr": {
        # Rules
        "pressure": "Pression psychologique : {label}",
        "pressure.urgent": "urgence",
        "pressure.block": "menace de blocage",
        "pressure.suspend": "menace de suspension",
        "pressure.deadline": "délai artificiel",
        "secret_request": "Demande d'information confidentielle : « {word} »",
        "advance_fee": "Paiement demandé à l'avance : « {word} »",
        "official_sender": "Expéditeur officiel : {institution} ({domain})",
        "origin.foreign_for_local_brand": "Se présente comme {brand} mais a été envoyé depuis l'étranger ({country})",
        "origin.datacenter": "Envoyé depuis un serveur d'hébergement ({country}), pas depuis un réseau d'opérateur ou de particulier",
        "origin.proxy": "Envoyé à travers un VPN ou un proxy qui masque l'expéditeur",
        "origin.blacklisted": "Le serveur d'envoi figure sur des listes noires anti-spam publiques",
        "origin.scripted": "Envoyé par un script automatique (envoi en masse), pas par une messagerie classique",
        "origin.timezone_mismatch": "Le fuseau horaire de l'email ne correspond pas à la localisation du serveur d'envoi",
        "sender_imitates": "L'expéditeur imite {institution} : {domain}",
        "reply_to_other": "Les réponses partent vers un autre domaine ({domain})",
        "auth_failed": "Échec de l'authentification de l'expéditeur : {methods}",
        "dangerous_attachment": "Pièce jointe dangereuse : {filename}",
        "ai_prefix": "IA : {reason}",
        "default_recommendation": "Ne cliquez sur aucun lien et vérifiez auprès du canal officiel. "
                                  "Signalez au CIRT-CM : 8202 / alerts@cirt.cm",
        # URL intelligence
        "url.lookalike": "Domaine qui imite {imitates} ({institution})",
        "url.brand": "Le lien utilise le nom de {institution} sans être son site officiel",
        "url.ip": "Adresse IP utilisée à la place d'un nom de domaine",
        "url.tld": "Extension de domaine très utilisée par les fraudeurs ({tld})",
        "url.shortener": "Lien raccourci qui cache la vraie destination",
        "url.punycode": "Domaine avec caractères déguisés (punycode)",
        "url.subdomains": "Nombreux sous-domaines",
        "url.http": "Connexion non sécurisée (http)",
        "url.credentials": "Identifiants cachés dans l'adresse du lien",
        "url.lure": "Mots d'hameçonnage dans le lien (login, verify, secure…)",
        "url.xgb": "Modèle XGB : lien malveillant à {pct} %",
        "url.blocklisted": "Domaine sur la liste noire PhishGuard (menace confirmée)",
        # Fusion overrides
        "override.strong": "Preuve forte (usurpation de marque ou lien sur liste noire) : score minimum 85",
        "override.official": "Expéditeur officiel authentifié (SPF/DKIM/DMARC) sans lien suspect : score maximum 30",
        # Input errors
        "error.too_short": "Message trop court pour être analysé (10 caractères minimum).",
        "error.eml_unreadable": "Fichier .eml illisible : {detail}",
        "error.eml_no_headers": "Fichier .eml invalide : aucun en-tête trouvé.",
        "error.eml_no_text": "Le fichier .eml ne contient aucun texte analysable.",
        "error.eml_only": "Seuls les fichiers .eml sont acceptés.",
        "error.rate_limited": "Trop d'analyses depuis cette connexion. Connectez-vous ou réessayez dans une heure.",
        "error.claim_invalid": "Cette analyse a expiré ou appartient à un autre compte. Relancez l'analyse.",
        "error.not_found": "Élément introuvable.",
        "gated.tip": "En attendant le résultat : ne cliquez sur aucun lien et ne communiquez aucun code, PIN ou mot de passe.",
        "mailbox.not_configured": "Ce fournisseur n'est pas encore configuré par l'administrateur.",
        "mailbox.paused": "L'analyse de cette boîte est en pause.",
        "mailbox.error.unreachable": "Le fournisseur de messagerie est injoignable. Réessayez plus tard.",
        "mailbox.error.token": "La connexion à la boîte mail a échoué. Reconnectez-la.",
        "mailbox.error.revoked": "L'accès à la boîte mail a été retiré. Reconnectez-la pour reprendre l'analyse.",
        "mailbox.error.unauthorized": "L'accès à la boîte mail a expiré. Reconnectez-la.",
        "mailbox.error.forbidden": "PhishGuard n'a pas la permission de lire cette boîte (API désactivée ou compte non autorisé).",
        "mailbox.error.provider": "Le fournisseur de messagerie a renvoyé une erreur.",
        "notif.mailbox_threat": "Email dangereux dans votre boîte mail, de {mailbox}",
        "notif.review_phishing": "Votre signalement est confirmé : c'était bien une arnaque",
        "notif.review_safe": "Votre signalement a été vérifié : ce message était sans danger",
        "notif.review_body": "Merci ! Votre signalement aide à protéger les autres utilisateurs. Message : {text}",
        "error.too_large": "Fichier trop volumineux (5 Mo maximum).",
        "unnamed_attachment": "sans-nom",
        # Dashboards
        "notif.threat": "Menace détectée",
        "notif.suspicious": "Message suspect",
        "notif.score": "Score de risque {score}/100 : {text}",
        "notif.mfa_title": "Protégez votre compte",
        "notif.mfa_body": "Activez la double authentification (code OTP) dans Paramètres › Sécurité.",
        "message.default_title": "Analyse de message",
        "sender.unknown": "Expéditeur inconnu",
        "source.visitor": "Visiteur (page d’accueil)",
        "engine.xgb": "XGBoost (liens)",
        "engine.xgb_biased": "biais détecté — à réentraîner",
        "engine.xgb_untrained": "non entraîné",
        "engine.nb": "Naive Bayes (texte)",
        "engine.rules": "Règles expertes CM",
        "map.hq": "Yaoundé, Cameroun",
    },
    "en": {
        "pressure": "Psychological pressure: {label}",
        "pressure.urgent": "urgency",
        "pressure.block": "threat of blocking",
        "pressure.suspend": "threat of suspension",
        "pressure.deadline": "artificial deadline",
        "secret_request": "Request for confidential information: \"{word}\"",
        "advance_fee": "Payment requested in advance: \"{word}\"",
        "official_sender": "Official sender: {institution} ({domain})",
        "origin.foreign_for_local_brand": "Presents itself as {brand} but was sent from abroad ({country})",
        "origin.datacenter": "Sent from a hosting server ({country}), not from an operator or home network",
        "origin.proxy": "Sent through a VPN or proxy that hides the sender",
        "origin.blacklisted": "The sending server is on public anti-spam blacklists",
        "origin.scripted": "Sent by an automated script (mass mailing), not a normal email app",
        "origin.timezone_mismatch": "The email's time zone doesn't match the sending server's location",
        "sender_imitates": "The sender imitates {institution}: {domain}",
        "reply_to_other": "Replies go to a different domain ({domain})",
        "auth_failed": "Sender authentication failed: {methods}",
        "dangerous_attachment": "Dangerous attachment: {filename}",
        "ai_prefix": "AI: {reason}",
        "default_recommendation": "Do not click any link and check with the official channel. "
                                  "Report it to CIRT-CM: 8202 / alerts@cirt.cm",
        "url.lookalike": "Domain imitating {imitates} ({institution})",
        "url.brand": "The link uses the name of {institution} without being its official site",
        "url.ip": "IP address used instead of a domain name",
        "url.tld": "Domain extension widely used by fraudsters ({tld})",
        "url.shortener": "Shortened link hiding the real destination",
        "url.punycode": "Domain with disguised characters (punycode)",
        "url.subdomains": "Many subdomains",
        "url.http": "Insecure connection (http)",
        "url.credentials": "Credentials hidden in the link address",
        "url.lure": "Phishing words in the link (login, verify, secure…)",
        "url.xgb": "XGB model: {pct}% likely malicious link",
        "url.blocklisted": "Domain on the PhishGuard blocklist (confirmed threat)",
        "override.strong": "Strong evidence (brand impersonation or blocklisted link): minimum score 85",
        "override.official": "Authenticated official sender (SPF/DKIM/DMARC) with no suspicious link: maximum score 30",
        "error.too_short": "Message too short to analyze (10 characters minimum).",
        "error.eml_unreadable": "Unreadable .eml file: {detail}",
        "error.eml_no_headers": "Invalid .eml file: no headers found.",
        "error.eml_no_text": "The .eml file contains no text to analyze.",
        "error.eml_only": "Only .eml files are accepted.",
        "error.rate_limited": "Too many scans from this connection. Sign in or try again in an hour.",
        "error.claim_invalid": "This analysis has expired or belongs to another account. Please scan again.",
        "error.not_found": "Item not found.",
        "gated.tip": "While you wait for the result: don't click any link and never share a code, PIN or password.",
        "mailbox.not_configured": "This provider has not been configured by the administrator yet.",
        "mailbox.paused": "Scanning of this mailbox is paused.",
        "mailbox.error.unreachable": "The email provider can't be reached. Try again later.",
        "mailbox.error.token": "Connecting to the mailbox failed. Please reconnect it.",
        "mailbox.error.revoked": "Access to the mailbox was removed. Reconnect it to resume scanning.",
        "mailbox.error.unauthorized": "Access to the mailbox has expired. Please reconnect it.",
        "mailbox.error.forbidden": "PhishGuard isn't allowed to read this mailbox (API disabled or account not authorised).",
        "mailbox.error.provider": "The email provider returned an error.",
        "notif.mailbox_threat": "Dangerous email in your mailbox, from {mailbox}",
        "notif.review_phishing": "Your report is confirmed: it was a scam",
        "notif.review_safe": "Your report was checked: this message was safe",
        "notif.review_body": "Thank you! Your report helps protect other users. Message: {text}",
        "error.too_large": "File too large (5 MB maximum).",
        "unnamed_attachment": "unnamed",
        "notif.threat": "Threat detected",
        "notif.suspicious": "Suspicious message",
        "notif.score": "Risk score {score}/100: {text}",
        "notif.mfa_title": "Protect your account",
        "notif.mfa_body": "Turn on two-factor authentication (OTP code) in Settings › Security.",
        "message.default_title": "Message analysis",
        "sender.unknown": "Unknown sender",
        "source.visitor": "Visitor (home page)",
        "engine.xgb": "XGBoost (links)",
        "engine.xgb_biased": "bias detected — retrain needed",
        "engine.xgb_untrained": "not trained",
        "engine.nb": "Naive Bayes (text)",
        "engine.rules": "Cameroon expert rules",
        "map.hq": "Yaoundé, Cameroon",
    },
}


def normalize_lang(value: str | None) -> str:
    """'en', 'en-CM', 'en-US,en;q=0.9' -> 'en'; anything unknown -> 'fr'."""
    code = (value or "").split(",")[0].split(";")[0].strip().lower()[:2]
    return code if code in LANGUAGES else DEFAULT_LANG


def request_lang() -> str:
    """Language of the current Flask request (Accept-Language header)."""
    from flask import has_request_context, request
    return normalize_lang(request.headers.get('Accept-Language')) if has_request_context() else DEFAULT_LANG


def tr(lang: str, key: str, **params) -> str:
    table = MESSAGES.get(lang, MESSAGES[DEFAULT_LANG])
    template = table.get(key) or MESSAGES[DEFAULT_LANG].get(key, key)
    return template.format(**params) if params else template
