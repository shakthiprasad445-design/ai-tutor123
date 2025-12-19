from flask import Flask, render_template, request, session, redirect, url_for
from google import genai
from google.genai.errors import ClientError
import os
import time

# ---------------- CONFIG ----------------

API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"

MAX_MESSAGES = 6
COOLDOWN_SECONDS = 30

# ----------------------------------------

client = genai.Client(api_key=API_KEY)

app = Flask(__name__)
app.secret_key = "chat-secret-key"

# ---------------- HELPERS ----------------

def trim_chat(chat):
    return chat[-MAX_MESSAGES:]


def ask_tutor(question):
    prompt = f"""
You are a kind tutor for children aged 8 to 16.
Explain step by step using short paragraphs.
Do not use stars or markdown.
At the end clearly write: Final Answer:

Student question: {question}
Tutor response:
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )
    return response.text.strip()


# ---------------- ROUTES ----------------

@app.route("/", methods=["GET", "POST"])
def home():
    if "chat" not in session:
        session["chat"] = []

    if request.method == "POST":
        session["pending_question"] = request.form["question"]
        session["thinking"] = True
        session.modified = True
        return redirect(url_for("home"))

    if session.get("thinking"):
        session["thinking"] = False
        question = session.pop("pending_question", None)

        if question:
            session["chat"].append(("user", question))
            session["chat"] = trim_chat(session["chat"])

            now = time.time()
            cooldown_until = session.get("cooldown_until", 0)

            if now < cooldown_until:
                wait = int(cooldown_until - now)
                tutor_reply = (
                    f"I need a short break right now.\n\n"
                    f"Please wait about {wait} seconds and ask again 😊"
                )
            else:
                try:
                    tutor_reply = ask_tutor(question)
                except ClientError as e:
                    if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                        session["cooldown_until"] = time.time() + COOLDOWN_SECONDS
                        tutor_reply = (
                            "I need a short break because many students are asking questions right now.\n\n"
                            "Please wait about 30 seconds and then ask again 😊"
                        )
                    else:
                        tutor_reply = "Something went wrong. Please try again."

            session["chat"].append(("tutor", tutor_reply))
            session["chat"] = trim_chat(session["chat"])
            session.modified = True

        return redirect(url_for("home"))

    return render_template(
        "index.html",
        chat=session["chat"],
        thinking=session.get("thinking", False)
    )


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run()
