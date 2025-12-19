from google import genai

# 👇 Replace with your real API key
API_KEY = "AIzaSyCrBXHCB5YgP6jv5agvOEzmwcRUhULQkaM"

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-2.5-flash"  # Supported cloud model

def ask_tutor(question):
    # system instruction includes asking guiding questions and giving the final answer
    system_instruction = f"""
You are a kind tutor for children aged 8 to 16.
Explain step by step.
Ask guiding questions to help the student think.
Use simple words.
Encourage effort.
At the end, always give the final answer clearly.
Student question: {question}
Tutor response:
"""
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=system_instruction
    )
    return response.text

print("AI Tutor is ready! Type your question or 'quit' to exit.")

while True:
    user_question = input("\nAsk the tutor: ")
    if user_question.lower() == "quit":
        break
    reply = ask_tutor(user_question)
    print("\nTutor:\n", reply)
