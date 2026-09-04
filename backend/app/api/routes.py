# backend/app/api/routes.py
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Analysis
import json
from datetime import datetime

# NEW IMPORT
from app.ml_engine.hybrid_detector import HybridDetector

api_bp = Blueprint('api', __name__)
detector = HybridDetector() # Initialize once at start


def _normalize_verdict(verdict):
    normalized = (verdict or '').lower()
    if normalized in {'critical', 'high', 'phishing'}:
        return 'phishing'
    if normalized in {'medium', 'suspicious'}:
        return 'suspicious'
    return 'legitimate'


@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'PhishGuard-AI API', 'version': '1.0.0'})

@api_bp.route('/analyze', methods=['POST'])
def analyze_message():
    try:
        data = request.get_json()
        text = data.get('text', '')
        sender_domain = data.get('sender_domain') # Optional
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400

        # 1. Call the Hybrid Detector
        result = detector.analyze(text, sender_domain)
        result['verdict'] = _normalize_verdict(result.get('verdict'))
        result['score'] = round(float(result.get('score', 0)), 2)

        # 2. Save to Database
        user_id = current_user.id if current_user.is_authenticated else None
        analysis = Analysis(
            user_id=user_id,
            text_source=text[:1000],
            score_risk=result['score'],
            verdict=result['verdict'],
            indicators=json.dumps(result['indicators'])
        )
        db.session.add(analysis)
        db.session.commit()
        result['analysis_id'] = analysis.id

        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/analysis/message', methods=['POST'])
def analysis_message_compat():
    return analyze_message()


@api_bp.route('/analysis/report', methods=['POST'])
def analysis_report_compat():
    data = request.get_json() or {}
    text = data.get('text', '')
    result = data.get('result')
    if not text or not result:
        return jsonify({'reported': False}), 400
    return jsonify({'reported': True}), 200


@api_bp.route('/threats/categories', methods=['GET'])
def get_threat_categories():
    categories = [
        {
            'id': 1,
            'name': 'Phishing / Hameçonnage',
            'icon': 'envelope',
            'color': 'red',
            'priority': 1,
            'description': "Tentative de fraude par email, SMS ou appel pour obtenir vos informations personnelles.",
            'mechanism': "L'attaquant se fait passer pour une institution légitime et vous pousse à cliquer sur un faux lien.",
            'warningSigns': 'Urgence artificielle, fautes d’orthographe, lien suspect, demande de données personnelles.',
            'recommendedAction': 'Ne cliquez jamais sur les liens. Vérifiez toujours via le canal officiel.'
        },
        {
            'id': 2,
            'name': 'Fraude Mobile Money',
            'icon': 'mobile',
            'color': 'orange',
            'priority': 2,
            'description': "Escroquerie par téléphone ou SMS où l'attaquant se fait passer pour un agent MTN/Orange.",
            'mechanism': "L'attaquant demande votre code PIN ou un OTP pour détourner votre argent.",
            'warningSigns': 'Demande de PIN/OTP, ton pressant, numéro non officiel.',
            'recommendedAction': 'Ne jamais communiquer votre PIN. Raccrochez et rappelez le numéro officiel.'
        },
        {
            'id': 3,
            'name': 'Ingénierie sociale',
            'icon': 'people',
            'color': 'purple',
            'priority': 3,
            'description': 'Manipulation psychologique pour obtenir des informations confidentielles.',
            'mechanism': "L'attaquant exploite la confiance, la peur ou l'urgence pour vous faire agir.",
            'warningSigns': 'Appel à l’émotion, urgence familiale, demande d’argent pressante.',
            'recommendedAction': 'Toujours vérifier par un second canal avant d’agir.'
        },
        {
            'id': 4,
            'name': 'Faux profils / usurpation',
            'icon': 'incognito',
            'color': 'pink',
            'priority': 4,
            'description': "Compte WhatsApp/Facebook reprenant le nom et la photo d'un proche pour demander de l'argent.",
            'mechanism': 'L’attaquant simule l’identité d’un proche pour réclamer de l’argent.',
            'warningSigns': 'Nouveau numéro, demande d’argent inhabituelle, ton urgent.',
            'recommendedAction': 'Vérifier l’identité par un autre canal avant tout envoi.'
        },
        {
            'id': 5,
            'name': 'Rançongiciel (Ransomware)',
            'icon': 'lock',
            'color': 'red',
            'priority': 5,
            'description': 'Chiffrement de fichiers contre une rançon, ciblant souvent les PME et administrations.',
            'mechanism': 'Un fichier malveillant chiffre vos données et exige une rançon.',
            'warningSigns': 'Fichiers illisibles, ralentissement soudain, message de rançon.',
            'recommendedAction': 'Sauvegarder régulièrement et alerter les autorités.'
        },
        {
            'id': 6,
            'name': 'SIM swapping',
            'icon': 'sim',
            'color': 'yellow',
            'priority': 6,
            'description': "L'attaquant fait transférer frauduleusement votre numéro vers une autre SIM.",
            'mechanism': 'L’attaquant usurpe votre identité auprès de l’opérateur pour obtenir une nouvelle SIM.',
            'warningSigns': 'Perte soudaine du signal, comptes suspects.',
            'recommendedAction': 'Contacter immédiatement l’opérateur via un canal officiel.'
        },
        {
            'id': 7,
            'name': 'Faux sites / applications',
            'icon': 'globe',
            'color': 'indigo',
            'priority': 7,
            'description': 'Faux site bancaire visuellement identique à l’original, ou APK modifié.',
            'mechanism': 'Le faux site ou l’application vole vos identifiants ou vos codes.',
            'warningSigns': 'URL légèrement différente, absence de HTTPS, permissions excessives.',
            'recommendedAction': 'Vérifier l’URL exacte et installer uniquement depuis les stores officiels.'
        },
        {
            'id': 8,
            'name': 'Arnaques emploi / bourses',
            'icon': 'briefcase',
            'color': 'teal',
            'priority': 8,
            'description': "Fausses offres d'emploi ou de bourses demandant des frais de dossier.",
            'mechanism': 'Une offre trop belle pour être vraie demande un paiement avant toute procédure.',
            'warningSigns': 'Paiement demandé avant embauche, offre trop belle.',
            'recommendedAction': 'Vérifier auprès du site officiel avant tout paiement.'
        },
        {
            'id': 9,
            'name': 'Arnaques sentimentales',
            'icon': 'heart',
            'color': 'rose',
            'priority': 9,
            'description': 'Relation en ligne développée sur plusieurs semaines, puis demande d’argent.',
            'mechanism': 'L’attaquant crée une relation de confiance pour forcer le transfert d’argent.',
            'warningSigns': 'Refus systématique d’appel vidéo, demandes d’argent répétées.',
            'recommendedAction': 'Ne jamais envoyer d’argent sans confirmation en ligne ou hors ligne.'
        },
        {
            'id': 10,
            'name': 'Malware / APK piraté',
            'icon': 'bug',
            'color': 'gray',
            'priority': 10,
            'description': 'Téléchargement d’applications malveillantes hors des stores officiels.',
            'mechanism': 'Une application pirate installe un malware sur votre téléphone.',
            'warningSigns': 'Permissions excessives, ralentissements, messages suspects.',
            'recommendedAction': 'N’installer que depuis les stores officiels et vérifier les permissions.'
        },
        {
            'id': 11,
            'name': 'Deepfake / fraude par IA',
            'icon': 'robot',
            'color': 'violet',
            'priority': 11,
            'description': "Appel avec voix clonée d'un proche demandant un virement urgent.",
            'mechanism': 'Une voix clonée détourne votre confiance pour obtenir de l’argent.',
            'warningSigns': 'Demande d’argent urgente avec voix connue.',
            'recommendedAction': 'Confirmer par un autre canal avant d’effectuer un transfert.'
        },
        {
            'id': 12,
            'name': 'Fuite de données',
            'icon': 'database',
            'color': 'slate',
            'priority': 12,
            'description': 'Données personnelles exfiltrées puis revendues.',
            'mechanism': 'Une faille de sécurité expose des données sensibles.',
            'warningSigns': 'Sollicitations ciblées, notifications inhabituelles.',
            'recommendedAction': 'Limiter le partage de données et surveiller ses comptes.'
        }
    ]
    return jsonify(categories)


@api_bp.route('/threats/intel', methods=['GET'])
def get_threat_intel():
    intel = [
        {
            'id': 'ti-1',
            'title': 'Nouveau kit de phishing ciblant les usagers MTN',
            'source': 'CIRT-CM',
            'category': 'Phishing',
            'date': '2026-09-03',
            'summary': 'Un kit de phishing vendu sur Telegram cible les utilisateurs de MTN Mobile Money via de fausses invites USSD.'
        },
        {
            'id': 'ti-2',
            'title': 'Vague de ransomware contre des PME locales',
            'source': 'SecurityWeek',
            'category': 'Ransomware',
            'date': '2026-09-02',
            'summary': 'Plusieurs PME de Douala ont été touchées par des rançongiciels exigeant un paiement en Bitcoin.'
        },
        {
            'id': 'ti-3',
            'title': 'Hausse des arnaques par voix clonée',
            'source': 'BBC News',
            'category': 'Deepfake',
            'date': '2026-09-01',
            'summary': "Des criminels utilisent l'IA pour cloner des voix de proches et déclencher des virements en urgence."
        },
        {
            'id': 'ti-4',
            'title': 'Alerte fraude par SIM swap',
            'source': 'Orange CM',
            'category': 'SIM Swapping',
            'date': '2026-08-30',
            'summary': 'Orange Cameroun signale une technique où des attaquants se font passer pour le service client.'
        },
        {
            'id': 'ti-5',
            'title': "Fausses offres d'emploi sur les réseaux sociaux",
            'source': 'ANTIC',
            'category': 'Emploi',
            'date': '2026-08-28',
            'summary': 'Des offres fictives réclament des « frais de dossier » pour des postes inexistants.'
        },
        {
            'id': 'ti-6',
            'title': 'Fuite de données sur un portail gouvernemental',
            'source': 'TechCrunch',
            'category': 'Fuite de données',
            'date': '2026-08-27',
            'summary': 'Une vulnérabilité a exposé des identifiants personnels ; un changement de mot de passe est recommandé.'
        }
    ]
    return jsonify(intel)