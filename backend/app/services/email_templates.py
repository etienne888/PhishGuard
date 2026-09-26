"""
HTML email templates.

Emails use table layout and inline styles only: Gmail, Outlook and mobile
clients strip <style> blocks and ignore flexbox/grid.
"""

from datetime import datetime, timedelta, timezone
from html import escape

# Cameroon time (WAT, UTC+1, no DST)
WAT = timezone(timedelta(hours=1))
LOGO_CID = "phishguard-logo"


def verification_code_email(name: str, code: str, minutes: int = 5) -> tuple[str, str, str]:
    """Return (subject, plain_text, html) for a one-time verification code."""
    now = datetime.now(WAT)
    expires = (now + timedelta(minutes=minutes)).strftime("%H:%M")
    requested = now.strftime("%d/%m/%Y à %H:%M")
    spaced = f"{code[:3]} {code[3:]}" if len(code) == 6 else code
    safe_name = escape(name)

    subject = f"{code} est votre code de vérification PhishGuard-AI"

    text = (
        f"Bonjour {name},\n\n"
        f"Votre code de vérification PhishGuard-AI est : {spaced}\n\n"
        f"Ce code expire dans {minutes} minutes (à {expires}, heure du Cameroun).\n"
        f"Demande effectuée le {requested}.\n\n"
        "Ne partagez jamais ce code. L'équipe PhishGuard-AI ne vous le demandera "
        "jamais par téléphone, SMS ou WhatsApp.\n\n"
        "Si vous n'êtes pas à l'origine de cette demande, ignorez simplement cet email : "
        "votre compte reste protégé.\n\n"
        "— L'équipe PhishGuard-AI\n"
        "Protéger les citoyens camerounais contre le phishing."
    )

    html = f"""\
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light only">
<title>{subject}</title>
</head>
<body style="margin:0;padding:0;background:#EEF3FA;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1E293B;">
<!-- Preheader: the preview line shown next to the subject in the inbox -->
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">Votre code expire à {expires}. Ne le partagez avec personne.</div>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#EEF3FA;padding:32px 12px;">
<tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;">

  <!-- Brand -->
  <tr><td align="center" style="padding:0 0 20px;">
    <img src="cid:{LOGO_CID}" width="56" height="56" alt="PhishGuard-AI" style="display:block;border:0;">
    <div style="margin-top:8px;font-size:17px;font-weight:800;letter-spacing:-0.2px;color:#0B1C3C;">
      Phish<span style="color:#2563EB;">Guard</span><span style="color:#06B6D4;">-AI</span>
    </div>
  </td></tr>

  <!-- Card -->
  <tr><td style="background:#FFFFFF;border-radius:20px;box-shadow:0 12px 32px rgba(30,64,175,0.10);overflow:hidden;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      <tr><td style="height:5px;background:#2563EB;background-image:linear-gradient(90deg,#2563EB,#06B6D4);font-size:0;line-height:0;">&nbsp;</td></tr>
      <tr><td style="padding:36px 36px 8px;">
        <p style="margin:0 0 6px;font-size:13px;font-weight:600;letter-spacing:1.2px;text-transform:uppercase;color:#2563EB;">Vérification de sécurité</p>
        <h1 style="margin:0 0 16px;font-size:22px;line-height:1.3;color:#0B1C3C;">Bonjour {safe_name},</h1>
        <p style="margin:0;font-size:15px;line-height:1.6;color:#475569;">
          Utilisez le code ci-dessous pour confirmer votre adresse email et sécuriser votre compte PhishGuard-AI.
        </p>
      </td></tr>

      <!-- Code -->
      <tr><td align="center" style="padding:24px 36px;">
        <table role="presentation" cellpadding="0" cellspacing="0" style="background:#F1F6FF;border:1px solid #DBEAFE;border-radius:16px;">
          <tr><td align="center" style="padding:20px 32px 8px;">
            <span style="font-family:'SF Mono',Consolas,'Courier New',monospace;font-size:36px;font-weight:700;letter-spacing:10px;color:#0B1C3C;">{spaced}</span>
          </td></tr>
          <tr><td align="center" style="padding:0 32px 18px;font-size:13px;color:#64748B;">
            &#9201; Expire dans <strong style="color:#0B1C3C;">{minutes} minutes</strong> (à {expires})
          </td></tr>
        </table>
      </td></tr>

      <!-- Security notice -->
      <tr><td style="padding:0 36px 28px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#FFF7ED;border-radius:12px;">
          <tr><td style="padding:14px 16px;font-size:13px;line-height:1.55;color:#9A3412;">
            <strong>&#128274; Ne partagez jamais ce code.</strong> L'équipe PhishGuard-AI ne vous le demandera
            jamais par téléphone, SMS ou WhatsApp. Toute personne qui le réclame tente une arnaque.
          </td></tr>
        </table>
      </td></tr>

      <tr><td style="padding:0 36px 32px;font-size:13px;line-height:1.6;color:#64748B;border-top:1px solid #F1F5F9;">
        <p style="margin:20px 0 0;">
          Vous n'êtes pas à l'origine de cette demande ? Ignorez cet email : aucun changement ne sera
          effectué et votre compte reste protégé.
        </p>
        <p style="margin:12px 0 0;font-size:12px;color:#94A3B8;">Demande effectuée le {requested} (heure du Cameroun).</p>
      </td></tr>
    </table>
  </td></tr>

  <!-- Footer -->
  <tr><td align="center" style="padding:22px 12px 0;font-size:12px;line-height:1.6;color:#94A3B8;">
    <strong style="color:#64748B;">PhishGuard-AI</strong> — Protéger les citoyens camerounais contre le phishing.<br>
    Un message suspect ? Signalez-le au CIRT-CM : 8202 · alerts@cirt.cm<br>
    Cet email a été envoyé automatiquement, merci de ne pas y répondre.
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""
    return subject, text, html


_VERDICT_STYLE = {
    "phishing": ("#DC2626", "#FEF2F2", "&#9888;", "Dangereux : c'est une tentative d'arnaque"),
    "suspicious": ("#D97706", "#FFFBEB", "&#9888;", "Suspect : soyez très prudent"),
    "legitimate": ("#059669", "#ECFDF5", "&#10003;", "Aucune menace détectée"),
}


def verdict_email(name: str, subject_checked: str, verdict: str | None, score: float | None,
                  reasons: list[str], recommendation: str | None, link: str) -> tuple[str, str, str]:
    """Reply to an email forwarded to PhishGuard. `verdict=None`: sign in to see the result."""
    safe_name = escape(name)
    checked = escape(subject_checked or "(sans objet)")
    if verdict is None:
        subject = "Votre analyse PhishGuard-AI est prête"
        headline, colour, bg, icon = "Analyse terminée — connectez-vous pour voir le résultat", "#2563EB", "#EFF6FF", "&#128274;"
        body_html = (
            '<p style="margin:0;font-size:15px;line-height:1.6;color:#475569;">Nous avons analysé le message '
            f'« <strong>{checked}</strong> ». Pour voir le verdict et les conseils, connectez-vous ou créez '
            'votre compte gratuit avec cette adresse email.</p>'
            '<p style="margin:12px 0 0;font-size:13px;color:#9A3412;"><strong>En attendant :</strong> ne cliquez sur '
            'aucun lien et ne communiquez aucun code ni mot de passe.</p>')
        text_body = (f"Bonjour {name},\n\nNous avons analysé « {subject_checked} ». Connectez-vous pour voir "
                     f"le résultat : {link}\n\nEn attendant, ne cliquez sur aucun lien et ne donnez aucun code.")
        button = "Voir le résultat"
    else:
        colour, bg, icon, headline = _VERDICT_STYLE.get(verdict, _VERDICT_STYLE["suspicious"])
        subject = f"[{'DANGER' if verdict == 'phishing' else 'SUSPECT' if verdict == 'suspicious' else 'OK'}] Résultat PhishGuard-AI : {subject_checked or 'message transféré'}"[:150]
        items = "".join(f'<li style="margin:0 0 6px;">{escape(r)}</li>' for r in reasons[:5])
        body_html = (
            f'<p style="margin:0 0 12px;font-size:15px;line-height:1.6;color:#475569;">Message analysé : '
            f'« <strong>{checked}</strong> » — score de risque <strong>{round(score or 0)}/100</strong>.</p>'
            + (f'<ul style="margin:0 0 12px;padding-left:18px;font-size:14px;line-height:1.5;color:#334155;">{items}</ul>' if items else '')
            + (f'<p style="margin:0;padding:12px 14px;background:#F1F6FF;border-radius:12px;font-size:14px;color:#1E3A8A;">'
               f'&#128073; {escape(recommendation)}</p>' if recommendation else ''))
        text_body = (f"Bonjour {name},\n\n{headline}\nMessage : {subject_checked}\nScore : {round(score or 0)}/100\n\n"
                     + "".join(f"- {r}\n" for r in reasons[:5])
                     + (f"\n{recommendation}\n" if recommendation else "") + f"\nDétails : {link}")
        button = "Voir l'analyse complète"

    html = f"""\
<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light only"><title>{escape(subject)}</title></head>
<body style="margin:0;padding:0;background:#EEF3FA;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1E293B;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#EEF3FA;padding:32px 12px;">
<tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:540px;">
  <tr><td align="center" style="padding:0 0 20px;">
    <img src="cid:{LOGO_CID}" width="52" height="52" alt="PhishGuard-AI" style="display:block;border:0;">
  </td></tr>
  <tr><td style="background:#FFFFFF;border-radius:20px;box-shadow:0 12px 32px rgba(30,64,175,0.10);overflow:hidden;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      <tr><td style="height:5px;background:{colour};font-size:0;line-height:0;">&nbsp;</td></tr>
      <tr><td style="padding:30px 32px 6px;">
        <p style="margin:0 0 14px;font-size:15px;color:#0B1C3C;">Bonjour {safe_name},</p>
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{bg};border-radius:14px;">
          <tr><td style="padding:14px 16px;font-size:16px;font-weight:700;color:{colour};">{icon} {headline}</td></tr>
        </table>
      </td></tr>
      <tr><td style="padding:16px 32px 8px;">{body_html}</td></tr>
      <tr><td align="center" style="padding:18px 32px 30px;">
        <a href="{escape(link)}" style="display:inline-block;background:#2563EB;color:#FFFFFF;text-decoration:none;font-weight:600;font-size:14px;padding:12px 26px;border-radius:12px;">{button}</a>
      </td></tr>
    </table>
  </td></tr>
  <tr><td align="center" style="padding:22px 12px 0;font-size:12px;line-height:1.6;color:#94A3B8;">
    Vous avez transféré ce message à PhishGuard-AI pour vérification.<br>
    Signalez les arnaques au CIRT-CM : 8202 · alerts@cirt.cm
  </td></tr>
</table></td></tr></table></body></html>"""
    return subject, text_body, html
