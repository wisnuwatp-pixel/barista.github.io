import base64
import pandas as pd
import streamlit as st
from config import get_db  # ดึงฟังก์ชันเชื่อมต่อฐานข้อมูลจาก config.py


# =========================================================
# 💬 Dialog Popup: ยืนยันการลบข้อมูลหมวดหมู่
# =========================================================
@st.dialog("⚠️ ยืนยันการลบข้อมูล")
def delete_dialog(cat_id, cat_name):
    """ป๊อปอัพยืนยันการลบหมวดหมู่ เพื่อป้องกันการเผลอกดลบโดยไม่ตั้งใจ"""
    st.write(f"คุณต้องการลบหมวดหมู่ **[{cat_id}] {cat_name}** ใช่หรือไม่?")

    col_cancel, col_confirm = st.columns(2)

    if col_cancel.button("ยกเลิก", use_container_width=True):
        st.rerun()

    if col_confirm.button(
        "🗑️ ยืนยันลบ", type="primary", use_container_width=True
    ):
        conn = get_db()
        try:
            conn.execute(
                "DELETE FROM category WHERE category_id = ?", (cat_id,)
            )
            conn.commit()
            st.toast(f"ลบหมวดหมู่ '{cat_name}' เรียบร้อยแล้ว", icon="✅")

            st.session_state["edit_cat"] = None
            st.rerun()
        except Exception as e:
            st.error(f"ไม่สามารถลบได้: {e}")
        finally:
            conn.close()


# =========================================================
# 🛠️ HELPER FUNCTIONS: ฟังก์ชันสำหรับอัปโหลดข้อมูลจาก DF
# =========================================================
def import_categories_from_df(df: pd.DataFrame) -> int:
    """นำเข้าข้อมูลหมวดหมู่จาก DataFrame เข้าฐานข้อมูล (UPSERT)"""
    conn = get_db()
    required_cols = ["category_id", "category_name", "type"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = "วัตถุดิบ" if col == "type" else ""

    count = 0
    try:
        with conn:
            for _, row in df.iterrows():
                cat_id = str(row["category_id"]).strip() if pd.notna(row["category_id"]) else ""
                if not cat_id:
                    continue

                cat_name = str(row["category_name"]).strip() if pd.notna(row["category_name"]) else ""
                cat_type = str(row["type"]).strip() if pd.notna(row["type"]) else "วัตถุดิบ"

                conn.execute(
                    """
                    INSERT INTO category (category_id, category_name, type)
                    VALUES (?, ?, ?)
                    ON CONFLICT(category_id) DO UPDATE SET
                        category_name=excluded.category_name,
                        type=excluded.type
                    """,
                    (cat_id, cat_name, cat_type),
                )
                count += 1
    finally:
        conn.close()
    return count


# =========================================================
# 🚀 Render Main Tab: ฟังก์ชันหลักในการแสดงผลหน้า หมวดหมู่
# =========================================================
def render():
    st.header("📁 จัดการหมวดหมู่ (Category)")

    # 1. จัดเตรียม Session States
    if "edit_cat" not in st.session_state:
        st.session_state["edit_cat"] = None

    if "expand_form" not in st.session_state:
        st.session_state["expand_form"] = False

    is_editing = st.session_state["edit_cat"] is not None

    if is_editing:
        st.session_state["expand_form"] = True

    # =========================================================
    # SECTION 1: ฟอร์มจัดการข้อมูลหมวดหมู่ (Expander)
    # =========================================================
    form_title = (
        f"✏️ แก้ไขหมวดหมู่: {st.session_state['edit_cat']['category_id']}"
        if is_editing
        else "➕ เพิ่มหมวดหมู่ใหม่"
    )

    with st.expander(form_title, expanded=st.session_state["expand_form"]):
        default_id = (
            st.session_state["edit_cat"]["category_id"] if is_editing else ""
        )
        default_name = (
            st.session_state["edit_cat"]["category_name"] if is_editing else ""
        )
        default_type = (
            st.session_state["edit_cat"]["type"] if is_editing else "วัตถุดิบ"
        )
        type_idx = 0 if default_type == "วัตถุดิบ" else 1

        with st.form("category_form", clear_on_submit=not is_editing):
            c1, c2, c3 = st.columns([1.5, 2.5, 1.5])

            cat_id = c1.text_input(
                "รหัสหมวดหมู่",
                value=default_id,
                disabled=is_editing,
                placeholder="CAT-",
            )
            cat_name = c2.text_input(
                "ชื่อหมวดหมู่", value=default_name, placeholder="..."
            )
            cat_type = c3.selectbox("ประเภท", ["วัตถุดิบ", "เมนู"], index=type_idx)

            if is_editing:
                col_save, col_cancel, col_del = st.columns([1, 1, 1])
                submit_btn = col_save.form_submit_button(
                    "💾 บันทึก", type="primary", use_container_width=True, key="btn_save"
                )
                cancel_btn = col_cancel.form_submit_button(
                    "❌ ยกเลิก", use_container_width=True
                )
                delete_btn = col_del.form_submit_button(
                    "🗑️ ลบหมวดหมู่", type="secondary", use_container_width=True
                )

                if cancel_btn:
                    st.session_state["edit_cat"] = None
                    st.session_state["expand_form"] = False
                    st.rerun()

                if delete_btn:
                    delete_dialog(
                        st.session_state["edit_cat"]["category_id"],
                        st.session_state["edit_cat"]["category_name"],
                    )
            else:
                b_space, b_submit = st.columns([3.5, 1.5])
                with b_submit:
                    submit_btn = st.form_submit_button(
                        "💾 บันทึก",type="primary",use_container_width=True, key="btn_save"
                    )

            if submit_btn:
                if not cat_id.strip() or not cat_name.strip():
                    st.session_state["expand_form"] = True
                    st.error("กรุณากรอกรหัสและชื่อหมวดหมู่ให้ครบถ้วน")
                else:
                    conn = get_db()
                    try:
                        if is_editing:
                            conn.execute(
                                """
                                UPDATE category 
                                SET category_name = ?, type = ? 
                                WHERE category_id = ?
                                """,
                                (cat_name.strip(), cat_type, cat_id.strip()),
                            )
                            conn.commit()
                            st.toast("อัปเดตข้อมูลเรียบร้อยแล้ว!", icon="✅")
                            st.session_state["edit_cat"] = None
                        else:
                            conn.execute(
                                "INSERT INTO category VALUES (?, ?, ?)",
                                (cat_id.strip(), cat_name.strip(), cat_type),
                            )
                            conn.commit()
                            st.toast("เพิ่มหมวดหมู่เรียบร้อยแล้ว!", icon="🎉")

                        st.session_state["expand_form"] = False
                        st.rerun()
                    except Exception as e:
                        st.session_state["expand_form"] = True
                        st.error(
                            f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}"
                        )
                    finally:
                        conn.close()


    # =========================================================
    # SECTION 3: ตารางแสดงรายการหมวดหมู่ทั้งหมด + ช่องค้นหา
    # =========================================================
    with st.container(border=True):
        st.markdown(
            """
            <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 8px;">
                📋 รายการหมวดหมู่ทั้งหมด 
                <span style="font-size: 0.85rem; font-weight: 400; color: #8b949e; margin-left: 6px;">
                    (คลิกที่แถวเพื่อแก้ไข)
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ช่องค้นหา
        search_kw = (
            st.text_input(
                "🔍 ค้นหาหมวดหมู่",
                placeholder="พิมพ์รหัส, ชื่อ หรือประเภทเพื่อค้นหา...",
                label_visibility="collapsed",
            )
            .strip()
            .lower()
        )

        # ดึงข้อมูลจากฐานข้อมูล
        conn = get_db()
        try:
            categories = conn.execute("SELECT * FROM category").fetchall()
        finally:
            conn.close()

        cat_list = [dict(c) for c in categories]

        # กรองรายการตามคำค้นหา
        filtered_cats = [
            c
            for c in cat_list
            if search_kw in c["category_id"].lower()
            or search_kw in c["category_name"].lower()
            or search_kw in c["type"].lower()
        ]

        # แสดงผลตารางแบบ Interactive
        if filtered_cats:
            df = pd.DataFrame(filtered_cats)
            df_display = df.rename(
                columns={
                    "category_id": "รหัสหมวดหมู่",
                    "category_name": "ชื่อหมวดหมู่",
                    "type": "ประเภท",
                }
            )

            event = st.dataframe(
                df_display,
                use_container_width=True,
                height=400,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
            )

            if event.selection.rows:
                selected_idx = event.selection.rows[0]
                selected_item = filtered_cats[selected_idx]

                if st.session_state["edit_cat"] != selected_item:
                    st.session_state["edit_cat"] = selected_item
                    st.rerun()
        else:
            st.info("ไม่พบข้อมูลหมวดหมู่")

    # =========================================================
    # SECTION 2: นำเข้าข้อมูลด้วยไฟล์ CSV / Excel (แบบ Expander ขยายตัวได้)
    # =========================================================
    with st.expander("📤 นำเข้าข้อมูลด้วยไฟล์ CSV / Excel (Bulk Import)", expanded=False):
        st.markdown(
            """
            **คำแนะนำการเตรียมไฟล์:**
            * รองรับไฟล์ **CSV** และ **Excel (.xlsx, .xls)**
            * คอลัมน์ที่จำเป็นต้องมีในไฟล์: `category_id`, `category_name`, `type`
            * *หมายเหตุ:* ในช่อง `type` สามารถระบุเป็น `วัตถุดิบ` หรือ `เมนู` ได้
            """
        )

        uploaded_file = st.file_uploader(
            "เลือกไฟล์ข้อมูลหมวดหมู่",
            type=["csv", "xlsx", "xls"],
            key="cat_bulk_import_file",
        )

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file)

                st.write("🔍 **ตัวอย่างข้อมูลที่จะนำเข้า:**")
                st.dataframe(df_upload.head(), use_container_width=True)

                col_imp_space, col_imp_btn = st.columns([3, 1.2])
                with col_imp_btn:
                    if st.button(
                        "🚀 ยืนยันการนำเข้า",type="primary",use_container_width=True,key="btn_save"
                    ):
                        count = import_categories_from_df(df_upload)
                        st.toast(
                            f"นำเข้าข้อมูลสำเร็จทั้งหมด {count} รายการ!",
                            icon="🎉",
                        )
                        st.rerun()

            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")
