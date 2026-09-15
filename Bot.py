
import os
import requests
from flask import Flask, jsonify, request
from google import genai

app = Flask(__name__)

# Read keys from Render's Environment Variables
GOOGLE_API_KEY = os.environ.get(
    "GOOGLE_API_KEY", "AQ.Ab8RN6KBOyVJQr-WY84p7DvOlug7dn-aweHb0QO3z_rEGebz6w"
)
WHATSAPP_TOKEN = os.environ.get(
    "WHATSAPP_TOKEN",
    "WAAVgkLvKl4M9Ry2U2dr4ZCEhFw0yyKnQQvenRwCtBhczbEwDOCik3pKGlQZCBlL7FCGdZAMwyEZCaktLltMVuT141lCyvvLWkAuNPYY6QsZBtxkmbobbbEE3HwmadWTWdmBZC65xxJ7HjUR9NNEwGwtVFUXNnAGdAZAFGuHMGdhaMoLAT9sZD",
)

MODEL_ID = "gemma-4-31b-it"

client = genai.Client(api_key=GOOGLE_API_KEY)


def ask_gemma(prompt: str) -> str:
    try:
        response = client.models.generate_content(
            model=MODEL_ID, contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Error querying Gemma: {e}")
        return "Sorry, I had trouble processing that request."


def send_whatsapp_reply(recipient_id: str, message_text: str):
    url = "https://graph.facebook.com/v21.0/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_id,
        "type": "text",
        "text": {"body": message_text},
    }
    requests.post(url, headers=headers, json=payload)


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if messages:
            msg = messages[0]
            sender_id = msg.get("from")
            user_text = msg.get("text", {}).get("body")

            if user_text and sender_id:
                reply = ask_gemma(user_text)
                send_whatsapp_reply(sender_id, reply)
    except Exception as e:
        print(f"Webhook error: {e}")

    return jsonify({"status": "success"}), 200


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    challenge = request.args.get("hub.challenge")
    return challenge if challenge else ("OK", 200)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
