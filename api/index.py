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
    print("WEBHOOK:", data)

    # 1️⃣ ignora qualquer coisa que não seja mensagem
    if "messages" not in data:
        return {"status": "ignored_not_message"}

    message = data["messages"][0]

    # 2️⃣ ignora mensagens do próprio bot
    if message.get("from_me"):
        return {"status": "ignored_from_me"}

    # 3️⃣ ignora mensagens de grupo
    # grupos sempre terminam com @g.us
    chat_id = message.get("chat_id") or message.get("from")
    if chat_id and chat_id.endswith("@g.us"):
        return {"status": "ignored_group"}

    # 4️⃣ pega o número corretamente
    from_number = message.get("from")

    # 5️⃣ pega texto (todos formatos possíveis)
    text = (
        message.get("text", {}).get("body")
        or message.get("text")
        or ""
    ).strip()

    if not text:
        return {"status": "ignored_no_text"}

    # 6️⃣ lógica do bot
    if text in SEGURADORAS:
        seguradora = SEGURADORAS[text]
        reply = (
            f"📞 {seguradora['nome']}\n"
            f"Telefone: {seguradora['telefone']}"
        )
    else:
        reply = build_menu()

    # 7️⃣ envia resposta
    send_message(from_number, reply)

    return {"status": "sent"}
