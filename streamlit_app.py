import streamlit as st
import base64
from groq import Groq

# 1. ตั้งค่าธีมแบบมินิมอล (จำกัดความกว้างให้เหมือนแอปแชทมาตรฐาน)
st.set_page_config(page_title="ADISORN AI", page_icon="🤖")

# 2. ปรับแต่ง CSS เพื่อความมินิมอล
st.markdown("""
    <style>
    .main {background-color: #ffffff;}
    .stChatFloatingInputContainer {border-radius: 20px;}
    div[data-testid="stSidebar"] {background-color: #f8f9fa;}
    .stButton>button {border-radius: 20px; border: 1px solid #ddd;}
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 ADISORN AI 2.0")

if "GROQ_API_KEY" not in st.secrets:
    st.error("กรุณาตั้งค่า GROQ_API_KEY ในระบบ Secrets")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ย้ายเครื่องมือไปไว้ซ้าย
with st.sidebar:
    st.caption("Settings")
    uploaded_file = st.file_uploader("แนบรูปภาพ", type=["jpg", "jpeg", "png"])
    if st.button("🔄 รีเซ็ตแชท"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("พิมพ์ข้อความถึง Adisorn AI..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    
    image_url = None
    if uploaded_file:
        base64_image = encode_image(uploaded_file)
        image_url = f"data:image/jpeg;base64,{base64_image}"
        st.image(uploaded_file, width=200) # ย่อรูปให้เล็กลง

    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("กำลังประมวลผล..."):
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
