import streamlit as st
import base64
from groq import Groq

st.title("🤖 ADISORN AI 2.0 (Vision Version)")
st.subheader("ผู้ช่วยส่วนตัว - วิเคราะห์ได้ทั้งข้อความและรูปภาพ")

if "GROQ_API_KEY" not in st.secrets:
    st.error("กรุณาตั้งค่า GROQ_API_KEY ในระบบ Secrets")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ปุ่มรีเซ็ตแชท
if st.button("🔄 เริ่มคุยใหม่"):
    st.session_state.messages = []
    st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

# ฟังก์ชันแปลงรูปภาพเป็น Base64
def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

# อัปโหลดไฟล์รูปภาพ
uploaded_file = st.file_uploader("อัปโหลดรูปภาพเพื่อวิเคราะห์...", type=["jpg", "jpeg", "png"])

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("พิมพ์ถาม หรืออัปโหลดรูปภาพแล้วพิมพ์ถาม..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # ถ้ามีรูปอัปโหลด
    image_url = None
    if uploaded_file:
        base64_image = encode_image(uploaded_file)
        image_url = f"data:image/jpeg;base64,{base64_image}"
        st.image(uploaded_file, caption="รูปที่อัปโหลด", width=300)

    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("กำลังวิเคราะห์..."):
            try:
                system_message = {"role": "system", "content": "คุณคือ ADISORN AI 2.0 ผู้เชี่ยวชาญด้านชีววิทยาที่พัฒนาโดยอดิศร สามารถวิเคราะห์ภาพและข้อความได้อย่างแม่นยำ ห้ามตอบว่าเป็น Meta AI เด็ดขาด"}
                
                messages = [system_message] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                
                # ถ้ามีรูปภาพ ให้ปรับโครงสร้างข้อความเพื่อส่งให้โมเดล Vision
                if image_url:
                    messages[-1] = {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_input},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }

                completion = client.chat.completions.create(
                    model="llama-3.2-90b-vision-preview",
                    messages=messages,
                    temperature=0.3
                )
                response_text = completion.choices[0].message.content
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
