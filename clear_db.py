import streamlit as st
from config import get_db  # ดึงฟังก์ชันเชื่อมต่อฐานข้อมูลจาก config.py

# -------------------------------------------------------------------
# CONFIG & DICTIONARY
# -------------------------------------------------------------------
# รายชื่อตารางในระบบ (ชื่อที่แสดง : ชื่อตารางในฐานข้อมูลจริง)
TABLE_OPTIONS = {
    "วัตถุดิบ (ingredient)": "ingredient",
    "รายการเมนู (menu)": "menu",
    "หมวดหมู่ (category)": "category",
}


# -------------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------------
def clear_selected_tables(tables_to_clear: list[str]) -> tuple[bool, str]:
    """ลบข้อมูลในตารางที่ระบุผ่าน SQL DELETE (ใช้ Transaction)"""
    conn = get_db()
    try:
        with conn:
            for table_name in tables_to_clear:
                # ปลอดภัยเพราะ table_name กรองผ่าน TABLE_OPTIONS แล้ว
                conn.execute(f"DELETE FROM {table_name};")
        return True, f"ล้างข้อมูลในตาราง {', '.join(tables_to_clear)} เรียบร้อยแล้ว!"
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการล้างข้อมูล: {e}"
    finally:
        conn.close()


# -------------------------------------------------------------------
# DIALOG / POPUP CONFIRMATION
# -------------------------------------------------------------------
@st.dialog("⚠️ ยืนยันการล้างข้อมูลฐานข้อมูล")
def confirm_clear_dialog(selected_tables: list[str]):
    """Popup Dialog แจ้งเตือนและขอคำยืนยันก่อนลบข้อมูลจริง"""
    st.error("🚨 **คำเตือน:** การล้างข้อมูลจะไม่สามารถกู้คืนกลับมาได้!")
    st.write("ตารางที่จะถูกล้างข้อมูลทั้งหมด:")

    for table in selected_tables:
        st.markdown(f"- 📦 **`{table}`**")

    st.caption("โปรดตรวจสอบให้แน่ใจก่อนกดปุ่มยืนยันด้านล่าง")

    col_cancel, col_confirm = st.columns(2)

    with col_cancel:
        if st.button("❌ ยกเลิก", use_container_width=True):
            st.rerun()

    with col_confirm:
        if st.button("🔥 ยืนยันล้างข้อมูล", type="primary", use_container_width=True):
            success, message = clear_selected_tables(selected_tables)
            if success:
                st.session_state["clear_db_success"] = message
            else:
                st.session_state["clear_db_error"] = message
            st.rerun()


# -------------------------------------------------------------------
# MAIN RENDER FUNCTION
# -------------------------------------------------------------------
def render():
    st.title("🧹 ระบบล้างข้อมูลในฐานข้อมูล (Clear DB Utility)")

    # แสดงข้อความแจ้งเตือนผลลัพธ์
    if "clear_db_success" in st.session_state:
        st.success(st.session_state["clear_db_success"], icon="✅")
        del st.session_state["clear_db_success"]

    if "clear_db_error" in st.session_state:
        st.error(st.session_state["clear_db_error"], icon="❌")
        del st.session_state["clear_db_error"]

    st.warning(
        "⚠️ **ข้อควรระวัง:** ฟังก์ชันนี้จะทำการลบข้อมูลทั้งหมดในตารางที่คุณเลือก โปรดใช้ด้วยความระมัดระวัง"
    )

    with st.container(border=True):
        st.subheader("📋 เลือกตารางที่ต้องการล้างข้อมูล")

        # ปุ่มเลือกทั้งหมด / ยกเลิกทั้งหมด
        col_all_btn, _ = st.columns([2, 2])
        if "selected_tables_state" not in st.session_state:
            st.session_state["selected_tables_state"] = []

        # Multi-select เลือกตาราง
        selected_display_names = st.multiselect(
            "เลือกตาราง (สามารถเลือกได้มากกว่า 1 ตาราง):",
            options=list(TABLE_OPTIONS.keys()),
            key="db_tables_multiselect",
            help="เลือกตารางที่คุณต้องการล้างข้อมูลภายในออก",
        )

        st.markdown("---")

        col_space, col_action = st.columns([2.5, 1.5])
        with col_action:
            if st.button(
                "🗑️ ล้างข้อมูลที่เลือก",
                type="primary",
                use_container_width=True,
            ):
                if not selected_display_names:
                    st.warning("⚠️ กรุณาเลือกอย่างน้อย 1 ตารางที่ต้องการล้างข้อมูล")
                else:
                    # แปลง Display Name กลับเป็น Table Name ใน SQL
                    target_tables = [
                        TABLE_OPTIONS[name] for name in selected_display_names
                    ]
                    confirm_clear_dialog(target_tables)


if __name__ == "__main__":
    render()