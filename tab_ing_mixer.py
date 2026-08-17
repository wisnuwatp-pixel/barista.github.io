import pandas as pd
import streamlit as st
from config import get_db, init_db


# =========================================================
# 🗄️ Database Functions (ตรงตาม Schema recipe_items)
# =========================================================
def fetch_all_ingredients():
    """ดึงรายการวัตถุดิบเดี่ยวทั้งหมดมาแสดงใน Dropdown"""
    try:
        with get_db() as conn:
            query = "SELECT ingredient_id, ingredient_name, stock_unit FROM ingredient ORDER BY ingredient_id"
            return pd.read_sql_query(query, conn)
    except Exception:
        return pd.DataFrame(
            columns=["ingredient_id", "ingredient_name", "stock_unit"]
        )


def fetch_mix_recipe_summary():
    """ดึงตารางสรุปสูตรผสมย่อยทั้งหมด พร้อมชื่อสูตร (นับจาก parent_id ที่ขึ้นต้นด้วย MIX)"""
    try:
        with get_db() as conn:
            query = """
            SELECT 
                parent_id AS recipe_id,
                MAX(COALESCE(recipe_item_name, parent_id)) AS recipe_item_name,
                COUNT(recipe_item_id) AS item_count
            FROM recipe_items
            WHERE parent_id LIKE 'MIX%'
            GROUP BY parent_id
            ORDER BY parent_id
            """
            return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงสรุปสูตร: {e}")
        return pd.DataFrame(columns=["recipe_id", "recipe_item_name", "item_count"])


def fetch_recipe_items_by_parent(parent_id):
    """ดึงรายการส่วนผสมย่อยและชื่อสูตรตาม parent_id"""
    try:
        with get_db() as conn:
            query = """
            SELECT 
                recipe_item_id,
                recipe_item_name,
                child_id,
                quantity,
                unit
            FROM recipe_items
            WHERE parent_id = ?
            ORDER BY recipe_item_id
            """
            return pd.read_sql_query(query, conn, params=(str(parent_id),))
    except Exception:
        return pd.DataFrame(
            columns=["recipe_item_id", "recipe_item_name", "child_id", "quantity", "unit"]
        )


def save_entire_recipe(parent_id, recipe_item_name, items_list, ing_label_to_id_map):
    """บันทึกส่วนผสมย่อยลงตาราง recipe_items พร้อม recipe_item_name"""
    p_id_str = str(parent_id).strip()
    p_name_str = str(recipe_item_name).strip()

    with get_db() as conn:
        cursor = conn.cursor()

        # เคลียร์ส่วนผสมเก่าของ parent_id นี้
        cursor.execute(
            "DELETE FROM recipe_items WHERE parent_id = ?", (p_id_str,)
        )

        # บันทึกส่วนผสมชุดใหม่
        for item in items_list:
            child_val = str(item.get("child_id", "")).strip()
            c_id = ing_label_to_id_map.get(child_val, child_val)
            qty = item.get("quantity", 0.0)
            u_unit = str(item.get("unit", "")).strip()

            if c_id and qty > 0 and u_unit:
                cursor.execute(
                    """
                    INSERT INTO recipe_items (parent_id, recipe_item_name, child_id, quantity, unit)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (p_id_str, p_name_str, c_id, float(qty), u_unit),
                )

        conn.commit()


def delete_entire_recipe(parent_id):
    """ลบส่วนผสมทั้งหมดของ parent_id ออกจาก recipe_items"""
    p_id_str = str(parent_id).strip()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM recipe_items WHERE parent_id = ?", (p_id_str,)
        )
        conn.commit()


# =========================================================
# 💬 Dialog Popup: ยืนยันการลบสูตรผสม
# =========================================================
@st.dialog("⚠️ ยืนยันการลบสูตรผสม")
def delete_recipe_dialog(parent_id):
    """ป๊อปอัพยืนยันการลบสูตร"""
    st.write(f"คุณต้องการลบสูตรผสม **[{parent_id}]** ใช่หรือไม่?")
    st.caption("🚨 การลบจะทำให้ข้อมูลวัตถุดิบส่วนผสมในสูตรนี้ถูกลบทั้งหมด")

    col_cancel, col_confirm = st.columns(2)

    if col_cancel.button("ยกเลิก", use_container_width=True):
        st.rerun()

    if col_confirm.button("🔥 ยืนยันลบสูตร", type="primary", use_container_width=True):
        delete_entire_recipe(parent_id)
        st.toast(f"ลบสูตร [{parent_id}] เรียบร้อยแล้ว", icon="🗑️")

        if "current_edit_items" in st.session_state:
            del st.session_state["current_edit_items"]
        if "current_edit_name" in st.session_state:
            del st.session_state["current_edit_name"]

        # เลือกสูตรถัดไปขึ้นมาแทน
        df_after_del = fetch_mix_recipe_summary()
        if not df_after_del.empty:
            st.session_state["selected_mixer_id"] = str(
                df_after_del.iloc[0]["recipe_id"]
            )
        else:
            st.session_state["selected_mixer_id"] = "MIX-ING-001"

        st.rerun()


# =========================================================
# 🖥️ Main Render Function
# =========================================================
def render():
    try:
        init_db()
    except Exception:
        pass

    # Custom CSS ปรับขนาด Font ช่องกรอกข้อมูล
    st.markdown(
        """
        <style>
        div[data-baseweb="input"] input { font-size: 14px !important; }
        div[data-baseweb="select"] span { font-size: 14px !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.header("🧪 จัดการสูตรผสมย่อย (Mixer / Sub-Recipe)")

    df_summary = fetch_mix_recipe_summary()
    df_ing = fetch_all_ingredients()

    # แมปข้อมูลวัตถุดิบสำหรับแสดงใน Selectbox
    ing_map_options = {}
    ing_label_to_id = {}
    if not df_ing.empty:
        for _, row in df_ing.iterrows():
            label = f"{row['ingredient_id']} | {row['ingredient_name']}"
            ing_map_options[label] = row["ingredient_id"]
            ing_label_to_id[label] = row["ingredient_id"]
            ing_label_to_id[row["ingredient_id"]] = row["ingredient_id"]

    ing_options_list = list(ing_map_options.keys())

    # State Management Initial
    if "mode" not in st.session_state:
        st.session_state["mode"] = "edit"

    if "selected_mixer_id" not in st.session_state:
        if not df_summary.empty:
            st.session_state["selected_mixer_id"] = str(
                df_summary.iloc[0]["recipe_id"]
            )
        else:
            st.session_state["selected_mixer_id"] = "MIX-ING-001"

    # =========================================================
    # 📌 ส่วนที่ 1: ตารางสรุปรายการสูตรทั้งหมด
    # =========================================================
    c_top_title, c_top_btn = st.columns([3, 1])
    with c_top_title:
        st.subheader("📋 รายการสูตรผสมย่อยทั้งหมด")
    with c_top_btn:
        if st.button("➕ สร้างสูตรใหม่", use_container_width=True, type="primary", key="btn_create_new"):
            st.session_state["mode"] = "create"
            st.session_state["create_recipe_items"] = []
            st.rerun()

    if not df_summary.empty:
        df_summary_display = df_summary.copy()
        current_sel = str(st.session_state.get("selected_mixer_id", ""))

        df_summary_display.insert(
            0,
            "เลือก",
            df_summary_display["recipe_id"].astype(str) == current_sel,
        )

        edited_summary = st.data_editor(
            df_summary_display[
                ["เลือก", "recipe_id", "recipe_item_name", "item_count"]
            ],
            column_config={
                "เลือก": st.column_config.CheckboxColumn(
                    "เลือก",
                    help="ติ๊กเพื่อเลือกสูตรนี้ลงมาแก้ไข",
                    default=False,
                    width=50,
                ),
                "recipe_id": st.column_config.TextColumn(
                    "รหัสสูตรผสม (parent_id)", disabled=True, width=180
                ),
                "recipe_item_name": st.column_config.TextColumn(
                    "ชื่อสูตรผสม (recipe_item_name)", disabled=True, width=220
                ),
                "item_count": st.column_config.NumberColumn(
                    "จำนวนส่วนผสม", disabled=True, width=120
                ),
            },
            disabled=["recipe_id", "recipe_item_name", "item_count"],
            hide_index=True,
            use_container_width=True,
            key="summary_table_editor",
        )

        # ตรวจจับการเลือกสูตรจาก Checkbox
        newly_checked = edited_summary[
            (edited_summary["เลือก"] == True)
            & (edited_summary["recipe_id"].astype(str) != current_sel)
        ]

        if not newly_checked.empty:
            selected_id = str(newly_checked.iloc[0]["recipe_id"])
            st.session_state["selected_mixer_id"] = selected_id
            st.session_state["mode"] = "edit"
            if "current_edit_items" in st.session_state:
                del st.session_state["current_edit_items"]
            if "current_edit_name" in st.session_state:
                del st.session_state["current_edit_name"]
            st.toast(f"เลือกสูตร [{selected_id}] แล้ว", icon="👇")
            st.rerun()
    else:
        st.info("ยังไม่มีสูตรผสมในระบบ")

    st.markdown("---")

    # =========================================================
    # 📌 ส่วนที่ 2: แก้ไขสูตร
    # =========================================================
    if st.session_state["mode"] == "edit":
        active_id = st.session_state["selected_mixer_id"]

        st.subheader(f"🛠️ แก้ไขสูตรผสม: [{active_id}]")

        # โหลดส่วนผสมและชื่อสูตรถ้ายังไม่มีใน State
        if (
            "current_edit_items" not in st.session_state
            or st.session_state.get("active_edit_id") != active_id
        ):
            df_items = fetch_recipe_items_by_parent(active_id)
            id_to_label = {v: k for k, v in ing_map_options.items()}

            loaded_items = []
            init_name = ""
            if not df_items.empty:
                init_name = df_items.iloc[0].get("recipe_item_name") or ""

            for _, r in df_items.iterrows():
                child_label = id_to_label.get(r["child_id"], r["child_id"])
                loaded_items.append(
                    {
                        "child_id": child_label,
                        "quantity": float(r["quantity"]),
                        "unit": str(r["unit"]),
                    }
                )

            st.session_state["current_edit_items"] = loaded_items
            st.session_state["current_edit_name"] = str(init_name)
            st.session_state["active_edit_id"] = active_id

        # ช่องกรอกรหัสสูตร และ ชื่อสูตรผสม (recipe_item_name)
        c_edit_id, c_edit_name = st.columns([1, 2])
        with c_edit_id:
            edit_parent_id = st.text_input(
                "รหัสสูตรผสม (parent_id)",
                value=active_id,
                disabled=True,
                key="edit_parent_id_input",
            )
        with c_edit_name:
            edit_item_name = st.text_input(
                "ชื่อสูตรผสม (recipe_item_name)*",
                value=st.session_state.get("current_edit_name", ""),
                key="edit_recipe_item_name_input",
            )
            st.session_state["current_edit_name"] = edit_item_name

        items = st.session_state["current_edit_items"]

        st.markdown("##### 📝 รายการวัตถุดิบส่วนผสม:")

        l_h1, l_h2, l_h3, l_h4 = st.columns([3, 1.5, 1.5, 0.8])
        l_h1.caption("วัตถุดิบเดี่ยว (child_id)")
        l_h2.caption("ปริมาณที่ใช้ (quantity)")
        l_h3.caption("หน่วยวัด (unit)")
        l_h4.caption("ลบ")

        to_delete_idx = None
        for idx, item in enumerate(items):
            r_col1, r_col2, r_col3, r_col4 = st.columns([3, 1.5, 1.5, 0.8])

            curr_ing_idx = (
                ing_options_list.index(item["child_id"])
                if item["child_id"] in ing_options_list
                else 0
            )
            item["child_id"] = r_col1.selectbox(
                "วัตถุดิบ",
                options=ing_options_list,
                index=curr_ing_idx,
                key=f"e_ing_{active_id}_{idx}",
                label_visibility="collapsed",
            )

            item["quantity"] = r_col2.number_input(
                "ปริมาณ",
                min_value=0.1,
                value=float(item["quantity"]),
                step=1.0,
                key=f"e_qty_{active_id}_{idx}",
                label_visibility="collapsed",
            )

            unit_opts = ["ml", "g", "oz", "shot", "pcs"]
            u_idx = (
                unit_opts.index(item["unit"])
                if item["unit"] in unit_opts
                else 0
            )
            item["unit"] = r_col3.selectbox(
                "หน่วยวัด",
                options=unit_opts,
                index=u_idx,
                key=f"e_unit_{active_id}_{idx}",
                label_visibility="collapsed",
            )

            if r_col4.button(
                "🗑️", key=f"btn_del_item_{active_id}_{idx}", help="ลบรายการนี้"
            ):
                to_delete_idx = idx

        if to_delete_idx is not None:
            st.session_state["current_edit_items"].pop(to_delete_idx)
            st.rerun()

        if st.button("➕ เพิ่มวัตถุดิบส่วนผสม", key="btn_add_more_item"):
            default_ing = ing_options_list[0] if ing_options_list else ""
            st.session_state["current_edit_items"].append(
                {"child_id": default_ing, "quantity": 10.0, "unit": "ml"}
            )
            st.rerun()

        st.markdown("---")

        # ปุ่มบันทึก / ลบ
        b_col1, b_col2, _ = st.columns([1, 1, 1], gap="small")
        with b_col1:
            if st.button(
                "💾 บันทึก", type="primary", use_container_width=True, key="btn_save"
            ):
                if not edit_item_name.strip():
                    st.error("❌ กรุณากรอกชื่อสูตรผสม (recipe_item_name)")
                elif not st.session_state["current_edit_items"]:
                    st.error("❌ ต้องมีวัตถุดิบอย่างน้อย 1 รายการ")
                else:
                    save_entire_recipe(
                        edit_parent_id,
                        edit_item_name,
                        st.session_state["current_edit_items"],
                        ing_label_to_id,
                    )
                    st.toast(
                        f"อัปเดตสูตร [{edit_parent_id}] เรียบร้อยแล้ว!",
                        icon="✅",
                    )
                    st.rerun()

        with b_col2:
            if st.button("🗑️ ลบสูตรนี้", use_container_width=True):
                delete_recipe_dialog(edit_parent_id)

    # =========================================================
    # 📌 ส่วนที่ 3: โซนสร้างสูตรใหม่
    # =========================================================
    elif st.session_state["mode"] == "create":
        st.subheader("✨ สร้างสูตรผสมใหม่")

        # ฟอร์แมตรหัสอัตโนมัติ MIX-ING-00X
        next_number = len(df_summary) + 1
        new_auto_id = f"MIX-ING-{next_number:03d}"

        # ช่องกรอกรหัสสูตร และ ชื่อสูตรผสม
        c_create_id, c_create_name = st.columns([1, 2])
        with c_create_id:
            new_id = st.text_input(
                "รหัสสูตรใหม่ (parent_id)*",
                value=new_auto_id,
                key="create_new_id_input",
            )
        with c_create_name:
            new_item_name = st.text_input(
                "ชื่อสูตรผสม (recipe_item_name)*",
                placeholder="เช่น เบสนมสูตรกลมกล่อม",
                key="create_new_name_input",
            )

        st.markdown("---")
        st.markdown("##### 📝 รายการวัตถุดิบส่วนผสม:")

        if (
            "create_recipe_items" not in st.session_state
            or not st.session_state["create_recipe_items"]
        ):
            default_ing = ing_options_list[0] if ing_options_list else ""
            st.session_state["create_recipe_items"] = [
                {"child_id": default_ing, "quantity": 10.0, "unit": "ml"}
            ]

        create_items = st.session_state["create_recipe_items"]

        cl_h1, cl_h2, cl_h3, cl_h4 = st.columns([3, 1.5, 1.5, 0.8])
        cl_h1.caption("วัตถุดิบเดี่ยว (child_id)")
        cl_h2.caption("ปริมาณที่ใช้ (quantity)")
        cl_h3.caption("หน่วยวัด (unit)")
        cl_h4.caption("ลบ")

        del_create_idx = None
        for idx, item in enumerate(create_items):
            cr_col1, cr_col2, cr_col3, cr_col4 = st.columns(
                [3, 1.5, 1.5, 0.8]
            )

            curr_c_idx = (
                ing_options_list.index(item["child_id"])
                if item["child_id"] in ing_options_list
                else 0
            )
            item["child_id"] = cr_col1.selectbox(
                "วัตถุดิบ",
                options=ing_options_list,
                index=curr_c_idx,
                key=f"c_ing_{idx}",
                label_visibility="collapsed",
            )

            item["quantity"] = cr_col2.number_input(
                "ปริมาณ",
                min_value=0.1,
                value=float(item["quantity"]),
                step=1.0,
                key=f"c_qty_{idx}",
                label_visibility="collapsed",
            )

            unit_opts = ["ml", "g", "oz", "shot", "pcs"]
            u_c_idx = (
                unit_opts.index(item["unit"])
                if item["unit"] in unit_opts
                else 0
            )
            item["unit"] = cr_col3.selectbox(
                "หน่วยวัด",
                options=unit_opts,
                index=u_c_idx,
                key=f"c_unit_{idx}",
                label_visibility="collapsed",
            )

            if cr_col4.button(
                "🗑️", key=f"btn_del_create_{idx}", help="ลบรายการนี้"
            ):
                del_create_idx = idx

        if del_create_idx is not None:
            st.session_state["create_recipe_items"].pop(del_create_idx)
            st.rerun()

        if st.button("➕ เพิ่มวัตถุดิบส่วนผสม", key="btn_add_create_item"):
            default_ing = ing_options_list[0] if ing_options_list else ""
            st.session_state["create_recipe_items"].append(
                {"child_id": default_ing, "quantity": 10.0, "unit": "ml"}
            )
            st.rerun()

        st.markdown("---")
        btn_c1, btn_c2, _ = st.columns([1, 1, 1], gap="small")
        with btn_c1:
            if st.button(
                "💾 บันทึกสูตรใหม่", type="primary", use_container_width=True, key="btn_save"
            ):
                if not new_id.strip():
                    st.error("❌ กรุณากรอกรหัสสูตร (parent_id)")
                elif not new_item_name.strip():
                    st.error("❌ กรุณากรอกชื่อสูตรผสม (recipe_item_name)")
                elif not st.session_state["create_recipe_items"]:
                    st.error("❌ กรุณาเพิ่มส่วนผสมอย่างน้อย 1 รายการ")
                else:
                    save_entire_recipe(
                        new_id,
                        new_item_name,
                        st.session_state["create_recipe_items"],
                        ing_label_to_id,
                    )
                    st.toast(
                        f"สร้างสูตรใหม่ [{new_id}] สำเร็จแล้ว!", icon="🎉"
                    )
                    st.session_state["selected_mixer_id"] = new_id
                    st.session_state["mode"] = "edit"
                    if "create_recipe_items" in st.session_state:
                        del st.session_state["create_recipe_items"]
                    st.rerun()

        with btn_c2:
            if st.button("❌ ยกเลิก", use_container_width=True):
                st.session_state["mode"] = "edit"
                st.rerun()


if __name__ == "__main__":
    render()