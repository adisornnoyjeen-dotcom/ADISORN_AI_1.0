import streamlit as st
import base64
import json
from datetime import datetime
from groq import Groq

# ==========================================
# 1. การตั้งค่าหน้าจอและหน้าตา UI (Page Config & CSS)
# ==========================================
st.set_page_config(page_title="ADISORN AI 3.0", page_icon="🔮", layout="wide")

st.markdown("""
    <style>
    /* ปรับแต่งพื้นหลังและฟอนต์ */
    .stApp { background-color: #f4f6f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* ปรับแต่งความกว้างและสไตล์ของ Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e5e7eb;
    }
    
    /* กล่องข้อความของผู้ใช้ (User) */
    .user-bubble {
        background-color: #4F46E5; color: white; padding: 12px 18px; 
        border-radius: 18px 18px 0px 18px; margin-bottom: 10px; 
        max-width: 80%; float: right; clear: both; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* กล่องข้อความของ AI (Assistant) */
    .ai-bubble {
        background-color: #ffffff; color: #1f2937; padding: 12px 18px; 
        border-radius: 18px 18px 18px 0px; margin-bottom: 10px; 
        max-width: 80%; float: left; clear: both; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e5e7eb;
    }
    
    /* ตัวแบ่งเซกชันใน Sidebar */
    .sidebar-section {
        font-weight: bold;
        color: #4F46E5;
        margin-top: 15px;
        margin-bottom: 5px;
    }
    
    /* ล้าง float เมื่อจบแชท */
    .clear { clear: both; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ฟังก์ชันช่วยเหลือ (Helper Functions)
# ==========================================
def encode_image(image_file):
    """แปลงรูปภาพที่อัปโหลดเป็น Base64 เพื่อให้ AI อ่านได้"""
    return base64.b64encode(image_file.read()).decode('utf-8')

def export_chat_history():
    """แปลงประวัติแชทเป็นข้อความสำหรับดาวน์โหลด"""
    chat_text = "=== ADISORN AI 3.0 Chat History ===\n"
    chat_text += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    for msg in st.session_state.messages:
        role = "👤 You" if msg["role"] == "user" else "🤖 ADISORN AI"
        content = msg["content"]
        if isinstance(content, list):
            content = content[0]["text"] + " [แนบรูปภาพ]"
        chat_text += f"{role}:\n{content}\n\n{'-'*40}\n\n"
    return chat_text

# ==========================================
# 3. การจัดการสถานะ (Session State Initialization)
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_persona" not in st.session_state:
    st.session_state.current_persona = "ผู้ช่วยทั่วไป"

# ตรวจสอบ API Key
if "GROQ_API_KEY" not in st.secrets:
    st.error("⚠️ กรุณาตั้งค่า GROQ_API_KEY ในระบบ Secrets ของ Streamlit")
    st.stop()
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ==========================================
# 4. เมนูฝั่งซ้ายทั้งหมด (Unified Sidebar Control Panel)
# ==========================================
with st.sidebar:
    st.title("🔮 ADISORN 3.0")
    st.caption("Ultimate AI Dashboard")
    
    if st.button("➕ สร้างแชทใหม่ (New Chat)", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    # 4.1 ระบบปรับแต่งบทบาท (AI Persona Settings)
    st.markdown("<p class='sidebar-section'>🎭 ปรับแต่งบทบาท AI</p>", unsafe_allow_html=True)
    persona_options = {
        "ผู้ช่วยทั่วไป": "คุณคือ ADISORN AI 3.0 ผู้ช่วยอัจฉริยะ ตอบคำถามเป็นภาษาไทยอย่างเป็นมิตร",
        "นักชีววิทยา": "คุณคือ ศ.ดร.อดิศร ผู้เชี่ยวชาญด้านชีววิทยา ตอบด้วยข้อมูลเชิงลึกและศัพท์วิชาการ",
        "โปรแกรมเมอร์": "คุณคือ Senior Developer ชื่ออดิศร เชี่ยวชาญการเขียนโค้ด ตอบสั้นๆ พร้อมโค้ดตัวอย่าง",
        "นักการตลาด": "คุณคือ Marketing Guru ชื่ออดิศร เชี่ยวชาญการสร้างแบรนด์ เน้นตอบไอเดียที่แปลกใหม่"
    }
    selected_persona = st.selectbox("เลือก Persona ของระบบ:", list(persona_options.keys()), label_visibility="collapsed")
    
    # 4.2 ปรับระดับความสร้างสรรค์ (Temperature Setting)
    st.markdown("<p class='sidebar-section'>🌡️ ความสร้างสรรค์ของคำตอบ</p>", unsafe_allow_html=True)
    temperature = st.slider("0 = เป๊ะวิชาการ, 1 = มโนเก่ง", min_value=0.0, max_value=1.0, value=0.3, step=0.1)
    
    st.divider()
    
    # 4.3 อัปโหลดรูปภาพเพื่อใช้วิเคราะห์ (Vision Input)
    st.markdown("<p class='sidebar-section'>👁️ ระบบวิเคราะห์รูปภาพ</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("แนบไฟล์ JPG หรือ PNG:", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="รูปภาพปัจจุบันที่แนบอยู่", use_column_width=True)
        
    st.divider()
    
    # 4.4 การจัดการประวัติแชท (Chat Utilities)
    st.markdown("<p class='sidebar-section'>📦 จัดการข้อมูลแชท</p>", unsafe_allow_html=True)
    if st.button("📝 สรุปบทสนทนาทั้งหมด", use_container_width=True):
        if len(st.session_state.messages) > 0:
            st.session_state.quick_prompt = "สรุปบทสนทนาที่เราคุยกันมาทั้งหมดให้สั้นกระชับเป็นข้อๆ"
            st.rerun()
        else:
            st.warning("ยังไม่มีข้อความให้สรุปครับ")
            
    if len(st.session_state.messages) > 0:
        chat_data = export_chat_history()
        st.download_button(
            label="💾 ดาวน์โหลดแชทเก็บไว้ (.txt)",
            data=chat_data,
            file_name=f"Adisorn_AI_Chat_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    st.divider()
    
    # 4.5 เมนูลัดในการถามคำถาม (Quick Prompts)
    st.markdown("<p class='sidebar-section'>📌 คำถามด่วนที่ใช้บ่อย</p>", unsafe_allow_html=True)
    if st.button("🧬 อธิบายเรื่องพริออน (Prion)", use_container_width=True):
        st.session_state.quick_prompt = "อธิบายเรื่องโปรตีนพริออนให้เข้าใจง่ายๆ หน่อย"
        st.rerun()
    if st.button("💻 ช่วยเขียนโค้ด Python", use_container_width=True):
        st.session_state.quick_prompt = "เขียนโค้ด Python สำหรับทำกราฟแท่งแบบง่ายๆ"
        st.rerun()
    if st.button("📊 ร่างแผนการตลาด", use_container_width=True):
        st.session_state.quick_prompt = "ช่วยคิดแผนโปรโมทเพจให้หน่อย เอาแบบคนแชร์เยอะๆ"
        st.rerun()

# ==========================================
# 5. หน้าจอแชทหลัก (Centered Chat Area)
# ==========================================
# จัดหน้าหลักให้อยู่กึ่งกลาง ไม่กว้างจนเกินไปเพื่อความสบายตาในการอ่านแชท
_, col_main, _ = st.columns([1, 4, 1])

with col_main:
    st.write("### 💬 บทสนทนาของ ADISORN AI")
    
    # แสดงประวัติแชททั้งหมด
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            content = msg["content"]
            if isinstance(content, list): # กรณีมีการแนบภาพ
                st.markdown(f"<div class='user-bubble'>{content[0]['text']} <br><i>[📷 ส่งรูปภาพ]</i></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='user-bubble'>{content}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='ai-bubble'><b>🤖 ADISORN AI:</b><br>{msg['content']}</div>", unsafe_allow_html=True)
            
    st.markdown("<div class='clear'></div>", unsafe_allow_html=True)

    # จัดการการพิมพ์ส่งข้อความ
    user_input = st.chat_input("พิมพ์ข้อความ หรือส่งภาพผ่านเมนูด้านซ้ายเพื่อเริ่มวิเคราะห์...")
    
    # กรณีเลือกใช้งานจาก Quick Prompts/Summarize
    if "quick_prompt" in st.session_state:
        user_input = st.session_state.quick_prompt
        del st.session_state.quick_prompt

    if user_input:
        # แสดงข้อความฝั่งผู้ใช้ทันที
        st.markdown(f"<div class='user-bubble'>{user_input}</div><div class='clear'></div>", unsafe_allow_html=True)
        
        image_url = None
        message_content = user_input
        
        # แนบรูปภาพเข้าระบบประมวลผล (หากมีการเลือกรูปภาพไว้ใน Sidebar)
        if uploaded_file:
            base64_image = encode_image(uploaded_file)
            image_url = f"data:image/jpeg;base64,{base64_image}"
            message_content = [
                {"type": "text", "text": user_input},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
            
        st.session_state.messages.append({"role": "user", "content": message_content})
        
        # ส่งคำร้องขอไปยังเซิร์ฟเวอร์ Groq
        with st.spinner("AI กำลังวิเคราะห์ข้อมูล..."):
            try:
                system_instruction = persona_options[selected_persona]
                system_message = {"role": "system", "content": system_instruction}
                
                full_messages = [system_message] + st.session_state.messages
                
                completion = client.chat.completions.create(
                    model="llama-3.2-90b-vision-preview",
                    messages=full_messages,
                    temperature=temperature,
                    max_tokens=2048
                )
                
                response_text = completion.choices[0].message.content
                
                # แสดงผลคำตอบ
                st.markdown(f"<div class='ai-bubble'><b>🤖 ADISORN AI:</b><br>{response_text}</div><div class='clear'></div>", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                
                # ทำการรีโหลดสถานะหน้าจอเพื่ออัปเดตแชทบับเบิ้ล
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}")
