import base64
import pandas as pd
import streamlit as st
from config import get_db


# -------------------------------------------------------------------
# CUSTOM CSS (NORDIC MINIMALIST STYLING)
# -------------------------------------------------------------------
def apply_menu_styles():
    st.markdown(
        """
        <style>
        /* สไตล์ Card สรุปตัวเลข Metrics ด้านบน */
        .metric-card {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 14px 20px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        }
        .metric-label {
            font-size: 0.82rem;
            color: #64748B;
            font-weight: 600;
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .metric-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #0F172A;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )


# -------------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------------


def get_all_menus() -> pd.DataFrame:
    """ดึงข้อมูลเมนูทั้งหมดพร้อมชื่อหมวดหมู่"""
    conn = get_db()
    try:
        query = """
            SELECT 
                m.menu_id, 
                m.category_id, 
                c.category_name,
                m.menu_name, 
                m.price, 
                m.note, 
                m.img_url
            FROM menu m
            LEFT JOIN category c ON TRIM(UPPER(m.category_id)) = TRIM(UPPER(c.category_id))
            ORDER BY m.menu_id
        """
        df = pd.read_sql_query(query, conn)
    except Exception:
        df = pd.read_sql_query("SELECT * FROM menu", conn)
    finally:
        conn.close()
    return df


def get_all_categories() -> pd.DataFrame:
    """ดึงข้อมูลหมวดหมู่ทั้งหมดออกมาเป็น DataFrame"""
    conn = get_db()
    try:
        df = pd.read_sql_query(
            "SELECT * FROM category ORDER BY category_id", conn
        )
    except Exception:
        df = pd.DataFrame(columns=["category_id", "category_name"])
    finally:
        conn.close()
    return df


def save_menu(
    menu_id: str,
    category_id: str,
    menu_name: str,
    price: float,
    note: str,
    img_url: str,
):
    """บันทึกหรืออัปเดตข้อมูลเมนู (UPSERT)"""
    conn = get_db()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO menu (menu_id, category_id, menu_name, price, note, img_url)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(menu_id) DO UPDATE SET
                    category_id=excluded.category_id,
                    menu_name=excluded.menu_name,
                    price=excluded.price,
                    note=excluded.note,
                    img_url=excluded.img_url
                """,
                (menu_id, category_id, menu_name, price, note, img_url),
            )
    finally:
        conn.close()


def delete_menu(menu_id: str):
    """ลบเมนูตาม menu_id"""
    conn = get_db()
    try:
        with conn:
            conn.execute("DELETE FROM menu WHERE menu_id = ?", (menu_id,))
    finally:
        conn.close()


def convert_image_to_base64(uploaded_file) -> str:
    """แปลงไฟล์ภาพอัปโหลดให้เป็น Base64 Data URL สำหรับเก็บลง Database"""
    bytes_data = uploaded_file.getvalue()
    base64_str = base64.b64encode(bytes_data).decode()
    mime_type = uploaded_file.type
    return f"data:{mime_type};base64,{base64_str}"


# -------------------------------------------------------------------
# DIALOG / POPUP FUNCTIONS
# -------------------------------------------------------------------


@st.dialog("⚠️ ยืนยันการลบรายการ")
def confirm_delete_dialog():
    target = st.session_state.get("delete_target")
    if not target:
        return

    st.write(
        f"คุณต้องการลบเมนู **{target['name']}** (`{target['id']}`) ใช่หรือไม่?"
    )
    st.caption("🚨 การกระทำนี้ไม่สามารถย้อนกลับได้")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("❌ ยกเลิก", use_container_width=True):
            st.session_state["delete_target"] = None
            st.rerun()
    with col2:
        if st.button("🗑️ ยืนยันลบ", type="primary", use_container_width=True):
            delete_menu(target["id"])
            st.session_state["success_msg"] = (
                f"ลบเมนู [{target['id']}] สำเร็จแล้ว!"
            )
            st.session_state["delete_target"] = None
            st.rerun()


# -------------------------------------------------------------------
# MAIN RENDER FUNCTION
# -------------------------------------------------------------------


def render():
    apply_menu_styles()

    st.title("🥤 ระบบจัดการเมนู (Menu Management)")
    st.caption("จัดการเมนูเครื่องดื่ม/อาหาร ราคาขาย หมวดหมู่ และรูปภาพแสดงผล")

    if st.session_state.get("delete_target"):
        confirm_delete_dialog()

    if "success_msg" in st.session_state:
        st.success(st.session_state["success_msg"], icon="✅")
        del st.session_state["success_msg"]

    df_menus = get_all_menus()
    df_categories = get_all_categories()

    # ---------------------------------------------------------------
    # 1. Top Section: Metrics
    # ---------------------------------------------------------------
    total_count = len(df_menus)
    avg_price = (
        df_menus["price"].mean()
        if not df_menus.empty and "price" in df_menus
        else 0.0
    )

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">เมนูทั้งหมด</div><div class="metric-value">{total_count} รายการ</div></div>',
            unsafe_allow_html=True,
        )
    with col_m2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">ราคาขายเฉลี่ย</div><div class="metric-value">฿{avg_price:,.2f}</div></div>',
            unsafe_allow_html=True,
        )
    with col_m3:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">หมวดหมู่ทั้งหมด</div><div class="metric-value">{len(df_categories)} หมวด</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------
    # 2. โซนควบคุมหลัก: [เลือกรายการแก้ไข/ลบ]
    # ---------------------------------------------------------------
    options = ["-- เพิ่มเมนูใหม่ --"] + (
        [
            f"{row['menu_id']} - {row['menu_name']}"
            for _, row in df_menus.iterrows()
        ]
        if not df_menus.empty
        else []
    )

    selected_option = st.selectbox(
        "📌 เลือกรายการเพื่อแก้ไข/ลบ (หรือเลือก 'เพิ่มเมนูใหม่')",
        options,
        key="selected_menu_option",
    )

    # ---------------------------------------------------------------
    # 3. เตรียมข้อมูลค่า Default เมื่อเลือกรายการ
    # ---------------------------------------------------------------
    default_id = ""
    default_cat = ""
    default_name = ""
    default_price_str = ""
    default_note = ""
    default_img = ""
    is_edit_mode = False

    if selected_option != "-- เพิ่มเมนูใหม่ --":
        is_edit_mode = True
        selected_id = selected_option.split(" - ")[0]
        selected_row = df_menus[df_menus["menu_id"] == selected_id].iloc[0]

        default_id = str(selected_row["menu_id"])
        default_cat = (
            str(selected_row["category_id"]).strip()
            if pd.notna(selected_row["category_id"])
            else ""
        )
        default_name = (
            str(selected_row["menu_name"]).strip()
            if pd.notna(selected_row["menu_name"])
            else ""
        )

        if pd.notna(selected_row["price"]):
            price_val = float(selected_row["price"])
            default_price_str = (
                str(int(price_val))
                if price_val.is_integer()
                else str(price_val)
            )

        default_note = (
            str(selected_row["note"]).strip()
            if pd.notna(selected_row["note"])
            else ""
        )
        default_img = (
            str(selected_row["img_url"]).strip()
            if pd.notna(selected_row["img_url"])
            else ""
        )

    # ---------------------------------------------------------------
    # 4. สร้าง รายการ Category Options + MATCHING LOGIC ป้องกันค่าหาย
    # ---------------------------------------------------------------
    cat_options = ["-- ไม่ระบุหมวดหมู่ --"]
    cat_id_list = [""]  # ดัชนี 0 คือค่าว่าง

    if not df_categories.empty and "category_id" in df_categories.columns:
        for _, c_row in df_categories.iterrows():
            c_id = str(c_row["category_id"]).strip()
            if not c_id:
                continue
            c_name = (
                str(c_row["category_name"]).strip()
                if "category_name" in c_row and pd.notna(c_row["category_name"])
                else ""
            )
            label = f"{c_id} - {c_name}" if c_name else c_id
            cat_options.append(label)
            cat_id_list.append(c_id)

    # คำนวณ index ของหมวดหมู่เดิม (Case-insensitive matching)
    default_cat_index = 0
    if default_cat:
        norm_default_cat = default_cat.upper()
        norm_cat_list = [x.upper() for x in cat_id_list]

        if norm_default_cat in norm_cat_list:
            default_cat_index = norm_cat_list.index(norm_default_cat)
        else:
            # กรณีที่รหัสหมวดหมู่อยู่ในตาราง menu แต่ไม่อยู่ในตาราง category
            # ให้ดึงเข้ามาเพิ่มในรายการตัวเลือก เพื่อไม่ให้ค่าเดิมถูกลบหลุดหายไป
            cat_options.append(f"{default_cat} (ไม่พบในตารางหมวดหมู่)")
            cat_id_list.append(default_cat)
            default_cat_index = len(cat_id_list) - 1

    key_prefix = default_id if is_edit_mode else "new_menu_form"
    card_title = (
        f"📝 แก้ไขเมนู: {default_name} ({default_id})"
        if is_edit_mode
        else "➕ ฟอร์มเพิ่มเมนูอาหารใหม่"
    )

    # ---------------------------------------------------------------
    # 5. ฟอร์มเพิ่ม / แก้ไข
    # ---------------------------------------------------------------
    with st.expander(card_title, expanded=is_edit_mode):
        with st.form("menu_form"):
            col1, col2 = st.columns(2)

            with col1:
                menu_id = st.text_input(
                    "รหัสเมนู *",
                    value=default_id,
                    disabled=is_edit_mode,
                    key=f"input_id_{key_prefix}",
                )

                selected_cat_option = st.selectbox(
                    "หมวดหมู่",
                    options=cat_options,
                    index=default_cat_index,
                    key=f"input_cat_{key_prefix}",
                )

                menu_name = st.text_input(
                    "ชื่อเมนู *",
                    value=default_name,
                    key=f"input_name_{key_prefix}",
                )

            with col2:
                price_input = st.text_input(
                    "ราคา (บาท)",
                    value=default_price_str,
                    placeholder="เช่น 55 หรือ 60.50",
                    key=f"input_price_{key_prefix}",
                )

                note = st.text_area(
                    "ส่วนผสม / หมายเหตุ (สำหรับบาริสต้า)",
                    value=default_note,
                    height=108,
                    key=f"input_note_{key_prefix}",
                )

            col_img1, col_img2 = st.columns(2)
            with col_img1:
                uploaded_img_file = st.file_uploader(
                    "อัปโหลดรูปภาพเมนู",
                    type=["jpg", "jpeg", "png", "webp"],
                    key=f"input_file_{key_prefix}",
                )
            with col_img2:
                img_url_input = st.text_input(
                    "หรือระบุ ลิงก์รูปภาพ (img_url)",
                    value=default_img,
                    placeholder="https://example.com/image.jpg",
                    key=f"input_url_{key_prefix}",
                )

            if default_img:
                st.markdown("**🖼️ ภาพตัวอย่างปัจจุบัน:**")
                try:
                    st.image(default_img, width=120)
                except Exception:
                    st.caption("⚠️ ไม่สามารถโหลดตัวอย่างรูปภาพได้")

            st.caption("* จำเป็นต้องกรอกข้อมูล")

            delete_btn = False
            if is_edit_mode:
                col_save, col_del = st.columns(2)
                with col_save:
                    submit_btn = st.form_submit_button("💾 บันทึกข้อมูล",type="primary",use_container_width=True, key="btn_save"
                    )
                with col_del:
                    delete_btn = st.form_submit_button(
                        "🗑️ ลบรายการเมนูนี้",
                        type="secondary",
                        use_container_width=True,
                    )
            else:
                submit_btn = st.form_submit_button(
                    "💾 บันทึกข้อมูล", type="primary", use_container_width=True
                )

        if delete_btn:
            st.session_state["delete_target"] = {
                "id": default_id,
                "name": default_name,
            }
            st.rerun()

        if submit_btn:
            # ดึงค่าหมวดหมู่ตาม Index หรือจากข้อความที่เลือก
            sel_idx = cat_options.index(selected_cat_option)
            category_id = cat_id_list[sel_idx]

            parsed_price = 0.0
            if price_input.strip():
                try:
                    parsed_price = float(price_input.strip().replace(",", ""))
                except ValueError:
                    st.error("❌ กรุณากรอกราคาให้เป็นตัวเลขที่ถูกต้อง")
                    st.stop()

            if not menu_id.strip() or not menu_name.strip():
                st.error("❌ กรุณากรอก 'รหัสเมนู' และ 'ชื่อเมนู' ให้ครบถ้วน")
            else:
                final_img_url = default_img
                if uploaded_img_file is not None:
                    final_img_url = convert_image_to_base64(uploaded_img_file)
                elif img_url_input.strip():
                    final_img_url = img_url_input.strip()

                save_menu(
                    menu_id.strip(),
                    category_id.strip(),
                    menu_name.strip(),
                    parsed_price,
                    note.strip(),
                    final_img_url,
                )
                action_text = "อัปเดต" if is_edit_mode else "เพิ่ม"
                st.session_state["success_msg"] = (
                    f"{action_text}เมนู [{menu_id.strip()}] เรียบร้อยแล้ว!"
                )
                st.rerun()

    st.markdown("---")

    # ---------------------------------------------------------------
    # 6. ตารางแสดงผล
    # ---------------------------------------------------------------
    st.header("📋 รายการเมนูในระบบ")

    if df_menus.empty:
        st.info("ยังไม่มีข้อมูลเมนูในระบบ")
    else:
        col_search, col_count = st.columns(
            [3, 1], vertical_alignment="bottom"
        )
        with col_search:
            search_query = st.text_input(
                "🔍 ค้นหาเมนู (ตามชื่อ หรือ รหัสเมนู)", ""
            )

        if search_query.strip():
            df_filtered = df_menus[
                df_menus["menu_name"].str.contains(
                    search_query, case=False, na=False
                )
                | df_menus["menu_id"].str.contains(
                    search_query, case=False, na=False
                )
            ]
        else:
            df_filtered = df_menus

        with col_count:
            st.caption(f"แสดงทั้งหมด {len(df_filtered)} รายการ")

        cols_config = {
            "img_url": st.column_config.ImageColumn(
                "ภาพตัวอย่าง", width="small"
            ),
            "menu_id": st.column_config.TextColumn("รหัสเมนู", width="small"),
            "category_id": st.column_config.TextColumn(
                "รหัสหมวดหมู่", width="small"
            ),
            "category_name": st.column_config.TextColumn(
                "ชื่อหมวดหมู่", width="medium"
            ),
            "menu_name": st.column_config.TextColumn(
                "ชื่อเมนู", width="large"
            ),
            "price": st.column_config.NumberColumn(
                "ราคาขาย", format="฿%.2f", width="small"
            ),
            "note": st.column_config.TextColumn(
                "ส่วนผสม/หมายเหตุ", width="medium"
            ),
        }

        st.dataframe(
            df_filtered,
            use_container_width=True,
            height=420,
            column_config=cols_config,
            hide_index=True,
        )