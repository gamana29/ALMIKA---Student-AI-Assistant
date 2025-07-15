import streamlit as st
import base64
import os
import json
import zipfile
import io
import random
from collections import Counter
from chatbot_model import load_faq, generate_gpt_response
import fitz  

st.set_page_config(page_title="Almika - Student Assistant", page_icon="🎓", layout="wide")


def chatbot_page():
    faq_data = load_faq()

    if "history" not in st.session_state:
        st.session_state.history = []
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False
    if "email" not in st.session_state:
        st.session_state.email = ""
    if "selected_question" not in st.session_state:
        st.session_state.selected_question = ""
    if "pdf_text" not in st.session_state:
        st.session_state.pdf_text = ""

    os.makedirs("chat_data", exist_ok=True)

    def load_user_history(email):
        filepath = f"chat_data/{email}.json"
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return json.load(f)
        return []

    def save_user_history(email, history):
        filepath = f"chat_data/{email}.json"
        with open(filepath, "w") as f:
            json.dump(history, f)

    def suggest_followups(question):
        keywords = [word.strip('?.,').lower() for word in question.split() if len(word) > 3]
        random.shuffle(keywords)
        suggestions = [f"Can you explain more about {kw}?" for kw in keywords[:2]]
        suggestions.append("Can you show examples?")
        return suggestions

    def extract_pdf_text(uploaded_file):
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            return "\n".join([page.get_text() for page in doc])


    st.markdown("""
        <style>
        html, body, .stApp {
            font-family: 'Poppins', sans-serif;
            background-color: #fdfdfd;
            color: #222;
        }
        .chat-container {
            max-height: 65vh;
            overflow-y: auto;
            padding: 1rem;
            border-radius: 20px;
            background-color: #f9f9f9;
            box-shadow: 0 3px 20px rgba(0,0,0,0.05);
        }
        .chat-bubble-user {
            align-self: flex-end;
            background-color: #d0e8ff;
            padding: 12px 18px;
            margin: 10px 0;
            border-radius: 20px 20px 5px 20px;
            max-width: 80%;
            word-wrap: break-word;
        }
        .chat-bubble-bot {
            align-self: flex-start;
            background-color: #f0f0f0;
            padding: 12px 18px;
            margin: 10px 0;
            border-radius: 20px 20px 20px 5px;
            max-width: 80%;
            word-wrap: break-word;
        }
        .floating-icons {
            position: fixed;
            top: 12%;
            right: 2%;
            font-size: 1.8rem;
            opacity: 0.15;
        }
        .floating-icons span {
            display: block;
            margin: 1rem;
            animation: float 6s ease-in-out infinite;
        }
        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-12px); }
            100% { transform: translateY(0px); }
        }
        </style>
        <div class="floating-icons">
            <span>📘</span>
            <span>💡</span>
            <span>🧠</span>
        </div>
    """, unsafe_allow_html=True)

    tips = [
        "📘 Tip: Break your study into 25-minute sprints (Pomodoro).",
        "💡 Concept > Memorization. Understand the 'why'!",
        "🔍 Rephrase problems in your own words to understand them better.",
        "📚 Review summaries before deep study.",
        "🧠 Practice spaced repetition for better memory retention."
    ]
    st.info(random.choice(tips))

    col1, col2, col3 = st.columns([1.2, 3.5, 1.3])

    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/4712/4712104.png", width=60)
        st.markdown("### 📚 Navigation")
        st.caption("Interact with Almika in the center panel.")
        st.markdown("---")
        st.markdown("### 🕓 Previous Chats")
        if st.session_state.history:
            for idx, (q, _) in enumerate(reversed(st.session_state.history[-10:]), 1):
                if st.button(f"{idx}. {q[:40]}{'...' if len(q)>40 else ''}", key=f"prev_{idx}"):
                    st.session_state.selected_question = q
                    st.experimental_rerun()
        else:
            st.info("No previous chats yet.")

    with col2:
        st.markdown("<h2 style='text-align:center;'>💬 Talk to Almika</h2>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/219/219986.png", width=80)

        if st.session_state.selected_question:
            question = st.session_state.selected_question
            st.session_state.selected_question = ""
        else:
            question = st.text_input("Ask anything about academics, careers, or trends...")

        if question:
            with st.spinner("Almika is typing..."):
                if st.session_state.pdf_text:
                    prompt = f"Based on the following PDF content, answer the question:\n{st.session_state.pdf_text[:3000]}\n\nQ: {question}"
                    answer = generate_gpt_response(prompt, faq_data)
                else:
                    answer = generate_gpt_response(question, faq_data)
                st.session_state.history.append((question, answer))
                if st.session_state.email:
                    save_user_history(st.session_state.email, st.session_state.history)

        chat_class = "chat-container dark" if st.session_state.dark_mode else "chat-container"
        st.markdown(f"<div class='{chat_class}'>", unsafe_allow_html=True)
        for i, (q, a) in enumerate(st.session_state.history):
            user_class = "chat-bubble-user dark" if st.session_state.dark_mode else "chat-bubble-user"
            bot_class = "chat-bubble-bot dark" if st.session_state.dark_mode else "chat-bubble-bot"
            st.markdown(f"<div class='{user_class}'>{q}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='{bot_class}'>🤖 {a}</div>", unsafe_allow_html=True)

            cols = st.columns([1, 1])
            with cols[0]:
                if st.button("👍 Helpful", key=f"like_{i}"):
                    st.toast("Thanks for your feedback! 😊")
            with cols[1]:
                if st.button("👎 Not Helpful", key=f"dislike_{i}"):
                    st.toast("We'll try to improve it! 🔧")

            # Follow-up suggestions
            for s in suggest_followups(q):
                st.markdown(f"<span style='font-size:0.9rem; color:#555;'>💡 {s}</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("### ⚙️ Options")

        if st.button("📦 Export All Chats (ZIP)"):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for file in os.listdir("chat_data"):
                    zipf.write(os.path.join("chat_data", file), arcname=file)
            b64 = base64.b64encode(zip_buffer.getvalue()).decode()
            st.markdown(f'<a href="data:application/zip;base64,{b64}" download="all_chats.zip">📥 Download All Chats</a>', unsafe_allow_html=True)

        with st.expander("📧 Login with Email"):
            with st.form("login_form"):
                email = st.text_input("Email Address")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("🔐 Login")
                if submitted:
                    if email and password:
                        st.success(f"✅ Logged in as {email}")
                        st.session_state.email = email
                        st.session_state.history = load_user_history(email)
                    else:
                        st.error("⚠️ Please enter both email and password.")

        if st.session_state.email and st.button("🚪 Logout"):
            st.session_state.email = ""
            st.session_state.history = []
            st.success("Logged out successfully.")
            st.experimental_rerun()

        st.markdown("---")
        st.markdown("### 📄 Upload PDF")
        pdf_file = st.file_uploader("Upload a PDF to ask questions from", type="pdf")
        if pdf_file:
            st.session_state.pdf_text = extract_pdf_text(pdf_file)
            st.success("✅ PDF uploaded and processed!")

        st.markdown("---")
        dark_toggle = st.checkbox("🌙 Dark Mode", value=st.session_state.dark_mode)
        st.session_state.dark_mode = dark_toggle
        if st.session_state.dark_mode:
            st.markdown("""
                <style>
                html, body, .stApp {
                    background-color: #111 !important;
                    color: #eee !important;
                }
                </style>
            """, unsafe_allow_html=True)


    with st.expander("📜 Full Chat Log"):
        for q, a in st.session_state.history:
            st.markdown(f"**You:** {q}")
            st.markdown(f"**Almika:** 🤖 {a}")
            st.markdown("---")



def subject_explanations():
    st.title("📚 Subject Explanations")
    topic = st.text_input("Enter the academic topic you want explained:")
    level = st.selectbox("Select explanation level:", ["Beginner", "Intermediate", "Advanced"])

    if topic:
        with st.spinner("Generating explanation using AI..."):
            faq_data = load_faq()
            prompt = f"Explain the topic '{topic}' at a {level.lower()} level in a clear and detailed way with examples."
            explanation = generate_gpt_response(prompt, faq_data)

            summary_prompt = f"Give a 3-line summary of the topic '{topic}'."
            summary = generate_gpt_response(summary_prompt, faq_data)

            quiz_prompt = f"Create a 3-question multiple-choice quiz on the topic '{topic}'."
            quiz = generate_gpt_response(quiz_prompt, faq_data)

            st.markdown(f"### Explanation of **{topic}**")
            st.markdown(explanation)
            st.markdown("---")
            st.markdown(f"**TL;DR**: {summary}")
            st.markdown("---")
            st.markdown("### 📝 Practice Quiz")
            st.markdown(quiz)



def homework_helper():
    st.title("📝 Homework Helper")
    question = st.text_area("Paste your homework question:")

    if st.button("Get Step-by-Step Help"):
        with st.spinner("Working on your homework question..."):
            faq_data = load_faq()

            prompt = f"""Give a detailed, step-by-step solution to the following academic homework question. 
Explain clearly like a teacher helping a student. Use bullet points, equations, or examples where needed.

Question: {question}"""

            answer = generate_gpt_response(prompt, faq_data)

            st.markdown("### 🧩 Step-by-Step Solution:")
            st.markdown(answer)


def exam_preparation():
    st.title("🧪 Exam Preparation Mode (Quiz)")
    questions = [
        {"q": "What is the capital of France?", "a": "Paris"},
        {"q": "Who wrote 'To Kill a Mockingbird'?", "a": "Harper Lee"},
        {"q": "What is the formula for water?", "a": "H₂O"},
    ]
    idx = st.session_state.get("quiz_index", 0)
    score = st.session_state.get("quiz_score", 0)

    if idx >= len(questions):
        st.success(f"Quiz finished! Your score: {score}/{len(questions)}")
        if st.button("Restart Quiz"):
            st.session_state.quiz_index = 0
            st.session_state.quiz_score = 0
            st.rerun()  # <- updated here
        return

    q = questions[idx]["q"]
    st.write(f"Q{idx+1}: {q}")
    answer = st.text_input("Your answer:")

    if st.button("Submit Answer"):
        if answer.strip().lower() == questions[idx]["a"].lower():
            st.success("Correct!")
            st.session_state.quiz_score = score + 1
        else:
            st.error(f"Wrong! Correct answer is: {questions[idx]['a']}")
        st.session_state.quiz_index = idx + 1
        st.rerun() 


def academic_calendar():
    st.title("📅 Academic Calendar & Reminders")
    if "events" not in st.session_state:
        st.session_state.events = []
    with st.form("add_event"):
        date = st.date_input("Event Date")
        name = st.text_input("Event Name")
        submitted = st.form_submit_button("Add Event")
        if submitted:
            st.session_state.events.append({"date": str(date), "name": name})
            st.success("Event added!")

    if st.session_state.events:
        st.markdown("### Upcoming Events")
        for event in sorted(st.session_state.events, key=lambda e: e["date"]):
            st.write(f"- {event['date']}: {event['name']}")


def citation_generator():
    st.title("📚 Citation & Reference Generator")
    author = st.text_input("Author(s)")
    title = st.text_input("Title")
    journal = st.text_input("Journal/Publisher")
    year = st.text_input("Year")
    doi = st.text_input("DOI (optional)")
    style = st.selectbox("Citation Style", ["APA", "MLA", "IEEE"])

    if st.button("Generate Citation"):
        citation = ""
        if style == "APA":
            citation = f"{author} ({year}). {title}. {journal}."
            if doi:
                citation += f" https://doi.org/{doi}"
        elif style == "MLA":
            citation = f"{author}. \"{title}.\" {journal}, {year}."
        else:  # IEEE
            citation = f"{author}, \"{title},\" {journal}, {year}."
        st.markdown(f"### {style} Citation:")
        st.code(citation)

def latest_academic_trends():
    st.title("📰 Latest Academic Trends")
  
    trends = [
        "AI models are transforming education with personalized learning.",
        "Quantum computing research is advancing rapidly.",
        "New algorithms improve data privacy and security.",
    ]
    for t in trends:
        st.write(f"- {t}")

def main():
    st.sidebar.title("Almika - Student Assistant")
    selection = st.sidebar.radio("Navigate", [
        "Chatbot",
        "Subject Explanations",
        "Homework Helper",
        "Exam Preparation",
        "Academic Calendar",
        "Citation Generator",
        
    ])

    if selection == "Chatbot":
        chatbot_page()
    elif selection == "Subject Explanations":
        subject_explanations()
    elif selection == "Homework Helper":
        homework_helper()
    elif selection == "Exam Preparation":
        exam_preparation()
    elif selection == "Academic Calendar":
        academic_calendar()
    elif selection == "Citation Generator":
        citation_generator()
    

if __name__ == "__main__":
    main()
