import os, time, requests

BOT_TOKEN  = os.environ["BOT_TOKEN"]
GEMINI_KEY = os.environ["GEMINI_KEY"]

SYSTEM_PROMPT = (
    "Отвечай простым текстом без форматирования: без звёздочек, решёток, "
    "знаков доллара, LaTeX и Markdown. Будь кратким и понятным."
)

def gemini(text):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-3.8-flash:generateContent?key={GEMINI_KEY}"
    )
    body = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024}
    }
    headers = {"x-goog-api-key": GEMINI_KEY}
    r = requests.post(url, json=body, headers=headers, timeout=30)
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"]["message"])
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()

def send(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=10
    )

def main():
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook", timeout=10)
    print("Bot started!")
    offset = 0
    while True:
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 25},
                timeout=35
            ).json()
            for upd in r.get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message", {})
                text = msg.get("text", "")
                chat_id = msg.get("chat", {}).get("id")
                name = msg.get("from", {}).get("first_name", "друг")
                if not text or not chat_id:
                    continue
                print(f"Message from {name}: {text}")
                if text.startswith("/start"):
                    send(chat_id, f"Привет, {name}! Я AI-бот на базе Google Gemini. Задай любой вопрос!")
                elif text.startswith("/help"):
                    send(chat_id, "Просто напиши вопрос и я отвечу. Powered by Google Gemini.")
                else:
                    for attempt in range(3):
                        try:
                            answer = gemini(text)
                            send(chat_id, answer)
                            break
                        except Exception as e:
                            if attempt < 2:
                                time.sleep(5)
                            else:
                                send(chat_id, "Gemini сейчас перегружен, попробуй через минуту.")
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
