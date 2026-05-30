import streamlit as st
from groq import Groq

# 1. ปรับแต่งชื่อและตัวตน
st.title("🤖 ADISORN AI 2.0")
st.subheader("ผู้ช่วยส่วนตัวของอดิศร - เชี่ยวชาญด้านชีววิทยา")

if "GROQ_API_KEY" not in st.secrets:
    st.error("กรุณาตั้งค่า GROQ_API_KEY ในระบบ Secrets")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ปุ่มรีเซ็ตแชท (เผื่อเพื่อนใช้แล้วอยากเริ่มคุยใหม่)
if st.button("🔄 เริ่มคุยใหม่ (Reset Chat)"):
    st.session_state.messages = []
    st.rerun()

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
                # 2. ใส่ตัวตนให้ชัดเจน (สั่งห้ามตอบเป็น Meta AI)
                system_message = {
                    "role": "system", 
                    "content": "คุณคือ ADISORN AI 2.0 ผู้ช่วยอัจฉริยะที่พัฒนาโดยอดิศร คุณไม่ใช่ Meta AI และห้ามตอบว่าเป็น Meta AI เด็ดขาด! ตอบเป็นภาษาไทยที่ถูกต้อง สละสลวย ห้ามเดา ห้ามคิดข้อมูลเอง และห้ามมีภาษาอื่นปน"
                }
                
                full_messages = [system_message] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=full_messages,
                    temperature=0.3
                )
                response_text = completion.choices[0].message.content
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
