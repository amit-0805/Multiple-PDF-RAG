# frontend/app.py
import streamlit as st
import requests
import json
from datetime import datetime

# Constants
BACKEND_URL = "http://localhost:8000"
OPENAI_MODELS = ["gpt-4", "gpt-4o", "gpt-4o-mini"]
GROQ_MODELS = ["Gemma2-9b-It", "Deepseek-R1-Distill-Llama-70b", "Mixtral-8x7b-32768"]

def initialize_session_state():
    """Initialize session state variables"""
    if "chats" not in st.session_state:
        st.session_state.chats = {}
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    if "uploaded_pdfs" not in st.session_state:
        st.session_state.uploaded_pdfs = {}

def create_new_chat():
    """Create a new chat session for all PDFs"""
    chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_count = len(st.session_state.uploaded_pdfs)
    
    if pdf_count == 0:
        return None
    
    st.session_state.chats[chat_id] = {
        "messages": [],
        "title": f"Chat with {pdf_count} PDFs" if pdf_count > 1 else f"Chat with 1 PDF",
        "timestamp": datetime.now(),
    }
    st.session_state.current_chat_id = chat_id
    return chat_id

def start_new_chat():
    """Reset current chat to start a new one"""
    st.session_state.current_chat_id = None

def display_chat_history():
    """Display chat messages from current chat"""
    if st.session_state.current_chat_id:
        for message in st.session_state.chats[st.session_state.current_chat_id]["messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

def fetch_pdfs_from_backend():
    """Fetch the list of PDFs from the backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/pdfs")
        if response.status_code == 200:
            st.session_state.uploaded_pdfs = response.json()["pdfs"]
        else:
            st.error(f"Error fetching PDFs: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error connecting to backend: {str(e)}")

def main():
    st.set_page_config(page_title="Multi-PDF Chat", layout="wide")
    
    initialize_session_state()
    
    # Sidebar with three sections
    with st.sidebar:
        st.title("Multi-PDF Chat")
        
        # New Chat Button at the top of sidebar
        if st.button("➕ New Chat", type="primary", use_container_width=True):
            start_new_chat()
            st.rerun()
        
        st.divider()
        
        # Section 1: Model Configuration
        with st.expander("🤖 Model Configuration", expanded=True):
            model_type = st.radio("Select Model Provider:", ["OpenAI", "Groq"])
            
            if model_type == "OpenAI":
                api_key = st.text_input("OpenAI API Key:", type="password")
                model_name = st.selectbox("Select Model:", OPENAI_MODELS)
            else:
                api_key = st.text_input("Groq API Key:", type="password")
                model_name = st.selectbox("Select Model:", GROQ_MODELS)
            
            temperature = st.slider(
                "Temperature:",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.1
            )
            st.text("Temperature: Temperature tells how much creative the model gets in generating output")
            
            max_tokens = st.slider(
                "Max Tokens:",
                min_value=100,
                max_value=4096,
                value=2048,
                step=100
            )
            st.text("max_tokens: Limits the maximum number of tokens the model can generate in output")
        
        # Section 2: Uploaded Files Reference
        with st.expander("📚 Uploaded PDFs", expanded=True):
            # Refresh button to fetch the latest PDFs
            if st.button("🔄 Refresh PDFs"):
                fetch_pdfs_from_backend()
                st.rerun()
            
            if not st.session_state.uploaded_pdfs:
                st.info("No PDFs uploaded yet")
                fetch_pdfs_from_backend()
            else:
                st.write("Your uploaded PDFs:")
                for pdf_id, pdf_name in st.session_state.uploaded_pdfs.items():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"📄 {pdf_name}")
                    with col2:
                        if st.button("🗑️", key=f"delete_pdf_{pdf_id}"):
                            try:
                                response = requests.delete(f"{BACKEND_URL}/pdfs/{pdf_id}")
                                if response.status_code == 200:
                                    fetch_pdfs_from_backend()
                                    st.success(f"PDF {pdf_name} removed successfully")
                                    st.rerun()
                                else:
                                    st.error(f"Error removing PDF: {response.json().get('detail', 'Unknown error')}")
                            except Exception as e:
                                st.error(f"Error connecting to backend: {str(e)}")
        
        # Section 3: Chat History
        with st.expander("💬 Chat History", expanded=True):
            if st.session_state.chats:
                for chat_id, chat_data in sorted(
                    st.session_state.chats.items(),
                    key=lambda x: x[1]["timestamp"],
                    reverse=True
                ):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        if st.button(
                            chat_data["title"],
                            key=f"chat_{chat_id}",
                            use_container_width=True
                        ):
                            st.session_state.current_chat_id = chat_id
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"delete_{chat_id}"):
                            del st.session_state.chats[chat_id]
                            if chat_id == st.session_state.current_chat_id:
                                st.session_state.current_chat_id = None
                            st.rerun()
    
    # Main area
    if not st.session_state.current_chat_id:
        st.title("Chat with Multiple PDFs")
        
        # File upload section
        uploaded_file = st.file_uploader("Upload a PDF", type=['pdf'], accept_multiple_files=True)
        if uploaded_file:
            processed_files = 0
            failed_files = 0
            
            for file in uploaded_file:
                with st.status(f"Processing {file.name}..."):
                    try:
                        files = {"file": file}
                        response = requests.post(f"{BACKEND_URL}/upload", files=files)
                        
                        if response.status_code == 200:
                            processed_files += 1
                            pdf_id = response.json()["pdf_id"]
                            pdf_name = response.json()["pdf_name"]
                            # Update the local cache of uploaded PDFs
                            st.session_state.uploaded_pdfs[pdf_id] = pdf_name
                        else:
                            failed_files += 1
                            st.error(f"Error processing {file.name}: {response.json().get('detail', 'Unknown error')}")
                    except Exception as e:
                        failed_files += 1
                        st.error(f"Error connecting to backend for {file.name}: {str(e)}")
            
            if processed_files > 0:
                st.success(f"{processed_files} PDFs processed successfully!")
                
                # Create a new chat if there are PDFs and there was at least one newly processed
                if create_new_chat():
                    st.rerun()
            
            if failed_files > 0:
                st.warning(f"{failed_files} PDFs failed to process.")
        
        # Start new chat with existing PDFs
        if st.session_state.uploaded_pdfs:
            st.write(f"You have {len(st.session_state.uploaded_pdfs)} PDFs ready for chatting")
            if st.button("Start a new chat with all PDFs"):
                if create_new_chat():
                    st.rerun()
    
    else:
        # Active chat interface
        current_chat = st.session_state.chats[st.session_state.current_chat_id]
        
        # Show current chat context
        st.title(current_chat["title"])
        pdf_count = len(st.session_state.uploaded_pdfs)
        st.info(f"📚 Currently chatting with {pdf_count} PDF{'s' if pdf_count > 1 else ''}")
        
        # Display PDF list in the chat header
        if pdf_count > 0:
            with st.expander("View PDF list"):
                for pdf_id, pdf_name in st.session_state.uploaded_pdfs.items():
                    st.write(f"📄 {pdf_name}")
        
        # Chat interface
        display_chat_history()
        
        # Chat input
        if query := st.chat_input("Ask a question about your PDFs:"):
            if not api_key:
                st.warning("Please enter an API key.")
                return
            
            # Add user message to chat history
            current_chat["messages"].append({"role": "user", "content": query})
            with st.chat_message("user"):
                st.markdown(query)
            
            # Get response from backend
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        chat_request = {
                            "query": query,
                            "api_key": api_key,
                            "model_type": model_type.lower(),
                            "model_name": model_name,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                            "session_id": st.session_state.current_chat_id
                        }
                        
                        response = requests.post(
                            f"{BACKEND_URL}/chat",
                            json=chat_request,
                            timeout=60
                        )
                        
                        if response.status_code == 200:
                            assistant_response = response.json()["response"]
                            st.markdown(assistant_response)
                            current_chat["messages"].append({
                                "role": "assistant",
                                "content": assistant_response
                            })
                        else:
                            error_detail = response.json().get('detail', 'Unknown error')
                            st.error(f"Error: {error_detail}")
                    except requests.exceptions.Timeout:
                        st.error("Request timed out. Please try again.")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error connecting to backend: {str(e)}")
                    except Exception as e:
                        st.error(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()