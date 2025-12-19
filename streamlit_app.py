import streamlit as st
import requests
import time
import os

st.set_page_config(page_title="AI News Agent", page_icon="📰", layout="centered")
st.title("📰 AI News Agent")
st.write("Generate creative, factual news articles with AI.")

API_URL = "http://localhost:8000/api/v1/articles/generate"

# Input for topic
topic = st.text_input("Enter a news topic:", "Latest developments in AI technology")

# Initialize session state
if 'article' not in st.session_state:
    st.session_state['article'] = None
if 'status' not in st.session_state:
    st.session_state['status'] = None
if 'references' not in st.session_state:
    st.session_state['references'] = None
if 'research_summary' not in st.session_state:
    st.session_state['research_summary'] = None
if 'file_path' not in st.session_state:
    st.session_state['file_path'] = None
if 'markdown_content' not in st.session_state:
    st.session_state['markdown_content'] = None

# Generate Article Button
if st.button("Generate Article", type="primary"):
    # Reset session state
    st.session_state['article'] = None
    st.session_state['status'] = None
    st.session_state['references'] = None
    st.session_state['research_summary'] = None
    st.session_state['file_path'] = None
    st.session_state['markdown_content'] = None
    
    with st.spinner("🤖 AI agents are working on your article..."):
        # Show progress steps
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Update progress
            status_text.text("🔍 Researching the topic...")
            progress_bar.progress(25)
            
            # Make API call
            response = requests.post(API_URL, json={"topic": topic}, timeout=120)
            
            status_text.text("✍️ Writing the article...")
            progress_bar.progress(50)
            
            time.sleep(1)  # Brief pause for effect
            
            status_text.text("📝 Editing and finalizing...")
            progress_bar.progress(75)
            
            data = response.json()
            
            status_text.text("💾 Saving to file...")
            progress_bar.progress(90)
            
            # Store results in session state
            st.session_state['status'] = data.get('status')
            st.session_state['article'] = data.get('article')
            st.session_state['references'] = data.get('references')
            st.session_state['research_summary'] = data.get('research_summary')
            st.session_state['file_path'] = data.get('file_path')
            st.session_state['markdown_content'] = data.get('markdown_content')
            
            progress_bar.progress(100)
            status_text.text("✅ Complete!")
            time.sleep(0.5)
            status_text.empty()
            progress_bar.empty()
            
        except requests.exceptions.Timeout:
            st.error("⏱️ Request timed out. The article generation is taking longer than expected.")
        except Exception as e:
            st.error(f"❌ Failed to contact API: {e}")

# Display results if available
if st.session_state['status']:
    status = st.session_state['status']
    
    if status == "completed":
        st.success("✅ Article generated successfully!")
        
        article = st.session_state['article']
        file_path = st.session_state['file_path']
        markdown_content = st.session_state['markdown_content']
        
        # Display file saved information
        if file_path:
            st.info(f"💾 Article saved to: `{os.path.basename(file_path)}`")
        
        st.markdown("---")
        st.markdown("### 📰 Generated Article")
        
        # Display markdown content from .md file if available
        if markdown_content:
            st.markdown("#### Markdown Preview from .md file")
            st.markdown(markdown_content, unsafe_allow_html=True)
            st.markdown("---")
        
        # Create a container for the article
        article_container = st.container()
        with article_container:
            # Stream article content
            article_placeholder = st.empty()
            displayed_text = ""
            for i, char in enumerate(article):
                displayed_text += char
                if i % 10 == 0:  # Update every 10 characters for smoother display
                    article_placeholder.markdown(displayed_text)
                    time.sleep(0.01)
            article_placeholder.markdown(article)
        
        st.markdown("---")
        
        # Download buttons section
        col1, col2 = st.columns(2)
        
        with col1:
            # Download button for markdown
            if st.session_state['markdown_content']:
                st.download_button(
                    label="📥 Download as Markdown",
                    data=st.session_state['markdown_content'],
                    file_name=f"article_{int(time.time())}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            else:
                st.info("No markdown content available for download.")
        
        with col2:
            # Download button for text
            if article:
                st.download_button(
                    label="📄 Download as Text",
                    data=article,
                    file_name=f"article_{int(time.time())}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        
        # References section
        if st.session_state['references']:
            with st.expander("🔗 View References", expanded=False):
                st.markdown("**Sources used for this article:**")
                for i, ref in enumerate(st.session_state['references'], 1):
                    st.markdown(f"{i}. [{ref}]({ref})")
        
        # Research summary section
        if st.session_state['research_summary']:
            with st.expander("📊 View Research Summary", expanded=False):
                st.markdown("**Research findings:**")
                st.write(st.session_state['research_summary'])
        
    elif status == "failed":
        st.error("❌ Failed to generate article. Please try again.")
    else:
        st.info(f"⏳ Status: {status}. Please wait...")

# Sidebar with information
with st.sidebar:
    st.header("ℹ️ About")
    st.write("""
    This AI News Agent uses multiple specialized agents to:
    
    1. 🔍 **Research** - Gather information from the web
    2. ✍️ **Write** - Create engaging news articles
    3. 📝 **Edit** - Polish and improve content
    4. 💾 **Save** - Store articles as markdown files
    
    All articles are automatically saved to the `generated_articles` folder on the server.
    """)
    
    st.markdown("---")
    st.header("💡 Tips")
    st.write("""
    - Be specific with your topic
    - Use current events for best results
    - Articles are saved with timestamps
    - Download in markdown or text format
    """)
    
    st.markdown("---")
    st.caption("Powered by LangGraph & FastAPI")