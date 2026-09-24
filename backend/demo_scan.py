"""
Run the v2 pipeline on sample messages and print the result.

    python demo_scan.py              # built-in samples
    python demo_scan.py path/to.eml  # analyse an .eml file

Needs no database or server. Set ANTHROPIC_API_KEY in .env to enable the AI signal.
"""

import sys

from dotenv import load_dotenv

load_dotenv()

from app.pipeline import ParseError, run_pipeline  # noqa: E402

SAMPLES = {
    "Fausse alerte MTN (SMS)": (
        "Cher client MTN, votre compte Mobile Money a ete temporairement bloque pour "
        "verification. Cliquez ici pour le reactiver dans les 24h : "
        "http://mtn-secure-cm.tk/verify. Ne pas repondre a ce message."
    ),
    "Faux agent Orange (WhatsApp)": (
        "Bonjour je suis agent Orange Money, votre compte presente une anomalie. "
        "Envoyez moi votre code PIN pour le securiser urgent sinon il sera suspendu."
    ),
    "Offre d'emploi frauduleuse": (
        "RECRUTEMENT MINFOPRA 2026 : 500 postes disponibles. Envoyez 10 000 FCFA de frais "
        "de dossier au 677 12 34 56 avant vendredi. Infos : https://bit.ly/recrut-cm"
    ),
    "Vrai message MTN": (
        "MTN MoMo: Vous avez recu 5000 FCFA de JEAN. Nouveau solde: 25000 FCFA. "
        "Transaction ID: 8845521. *126#"
    ),
    "Message personnel": "Salut, on se retrouve toujours a 14h demain pour la reunion ?",
}

EMAIL_SAMPLE = b"""From: "MTN Cameroon" <support@mtnmobil3money.com>
Reply-To: recover@gmail-secure.xyz
To: client@example.cm
Subject: URGENT - Compte MoMo suspendu
Authentication-Results: mx.example.cm; spf=fail smtp.mailfrom=mtnmobil3money.com; dkim=none; dmarc=fail
Content-Type: text/html; charset=utf-8

<p>Votre compte sera <b>suspendu</b>. Confirmez votre mot de passe ici :
<a href="http://192.168.4.20/login">www.mtn.cm/secure</a></p>
"""

ICONS = {"Critical": "🚨", "High": "🔴", "Medium": "🟠", "Low": "🟢"}


def show(title, result):
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")
    print(f"{ICONS[result['verdict']]} {result['verdict'].upper()}  —  score {result['score']}/100"
          f"  ({result['duration_ms']} ms)")
    signals = ", ".join(
        f"{k}={v if v is not None else 'n/a'} (poids {result['weights'].get(k, 0):.0%})"
        for k, v in result["signals"].items())
    print(f"Signaux : {signals}")
    for override in result["overrides"]:
        print(f"⚖️  {override}")
    if result["ai"]:
        ai = result["ai"]
        print(f"IA ({result['ai_model']}) : {ai['classification']} / {ai['category']} ({ai['confidence']}%)")
    print("Indices :")
    for item in result["evidence"][:12] or ["(aucun)"]:
        print(f"  • {item}")
    print(f"👉 {result['recommendation']}")


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], "rb") as fh:
            show(sys.argv[1], run_pipeline(raw_eml=fh.read()))
        return
    for title, text in SAMPLES.items():
        show(title, run_pipeline(text=text))
    show("E-mail usurpant MTN (.eml)", run_pipeline(raw_eml=EMAIL_SAMPLE))
    try:
        run_pipeline(text="ok")
    except ParseError as exc:
        print(f"\nMessage vide/court → erreur contrôlée : {exc}")


if __name__ == "__main__":
    main()
