import streamlit as st
from models.agents import create_supervisor_agent

def app():
    st.set_page_config(page_title="Restaurant AI Assistant", layout="wide")
    
    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "supervisor_agent" not in st.session_state:
        st.session_state.supervisor_agent = create_supervisor_agent()
    
    # Page title
    st.title("Restaurant AI Assistant")
    st.markdown("Chat with our AI assistant for reservations, orders, and information")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response (placeholder - integrate with your backend)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.write_stream(st.session_state.supervisor_agent.stream(
                    {"messages": st.session_state.messages}
                ))
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response[-1]['model']['messages'][0].content})
        
        # Rerun to update the chat display
        st.rerun()
    
    # Sidebar with options
    with st.sidebar:
        st.header("Options")
        
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.rerun()


if __name__ == "__main__":
    app()