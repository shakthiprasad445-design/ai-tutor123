from flask import Flask, render_template, request, session, redirect, url_for
from google import genai
from google.genai.errors import ClientError
import time
import os
# ---------------- CONFIG ----------------

API_KEY = os.environ.get("GEMINI_API_KEY")

MODEL_NAME = "gemini-2.5-flash"

MAX_MESSAGES = 6  # keep last 3 Q&A only

# ----------------------------------------

client = genai.Client(api_key=API_KEY)

app = Flask(__name__)
app.secret_key = "chat-secret-key"

# ---------------- HELPERS ----------------

def trim_chat(chat):
    if len(chat) > MAX_MESSAGES:
        return chat[-MAX_MESSAGES:]
    return chat


def ask_tutor(question):
    prompt = f"""
You are a kind tutor for children aged 8 to 16.
Explain step by step using short paragraphs.
Do not use stars or markdown.
At the end clearly write: Final Answer:

Student question: {question}
Tutor response:
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        return response.text.strip()

    except ClientError as e:
        error_text = str(e)

        if "RESOURCE_EXHAUSTED" in error_text or "429" in error_text:
            return (
                "I need a short break because many students are asking questions right now.\n\n"
                "Please wait about 20 seconds and then ask again 😊"
            )

        return "Something went wrong. Please try again in a moment."


# ---------------- ROUTES ----------------

@app.route("/", methods=["GET", "POST"])
def home():
    if "chat" not in session:
        session["chat"] = []

    # STEP 1: user submits question
    if request.method == "POST":
        session["pending_question"] = request.form["question"]
        session["thinking"] = True
        session.modified = True
        return redirect(url_for("home"))

    # STEP 2: thinking → generate answer
    if session.get("thinking"):
        question = session.pop("pending_question", None)
        session["thinking"] = False

        if question:
            # append user question ONCE
            session["chat"].append(("user", question))
            session["chat"] = trim_chat(session["chat"])

            tutor_reply = ask_tutor(question)

            # append tutor reply
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
    app.run(debug=True)
