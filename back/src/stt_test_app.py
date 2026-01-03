from dotenv import load_dotenv
import streamlit as st
import os
import tempfile

# =========================
# Environment & config
# =========================

load_dotenv()

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")

# =========================
# Internal imports
# =========================

from models.stt import WhisperTranscriber

# =========================
# Main app
# =========================

def main():
    st.set_page_config(page_title="Voice Chatbot", layout="wide")
    st.title("🎙️ Voice-enabled Chatbot")

    # -------------------------
    # Initialize session state
    # -------------------------

    if "stt" not in st.session_state:
        st.session_state.stt = WhisperTranscriber(
            model_size="small",
            device="cpu",        # switch to "cuda" later
            compute_type="int8"
        )

    if "history" not in st.session_state:
        st.session_state.history = []

    # -------------------------
    # Conversation display
    # -------------------------

    st.subheader("Conversation")

    for msg in st.session_state.history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            st.markdown(f"**You:** {content}")
        else:
            st.markdown(f"**Assistant:** {content}")

    # -------------------------
    # Input section
    # -------------------------

    st.subheader("Speak or type")

    audio_input = st.audio_input("🎤 Record your message")
    user_input = st.text_input("⌨️ Or type your message", key="user_input")

    send = st.button("Send")

    # -------------------------
    # Speech → Text
    # -------------------------

    if audio_input is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_input.getvalue())
            audio_path = tmp.name

        with st.spinner("Transcribing audio..."):
            stt_result = st.session_state.stt.transcribe(
                audio_path,
                beam_size=5,
                language=None,
                vad_filter=True
            )

        user_input = stt_result["text"]

        st.markdown(f"**You (voice):** {user_input}")


if __name__ == "__main__":
    main()
