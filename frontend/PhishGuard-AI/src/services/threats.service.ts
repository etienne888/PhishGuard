import { api } from './api'
import type { ThreatCategory, ThreatIntelItem } from '@/types'

const SEED_CATEGORIES: ThreatCategory[] = [
  { id: 1, name: 'Phishing / Hameçonnage', icon: 'envelope', color: 'red', priority: 1, description: "Tentative de fraude par email, SMS ou appel pour obtenir vos informations personnelles.", mechanism: "L'attaquant se fait passer pour une institution légitime (banque, opérateur mobile, administration) et vous envoie un lien vers un faux site de connexion.", warningSigns: "Urgence artificielle, fautes d'orthographe, lien suspect, demande de données personnelles.", recommendedAction: 'Ne cliquez jamais sur les liens. Vérifiez toujours via le canal officiel. Signalez au CIRT-CM.' },
  { id: 2, name: 'Fraude Mobile Money', icon: 'mobile', color: 'orange', priority: 2, description: "Escroquerie par téléphone ou SMS où l'attaquant se fait passer pour un agent MTN/Orange.", mechanism: "L'attaquant appelle en se présentant comme agent officiel et demande votre code PIN ou vous invite à effectuer une opération frauduleuse.", warningSigns: 'Demande de PIN/OTP par téléphone, ton pressant, numéro non officiel.', recommendedAction: 'Ne jamais communiquer votre PIN. Raccrochez et rappelez le numéro officiel de l’opérateur.' },
  { id: 3, name: 'Ingénierie sociale', icon: 'people', color: 'purple', priority: 3, description: 'Manipulation psychologique pour obtenir des informations confidentielles.', mechanism: "L'attaquant exploite la confiance, la peur ou l'urgence pour vous faire agir contre votre intérêt.", warningSigns: "Appel à l'émotion, urgence familiale, demande d'argent pressante.", recommendedAction: "Toujours vérifier par un second canal avant d'agir, même en situation d'urgence." },
  { id: 4, name: 'Faux profils / usurpation', icon: 'incognito', color: 'pink', priority: 4, description: "Compte WhatsApp/Facebook reprenant le nom et la photo d'un proche pour demander de l'argent.", mechanism: "L'attaquant crée un faux profil et contacte les proches de la victime pour demander un transfert d'argent.", warningSigns: 'Nouveau numéro non confirmé, demande d’argent inhabituelle, ton urgent.', recommendedAction: 'Vérifier l’identité par un canal déjà connu avant tout envoi. Signaler le faux compte.' },
  { id: 5, name: 'Rançongiciel (Ransomware)', icon: 'lock', color: 'red', priority: 5, description: 'Chiffrement de fichiers contre une rançon, ciblant souvent les PME et administrations.', mechanism: "L'attaquant infecte un système via une pièce jointe piégée ou un VPN non mis à jour, puis chiffre les fichiers.", warningSigns: 'Ralentissements soudains, fichiers illisibles, message de rançon.', recommendedAction: "Sauvegardes hors ligne régulières, mises à jour systèmes, ne jamais payer, alerter l'ANTIC/CIRT-CM." },
  { id: 6, name: 'SIM swapping', icon: 'sim', color: 'yellow', priority: 6, description: "L'attaquant fait transférer frauduleusement votre numéro vers une autre SIM.", mechanism: "L'attaquant usurpe votre identité auprès de l'opérateur pour obtenir une nouvelle SIM à votre nom.", warningSigns: 'Perte soudaine et inexpliquée du réseau, puis notifications de comptes inhabituelles.', recommendedAction: "Contacter immédiatement l'opérateur par un canal officiel et sécuriser les comptes liés." },
  { id: 7, name: 'Faux sites / applications', icon: 'globe', color: 'indigo', priority: 7, description: 'Faux site bancaire visuellement identique à l’original, ou APK modifié.', mechanism: "L'attaquant crée un site ou une application imitant un service légitime pour voler vos identifiants.", warningSigns: 'URL légèrement différente, absence de HTTPS, demandes de permissions excessives.', recommendedAction: "Vérifier l'URL exacte et le certificat. N'installer que depuis les stores officiels." },
  { id: 8, name: 'Arnaques emploi / bourses', icon: 'briefcase', color: 'teal', priority: 8, description: "Fausses offres d'emploi ou de bourses demandant des frais de dossier.", mechanism: "L'attaquant publie une offre alléchante et demande un paiement avant toute procédure officielle.", warningSigns: 'Paiement demandé avant toute embauche/inscription officielle, offre trop belle.', recommendedAction: 'Vérifier auprès du site officiel de l’organisme avant tout paiement.' },
  { id: 9, name: 'Arnaques sentimentales', icon: 'heart', color: 'rose', priority: 9, description: 'Relation en ligne développée sur plusieurs semaines, puis demande d’argent.', mechanism: "L'attaquant crée une relation de confiance puis invente un problème soudain nécessitant de l'argent.", warningSigns: "Refus systématique d'appel vidéo, demandes d'argent répétées.", recommendedAction: "Ne jamais envoyer d'argent à une personne jamais rencontrée physiquement ou en vidéo vérifiée." },
  { id: 10, name: 'Malware / APK piraté', icon: 'bug', color: 'gray', priority: 10, description: 'Téléchargement d’applications malveillantes hors des stores officiels.', mechanism: "L'attaquant propose une application gratuite qui contient un malware pour espionner ou voler des données.", warningSigns: 'Permissions excessives demandées (SMS, contacts, accessibilité).', recommendedAction: "N'installer que depuis Google Play. Vérifier les permissions avant installation." },
  { id: 11, name: 'Deepfake / fraude par IA', icon: 'robot', color: 'violet', priority: 11, description: "Appel avec voix clonée d'un proche demandant un virement urgent.", mechanism: "L'attaquant utilise l'IA pour cloner la voix d'un proche et vous appeler en demandant de l'argent.", warningSigns: 'Demande d’argent inhabituelle même avec une voix reconnue.', recommendedAction: 'Vérifier l’identité par un second canal, même si la voix semble authentique.' },
  { id: 12, name: 'Fuite de données', icon: 'database', color: 'slate', priority: 12, description: 'Données personnelles (CNI, numéro, historique) exfiltrées puis revendues.', mechanism: "L'attaquant exploite une faille de sécurité pour voler des données personnelles et les revendre.", warningSigns: 'Sollicitations très ciblées et personnalisées reçues après un incident connu.', recommendedAction: 'Limiter le partage de données sensibles. Surveiller ses comptes après une fuite signalée.' }
]

const SEED_INTEL: ThreatIntelItem[] = [
  { id: 'ti-1', title: 'Nouveau kit de phishing ciblant les usagers MTN', source: 'CIRT-CM', category: 'Phishing', date: '2026-09-03', summary: 'Un kit de phishing vendu sur Telegram cible les utilisateurs de MTN Mobile Money via de fausses invites USSD.' },
  { id: 'ti-2', title: 'Vague de ransomware contre des PME locales', source: 'SecurityWeek', category: 'Ransomware', date: '2026-09-02', summary: 'Plusieurs PME de Douala ont été touchées par des rançongiciels exigeant un paiement en Bitcoin.' },
  { id: 'ti-3', title: 'Hausse des arnaques par voix clonée', source: 'BBC News', category: 'Deepfake', date: '2026-09-01', summary: "Des criminels utilisent l'IA pour cloner des voix de proches et déclencher des virements en urgence." },
  { id: 'ti-4', title: 'Alerte fraude par SIM swap', source: 'Orange CM', category: 'SIM Swapping', date: '2026-08-30', summary: 'Orange Cameroun signale une technique où des attaquants se font passer pour le service client.' },
  { id: 'ti-5', title: "Fausses offres d'emploi sur les réseaux sociaux", source: 'ANTIC', category: 'Emploi', date: '2026-08-28', summary: 'Des offres fictives réclament des « frais de dossier » pour des postes inexistants.' },
  { id: 'ti-6', title: 'Fuite de données sur un portail gouvernemental', source: 'TechCrunch', category: 'Fuite de données', date: '2026-08-27', summary: 'Une vulnérabilité a exposé des identifiants personnels ; un changement de mot de passe est recommandé.' }
]

export const threatsService = {
  async getCategories(): Promise<ThreatCategory[]> {
    try {
      return await api.get<ThreatCategory[]>('/threats/categories')
    } catch {
      return SEED_CATEGORIES
    }
  },

  async getThreatIntel(): Promise<ThreatIntelItem[]> {
    try {
      return await api.get<ThreatIntelItem[]>('/threats/intel')
    } catch {
      // simulate scraper latency for the refresh interaction
      await new Promise((resolve) => setTimeout(resolve, 900))
      return SEED_INTEL
    }
  }
}
