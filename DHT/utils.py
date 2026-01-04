import requests
from django.conf import settings


def send_telegram(text: str) -> bool:
    """
    Envoie un message Telegram via l'API officielle.
    Retourne True si OK, sinon False et affiche l'erreur.
    """
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", None)

    if not token or not chat_id:
        print("❌ Telegram: TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID manquant dans settings.py")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        r = requests.post(
            url,
            data={"chat_id": chat_id, "text": text},
            timeout=10
        )

        if not r.ok:
            print(f"❌ Telegram HTTP {r.status_code}: {r.text}")
            return False

        print("✅ Telegram OK")
        return True

    except Exception as e:
        print("❌ Erreur Telegram :", e)
        return False
