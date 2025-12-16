import streamlit as st
import requests
import time

st.set_page_config(page_title="AI News Agent", page_icon="📰", layout="centered")
st.title("📰 AI News Agent")
st.write("Generate creative, factual news articles with AI.")

API_URL = "http://localhost:8000/api/v1/articles/generate"

# Input for topic
topic = st.text_input("Enter a news topic:", "Latest developments in AI technology")

if 'article' not in st.session_state:
    st.session_state['article'] = None
if 'status' not in st.session_state:
    st.session_state['status'] = None
if 'references' not in st.session_state:
    st.session_state['references'] = None
if 'research_summary' not in st.session_state:
    st.session_state['research_summary'] = None

if st.button("Generate Article"):
    st.session_state['article'] = None
    st.session_state['status'] = None
    st.session_state['references'] = None
    st.session_state['research_summary'] = None
    with st.spinner("Submitting request to AI News Agent..."):
        try:
            response = requests.post(API_URL, json={"topic": topic})
            data = response.json()
            st.session_state['status'] = data.get('status')
            st.session_state['article'] = data.get('article')
            st.session_state['references'] = data.get('references')
            st.session_state['research_summary'] = data.get('research_summary')
        except Exception as e:
            st.error(f"Failed to contact API: {e}")

if st.session_state['status']:
    status = st.session_state['status']
    if status == "completed":
        st.success("Article generated!")
        article = st.session_state['article']
        # Stream article
        for line in article.splitlines():
            st.write(line)
            time.sleep(0.05)
        # Download markdown content directly from API response
        if st.button("Download Article as Markdown"):
            if article:
                st.download_button(
                    label="Click to Download final.md",
                    data=article,
                    file_name="final.md",
                    mime="text/markdown"
                )
            else:
                st.info("No article content available for download.")
        if st.session_state['references']:
            st.markdown("**References:**")
            for ref in st.session_state['references']:
                st.markdown(f"- [{ref}]({ref})")
        if st.session_state['research_summary']:
            with st.expander("Show Research Summary"):
                st.write(st.session_state['research_summary'])
    elif status == "failed":
        st.error("Failed to generate article.")
    else:
        st.info(f"Status: {status}. Please wait...")
