import streamlit as st
import google.generativeai as genai
import json
import re

# Set the page configuration for a better look
st.set_page_config(
    page_title="مُدرِّس طقس الفضاء",
    page_icon="☀️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# API Keys and Models
genai.configure(api_key="AIzaSyC97AZInLjYT9Z6eBPorBgBlTJ3DL6Mtsc")
TEXT_MODEL = "gemini-1.5-flash"

# --- CSS Styling for better UI ---
st.markdown("""
<style>
/* Adjust the font size of the chat messages */
.stChatMessage > div[data-testid="stChatMessageContent"] {
    font-size: 1.2rem;
    line-height: 1.6;
}

/* Align text based on language */
/* User message container */
.stChatMessage > div:nth-child(1) {
    text-align: right;
}

/* Assistant message container */
.stChatMessage > div:nth-child(2) {
    text-align: right;
}

/* Assistant message content alignment based on content language */
.stChatMessage > div[data-testid="stChatMessageContent"] > p {
    text-align: inherit;
    direction: rtl; /* Default to right-to-left for Arabic */
}
.stChatMessage > div[data-testid="stChatMessageContent"] > p:first-letter {
    text-align: left;
    direction: ltr; /* Override for English */
}

/* Make input field bigger */
.st-emotion-cache-1c7y2qn {
    font-size: 1.2rem;
}

/* Change font for better readability for kids */
html, body, [class*="st-"] {
    font-family: 'Segoe UI', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
}
</style>
""", unsafe_allow_html=True)


# --- Utility Functions ---

def clean_markdown_json(raw_text):
    """Strips markdown code fences from a string containing JSON."""
    return re.sub(r"^```json\s*|\s*```$", "", raw_text.strip(), flags=re.DOTALL)

def get_space_weather_response(user_question, chat_history):
    """
    Calls the Gemini API to get a space weather explanation for kids,
    including the conversation history.
    """
    # Create the chat session with a pre-defined system instruction
    chat = genai.GenerativeModel(TEXT_MODEL).start_chat(history=chat_history)

    try:
        response = chat.send_message(user_question)
        raw_text = response.text
        cleaned_text = clean_markdown_json(raw_text)
        return json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        # If the model gives a non-JSON response, return a canned error message
        st.error(f"حدث خطأ في استجابة النموذج: {e}")
        st.code(raw_text, language="json")
        return None
    except Exception as e:
        # For other errors, check for safety violations
        if "Blocked due to safety" in str(e):
            st.error("أعتذر، لا أستطيع الإجابة على هذا السؤال. يرجى طرح سؤال آخر.")
            return None
        return {"answer_text": "لم أفهم سؤالك، هل يمكنك المحاولة مرة أخرى؟", "glossary": [], "language": "ar", "suggested_followup": None}

# --- Streamlit Chat UI ---

st.title("☀️ مُدرِّس طقس الفضاء")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.chat_history = [
        {"role": "user", "parts": [
            {"text": """
            You are a friendly bilingual kids’ tutor about space weather (solar flares, solar wind, CMEs, auroras).
            - Audience: children ages 7–14.
            - Language: detect user input language (Arabic or English) and reply in the same.
            - You can understand and respond in Egyptian Arabic dialect. For example, if the user says "اه", you should understand it as "نعم" or "ايوه".
            - Explain with 2-4 bullet points or a tiny analogy.
            - End with one friendly follow-up question unless user asks for “no questions”.
            - Do NOT ask for personal data or unsafe experiments.
            - Out of scope (e.g. astrology): politely explain it’s not science and redirect.
            - IMPORTANT: If the user's question is not understandable or is out of context, respond with "لم أفهم سؤالك، هل يمكنك المحاولة مرة أخرى؟". Do NOT give a generic, positive response like "يا سلام! سؤالك رائع!" in this case.
            - At the very beginning of the chat, just introduce yourself and wait for the user's question. Do not provide any information until the user asks a question.

            Return output as pure JSON (no markdown fences), with this schema:
            {{
              "language": "ar|en",
              "answer_text": "the explanation to show the child",
              "suggested_followup": "short question string or null"
            }}
            """}
        ]},
        {"role": "model", "parts": [
            {"text": """
            {
              "language": "ar",
              "answer_text": "أهلاً بك! أنا معلّمك الخاص في طقس الفضاء، اسألني أي شيء تريد معرفته!",
              "suggested_followup": null
            }
            """}
        ]}
    ]
    # Add the initial welcome message to the display
    initial_message = json.loads(st.session_state.chat_history[1]["parts"][0]["text"])
    st.session_state.messages.append({"role": "assistant", "content": initial_message["answer_text"]})


# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("اسألني أي شيء عن طقس الفضاء..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("أفكر..."):
        # Get response from the text model, including chat history
        response_data = get_space_weather_response(prompt, st.session_state.chat_history)

        if response_data:
            # Create the response message for the chat
            full_response = response_data.get("answer_text", "لم يتم العثور على إجابة.")
            if response_data.get("suggested_followup"):
                full_response += f"\n\n{response_data['suggested_followup']}"

            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                st.markdown(full_response)

            # Add assistant response to chat history
            message_data = {
                "role": "assistant",
                "content": full_response,
                "suggested_followup": response_data.get("suggested_followup")
            }

            st.session_state.messages.append(message_data)
            
            # Update chat history for the next turn
            st.session_state.chat_history.append({"role": "user", "parts": [{"text": prompt}]})
            st.session_state.chat_history.append({"role": "model", "parts": [{"text": full_response}]})
