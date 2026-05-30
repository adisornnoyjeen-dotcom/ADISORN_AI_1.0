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
    
    /* กล่อง Tools ด้านขวา */
    .tool-card {
        background-color: #ffffff; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #f0f0f0; margin-bottom: 15px;
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
        # ถ้าข้อความเป็น list (มีรูปภาพ) ให้ดึงเฉพาะ text มาแสดง
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
# 4. โครงสร้าง Layout (3 คอลัมน์)
# ==========================================
# ใช้ Sidebar เป็นเมนูซ้ายสุด และแบ่งจอหลักเป็น 2 ส่วน (แชท 70% | เครื่องมือ 30%)
st.sidebar.title("🔮 ADISORN 3.0")
st.sidebar.caption("Ultimate AI Dashboard")

with st.sidebar:
    if st.button("➕ สร้างแชทใหม่ (New Chat)", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    st.write("📌 **เมนูลัด (Quick Prompts)**")
    if st.button("🧬 อธิบายเรื่องพริออน (Prion)"):
        st.session_state.quick_prompt = "อธิบายเรื่องโปรตีนพริออนให้เข้าใจง่ายๆ หน่อย"
    if st.button("💻 ช่วยเขียนโค้ด Python"):
        st.session_state.quick_prompt = "เขียนโค้ด Python สำหรับทำกราฟแท่งแบบง่ายๆ"
    if st.button("📊 ร่างแผนการตลาด"):
        st.session_state.quick_prompt = "ช่วยคิดแผนโปรโมทเพจให้หน่อย เอาแบบคนแชร์เยอะๆ"

col_main, col_tools = st.columns([2.5, 1], gap="large")

# ==========================================
# 5. คอลัมน์ขวา: แผงควบคุมและเครื่องมือ (Tools Column)
# ==========================================
with col_tools:
    st.markdown("<div class='tool-card'>", unsafe_allow_html=True)
    st.write("### 🛠️ AI Settings")
    
    # 5.1 ระบบ Persona
    persona_options = {
        "ผู้ช่วยทั่วไป": "คุณคือ ADISORN AI 3.0 ผู้ช่วยอัจฉริยะ ตอบคำถามเป็นภาษาไทยอย่างเป็นมิตร",
        "นักชีววิทยา": "คุณคือ ศ.ดร.อดิศร ผู้เชี่ยวชาญด้านชีววิทยา ตอบด้วยข้อมูลเชิงลึกและศัพท์วิชาการ",
        "โปรแกรมเมอร์": "คุณคือ Senior Developer ชื่ออดิศร เชี่ยวชาญการเขียนโค้ด ตอบสั้นๆ พร้อมโค้ดตัวอย่าง",
        "นักการตลาด": "คุณคือ Marketing Guru ชื่ออดิศร เชี่ยวชาญการสร้างแบรนด์ เน้นตอบไอเดียที่แปลกใหม่"
    }
    selected_persona = st.selectbox("🎭 เลือกบทบาท AI:", list(persona_options.keys()))
    
    # 5.2 ปรับ Temperature
    st.write("🌡️ **ความสร้างสรรค์**")
    temperature = st.slider("0 = เป๊ะวิชาการ, 1 = มโนเก่ง", min_value=0.0, max_value=1.0, value=0.3, step=0.1)
    
    st.divider()
    
    # 5.3 อัปโหลดรูปภาพ (Vision)
    st.write("👁️ **ระบบวิเคราะห์ภาพ**")
    uploaded_file = st.file_uploader("แนบรูปภาพ (JPG, PNG)", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="พร้อมวิเคราะห์", use_column_width=True)
        
    st.divider()
    
    # 5.4 ฟีเจอร์เสริม (Summarize & Export)
    st.write("📦 **จัดการแชท**")
    if st.button("📝 สรุปแชททั้งหมด", use_container_width=True):
        if len(st.session_state.messages) > 0:
            st.session_state.quick_prompt = "สรุปบทสนทนาที่เราคุยกันมาทั้งหมดให้สั้นกระชับเป็นข้อๆ"
        else:
            st.warning("ยังไม่มีบทสนทนาให้สรุปครับ")
            
    if len(st.session_state.messages) > 0:
        chat_data = export_chat_history()
        st.download_button(
            label="💾 ดาวน์โหลดประวัติแชท (.txt)",
            data=chat_data,
            file_name=f"Adisorn_AI_Chat_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 6. คอลัมน์หลัก: หน้าจอแชท (Main Chat Area)
# ==========================================
with col_main:
    st.write("### 💬 บทสนทนา")
    
    # แสดงประวัติแชทด้วย CSS ที่กำหนดไว้
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            content = msg["content"]
            if isinstance(content, list): # กรณีมีรูปภาพ
                st.markdown(f"<div class='user-bubble'>{content[0]['text']} <br><i>[📷 ส่งรูปภาพ]</i></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='user-bubble'>{content}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='ai-bubble'><b>🤖 ADISORN AI:</b><br>{msg['content']}</div>", unsafe_allow_html=True)
            
    st.markdown("<div class='clear'></div>", unsafe_allow_html=True)

    # จัดการ Input จากผู้ใช้ (ทั้งจากการพิมพ์และ Quick Prompts)
    user_input = st.chat_input("พิมพ์ข้อความ หรือแนบรูปภาพทางขวาแล้วพิมพ์ถาม...")
    
    # ถ้ามีการกด Quick Prompt ให้เอาค่านั้นมาใช้แทนการพิมพ์
    if "quick_prompt" in st.session_state:
        user_input = st.session_state.quick_prompt
        del st.session_state.quick_prompt

    if user_input:
        # แสดงข้อความผู้ใช้
        st.markdown(f"<div class='user-bubble'>{user_input}</div><div class='clear'></div>", unsafe_allow_html=True)
        
        # เตรียมข้อมูลสำหรับส่งให้ Groq
        image_url = None
        message_content = user_input
        
        if uploaded_file:
            base64_image = encode_image(uploaded_file)
            image_url = f"data:image/jpeg;base64,{base64_image}"
            # จัดรูปแบบ payload สำหรับ Vision Model
            message_content = [
                {"type": "text", "text": user_input},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
            
        # บันทึกประวัติฝั่งผู้ใช้
        st.session_state.messages.append({"role": "user", "content": message_content})
        
        # ส่วนเรียก AI ประมวลผล
        with st.spinner("AI กำลังประมวลผล..."):
            try:
                # ดึง Persona ที่เลือกมาใช้
                system_instruction = persona_options[selected_persona]
                system_message = {"role": "system", "content": system_instruction}
                
                # ประกอบร่างข้อความทั้งหมด
                full_messages = [system_message] + st.session_state.messages
                
                # ยิง API ไปที่ Groq (ใช้โมเดล Vision เพื่อรองรับทั้งภาพและข้อความ)
                completion = client.chat.completions.create(
                    model="llama-3.2-90b-vision-preview",
                    messages=full_messages,
                    temperature=temperature,
                    max_tokens=2048 # กำหนดความยาวสูงสุดของคำตอบ
                )
                
                response_text = completion.choices[0].message.content
                
                # แสดงคำตอบและบันทึก
                st.markdown(f"<div class='ai-bubble'><b>🤖 ADISORN AI:</b><br>{response_text}</div><div class='clear'></div>", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                
                # สั่งรันหน้าจอใหม่เพื่อเคลียร์ช่อง Input และอัปเดต UI
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}")
