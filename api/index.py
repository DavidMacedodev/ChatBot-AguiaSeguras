from fastapi import FastAPI, Request
import requests
import os
from seguradoras import SEGURADORAS

app = FastAPI()

WHAPI_TOKEN = os.environ["WHAPI_TOKEN"]
WHAPI_URL = "https://gate.whapi.cloud/messages/text"

MENU_HEADER = (
    "Olá! 👋\n"
    "No momento estamos fora do horário de atendimento.\n\n"
    "Selecione sua seguradora:\n"
)

DIGIT_TO_KEYCAP = {
    "0": "0️⃣", "1": "1️⃣", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣",
    "5": "5️⃣", "6": "6️⃣", "7": "7️⃣", "8": "8️⃣", "9": "9️⃣",
}

def format_keycap_number(number_str: str) -> str:
    return "".join(DIGIT_TO_KEYCAP.get(d, d) for d in number_str)

def build_menu() -> str:
    items = [
        f"{format_keycap_number(k)} {v['nome']}"
        for k, v in sorted(SEGURADORAS.items(), key=lambda x: int(x[0]))
    ]
    return MENU_HEADER + "\n".join(items)

def send_message(to: str, text: str):
    requests.post(
        WHAPI_URL,
        headers={
            "Authorization": f"Bearer {WHAPI_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "to": to,
            "body": text,
        },
        timeout=10,
    )

@app.post("/api/webhook")
async def webhook(request: Request):
    data = await request.json()

    message = data.get("messages", [{}])[0]

    # 🚫 ignora mensagens do próprio bot
    if message.get("from_me"):
        return {"status": "ignored_from_me"}

    # 🚫 ignora mensagens sem texto
    if message.get("type") != "chat":
        return {"status": "ignored_type"}

    # 🚫 ignora mensagens antigas / duplicadas
    if message.get("is_forwarded") or message.get("is_status"):
        return {"status": "ignored_duplicate"}

    from_number = message["from"]
    text = message["text"]["body"].strip()

    if text in SEGURADORAS:
        seguradora = SEGURADORAS[text]
        reply = (
            f"📞 {seguradora['nome']}\n"
            f"Telefone: {seguradora['telefone']}"
        )
    else:
        reply = build_menu()

    send_message(from_number, reply)

    return {"status": "sent"}

