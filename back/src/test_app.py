from dotenv import load_dotenv
import streamlit as st
import os
import numpy as np

load_dotenv()

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")

from models.llm import MistralWrapper
from models.tts import stream_speech

def main():
	st.set_page_config(page_title="Voice Chatbot", layout="wide")
	st.title("Voice-enabled Chatbot")

	# Initialize LLM wrapper in session state
	if "llm" not in st.session_state:
		st.session_state.llm = MistralWrapper(api_key=MISTRAL_API_KEY)

	if "history" not in st.session_state:
		st.session_state.history = []

	st.subheader("Conversation")

	# Display chat messages
	for i, msg in enumerate(st.session_state.history):
		role = msg.get("role", "user")
		content = msg.get("content", "")
		if role == "user":
			st.markdown(f"**You:** {content}")
		else:
			st.markdown(f"**Assistant:** {content}")

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
	
		# Display the new assistant message
		st.markdown(f"**You:** {user_input}")
		st.markdown(f"**Assistant:** {assistant_text}")
		
		# Stream and play audio chunks with autoplay
		for wav_chunk, sample_rate in stream_speech(assistant_text):
			st.audio(wav_chunk, format="audio/wav", sample_rate=sample_rate, autoplay=True)

if __name__ == "__main__":
	main()
