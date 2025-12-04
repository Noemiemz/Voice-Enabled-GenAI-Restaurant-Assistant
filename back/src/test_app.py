from dotenv import load_dotenv
import streamlit as st
import os

load_dotenv()

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")

from models.llm import MistralWrapper
from models.tts import generate_speech

def main():
	st.set_page_config(page_title="Voice Chatbot", layout="wide")
	st.title("Voice-enabled Chatbot")

	# Initialize LLM wrapper in session state
	if "llm" not in st.session_state:
		st.session_state.llm = MistralWrapper(api_key=MISTRAL_API_KEY)

	if "history" not in st.session_state:
		st.session_state.history = []

	if "last_audio" not in st.session_state:
		st.session_state.last_audio = None

	st.subheader("Conversation")

	# Display chat messages with audio
	for i, msg in enumerate(st.session_state.history):
		role = msg.get("role", "user")
		content = msg.get("content", "")
		if role == "user":
			st.markdown(f"**You:** {content}")
		else:
			st.markdown(f"**Assistant:** {content}")
			# Display audio for the last assistant message
			if i == len(st.session_state.history) - 1 and st.session_state.last_audio is not None:
				wav_audio, sample_rate = st.session_state.last_audio
				st.audio(wav_audio, format="audio/wav", sample_rate=sample_rate)

	# Input area
	user_input = st.text_input("Type your message below", key="user_input")
	send = st.button("Send")

	if send and user_input:
		# Generate assistant text
		try:
			assistant_text, history = st.session_state.llm.generate(user_input, history=st.session_state.history)
			st.session_state.history = history
		except Exception as e:
			st.error(f"LLM error: {e}")
			print(e)
			assistant_text = "Sorry, I couldn't generate a response."
	
		# Synthesize speech and store in session state
		wav_audio, sample_rate = generate_speech(assistant_text)
		st.session_state.last_audio = (wav_audio, sample_rate)
		
		# Trigger rerun to update the chat display
		st.rerun()

if __name__ == "__main__":
	main()
