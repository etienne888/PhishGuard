"""
Build the PhishGuard training / evaluation corpus -> ml_data/corpus.csv

Columns: text, label (1 = phishing/scam, 0 = legitimate), lang, channel, family, template, source, split

Sources (always kept separate so every metric can be reported per source):
  synthetic  Cameroonian templates (fr / en / pcm) with random slot values. Hard negatives included:
             genuine messages that mention codes, amounts, accounts or official links; hard positives:
             scams without any link. TEST = templates never seen in training (no leakage).
  challenge  Hand-written, independent messages (not generated): an extra held-out test set.
  uci_sms    UCI SMS Spam Collection (Almeida & Hidalgo, 2011, CC BY 4.0), English; spam -> 1.
             Downloaded once into ml_data/raw/. Stratified 80/20 split.
  admin      Analyses labelled by administrators in the review queue (real, human-labelled data),
             exported when --with-db is given. Automatic decisions are excluded.

Usage:  python ml_data/build_dataset.py [--with-db] [--no-uci]
"""
from __future__ import annotations

import csv
import io
import os
import random
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'raw')
OUT = os.path.join(HERE, 'corpus.csv')
UCI_URL = 'https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip'
SEED = 42
VARIANTS = 14          # generated messages per template
TEST_TEMPLATE_SHARE = 0.25

rng = random.Random(SEED)

SLOTS = {
    'op': ['MTN', 'Orange', 'MTN MoMo', 'Orange Money', 'Camtel', 'Nexttel'],
    'bank': ['Afriland First Bank', 'BICEC', 'SGBC', 'UBA Cameroun', 'Ecobank', 'CCA Bank'],
    'amt': ['5 000', '10 000', '15 500', '25 000', '50 000', '75 000', '150 000', '250 000', '500 000', '1 000 000'],
    'fee': ['2 500', '3 000', '5 000', '7 500', '10 000'],
    'name': ['Awa', 'Jean', 'Mireille', 'Paul', 'Aïcha', 'Serge', 'Brenda', 'Ngono', 'Fotso', 'Mbarga'],
    'city': ['Yaoundé', 'Douala', 'Bafoussam', 'Garoua', 'Bamenda', 'Buea', 'Ngaoundéré', 'Kribi'],
    'hours': ['24h', '12h', '48h', '2 heures', '1 heure'],
    'bad': ['mtn-momo-verif.tk', 'orange-money-secure.ga', 'momo-bonus.xyz', 'afriland-secure-login.com',
            'bicec-update.online', 'eneo-paiement.online', 'cnps-remboursement.site', 'camtel-promo.click',
            'mtn-cm.top', 'orange-cm-verify.link', 'dhl-cameroun-colis.info', 'impots-cm.live'],
    'good': ['mtn.cm', 'orange.cm', 'afrilandfirstbank.com', 'eneo.cm', 'camtel.cm', 'impots.cm'],
    'phone': ['6 71 23 45 67', '6 90 11 22 33', '6 55 44 33 22', '6 98 76 54 32', '6 77 88 99 00'],
    'code': ['482913', '557201', '903348', '120775', '664019'],
    'day': ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi'],
    'day_en': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
    'time': ['8h30', '10h', '14h', '15h30', '17h'],
    'ref': ['CI240925.1834.A12', 'MP250912.0931.B77', 'TX9981273', 'REF-20260925-4412'],
    'job': ['agent de saisie', 'caissier', 'livreur', 'assistant administratif', 'community manager'],
    'shop': ['Jumia', 'Santa Lucia', 'Carrefour Market', 'Tradex', 'Glotelho'],
}

# (family, lang, channel, template) - label 1
PHISHING = [
    ('momo_suspension', 'fr', 'sms', '{op} : votre compte sera suspendu dans {hours} suite à une activité inhabituelle. Confirmez votre code PIN sur http://{bad}/confirm'),
    ('momo_suspension', 'fr', 'sms', 'Cher client {op}, votre compte Mobile Money est BLOQUÉ. Pour le réactiver, cliquez ici {bad} et saisissez votre code secret.'),
    ('momo_suspension', 'en', 'sms', '{op}: your account will be suspended within {hours} due to unusual activity. Verify your PIN now at http://{bad}'),
    ('momo_suspension', 'pcm', 'sms', '{op}: your account go block for {hours}. Enter your PIN for http://{bad} make e no block.'),
    ('pin_request', 'fr', 'sms', 'Service client {op} : un agent va vous appeler. Communiquez-lui le code à 6 chiffres reçu par SMS pour sécuriser votre compte.'),
    ('pin_request', 'fr', 'whatsapp', 'Bonjour, je suis agent {op}. Suite à une mise à jour, envoyez-moi votre code PIN et le code de confirmation que vous allez recevoir.'),
    ('pin_request', 'en', 'sms', '{op} customer care: an agent will call you. Please give him the verification code you receive to keep your line active.'),
    ('prize', 'fr', 'sms', 'Félicitations ! Votre numéro a gagné {amt} FCFA à la tombola {op}. Envoyez {fee} FCFA de frais de dossier au {phone} pour recevoir votre gain.'),
    ('prize', 'fr', 'sms', 'BRAVO {name} ! Vous êtes le grand gagnant de {amt} FCFA. Pour débloquer votre cadeau, payez {fee} FCFA de frais via {op}.'),
    ('prize', 'en', 'sms', 'Congratulations! Your number won {amt} FCFA in the {op} anniversary draw. Send {fee} FCFA processing fee to {phone} to claim.'),
    ('prize', 'pcm', 'whatsapp', 'Congrat! You don win {amt} FCFA for {op} promo. Send {fee} FCFA for {phone} make we release your money today.'),
    ('bank_login', 'fr', 'email', 'Cher client {bank}, une activité suspecte a été détectée sur votre compte. Connectez-vous immédiatement sur https://{bad} pour éviter le blocage de votre carte.'),
    ('bank_login', 'fr', 'email', '{bank} - Dernier avertissement : mettez à jour vos informations bancaires sous {hours} via http://{bad}/maj sinon votre compte sera fermé.'),
    ('bank_login', 'en', 'email', 'Dear {bank} customer, your card has been temporarily limited. Restore access by confirming your details at https://{bad}/secure'),
    ('utility', 'fr', 'sms', 'ENEO INFO : facture impayée de {amt} FCFA. Votre électricité sera coupée aujourd\'hui à {time}. Payez immédiatement sur {bad}'),
    ('utility', 'en', 'sms', 'ENEO: unpaid bill of {amt} FCFA. Power will be cut today at {time}. Pay now at http://{bad} to avoid disconnection.'),
    ('fake_job', 'fr', 'whatsapp', 'OFFRE D\'EMPLOI : recrutement de {job}s à {city}, salaire 250 000 FCFA. Frais d\'inscription {fee} FCFA à envoyer au {phone}. Places limitées !'),
    ('fake_job', 'fr', 'whatsapp', 'Gagnez {amt} FCFA par jour en aimant des vidéos depuis votre téléphone ! Inscription : {fee} FCFA sur WhatsApp au {phone}.'),
    ('fake_job', 'en', 'whatsapp', 'URGENT HIRING: {job} in {city}, 300,000 FCFA monthly. Pay {fee} FCFA registration fee to {phone} to secure your place.'),
    ('fake_relative', 'fr', 'whatsapp', 'Maman c\'est moi {name}, j\'ai changé de numéro. Je suis dans un problème, envoie-moi {amt} FCFA urgent sur ce numéro, je t\'explique après. Ne m\'appelle pas.'),
    ('fake_relative', 'pcm', 'whatsapp', 'Na me {name}, I don change number. Abeg send me {amt} FCFA quick quick for this number, I go explain you later. No call me now.'),
    ('fake_relative', 'en', 'sms', 'Hi it\'s {name}, my phone is broken, this is my new number. I need {amt} FCFA urgently for the hospital, please send via {op} now.'),
    ('wrong_transfer', 'fr', 'sms', 'Bonjour, j\'ai envoyé {amt} FCFA sur votre compte {op} par erreur. Svp renvoyez-les au {phone}, c\'est l\'argent de l\'hôpital de mon enfant.'),
    ('wrong_transfer', 'en', 'sms', 'Hello, I mistakenly sent {amt} FCFA to your {op} account. Please kindly return it to {phone}, it is for my school fees.'),
    ('delivery', 'fr', 'sms', 'DHL : votre colis est bloqué à la douane de {city}. Payez {fee} FCFA de frais sur http://{bad} sous {hours} sinon il sera retourné.'),
    ('delivery', 'en', 'email', 'Your parcel could not be delivered in {city}. Confirm your address and pay a {fee} FCFA fee at https://{bad}/track'),
    ('gov_refund', 'fr', 'email', 'CNPS : vous avez droit à un remboursement de {amt} FCFA. Remplissez le formulaire sur https://{bad} avec votre numéro de carte bancaire.'),
    ('gov_refund', 'fr', 'email', 'Direction Générale des Impôts : un trop-perçu de {amt} FCFA vous est dû. Confirmez vos coordonnées bancaires sur http://{bad} avant {day}.'),
    ('sim_swap', 'fr', 'sms', '{op} : votre carte SIM sera désactivée dans {hours}. Envoyez votre numéro CNI et le code reçu par SMS au {phone} pour la conserver.'),
    ('investment', 'fr', 'whatsapp', 'Investissez {fee} FCFA et recevez {amt} FCFA en 48h garanti ! Des centaines de Camerounais gagnent déjà. Contactez le {phone} vite.'),
    ('investment', 'en', 'whatsapp', 'Crypto opportunity: invest {fee} FCFA today and get {amt} FCFA in 3 days, 100% guaranteed. Join now via {bad}'),
]

# label 0 - includes hard negatives (codes, amounts, official links, urgency that is genuine)
LEGIT = [
    ('momo_receipt', 'fr', 'sms', 'Transfert reçu de {amt} FCFA de {name}. Nouveau solde : {amt} FCFA. ID de transaction : {ref}. Merci d\'utiliser {op}.'),
    ('momo_receipt', 'fr', 'sms', '{op} : vous avez payé {fee} FCFA chez {shop}. Frais : 0 FCFA. Réf : {ref}. Solde disponible : {amt} FCFA.'),
    ('momo_receipt', 'en', 'sms', 'You have received {amt} FCFA from {name}. Your new balance is {amt} FCFA. Transaction ID: {ref}. {op}'),
    ('momo_receipt', 'pcm', 'sms', '{op}: You don receive {amt} FCFA from {name}. Ref {ref}. Thank you.'),
    ('otp_genuine', 'fr', 'sms', 'Votre code de vérification est {code}. Il expire dans 5 minutes. Ne le communiquez à personne, même à un agent {op}.'),
    ('otp_genuine', 'en', 'sms', 'Your {bank} one-time code is {code}. Never share this code with anyone, our staff will never ask for it.'),
    ('bank_info', 'fr', 'email', '{bank} : votre relevé de compte du mois est disponible dans votre application mobile. Pour toute question, appelez le numéro au dos de votre carte.'),
    ('bank_info', 'fr', 'sms', '{bank} : un retrait de {amt} FCFA a été effectué au guichet de {city} le {day} à {time}. Si ce n\'est pas vous, appelez le service client.'),
    ('bank_info', 'en', 'email', 'Dear customer, {bank} branches will close at {time} on {day_en} for inventory. Our mobile app remains available.'),
    ('official_link', 'fr', 'sms', '{op} : découvrez nos nouveaux forfaits internet sur https://{good} ou composez le menu habituel. Stop pub : répondez STOP.'),
    ('official_link', 'en', 'email', 'Your monthly bill is available on https://{good}. Pay through your usual channel before the due date.'),
    ('utility_real', 'fr', 'sms', 'ENEO informe ses clients de {city} d\'une interruption programmée de courant le {day} de {time} à 16h pour travaux. Merci de votre compréhension.'),
    ('delivery_real', 'fr', 'sms', 'Bonjour {name}, votre commande {shop} sera livrée {day} entre {time} et 18h. Le livreur vous appellera à son arrivée.'),
    ('delivery_real', 'en', 'sms', 'Your {shop} order has shipped and will arrive in {city} on {day_en}. Track it in your account.'),
    ('personal', 'fr', 'whatsapp', 'Salut {name}, on se retrouve {day} à {time} au marché central de {city} ? Dis-moi si ça te va.'),
    ('personal', 'fr', 'whatsapp', 'Bonjour maman, je suis bien arrivé à {city}. Je t\'appelle ce soir après le travail. Bisous.'),
    ('personal', 'pcm', 'whatsapp', 'How far {name}? Make we meet for {city} {day_en} for {time}. I go call you.'),
    ('personal', 'en', 'sms', 'Hi {name}, the family meeting is on {day_en} at {time} in {city}. Please bring the photos.'),
    ('work', 'fr', 'email', 'Bonjour à tous, la réunion d\'équipe est reportée au {day} à {time}. Merci de préparer vos rapports d\'activité.'),
    ('work', 'en', 'email', 'Hello team, please find attached the minutes of {day_en}\'s meeting. The next review is at {time}.'),
    ('school', 'fr', 'sms', 'Les parents d\'élèves sont conviés à une réunion le {day} à {time} à l\'établissement. La présence de tous est souhaitée.'),
    ('money_family', 'fr', 'whatsapp', 'Papa je t\'ai envoyé {amt} FCFA par {op} pour les médicaments de grand-mère, tu confirmes réception ?'),
    ('money_family', 'en', 'whatsapp', '{name}, I sent the {amt} FCFA for the rent this morning, check your {op} and confirm please.'),
    ('promo_real', 'fr', 'sms', '{shop} : -20% sur les produits frais ce {day} dans votre magasin de {city}. Offre valable dans la limite des stocks.'),
    ('security_tip', 'fr', 'sms', '{op} vous rappelle : ne communiquez jamais votre code PIN, même à une personne se présentant comme un agent. En cas de doute appelez le service client.'),
    ('security_tip', 'en', 'sms', '{bank} will never ask for your password or code by SMS, email or phone. Report suspicious messages to our customer service.'),
    ('appointment', 'fr', 'sms', 'Rappel : votre rendez-vous à l\'hôpital de {city} est prévu le {day} à {time}. Merci de venir 15 minutes en avance.'),
    ('appointment', 'en', 'sms', 'Reminder: your appointment at the {bank} branch is on {day_en} at {time}. For questions, call the number on your card.'),
]

# Independent hand-written test messages (never generated, never used for training)
CHALLENGE = [
    (1, 'fr', 'Votre compte Orange Money a été suspendu pour raison de sécurité. Rendez-vous sur orange-money-cm.webflow.io pour le réactiver.'),
    (1, 'fr', 'Bonsoir, suite à une erreur système, votre prime de fidélité MTN de 35 000 F est en attente. Validez avec le code reçu en répondant à ce message.'),
    (1, 'fr', 'Madame, je suis le notaire de feu votre oncle. Un héritage de 45 millions vous revient, il faut payer les frais de succession d\'abord.'),
    (1, 'fr', 'Le Ministère recrute 500 jeunes pour le programme d\'emploi 2026. Envoyez 10 000 F pour valider votre dossier au 6 94 22 11 00.'),
    (1, 'en', 'Your Netflix subscription payment failed. Update your card within 24 hours at netflix-billing-cm.com to keep watching.'),
    (1, 'en', 'We noticed a login to your WhatsApp from a new device. If this wasn\'t you, send us the 6-digit code you just received.'),
    (1, 'pcm', 'My broda, na Orange promo, you don win phone and 100k. Just send 5k for delivery fee make dem bring am for your house.'),
    (1, 'fr', 'Alerte UBA : tentative de connexion bloquée. Validez votre identité avec votre code secret sur uba-cm-securite.net'),
    (1, 'fr', 'Bonjour, je vous ai transféré 25 000 F par erreur, c\'est pour l\'école de ma fille, aidez-moi à les récupérer au 6 80 12 34 56 svp.'),
    (1, 'en', 'Dear beneficiary, you have been selected for the World Bank COVID relief fund of $5,000. Reply with your full name and ID card number.'),
    (1, 'fr', 'Colis Chronopost en attente : payez 1 500 FCFA de frais de réexpédition ici http://chrono-livraison-cm.info avant ce soir.'),
    (1, 'fr', 'Rejoignez notre groupe d\'investissement : dépôt minimum 20 000 F, retour garanti 300% en une semaine. Places très limitées !!'),
    (0, 'fr', 'Transaction réussie. Vous avez envoyé 12 000 FCFA à ESSOMBA Martin. Frais 150 FCFA. Nouveau solde 8 450 FCFA.'),
    (0, 'fr', 'Votre code de confirmation Jumia est 773512. Ne le partagez avec personne.'),
    (0, 'fr', 'Chers abonnés, suite à des travaux, le réseau internet sera perturbé à Bonamoussadi cette nuit de 1h à 4h. Nous nous excusons pour la gêne.'),
    (0, 'en', 'Hey, are we still on for football on Saturday? Bring the ball, I forgot mine at the office.'),
    (0, 'fr', 'Bonjour Monsieur, je vous confirme la livraison des sacs de ciment demain matin à Mvog-Mbi. Merci de préparer le reste du paiement.'),
    (0, 'pcm', 'I don reach house. Tell mama say I go come Sunday for the njangi meeting.'),
    (0, 'fr', 'Rappel : la cotisation de la tontine est due ce samedi. Merci de verser votre part au trésorier comme d\'habitude.'),
    (0, 'en', 'Your electricity bill for September is 18 450 FCFA. You can pay at any ENEO agency or through your usual mobile money menu.'),
    (0, 'fr', 'Le cours de mathématiques de demain est déplacé en salle B12. Pensez à apporter vos calculatrices.'),
    (0, 'fr', 'Félicitations pour ton admission au concours ! Toute la famille est fière de toi, on fête ça dimanche.'),
    (0, 'en', 'Your appointment is confirmed for Tuesday 10:00 at the Douala branch. Please bring your ID card.'),
    (0, 'fr', 'Bonjour, votre carte bancaire expire le mois prochain. La nouvelle carte est disponible dans votre agence habituelle.'),
]


def fill(template: str) -> str:
    return template.format(**{k: rng.choice(v) for k, v in SLOTS.items()})


def synthetic_rows() -> list[dict]:
    rows = []
    for label, table in ((1, PHISHING), (0, LEGIT)):
        # Hold out whole templates for the test set (per label), so test messages are never
        # near-copies of training messages
        ids = list(range(len(table)))
        rng.shuffle(ids)
        test_ids = set(ids[:max(2, round(len(ids) * TEST_TEMPLATE_SHARE))])
        for i, (family, lang, channel, template) in enumerate(table):
            seen = set()
            for _ in range(VARIANTS * 3):
                text = fill(template)
                if text in seen:
                    continue
                seen.add(text)
                rows.append({'text': text, 'label': label, 'lang': lang, 'channel': channel, 'family': family,
                             'template': f'{"p" if label else "l"}{i}', 'source': 'synthetic',
                             'split': 'test' if i in test_ids else 'train'})
                if len(seen) >= VARIANTS:
                    break
    return rows


def challenge_rows() -> list[dict]:
    return [{'text': text, 'label': label, 'lang': lang, 'channel': 'mixed', 'family': 'challenge', 'template': f'c{i}',
             'source': 'challenge', 'split': 'test'} for i, (label, lang, text) in enumerate(CHALLENGE)]


def uci_rows() -> list[dict]:
    os.makedirs(RAW, exist_ok=True)
    path = os.path.join(RAW, 'SMSSpamCollection')
    if not os.path.exists(path):
        import urllib.request
        print('Downloading the UCI SMS Spam Collection...')
        data = urllib.request.urlopen(UCI_URL, timeout=60).read()
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            with open(path, 'wb') as fh:
                fh.write(zf.read('SMSSpamCollection'))
    rows = []
    with open(path, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            tag, _, text = line.rstrip('\n').partition('\t')
            if text:
                rows.append({'text': text, 'label': 1 if tag == 'spam' else 0, 'lang': 'en', 'channel': 'sms',
                             'family': 'uci', 'template': '', 'source': 'uci_sms', 'split': ''})
    # Stratified 80/20 split
    for label in (0, 1):
        subset = [r for r in rows if r['label'] == label]
        rng.shuffle(subset)
        cut = int(len(subset) * 0.8)
        for j, r in enumerate(subset):
            r['split'] = 'train' if j < cut else 'test'
    return rows


def admin_rows() -> list[dict]:
    """Human decisions from the review queue (needs the database)."""
    sys.path.insert(0, os.path.dirname(HERE))
    from app import create_app
    from app.models import Analysis
    app = create_app()
    rows = []
    with app.app_context():
        for a in Analysis.query.filter(Analysis.review_label.isnot(None), Analysis.review_source == 'admin').all():
            if a.text_source and len(a.text_source) > 15:
                rows.append({'text': a.text_source, 'label': 1 if a.review_label == 'phishing' else 0, 'lang': '',
                             'channel': a.source or 'web', 'family': 'admin', 'template': f'a{a.id}',
                             'source': 'admin', 'split': 'test' if a.id % 5 == 0 else 'train'})
    return rows


def main():
    rows = synthetic_rows() + challenge_rows()
    if '--no-uci' not in sys.argv:
        try:
            rows += uci_rows()
        except Exception as exc:  # offline: the corpus still builds without it
            print(f'UCI dataset skipped ({exc})')
    if '--with-db' in sys.argv:
        rows += admin_rows()
    with open(OUT, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=['text', 'label', 'lang', 'channel', 'family', 'template', 'source', 'split'])
        writer.writeheader()
        writer.writerows(rows)
    from collections import Counter
    stats = Counter((r['source'], r['split'], r['label']) for r in rows)
    print(f'Wrote {len(rows)} messages to {OUT}')
    for key in sorted(stats):
        print('  source=%-10s split=%-5s label=%s : %d' % (*key, stats[key]))


if __name__ == '__main__':
    main()
