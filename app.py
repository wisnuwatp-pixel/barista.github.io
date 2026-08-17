import importlib
import config
import streamlit as st
import styles

import tab_barista_trainee
import tab_dashboard as tab_dashboard
from db_manager import render_backup_ui

# =========================================================
# 1. Import โมดูลหน้างานต่างๆ
# =========================================================
import tab_category
import tab_barista_trainee  
import tab_ing_mixer
import tab_ingredient
import tab_menu 
import tab_recipe
import step_trainer

# บังคับ Reload โมดูลเพื่อให้เปลี่ยนโค้ดแล้ว Streamlit อัปเดตทันที
importlib.reload(styles)
importlib.reload(tab_barista_trainee)
importlib.reload(tab_category)
importlib.reload(tab_ing_mixer) 
importlib.reload(tab_ingredient)
importlib.reload(tab_menu)
importlib.reload(tab_recipe)
importlib.reload(step_trainer)

st.markdown(
    """
    <style>
    /* 🟢 ปุ่ม Primary ใน Sidebar (เมนูที่กดเลือกอยู่) */
    [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {
        background-color: #1E293B !important; /* สีกรมท่าเข้ม */
        color: #FFFFFF !important;
        border-color: #1E293B !important;
        font-weight: 600 !important;
    }
    
    /* 🖱️ ตอนเอาเมาส์ชี้ปุ่ม Primary (ปรับให้สว่างขึ้นเนียนๆ) */
    [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:hover {
        background-color: #334155 !important; /* Slate 700 */
        border-color: #334155 !important;
        color: #FFFFFF !important;
    }

    /* ⚪ ปุ่ม Secondary ใน Sidebar (เมนูอื่นๆ ที่ไม่ได้เลือก) */
    [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] {
        background-color: #F8FAFC !important;
        color: #475569 !important;
        border-color: #E2E8F0 !important;
    }
    
    /* 🖱️ ตอนเอาเมาส์ชี้ปุ่ม Secondary */
    [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover {
        background-color: #E2E8F0 !important;
        color: #0F172A !important;
        border-color: #CBD5E1 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 2. Page Config (ต้องเป็นคำสั่ง Streamlit ตัวแรกสุดเสมอ!)
# =========================================================
st.set_page_config(
    page_title="Grizzly Cafe - POS & Inventory",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# 3. Init DB & Apply Global Styles
# =========================================================
config.init_db()
styles.apply_global_styles()

# =========================================================
# 4. Sidebar Menu Configuration
# =========================================================
# ตั้งค่าหน้าเริ่มต้นถ้ายังไม่ได้เลือก
if "page" not in st.session_state:
    st.session_state["page"] = "หน้าหลัก"

# 📌 [จุดที่ 1 สำหรับเพิ่มเมนูใหม่]:
# เพิ่ม Tuple ("Key สำหรับอ้างอิงระบบ", "ข้อความปุ่มที่แสดงบน UI") ลงในรายการ menu_items
menu_items = [
    ("หน้าหลัก", "📊 หน้าหลัก"),
    ("เรียนรู้", "📚 trainee"),
    ("หมวดหมู่", "📁 หมวดหมู่"),
    ("วัตถุดิบ", "🛒 วัตถุดิบ"),
    ("สูตรผสมย่อย","🧪 สูตรผสมย่อย",), 
    ("เมนู", "🥤 เมนู"),
    ("สูตร", "📝 สูตร"),
    ("บันทึกการสั่งซื้อ", "🛒 บันทึกการสั่งซื้อ"),
    ("จัดการ", "⚙️ จัดการฐานข้อมูล (DB)"),
    ("สำรองข้อมูล", "💾 สำรองข้อมูล (Backup)")
]

# สร้าง UI เมนูที่ Sidebar

with st.sidebar:
    st.header("POS & Inventory V.1")
    st.subheader("📌 เมนูการทำงาน")

    # วนลูปสร้างปุ่มเมนูตามรายการใน menu_items
    for key_name, label in menu_items:
        is_active = st.session_state["page"] == key_name
        # ปุ่มที่กดเลือกอยู่จะเป็นสีหลัก (primary) ปุ่มอื่นเป็นสีรอง (secondary)
        if st.button(
            label,
            key=f"nav_{key_name}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state["page"] = key_name
            st.rerun()

# อ่านค่าหน้าที่เลือกอยู่ปัจจุบัน
page = st.session_state["page"]

# =========================================================
# 5. Spacer ส่วนกลาง (ดันระยะลงมาจากขอบบน)
# =========================================================
st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

# =========================================================
# 6. Page Routing (สลับการแสดงผลตามหน้างานที่เลือก)
# =========================================================
# 📌 [จุดที่ 2 สำหรับเพิ่มการเชื่อมโยงหน้าใหม่]:
# เพิ่มเงื่อนไข elif page == "Key_ที่ตั้งไว้": แล้วสั่งเรียกใช้ฟังก์ชัน render ของหน้านั้นๆ

if page == "หน้าหลัก":
    tab_dashboard.render()

elif page == "เรียนรู้":
    tab_barista_trainee.render()

elif page == "หมวดหมู่":
    tab_category.render()

elif page == "วัตถุดิบ":
    tab_ingredient.render()

elif page == "สูตรผสมย่อย":
    tab_ing_mixer.render()

elif page == "เมนู":
    tab_menu.render()

elif page == "สูตร":
    tab_recipe.render()

elif page == "บันทึกการสั่งซื้อ":
    st.subheader("🛒 บันทึกการสั่งซื้อ (Purchase Log)")

elif page== "จัดการ":
    step_trainer.render_table_manager()

elif page == "สำรองข้อมูล":
    render_backup_ui()