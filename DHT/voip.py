import socket
import time
from django.conf import settings


def trigger_sip_alert(user_extension: str | None = None) -> bool:
    """
    Déclenche un appel via Asterisk AMI.
    Retourne True si la commande AMI est envoyée, sinon False.
    Sécurisé: si VOIP_ENABLED=False => ne fait rien.
    """
    if not getattr(settings, "VOIP_ENABLED", False):
        return False

    host = getattr(settings, "ASTERISK_AMI_HOST", "127.0.0.1")
    port = int(getattr(settings, "ASTERISK_AMI_PORT", 5038))
    ami_user = getattr(settings, "ASTERISK_AMI_USER", "")
    ami_pass = getattr(settings, "ASTERISK_AMI_PASSWORD", "")
    target = user_extension or getattr(settings, "SIP_TARGET_EXTENSION", "6001")

    if not ami_user or not ami_pass:
        print("❌ VOIP: AMI user/pass manquants dans settings.py")
        return False

    # IMPORTANT:
    # On appelle SIP/<target> puis on route vers l’extension 777 (message audio) dans le contexte "biot_appel"
    actions = [
        "Action: Login",
        f"Username: {ami_user}",
        f"Secret: {ami_pass}",
        "",
        "Action: Originate",
        f"Channel: SIP/{target}",
        "Context: biot_appel",
        "Exten: 777",
        "Priority: 1",
        'CallerID: "Alerte IoT" <999>',
        "Async: yes",
        "",
        "Action: Logoff",
        "",
    ]

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((host, port))

        for line in actions:
            s.send((line + "\r\n").encode("utf-8"))
            time.sleep(0.05)

        _ = s.recv(1024)
        s.close()
        print(f"✅ VOIP: ordre d'appel envoyé vers extension {target}")
        return True

    except Exception as e:
        print(f"❌ VOIP: erreur connexion AMI ({host}:{port}) : {e}")
        return False
