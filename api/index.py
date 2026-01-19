from fastapi import FastAPI, Request
import requests
import os
from datetime import datetime, time
import pytz
from seguradoras import SEGURADORAS

app = FastAPI()

WHAPI_TOKEN = os.environ["WHAPI_TOKEN"]
WHAPI_URL = "https://gate.whapi.cloud/messages/text"

BR_TZ = pytz.timezone("America/Sao_Paulo")

MENU_HEADER = (
    "Olá! Aqui é Jessé da Águia Seguros.\n\n"
    "No momento estou fora do horário de atendimento.\n\n"
    "Caso esteja precisando de assistência 24hrs como: "
    "*Táxi*, *hotel*, *guincho*, *socorro mecânico* ou *elétrico*, "
    "envie o número *conforme a sua seguradora* para que eu te envie o número de assistência!\n\n"
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
    print(f"📤 Enviando mensagem para {to}")
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

def is_outside_business_hours() -> bool:
    now = datetime.now(BR_TZ)
    weekday = now.weekday()  # 0=segunda, 6=domingo
    current_time = now.time()


    # fim de semana → sempre ativo
    if weekday >= 5:
        return True

    # dias úteis
    start_business = time(7, 30)
    end_business = time(18, 0)

    # fora do horário comercial
    return current_time < start_business or current_time >= end_business

@app.post("/api/webhook")
async def webhook(request: Request):
    data = await request.json()

    if "messages" not in data:
        return {"status": "ignored_not_message"}

    message = data["messages"][0]

    if message.get("from_me"):
        return {"status": "ignored_from_me"}

    chat_id = message.get("chat_id") or message.get("from")
    if chat_id and chat_id.endswith("@g.us"):
        return {"status": "ignored_group"}

    from_number = message.get("from")

    text = (
        message.get("text", {}).get("body")
        or message.get("text")
        or ""
    ).strip()

    if not text:
        return {"status": "ignored_no_text"}

    # ⛔ dentro do horário comercial → bot não responde
    if not is_outside_business_hours():
        print("🛑 Dentro do horário comercial. Bot ignorou.")
        return {"status": "ignored_business_hours"}

    # 🤖 fora do horário → bot ativo
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
