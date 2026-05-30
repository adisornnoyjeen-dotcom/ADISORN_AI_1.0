import streamlit as st
import base64
from groq import Groq

# 1. ปรับ Layout ให้กระชับ สไตล์แชทบอททันสมัย
st.set_page_config(page_title="ADISORN AI", page_icon="🤖", layout="centered")

# 2. ปรับแต่งความงามด้วย CSS (มินิมอล)
st.markdown("""
    <style>
    .stApp {max-width: 800px; margin: auto;}
    .stChatMessage {border-radius: 15px !important;}
    h1 {font-size: 1.5rem !important; text-align: center; color: #333;}
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 ADISORN AI 2.0")

if "GROQ_API_KEY" not in st.secrets:
    st.error("ตั้งค่า GROQ_API_KEY ในระบบ Secrets ก่อนนะครับ")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# เครื่องมือใน Sidebar
with st.sidebar:
    st.write("### ⚙️ ปรับแต่ง")
    uploaded_file = st.file_uploader("แนบรูปภาพ", type=["jpg", "jpeg", "png"])
    if st.button("🔄 รีเซ็ตแชท"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

# แสดงประวัติแชท
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# การรับข้อมูล
if user_input := st.chat_input("พิมพ์ข้อความถึง Adisorn AI..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    
    image_url = None
    if uploaded_file:
        base64_image = encode_image(uploaded_file)
        image_url = f"data:image/jpeg;base64,{base64_image}"
        st.image(uploaded_file, width=150) # รูปเล็กดูดี

    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("กำลังคิด..."):
            try:
                system_message = {"role": "system", "content": "คุณคือ ADISORN AI 2.0 ผู้ช่วยด้านชีววิทยาที่พัฒนาโดยอดิศร ตอบสั้นกระชับ เป็นกันเอง และห้ามตอบว่าเป็น Meta AI"}
                messages = [system_message] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                
                if image_url:
                    messages[-1] = {"role": "user", "content": [{"type": "text", "text": user_input}, {"type": "image_url", "image_url": {"url": image_url}}]}

                completion = client.chat.completions.create(model="llama-3.2-90b-vision-preview", messages=messages, temperature=0.3)
                response_text = completion.choices[0].message.content
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
