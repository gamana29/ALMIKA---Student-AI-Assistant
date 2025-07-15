import json
import requests

# ✅ Replace with your OpenRouter key
API_KEY = "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"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "mistralai/mistral-7b-instruct"

def load_faq(path='data/faq_data.json'):
    with open(path, 'r') as file:
        return json.load(file)

def generate_gpt_response(question, faq_data):
    context = "\n".join([f"Q: {item['question']}\nA: {item['answer']}" for item in faq_data])

    prompt = f"""You are a helpful student assistant.
Use the following FAQs to answer the student's question accurately:

{context}

Student: {question}
Answer:"""

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5
    }

    response = requests.post(API_URL, headers=headers, json=data)
    result = response.json()

    return result['choices'][0]['message']['content'].strip()
