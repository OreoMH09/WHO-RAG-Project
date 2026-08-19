"""
Streamlit UI for WHO RAG System.
Interactive interface for asking health questions and getting cited answers.
"""
import streamlit as st
import os
from dotenv import load_dotenv
from rag.generate import answer_question
from search.vector_store import get_collection_stats
import config


# Load environment variables
load_dotenv()


# Auto-download database on first run (Streamlit Cloud)
@st.cache_resource(show_spinner=False)
def ensure_database_exists():
    """Download database from GitHub Releases if not present."""
    try:
        from download_database import setup_database
        setup_database()
    except Exception as e:
        print(f"Database setup: {e}")


# Run database setup
ensure_database_exists()


# Page configuration
st.set_page_config(
    page_title="WHO Health Information Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)


def check_setup():
    """Check if the system is properly set up."""
    errors = []
    warnings = []
    
    # Check API key - try both .env and Streamlit secrets
    api_key = None
    try:
        api_key = st.secrets.get("GROQ_API_KEY")
    except:
        api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        errors.append("❌ GROQ_API_KEY not found. Please add it to Streamlit secrets or .env file.")
    
    # Check if index exists
    try:
        stats = get_collection_stats()
        if stats["total_documents"] == 0:
            warnings.append({
                "message": "⚠️ No documents in the index yet.",
                "action": "build_index"
            })
    except Exception as e:
        errors.append(f"❌ Error accessing vector database: {e}")
    
    return errors, warnings


def display_source(source, index):
    """Display a single source citation."""
    with st.expander(f"📄 [{index}] {source['title']}", expanded=False):
        st.write(f"**URL:** {source['url']}")
        if source.get('date'):
            st.write(f"**Date:** {source['date']}")
        st.write(f"**Relevance Score:** {source['score']:.4f}")


def main():
    # Header
    st.title("🧠 WHO Brain Disease Information Assistant")
    st.markdown("""
    Ask questions about brain and neurological diseases based on World Health Organization sources.
    Topics include: Dementia, Alzheimer's, Parkinson's, Epilepsy, Stroke, and Mental Health.
    All answers include citations to WHO documents.
    """)
    
    # Check setup
    setup_errors, warnings = check_setup()
    
    if setup_errors:
        st.error("**Setup Issues:**")
        for error in setup_errors:
            st.write(error)
        st.info("""
        **Setup Instructions:**
        1. Add GROQ_API_KEY to Streamlit Secrets (for cloud) or .env file (for local)
        2. Build the document index (see below)
        """)
        return
    
    # Show warnings (non-blocking)
    if warnings:
        for warning in warnings:
            if warning["action"] == "build_index":
                st.warning(warning["message"])
                st.info("""
                **How to build the index:**
                
                The vector database is empty. You have two options:
                
                **Option 1: Auto-build sample index (10 pages)**
                """)
                
                if st.button("🔨 Build Sample Index Now (10 pages, ~2 min)", type="primary"):
                    with st.spinner("Building index... This will take ~2 minutes"):
                        try:
                            from ingestion.build_index import main as build_index
                            import sys
                            # Temporarily redirect stdout
                            old_argv = sys.argv
                            sys.argv = ['build_index', 'sample', '10']
                            build_index()
                            sys.argv = old_argv
                            st.success("✅ Index built successfully! Refresh the page.")
                            st.balloons()
                        except Exception as e:
                            st.error(f"Error building index: {e}")
                            import traceback
                            st.code(traceback.format_exc())
                
                st.info("""
                **Option 2: Build locally (Full index - 1,074 documents)**
                ```bash
                # On your computer:
                python -m ingestion.build_index full
                ```
                Then upload the `data/chroma_db/` folder to cloud storage.
                """)
                
                # Don't return - let them see the UI
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Get collection stats
        try:
            stats = get_collection_stats()
            st.success(f"✅ Index loaded: {stats['total_documents']} documents")
        except Exception as e:
            st.error(f"Error: {e}")
        
        st.divider()
        
        # Search settings
        st.subheader("Search Configuration")
        
        search_method = st.selectbox(
            "Search Method",
            ["hybrid", "vector", "bm25"],
            index=0,
            help="Hybrid combines vector similarity with keyword matching (BM25)"
        )
        
        top_k = st.slider(
            "Number of Sources",
            min_value=1,
            max_value=10,
            value=config.DEFAULT_TOP_K,
            help="How many source documents to retrieve"
        )
        
        st.divider()
        
        # Model settings
        st.subheader("Model Configuration")
        
        model = st.selectbox(
            "Groq Model",
            [
                "openai/gpt-oss-120b",  # Best quality
                "openai/gpt-oss-20b",   # Faster
                "qwen/qwen3.6-27b",     # Qwen
                "allam-2-7b"            # Smallest
            ],
            index=0,
            help="OpenAI GPT OSS 120B - Highest quality available"
        )
        
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=config.TEMPERATURE,
            step=0.1,
            help="0 = deterministic, 1 = creative"
        )
        
        st.divider()
        
        # About
        st.subheader("ℹ️ About")
        st.markdown("""
        This system uses:
        - **Focus:** Brain & Neurological Diseases
        - **Retrieval:** Semantic search over WHO documents
        - **Generation:** Groq API (GPT OSS 120B) for answer synthesis
        - **Citations:** All answers cite source documents
        
        **Note:** This is for educational purposes. Always consult healthcare professionals for medical advice.
        """)
    
    # Main content area
    st.divider()
    
    # Initialize session state for conversation history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display conversation history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Display sources if available
            if message.get("sources"):
                with st.expander("📚 Sources", expanded=False):
                    for i, source in enumerate(message["sources"], 1):
                        display_source(source, i)
    
    # Question input
    question = st.chat_input("Ask a health question...")
    
    if question:
        # Display user question
        with st.chat_message("user"):
            st.markdown(question)
        
        # Add to conversation history
        st.session_state.messages.append({
            "role": "user",
            "content": question
        })
        
        # Generate answer
        with st.chat_message("assistant"):
            with st.spinner("Searching WHO knowledge base..."):
                try:
                    result = answer_question(
                        question=question,
                        top_k=top_k,
                        search_method=search_method,
                        model=model,
                        temperature=temperature
                    )
                    
                    # Display answer
                    st.markdown(result["answer"])
                    
                    # Display sources
                    st.divider()
                    st.subheader("📚 Sources")
                    
                    for i, source in enumerate(result["sources"], 1):
                        display_source(source, i)
                    
                    # Display metadata
                    with st.expander("🔍 Query Details", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Search Method", result["search_method"])
                        with col2:
                            st.metric("Sources Retrieved", len(result["sources"]))
                        with col3:
                            st.metric("Model", result["model"])
                        
                        if "usage" in result:
                            st.write("**Token Usage:**")
                            st.write(f"- Prompt: {result['usage']['prompt_tokens']}")
                            st.write(f"- Completion: {result['usage']['completion_tokens']}")
                            st.write(f"- Total: {result['usage']['total_tokens']}")
                    
                    # Add to conversation history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["answer"],
                        "sources": result["sources"]
                    })
                    
                except Exception as e:
                    st.error(f"Error generating answer: {e}")
                    import traceback
                    with st.expander("Error details"):
                        st.code(traceback.format_exc())
    
    # Clear conversation button
    if st.session_state.messages:
        if st.sidebar.button("🗑️ Clear Conversation"):
            st.session_state.messages = []
            st.rerun()
    
    # Example questions
    if not st.session_state.messages:
        st.divider()
        st.subheader("💡 Example Questions")
        
        example_questions = [
            "What is dementia and what are its symptoms?",
            "How can Alzheimer's disease be prevented?",
            "What are the main types of epilepsy?",
            "What are the warning signs of stroke?",
            "How does Parkinson's disease affect the brain?",
        ]
        
        cols = st.columns(len(example_questions))
        for col, question in zip(cols, example_questions):
            with col:
                if st.button(question, use_container_width=True):
                    st.rerun()


if __name__ == "__main__":
    main()
