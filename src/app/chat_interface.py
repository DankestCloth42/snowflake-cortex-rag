import streamlit as st 

from src.rag_engine.hybrid_rag_pipeline import run_hybrid_rag




st.set_page_config(page_title="FIFA AI Scout", page_icon="⚽", layout="centered")

st.title("FIFA AI Scout ⚽")
st.caption("Powered by Snowflake, Cortex, and Gemini")

st.divider()



if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm your AI Data Scout. Ask me anything about FIFA players!"}
    ]


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])



if prompt := st.chat_input("E.g., Find players from Brazil who scored more than 10 goals in 2022..."):
    
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("🕵️ Searching Snowflake database & thinking..."):
            
            answer = run_hybrid_rag(prompt)
            
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})