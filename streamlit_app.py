import streamlit as st
from groq import Groq

st.title("🤖 ADISORN AI 2.0")

# ดึง API Key จากระบบ Secrets
if "GROQ_API_KEY" not in st.secrets:
    st.error("กรุณาตั้งค่า GROQ_API_KEY ในระบบ Secrets ก่อนนะครับ")
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
                # อัปเกรดคำสั่ง: สั่งห้ามมีภาษาอื่นหลุดมาเด็ดขาด
                system_message = {
                    "role": "system", 
                    "content": "คุณคือผู้เชี่ยวชาญวิชาชีววิทยาและการแพทย์ระดับสูง ต้องตอบเป็นภาษาไทยที่ถูกต้อง สละสลวย และเป็นธรรมชาติ 100% เท่านั้น ห้ามมีภาษาอื่น เช่น ภาษาจีน ภาษารัสเซีย หรือตัวอักษรต่างดาวปนมาในเนื้อหาเด็ดขาด (ยกเว้นคำศัพท์เทคนิคภาษาอังกฤษในวงเล็บ) หากไม่มีข้อมูลหรือไม่มั่นใจ ให้ปฏิเสธการตอบตรงๆ อย่างสุภาพ"
                }
                
                full_messages = [system_message] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

                # เพิ่ม temperature=0.3 เพื่อลดความเอ๋อและป้องกันโทเค็นภาษาอื่นหลุดมา
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
