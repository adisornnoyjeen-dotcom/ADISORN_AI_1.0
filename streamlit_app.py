import streamlit as st
import base64
import json
from datetime import datetime
from groq import Groq

# ==========================================
# 1. การตั้งค่าหน้าจอและหน้าตา UI (Page Config & CSS)
# ==========================================
# กำหนดหน้าจอแบบ Wide และตั้งชื่อหัวข้อเว็บ
st.set_page_config(page_title="ADISORN AI 3.0", page_icon="🔮", layout="wide")

# ปรับแต่งสไตล์เพื่อความงามแบบมินิมอลและเป็นระเบียบ
st.markdown("""
    <style>
    /* ปรับพื้นหลังหลักของเว็บ */
    .stApp { background-color: #f4f6f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* ปรับแต่งแถบเมนูด้านซ้าย (Sidebar) ให้ดูสะอาด สว่าง ตา */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e5e7eb;
    }
    
    /* สไตล์กล่องแชทฝั่งผู้ใช้ (User Bubble) */
    .user-bubble {
        background-color: #4F46E5; 
        color: white; 
        padding: 12px 18px; 
        border-radius: 18px 18px 0px 18px; 
        margin-bottom: 10px; 
        max-width: 80%; 
        float: right; 
        clear: both; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* สไตล์กล่องแชทฝั่ง AI (Assistant Bubble) */
    .ai-bubble {
        background-color: #ffffff; 
        color: #1f2937; 
        padding: 12px 18px; 
        border-radius: 18px 18px 18px 0px; 
        margin-bottom: 10px; 
        max-width: 80%; 
        float: left; 
        clear: both; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e5e7eb;
    }
    
    /* หัวข้อหมวดหมู่ในแถบ Sidebar */
    .sidebar-section {
        font-weight: bold;
        color: #4F46E5;
        margin-top: 15px;
        margin-bottom: 5px;
        font-size: 0.95rem;
    }
    
    /* เคลียร์ Float ของ CSS */
    .clear { clear: both; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ฟังก์ชันช่วยเหลือ (Helper Functions)
# ==========================================
def encode_image(image_file):
    """ทำการแปลงไฟล์รูปภาพที่อัปโหลดให้อยู่ในรูปแบบ Base64 เพื่อส่งต่อให้ Vision Model ทำงาน"""
    return base64.b64encode(image_file.read()).decode('utf-8')

def export_chat_history():
    """ดึงข้อมูลการแชททั้งหมดใน session มาจัดโครงสร้างข้อความเพื่อดาวน์โหลด"""
    chat_text = "=== ADISORN AI 3.0 Chat History ===\n"
    chat_text += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    for msg in st.session_state.messages:
        role = "👤 คุณ (You)" if msg["role"] == "user" else "🤖 ADISORN AI"
        content = msg["content"]
        # หากเนื้อหามีรูปภาพ ให้แยกข้อความออกแสดงผล
        if isinstance(content, list):
            content = content[0]["text"] + " [แนบไฟล์รูปภาพประกอบ]"
        chat_text += f"{role}:\n{content}\n\n{'-'*40}\n\n"
    return chat_text

# ==========================================
# 3. ตรวจสอบสถานะการทำงาน (Session State Initialization)
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_persona" not in st.session_state:
    st.session_state.current_persona = "ผู้ช่วยทั่วไป"

# เรียกดู Groq API Key จากระบบ Secrets ของเว็บบอร์ด
if "GROQ_API_KEY" not in st.secrets:
    st.error("⚠️ ไม่พบรหัส GROQ_API_KEY ในระบบ Secrets กรุณาตั้งค่าก่อนใช้งาน")
    st.stop()
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ==========================================
# 4. เมนูจัดการด้านซ้ายมือ (Unified Sidebar Panel)
# ==========================================
with st.sidebar:
    st.title("🔮 ADISORN 3.0")
    st.caption("ระบบแชทบอทวิชาการส่วนตัวของคุณ")
    
    # ปุ่มเริ่มการคุยใหม่
    if st.button("➕ สร้างแชทใหม่ (New Chat)", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    # 4.1 ระบบเลือกบทบาท (AI Persona Settings)
    st.markdown("<p class='sidebar-section'>🎭 ปรับแต่งบทบาท AI</p>", unsafe_allow_html=True)
    persona_options = {
        "ผู้ช่วยทั่วไป": "คุณคือ ADISORN AI 3.0 ผู้ช่วยอัจฉริยะ ตอบคำถามเป็นภาษาไทยอย่างเป็นมิตร มินิมอล",
        "นักชีววิทยา": "คุณคือ ศ.ดร.อดิศร ผู้เชี่ยวชาญด้านชีววิทยาและการแพทย์ระดับสูง ตอบด้วยข้อมูลเชิงลึกและศัพท์วิชาการ",
        "โปรแกรมเมอร์": "คุณคือ Senior Developer ชื่ออดิศร เชี่ยวชาญการเขียนโค้ด ตอบตรงประเด็นและให้ตัวอย่างโค้ดที่ถูกต้อง",
        "นักการตลาด": "คุณคือ Marketing Guru ชื่ออดิศร เชี่ยวชาญด้านจิตวิทยาและการตลาด เสนอไอเดียสร้างสรรค์ที่แปลกใหม่"
    }
    selected_persona = st.selectbox("เลือก Persona:", list(persona_options.keys()), label_visibility="collapsed")
    
    # 4.2 แถบเลื่อนปรับค่า Temperature
    st.markdown("<p class='sidebar-section'>🌡️ ระดับความสร้างสรรค์ของคำตอบ</p>", unsafe_allow_html=True)
    temperature = st.slider("0 = แน่นวิชาการ, 1 = ตอบแบบสร้างสรรค์", min_value=0.0, max_value=1.0, value=0.3, step=0.1)
    
    st.divider()

    # 4.3 เครื่องมืออัปโหลดภาพประกอบการวิเคราะห์ (Vision Input) - ดึงกลับมาแล้วจ้าบอส!
    st.markdown("<p class='sidebar-section'>👁️ ระบบวิเคราะห์รูปภาพ</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("แนบรูปภาพอ้างอิง:", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="รูปภาพที่เตรียมวิเคราะห์", use_column_width=True)
        
    st.divider()
    
    # 4.4 ฟังก์ชันจัดการเนื้อหา (Summarize & Export Tools)
    st.markdown("<p class='sidebar-section'>📦 เครื่องมือจัดการข้อมูล</p>", unsafe_allow_html=True)
    if st.button("📝 สรุปเรื่องราวทั้งหมดในแชท", use_container_width=True):
        if len(st.session_state.messages) > 0:
            st.session_state.quick_prompt = "สรุปบทสนทนาที่เราพูดคุยกันทั้งหมดตั้งแต่ต้นจนถึงตอนนี้ให้กระชับเป็นข้อๆ"
            st.rerun()
        else:
            st.warning("ยังไม่มีข้อความสนทนาให้สรุปครับบอส")
            
    if len(st.session_state.messages) > 0:
        chat_data = export_chat_history()
        st.download_button(
            label="💾 บันทึกการแชทลงเครื่อง (.txt)",
            data=chat_data,
            file_name=f"Adisorn_Chat_Log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    st.divider()
    
    # 4.5 ปุ่มคำถามยอดนิยม (Quick Prompts)
    st.markdown("<p class='sidebar-section'>📌 เมนูคำถามด่วน</p>", unsafe_allow_html=True)
    if st.button("🧬 ถามเรื่องพริออน (Prion)", use_container_width=True):
        st.session_state.quick_prompt = "อธิบายเกี่ยวกับโปรตีนพริออน (Prion) และโรคที่เกี่ยวข้องแบบละเอียดเข้าใจง่าย"
        st.rerun()
    if st.button("💻 ช่วยเขียนโปรแกรม Python", use_container_width=True):
        st.session_state.quick_prompt = "ช่วยเขียนโค้ดภาษา Python ดึงข้อมูลสภาพอากาศในปัจจุบันให้หน่อย"
        st.rerun()
    if st.button("📊 ร่างไอเดียเพิ่มยอดขาย", use_container_width=True):
        st.session_state.quick_prompt = "ช่วยเสนอไอเดียการทำการตลาดออนไลน์ให้เข้าถึงวัยรุ่นยุคปัจจุบันหน่อย"
        st.rerun()

# ==========================================
# 5. พื้นที่ส่วนแสดงบทสนทนาหลักกลางหน้าจอ (Centered Chat Area)
# ==========================================
# เว้นระยะด้านข้างเพื่อให้กล่องแชทอยู่บริเวณกึ่งกลางพอดีสายตา ไม่บานกว้างไป
_, col_main, _ = st.columns([1, 4, 1])

with col_main:
    st.write("### 💬 กล่องข้อความ ADISORN AI")
    
    # วนลูปวาดกล่องแชททีละรายการตามประวัติ
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            content = msg["content"]
            # ตรวจสอบรูปแบบกรณีเป็น List (มีข้อความพร้อมภาพ)
            if isinstance(content, list):
                st.markdown(f"<div class='user-bubble'>{content[0]['text']} <br><i>[📷 ส่งรูปภาพประกอบ]</i></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='user-bubble'>{content}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='ai-bubble'><b>🤖 ADISORN AI:</b><br>{msg['content']}</div>", unsafe_allow_html=True)
            
    st.markdown("<div class='clear'></div>", unsafe_allow_html=True)

    # ช่องรับข้อมูลข้อความ (Chat Input Bar)
    user_input = st.chat_input("พิมพ์ถามเรื่องชีววิทยา เขียนโค้ด หรือส่งรูปทางซ้ายเพื่อวิเคราะห์...")
    
    # ดักจับค่าจาก Quick Prompt / สรุปความ
    if "quick_prompt" in st.session_state:
        user_input = st.session_state.quick_prompt
        del st.session_state.quick_prompt

    if user_input:
        # วาดข้อความของผู้ใช้ที่เพิ่งส่งบนหน้าจอทันที
        image_url = None
        message_content = user_input
        selected_model = "llama-3.3-70b-versatile" # โมเดลค่าเริ่มต้นสำหรับพิมพ์คุย
        
        # หากใน Sidebar มีการแนบไฟล์ภาพ ให้เปลี่ยนไปใช้โมเดลวิเคราะห์ภาพอัตโนมัติ
        if uploaded_file:
            base64_image = encode_image(uploaded_file)
            image_url = f"data:image/jpeg;base64,{base64_image}"
            message_content = [
                {"type": "text", "text": user_input},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
            selected_model = "llama-3.2-11b-vision" # สลับมาใช้โมเดล Vision รุ่นมาตรฐาน
            st.markdown(f"<div class='user-bubble'>{user_input} <br><i>[📷 ส่งรูปภาพประกอบ]</i></div><div class='clear'></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='user-bubble'>{user_input}</div><div class='clear'></div>", unsafe_allow_html=True)
            
        st.session_state.messages.append({"role": "user", "content": message_content})
        
        # เริ่มเชื่อมต่อกับ Groq API เพื่อหาคำตอบ
        with st.spinner("ADISORN AI กำลังประมวลผลคำตอบ..."):
            try:
                system_instruction = persona_options[selected_persona]
                system_message = {"role": "system", "content": system_instruction}
                
                full_messages = [system_message] + st.session_state.messages
                
                # เรียกใช้โมเดลตามประเภทข้อมูลที่ส่งไป
                completion = client.chat.completions.create(
                    model=selected_model,
                    messages=full_messages,
                    temperature=temperature,
                    max_tokens=2048
                )
                
                response_text = completion.choices[0].message.content
                
                # แสดงผลและบันทึกข้อมูล
                st.markdown(f"<div class='ai-bubble'><b>🤖 ADISORN AI:</b><br>{response_text}</div><div class='clear'></div>", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                
                # สั่งรีรันแอปเพื่อจัดเรียงกล่องสนทนาให้สวยงามและรีเซ็ตค่า input
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาดในการรับข้อมูล: {e}")
