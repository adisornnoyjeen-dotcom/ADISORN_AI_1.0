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
                # 1. เปลี่ยนชื่อโมเดลเป็นรุ่นใหญ่ 70B ที่ฉลาดและแม่นยำขึ้นมาก
                # 2. ทำข้อ 3 โดยการแอบแฝง System Prompt สั่ง AI ว่าห้ามหลอน ห้ามแปลมั่ว
                system_message = {
                    "role": "system", 
                    "content": "คุณคือผู้เชี่ยวชาญวิชาชีววิทยาและการแพทย์ระดับสูง ตอบคำถามอิงตามหลักการทางวิทยาศาสตร์และข้อเท็จจริงที่ได้รับการพิสูจน์แล้วเท่านั้น หากไม่มีข้อมูลหรือไม่อมั่นใจ ให้ปฏิเสธการตอบตรงๆ อย่างสุภาพ ห้ามเดา ห้ามคิดข้อมูลขึ้นมาเอง และห้ามแปลภาษาเพี้ยนเด็ดขาด"
                }
                
                # รวมคำสั่งระบบเข้ากับบทสนทนาของคุณ
                full_messages = [system_message] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=full_messages
                )
                response_text = completion.choices[0].message.content
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
