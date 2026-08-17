import pandas as pd
import streamlit as st
from config import get_db  # ดึงฟังก์ชันเชื่อมต่อฐานข้อมูลจาก config.py


# =========================================================
# 💬 Dialog Popup: ยืนยันการลบข้อมูลวัตถุดิบ
# =========================================================
@st.dialog("⚠️ ยืนยันการลบข้อมูล")
def delete_dialog(ing_id, ing_name):
    """ป๊อปอัพยืนยันการลบวัตถุดิบ เพื่อป้องกันการเผลอกดลบโดยไม่ตั้งใจ"""
    st.write(f"คุณต้องการลบวัตถุดิบ **[{ing_id}] {ing_name}** ใช่หรือไม่?")

    col_cancel, col_confirm = st.columns(2)

    # ปุ่มยกเลิก
    if col_cancel.button("ยกเลิก", use_container_width=True):
        st.session_state["show_delete_dialog"] = False
        st.rerun()

    # ปุ่มยืนยันลบ
    if col_confirm.button(
        "🗑️ ยืนยันลบ", type="primary", use_container_width=True
    ):
        conn = get_db()
        try:
            conn.execute(
                "DELETE FROM ingredient WHERE ingredient_id = ?", (ing_id,)
            )
            conn.commit()
            st.toast(f"ลบวัตถุดิบ '{ing_name}' เรียบร้อยแล้ว", icon="✅")

            st.session_state["edit_ing"] = None
            st.session_state["expand_form"] = False
            st.session_state["show_delete_dialog"] = False
            if "ing_table" in st.session_state:
                st.session_state["ing_table"] = {"selection": {"rows": []}}
            st.rerun()
        except Exception as e:
            st.error(f"ไม่สามารถลบได้ (อาจมีการใช้งานวัตถุดิบนี้ในสูตร): {e}")
        finally:
            conn.close()


# =========================================================
# 🚀 Render Main Tab: ฟังก์ชันหลักในการแสดงผลหน้า วัตถุดิบ
# =========================================================
def render():
    st.header("🛒 จัดการวัตถุดิบ (Ingredient)")

    # 1. จัดเตรียม Session States
    if "edit_ing" not in st.session_state:
        st.session_state["edit_ing"] = None

    if "expand_form" not in st.session_state:
        st.session_state["expand_form"] = False

    if "show_delete_dialog" not in st.session_state:
        st.session_state["show_delete_dialog"] = False

    is_editing = st.session_state["edit_ing"] is not None

    if is_editing:
        st.session_state["expand_form"] = True

    # --- ดึงรายชื่อหมวดหมู่ทั้งหมดสำหรับฟอร์มป้อนข้อมูล ---
    conn = get_db()
    try:
        cat_df = pd.read_sql(
            "SELECT category_id, category_name FROM category ORDER BY category_name ASC",
            conn,
        )
    except Exception:
        cat_df = pd.DataFrame()
    finally:
        conn.close()

    cat_options = {}
    if not cat_df.empty:
        for _, row in cat_df.iterrows():
            cid_str = str(row["category_id"]).strip()
            cat_options[f"[{cid_str}] {row['category_name']}"] = cid_str
    else:
        cat_options = {"[NONE] ยังไม่มีหมวดหมู่": ""}

    cat_list = list(cat_options.keys())

    # =========================================================
    # SECTION 1.1: ฟอร์มจัดการข้อมูลวัตถุดิบ
    # =========================================================
    form_title = (
        f"✏️ แก้ไขวัตถุดิบ: {st.session_state['edit_ing']['ingredient_id']}"
        if is_editing
        else "➕ เพิ่มวัตถุดิบใหม่ (รายชิ้น)"
    )

    with st.expander(form_title, expanded=st.session_state["expand_form"]):
        default_id = (
            st.session_state["edit_ing"]["ingredient_id"] if is_editing else ""
        )
        default_name = (
            st.session_state["edit_ing"]["ingredient_name"]
            if is_editing
            else ""
        )
        default_cat_id = (
            str(st.session_state["edit_ing"].get("category_id", "")).strip()
            if is_editing and st.session_state["edit_ing"].get("category_id")
            else ""
        )
        default_unit = (
            st.session_state["edit_ing"].get("stock_unit", "g")
            if is_editing and st.session_state["edit_ing"].get("stock_unit")
            else "g"
        )

        raw_cost = (
            st.session_state["edit_ing"].get("cost_perunit", 0.0)
            if is_editing
            else 0.0
        )
        try:
            default_cost = float(raw_cost) if raw_cost is not None else 0.0
        except (ValueError, TypeError):
            default_cost = 0.0

        cat_idx = 0
        if is_editing and default_cat_id:
            for idx, (label, val) in enumerate(cat_options.items()):
                if val == default_cat_id:
                    cat_idx = idx
                    break

        units_list = ["g", "ml", "ชิ้น", "กล่อง", "ถุง", "กระป๋อง", "ฟอง", "kg", "L"]
        unit_idx = (
            units_list.index(default_unit) if default_unit in units_list else 0
        )

        with st.form("ingredient_form", clear_on_submit=not is_editing):
            c1, c2 = st.columns([1.5, 2.5])
            ing_id = c1.text_input(
                "รหัสวัตถุดิบ*",
                value=default_id,
                disabled=is_editing,
                placeholder="ING-",
            )
            ing_name = c2.text_input(
                "ชื่อวัตถุดิบ*", value=default_name, placeholder="..."
            )

            c3, c4, c5 = st.columns([2, 1.5, 1.5])
            selected_cat_label = c3.selectbox(
                "หมวดหมู่", cat_list, index=cat_idx
            )
            selected_cat_id = cat_options.get(selected_cat_label, "")

            stock_unit = c4.selectbox("หน่วยนับ", units_list, index=unit_idx)
            cost = c5.number_input(
                "ต้นทุนต่อหน่วย (บาท)",
                min_value=0.0,
                value=default_cost,
                step=0.5,
                format="%.2f",
            )

            if is_editing:
                b1, b2, b3 = st.columns([1.5, 1.5, 1])
                submit_btn = b1.form_submit_button(
                    "💾 บันทึกการแก้ไข", type="primary", use_container_width=True, key="btn_save"
                )
                cancel_btn = b2.form_submit_button(
                    "❌ ยกเลิก", use_container_width=True
                )
                delete_btn = b3.form_submit_button(
                    "🗑️ ลบวัตถุดิบ", use_container_width=True
                )

                if cancel_btn:
                    st.session_state["edit_ing"] = None
                    st.session_state["expand_form"] = False
                    if "ing_table" in st.session_state:
                        st.session_state["ing_table"] = {"selection": {"rows": []}}
                    st.rerun()

                if delete_btn:
                    st.session_state["show_delete_dialog"] = True
            else:
                b_space, b_submit = st.columns([3.5, 1.5])
                with b_submit:
                    submit_btn = st.form_submit_button(
                        "💾 บันทึกวัตถุดิบใหม่",type="primary",use_container_width=True, key="btn_save"
                    )

            if submit_btn:
                if not ing_id.strip() or not ing_name.strip():
                    st.session_state["expand_form"] = True
                    st.error("กรุณากรอกรหัสและชื่อวัตถุดิบให้ครบถ้วน")
                else:
                    conn = get_db()
                    try:
                        if is_editing:
                            conn.execute(
                                """
                                UPDATE ingredient 
                                SET ingredient_name = ?, category_id = ?, stock_unit = ?, cost_perunit = ?
                                WHERE ingredient_id = ?
                                """,
                                (
                                    ing_name.strip(),
                                    selected_cat_id if selected_cat_id else None,
                                    stock_unit,
                                    cost,
                                    ing_id.strip(),
                                ),
                            )
                            conn.commit()
                            st.toast("อัปเดตข้อมูลวัตถุดิบเรียบร้อยแล้ว!", icon="✅")
                            st.session_state["edit_ing"] = None
                            if "ing_table" in st.session_state:
                                st.session_state["ing_table"] = {"selection": {"rows": []}}
                        else:
                            conn.execute(
                                """
                                INSERT INTO ingredient (ingredient_id, ingredient_name, category_id, stock_unit, cost_perunit)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (
                                    ing_id.strip(),
                                    ing_name.strip(),
                                    selected_cat_id if selected_cat_id else None,
                                    stock_unit,
                                    cost,
                                ),
                            )
                            conn.commit()
                            st.toast("เพิ่มวัตถุดิบใหม่เรียบร้อยแล้ว!", icon="🎉")

                        st.session_state["expand_form"] = False
                        st.rerun()
                    except Exception as e:
                        st.session_state["expand_form"] = True
                        st.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}")
                    finally:
                        conn.close()

    if st.session_state.get("show_delete_dialog") and st.session_state["edit_ing"]:
        delete_dialog(
            st.session_state["edit_ing"]["ingredient_id"],
            st.session_state["edit_ing"]["ingredient_name"],
        )

    st.divider()

    # =========================================================
    # SECTION 2: ตารางแสดงรายการวัตถุดิบและการกรองข้อมูล
    # =========================================================
    st.markdown(
        """
        <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 8px;">
            📋 รายการวัตถุดิบทั้งหมด 
            <span style="font-size: 0.85rem; font-weight: 400; color: #8b949e; margin-left: 6px;">
                (คลิกที่แถวเพื่อแก้ไข)
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    query = """
    SELECT 
        i.ingredient_id,
        i.ingredient_name,
        i.category_id,
        COALESCE(c.category_name, 'ไม่ระบุหมวดหมู่') AS category_name,
        i.stock_unit,
        i.cost_perunit,
        i.current_stock,
        i.min_stock
    FROM ingredient i
    LEFT JOIN category c ON i.category_id = c.category_id
    ORDER BY i.ingredient_id ASC
    """

    conn = get_db()
    try:
        ingredients = conn.execute(query).fetchall()
    finally:
        conn.close()

    ing_list = [dict(row) for row in ingredients]

    # --- สรุปตัวเลือกหมวดหมู่ที่มีอยู่จริงในรายการวัตถุดิบ ---
    unique_cats = {}
    for item in ing_list:
        cat_id_raw = item.get("category_id")
        cat_id_key = str(cat_id_raw).strip() if cat_id_raw is not None else "NONE"
        cat_name_display = item.get("category_name", "ไม่ระบุหมวดหมู่")
        
        if cat_id_key not in unique_cats:
            unique_cats[cat_id_key] = cat_name_display

    # สร้าง Dictionary สำหรับ Dropdown กรอง
    filter_cat_dict = {"ALL": "แสดงทุกหมวดหมู่"}
    for cid, cname in unique_cats.items():
        if cid == "NONE":
            filter_cat_dict[cid] = "❓ ไม่ระบุหมวดหมู่"
        else:
            filter_cat_dict[cid] = f"📁 {cname} [{cid}]"

    col_cat_filter, col_search_filter = st.columns([2, 2])

    with col_cat_filter:
        selected_filter_cat = st.selectbox(
            "📁 กรองตามหมวดหมู่",
            options=list(filter_cat_dict.keys()),
            format_func=lambda x: filter_cat_dict[x],
            key="ing_cat_filter_selectbox"
        )

    with col_search_filter:
        search_kw = st.text_input(
            "🔍 ค้นหาวัตถุดิบ",
            placeholder="พิมพ์รหัส หรือ ชื่อวัตถุดิบ...",
            key="ing_search_kw_input"
        ).strip().lower()

    # --- Logic การกรองข้อมูล ---
    filtered_ings = []
    for item in ing_list:
        # 1. กรองตามหมวดหมู่
        item_cat_id = str(item.get("category_id")).strip() if item.get("category_id") is not None else "NONE"
        
        if selected_filter_cat == "ALL":
            cat_match = True
        else:
            cat_match = (item_cat_id == selected_filter_cat)

        # 2. กรองตามคำค้นหา
        if search_kw:
            search_match = (
                search_kw in str(item["ingredient_id"]).lower()
                or search_kw in str(item["ingredient_name"]).lower()
                or search_kw in str(item["category_name"]).lower()
            )
        else:
            search_match = True

        if cat_match and search_match:
            filtered_ings.append(item)

    # แสดงผลตาราง Dataframe
    if filtered_ings:
        df = pd.DataFrame(filtered_ings)

        df_display = df.rename(
            columns={
                "ingredient_id": "รหัสวัตถุดิบ",
                "ingredient_name": "ชื่อวัตถุดิบ",
                "category_name": "หมวดหมู่",
                "stock_unit": "หน่วยนับ",
                "cost_perunit": "ต้นทุน/หน่วย (บาท)",
                "current_stock": "คงเหลือ",
                "min_stock": "ขั้นต่ำ",
            }
        )[
            [
                "รหัสวัตถุดิบ",
                "ชื่อวัตถุดิบ",
                "หมวดหมู่",
                "หน่วยนับ",
                "ต้นทุน/หน่วย (บาท)",
                "คงเหลือ",
                "ขั้นต่ำ",
            ]
        ]

        event = st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
            key="ing_table",
            column_config={
                "ต้นทุน/หน่วย (บาท)": st.column_config.NumberColumn(format="%.2f ฿"),
                "คงเหลือ": st.column_config.NumberColumn(format="%.2f"),
                "ขั้นต่ำ": st.column_config.NumberColumn(format="%.2f"),
            },
        )

        if event.selection.rows:
            selected_idx = event.selection.rows[0]
            selected_item = filtered_ings[selected_idx]

            if st.session_state["edit_ing"] != selected_item:
                st.session_state["edit_ing"] = selected_item
                st.rerun()
    else:
        st.info("ไม่พบข้อมูลวัตถุดิบตามหมวดหมู่หรือคำค้นหานี้")

    # =========================================================
    # SECTION 1.2: Bulk Import (CSV)
    # =========================================================
    with st.expander("📥 นำเข้าข้อมูลวัตถุดิบจากไฟล์ CSV (Bulk Import)"):
        st.caption(
            "📌 **หัวคอลัมน์ใน CSV ที่รองรับ:** `ingredient_id`, `ingredient_name`, `category_id`, `stock_unit`, `cost_perunit`, `current_stock`, `min_stock`"
        )

        uploaded_file = st.file_uploader(
            "เลือกไฟล์ .csv เพื่อนำเข้า",
            type=["csv"],
            key="ing_csv_uploader",
        )

        if uploaded_file is not None:
            try:
                df_upload = pd.read_csv(uploaded_file)
                df_upload.columns = df_upload.columns.str.strip()

                required_cols = ["ingredient_id", "ingredient_name"]
                missing_cols = [col for col in required_cols if col not in df_upload.columns]

                if missing_cols:
                    st.error(f"❌ ไฟล์ CSV ขาดคอลัมน์จำเป็น: **{', '.join(missing_cols)}**")
                else:
                    if "category_id" not in df_upload.columns:
                        df_upload["category_id"] = None
                    if "stock_unit" not in df_upload.columns:
                        df_upload["stock_unit"] = "g"
                    if "cost_perunit" not in df_upload.columns:
                        df_upload["cost_perunit"] = 0.0
                    if "current_stock" not in df_upload.columns:
                        df_upload["current_stock"] = 0.0
                    if "min_stock" not in df_upload.columns:
                        df_upload["min_stock"] = 0.0

                    st.markdown("**ตัวอย่างข้อมูลที่จะนำเข้า (5 รายการแรก):**")
                    st.dataframe(df_upload.head(), use_container_width=True)

                    if st.button(
                        "🚀 ยืนยันนำเข้าข้อมูลลงฐานข้อมูล",
                        type="primary",
                        use_container_width=True,
                    ):
                        conn = get_db()
                        try:
                            records = []
                            for _, row in df_upload.iterrows():
                                records.append(
                                    (
                                        str(row["ingredient_id"]).strip(),
                                        str(row["ingredient_name"]).strip(),
                                        str(row["category_id"]).strip()
                                        if pd.notna(row["category_id"]) and str(row["category_id"]).strip() != ""
                                        else None,
                                        str(row["stock_unit"]).strip() if pd.notna(row["stock_unit"]) else "g",
                                        float(row["cost_perunit"]) if pd.notna(row["cost_perunit"]) else 0.0,
                                        float(row["current_stock"]) if pd.notna(row["current_stock"]) else 0.0,
                                        float(row["min_stock"]) if pd.notna(row["min_stock"]) else 0.0,
                                    )
                                )

                            conn.executemany(
                                """
                                INSERT OR REPLACE INTO ingredient 
                                (ingredient_id, ingredient_name, category_id, stock_unit, cost_perunit, current_stock, min_stock)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                """,
                                records,
                            )
                            conn.commit()

                            st.toast(f"นำเข้าข้อมูลสำเร็จทั้งหมด {len(records)} รายการ!", icon="🎉")
                            st.rerun()
                        except Exception as e:
                            st.error(f"เกิดข้อผิดพลาดขณะนำเข้าข้อมูล: {e}")
                        finally:
                            conn.close()
            except Exception as e:
                st.error(f"ไม่สามารถอ่านไฟล์ CSV ได้: {e}")