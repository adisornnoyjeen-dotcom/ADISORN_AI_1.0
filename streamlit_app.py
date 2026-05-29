import streamlit as st
from groq import Groq

st.set_page_config(page_title="ADISORN AI 2.0", page_icon="🤖")
st.title("🤖 ADISORN AI 2.0")

# ดึง API Key จากระบบ Secrets ของ Streamlit
if "GROQ_API_KEY" not in st.secrets:
    st.error("❌ กรุณาตั้งค่า GROQ_API_KEY ในระบบ Secrets ก่อนนะครับ")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("พิมพ์ข้อความคุยกับ AI ที่นี่..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("กำลังคิด..."):
            try:
                completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                )
                response_text = completion.choices[0].message.content
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
