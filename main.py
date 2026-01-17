from fastapi import FastAPI, Request
import requests
import os
from seguradoras import SEGURADORAS

app = FastAPI()

WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")

MENU_HEADER = (
    "Olá! 👋\n"
    "No momento estamos fora do horário de atendimento.\n\n"
    "Selecione sua seguradora:\n"
)

DIGIT_TO_KEYCAP = {
    "0": "0️⃣",
    "1": "1️⃣",
    "2": "2️⃣",
    "3": "3️⃣",
    "4": "4️⃣",
    "5": "5️⃣",
    "6": "6️⃣",
    "7": "7️⃣",
    "8": "8️⃣",
    "9": "9️⃣",
}

def format_keycap_number(number_str: str) -> str:
    return "".join(DIGIT_TO_KEYCAP.get(d, d) for d in number_str)

def build_menu() -> str:
    items = [
        f"{format_keycap_number(key)} {info['nome']}"
        for key, info in sorted(SEGURADORAS.items(), key=lambda kv: int(kv[0]))
    ]
    return MENU_HEADER + "\n".join(items)

def enviar_mensagem(chat_id: str, texto: str):
    url = "https://gate.whapi.cloud/messages/text"
    headers = {
        "Authorization": f"Bearer {WHAPI_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": chat_id,
        "body": texto
    }
    requests.post(url, headers=headers, json=payload)

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    message = data.get("message", {})
    chat_id = message.get("chatId")
    text = message.get("body", "").strip()

    if not chat_id or not text:
        return {"status": "ignored"}

    # Usuário escolheu opção
    if text in SEGURADORAS:
        seguradora = SEGURADORAS[text]
        enviar_mensagem(
            chat_id,
            f"📞 {seguradora['nome']}\nTelefone: {seguradora['telefone']}"
        )
        return {"status": "ok"}

    # Qualquer outra coisa → menu
    enviar_mensagem(chat_id, build_menu())
    return {"status": "ok"}
