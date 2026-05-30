import streamlit as st
import base64
import json
import requests
from datetime import datetime
from groq import Groq

# ==========================================
# 1. การตั้งค่าหน้าจอและหน้าตา UI (Page Config & CSS)
# ==========================================
# กำหนดหน้าจอแบบ Wide และตั้งชื่อหัวข้อเว็บ
st.set_page_config(page_title="ADISORN AI 3.0", page_icon="🔮", layout="wide")

# ปรับแต่งสไตล์เพื่อความงามแบบมินิมอลและระบบความปลอดภัยป้องกันการก๊อปปี้โค้ด
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

    /* ==========================================
       ระบบความปลอดภัย: ป้องกันการก๊อปปี้และซ่อนเมนู
       ========================================== */
    /* 1. ซ่อนปุ่มเมนูขวาบน (Hamburger Menu) และปุ่ม Deploy ของ Streamlit */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stDecoration"] {display: none;}
    
    /* 2. บล็อกการลากคลุมดำตัวอักษรเพื่อคัดลอก (Disable Text Selection) */
    body, .stApp, .user-bubble, .ai-bubble, p, span, div {
        -webkit-touch-callout: none; /* iOS Safari */
        -webkit-user-select: none;   /* Safari */
        -khtml-user-select: none;     /* Konqueror HTML */
        -moz-user-select: none;       /* Firefox */
        -ms-user-select: none;        /* Internet Explorer/Edge */
        user-select: none;            /* Non-prefixed version, currently supported by Chrome and Opera */
    }
    </style>
    
    <script>
    /* 3. บล็อกการคลิกขวาป้องกันการกด Inspect Element / View Source ด้วย JavaScript */
    document.addEventListener('contextmenu', event => event.preventDefault());
    
    /* 4. บล็อกปุ่มลัดแป้นพิมพ์ F12, Ctrl+Shift+I, Ctrl+Shift+J, Ctrl+U */
    document.onkeydown = function(e) {
        if (e.keyCode == 123) { // F12
            return false;
        }
        if (e.ctrlKey && e.shiftKey && e.keyCode == 'I'.charCodeAt(0)) { // Ctrl+Shift+I
            return false;
        }
        if (e.ctrlKey && e.shiftKey && e.keyCode == 'J'.charCodeAt(0)) { // Ctrl+Shift+J
            return false;
        }
        if (e.ctrlKey && e.keyCode == 'U'.charCodeAt(0)) { // Ctrl+U
            return false;
        }
    };
    </script>
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

# เรียกดู Groq API Key จากระบบ Secrets
if "GROQ_API_KEY" not in st.secrets:
    st.error("⚠️ ไม่พบรหัส GROQ_API_KEY ในระบบ Secrets กรุณาตั้งค่าก่อนใช้งาน")
    st.stop()

# เชื่อมต่อ Groq Client
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ตรวจสอบว่ามี Gemini API Key สำหรับโมเดลวิเคราะห์ภาพหรือไม่
gemini_key = st.secrets.get("GEMINI_API_KEY", "")

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
        "นักการตลาด": "คุณคือ Marketing Guru ชื่ออดิศร เชี่ยวชาญด้านจิตวิทยาและการตลาด เสนอไอเดียสร้างสรรค์ที่แปลกใหม่",
        "ไกด์นำเที่ยว": "คุณคือไกด์นำเที่ยวท้องถิ่นที่รอบรู้ เชี่ยวชาญเรื่องสถานที่ท่องเที่ยวและอาหารอร่อย",
        "เกมเมอร์": "คุณคือเกมเมอร์ตัวยง รู้ลึกรู้จริงเรื่องเกมทุกแนวและพร้อมป้ายยาเกมสนุกๆ ให้ผู้ใช้"
    }
    selected_persona = st.selectbox("เลือก Persona:", list(persona_options.keys()), label_visibility="collapsed")
    
    # 4.2 แถบเลื่อนปรับค่า Temperature
    st.markdown("<p class='sidebar-section'>🌡️ ระดับความสร้างสรรค์ของคำตอบ</p>", unsafe_allow_html=True)
    temperature = st.slider("0 = แน่นวิชาการ, 1 = ตอบแบบสร้างสรรค์", min_value=0.0, max_value=1.0, value=0.6, step=0.1)
    
    st.divider()

    # 4.3 หมวดแนะนำสิ่งต่างๆ (Smart Recommendations) - ฟีเจอร์ใหม่
    st.markdown("<p class='sidebar-section'>✨ หมวดแนะนำสิ่งต่างๆ</p>", unsafe_allow_html=True)
    with st.expander("คลิกเพื่อเลือกเรื่องที่อยากให้ AI แนะนำ", expanded=False):
        if st.button("🗺️ แนะนำสถานที่ท่องเที่ยว", use_container_width=True):
            st.session_state.quick_prompt = "ช่วยแนะนำสถานที่ท่องเที่ยวที่น่าสนใจในช่วงนี้ให้หน่อย ขอแบบมีจุดเด่นและกิจกรรมที่ห้ามพลาด"
            st.rerun()
        if st.button("🎮 แนะนำเกมน่าเล่น", use_container_width=True):
            st.session_state.quick_prompt = "ช่วยแนะนำวิดีโอเกมหรือเกมมือถือที่สนุกและกำลังฮิตในช่วงนี้ พร้อมบอกจุดเด่นและแนวเกมให้หน่อย"
            st.rerun()
        if st.button("🍜 แนะนำเมนูอาหารอร่อยๆ", use_container_width=True):
            st.session_state.quick_prompt = "ช่วยแนะนำเมนูอาหารเด็ดๆ พร้อมบอกรสชาติและวัตถุดิบคร่าวๆ เผื่อไปหาทานหรือทำกินเองหน่อย"
            st.rerun()
        if st.button("🍿 แนะนำหนัง / ซีรีส์", use_container_width=True):
            st.session_state.quick_prompt = "ช่วยแนะนำหนังหรือซีรีส์สนุกๆ ที่ควรดูให้หน่อย ขอพลอตเรื่องคร่าวๆ และเหตุผลที่ควรดู"
            st.rerun()
        
        st.divider()
        st.markdown("**💡 หรือกรอกเรื่องที่อยากให้แนะนำเอง:**")
        # ช่องกรอกแบบ Custom สำหรับขอคำแนะนำ
        custom_topic = st.text_input("พิมพ์เรื่องที่ต้องการ (เช่น คาเฟ่, หนังสือ):", placeholder="เช่น หนังสือพัฒนาตัวเอง...")
        if st.button("🔍 ค้นหาคำแนะนำ", use_container_width=True):
            if custom_topic:
                st.session_state.quick_prompt = f"ช่วยแนะนำเกี่ยวกับ '{custom_topic}' ให้หน่อย ขอแบบเจาะลึก น่าสนใจ และเป็นประโยชน์"
                st.rerun()
            else:
                st.warning("กรุณาพิมพ์เรื่องที่ต้องการให้แนะนำก่อนครับ")

    st.divider()

    # 4.4 เครื่องมืออัปโหลดภาพประกอบการวิเคราะห์ (Vision Input)
    st.markdown("<p class='sidebar-section'>👁️ ระบบวิเคราะห์รูปภาพ (Gemini Inside)</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("แนบรูปภาพอ้างอิง:", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="รูปภาพที่เตรียมวิเคราะห์", use_column_width=True)
        if not gemini_key:
            st.warning("💡 ตรวจพบการแนบรูปภาพ! กรุณาเพิ่มคีย์ `GEMINI_API_KEY` ในหน้า Secrets เพื่อปลดล็อกระบบวิเคราะห์รูปภาพฟรี")
        
    st.divider()
    
    # 4.5 ฟังก์ชันจัดการเนื้อหา (Summarize & Export Tools)
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

# ==========================================
# 5. พื้นที่ส่วนแสดงบทสนทนาหลักกลางหน้าจอ (Centered Chat Area)
# ==========================================
_, col_main, _ = st.columns([1, 4, 1])

with col_main:
    st.write("### 💬 กล่องข้อความ ADISORN AI")
    
    # วนลูปวาดกล่องแชททีละรายการตามประวัติ
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            content = msg["content"]
            if isinstance(content, list):
                st.markdown(f"<div class='user-bubble'>{content[0]['text']} <br><i>[📷 ส่งรูปภาพประกอบ]</i></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='user-bubble'>{content}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='ai-bubble'><b>🤖 ADISORN AI:</b><br>{msg['content']}</div>", unsafe_allow_html=True)
            
    st.markdown("<div class='clear'></div>", unsafe_allow_html=True)

    # ช่องรับข้อมูลข้อความ (Chat Input Bar)
    user_input = st.chat_input("พิมพ์ถามเรื่องชีววิทยา เขียนโค้ด ขอคำแนะนำ หรือส่งรูปทางซ้ายเพื่อวิเคราะห์...")
    
    # ดักจับค่าจาก Quick Prompt / สรุปความ / หมวดแนะนำ
    if "quick_prompt" in st.session_state:
        user_input = st.session_state.quick_prompt
        del st.session_state.quick_prompt

    if user_input:
        # วาดข้อความผู้ใช้ทันที
        st.markdown(f"<div class='user-bubble'>{user_input}</div><div class='clear'></div>", unsafe_allow_html=True)
        
        # คัดเลือกระบบโมเดลตามไฟล์รูปภาพ
        if uploaded_file and gemini_key:
            # ใช้ระบบวิเคราะห์ภาพระดับโลกของ Gemini 2.5 Flash
            base64_image = encode_image(uploaded_file)
            st.session_state.messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": user_input},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            })
            
            with st.spinner("ADISORN AI (Gemini Vision) กำลังสแกนภาพและประมวลผล..."):
                try:
                    system_instruction = persona_options[selected_persona]
                    
                    # เรียกใช้ Gemini REST API โดยตรงแบบเสถียรที่สุด
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
                    payload = {
                        "contents": [{
                            "role": "user",
                            "parts": [
                                {"text": user_input},
                                {
                                    "inlineData": {
                                        "mimeType": uploaded_file.type,
                                        "data": base64_image
                                    }
                                }
                            ]
                        }],
                        "systemInstruction": {
                            "parts": [{"text": system_instruction}]
                        },
                        "generationConfig": {
                            "temperature": temperature,
                            "maxOutputTokens": 2048
                        }
                    }
                    
                    response = requests.post(url, json=payload)
                    response_json = response.json()
                    
                    # ตรวจสอบความถูกต้องของคำตอบจาก API (ดักจับ API Key Gemini ผิดพลาด)
                    if "error" in response_json:
                        err_msg = response_json["error"].get("message", "")
                        if "api key" in err_msg.lower() or response.status_code == 400:
                            st.error("❌ **รหัส GEMINI_API_KEY ของบอสไม่ถูกต้อง!** \n\nกรุณาตรวจสอบว่าคัดลอกคีย์จาก Google AI Studio มาครบถ้วน ไม่มีตัวอักษรเกินหรือเว้นวรรคในหน้า Secrets นะครับ")
                        else:
                            st.error(f"❌ เกิดข้อผิดพลาดจากระบบวิเคราะห์ภาพ: {err_msg}")
                        st.stop()

                    response_text = response_json["candidates"][0]["content"]["parts"][0]["text"]
                    
                    st.markdown(f"<div class='ai-bubble'><b>🤖 ADISORN AI:</b><br>{response_text}</div><div class='clear'></div>", unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อระบบวิเคราะห์ภาพ: {e}")
        else:
            # ถ้าไม่มีรูปภาพ หรือยังไม่ได้ใส่คีย์วิเคราะห์ภาพของ Gemini ให้ใช้ Groq จัดการ
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            with st.spinner("ADISORN AI กำลังรวบรวมข้อมูลคำตอบให้คุณ..."):
                try:
                    system_instruction = persona_options[selected_persona]
                    system_message = {"role": "system", "content": system_instruction}
                    
                    # แปลงประวัติแชทให้เข้ากับฟอร์แมต Groq
                    formatted_messages = [system_message]
                    for m in st.session_state.messages:
                        # กรองเอาเฉพาะข้อมูลตัวอักษรเพื่อส่งไปที่โมเดลข้อความล้วน
                        if isinstance(m["content"], list):
                            formatted_messages.append({"role": m["role"], "content": m["content"][0]["text"]})
                        else:
                            formatted_messages.append({"role": m["role"], "content": m["content"]})
                    
                    # เรียกโมเดล Groq Llama 3.3 70B รุ่นเสถียรที่สุดในการสนทนาธรรมดา
                    completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=formatted_messages,
                        temperature=temperature,
                        max_tokens=2048
                    )
                    
                    response_text = completion.choices[0].message.content
                    st.markdown(f"<div class='ai-bubble'><b>🤖 ADISORN AI:</b><br>{response_text}</div><div class='clear'></div>", unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    st.rerun()
                    
                except Exception as e:
                    # ดักจับกรณี API Key ของ Groq ผิดพลาดในรูปแบบ 401 หรือ invalid_api_key
                    err_str = str(e).lower()
                    if "401" in err_str or "api_key" in err_str or "invalid" in err_str:
                        st.error("❌ **รหัส GROQ_API_KEY ของบอสไม่ถูกต้อง!** \n\nกรุณาตรวจสอบหน้า **Secrets ของ Streamlit** ว่าคีย์คัดลอกมาจาก Groq Console ครบทุกตัวอักษร ไม่มีตัวอักษรขาดหายหรือเว้นวรรคเกินเข้ามานะครับบอส")
                    else:
                        st.error(f"❌ เกิดข้อผิดพลาดในการประมวลผลข้อความ: {e}")
