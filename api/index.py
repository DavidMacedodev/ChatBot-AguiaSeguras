from fastapi import FastAPI, Request
from seguradoras import SEGURADORAS

app = FastAPI()

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

@app.post("/api/webhook")
async def webhook(request: Request):
    data = await request.json()

    message = (
        data.get("messages", [{}])[0]
        .get("text", {})
        .get("body", "")
        .strip()
    )

    if message in SEGURADORAS:
        seguradora = SEGURADORAS[message]
        return {
            "reply": (
                f"📞 {seguradora['nome']}\n"
                f"Telefone: {seguradora['telefone']}"
            )
        }

    return {"reply": build_menu()}
