import pandas as pd
import streamlit as st
from config import get_db


# =============================================================
# Helper Functions: คำนวณต้นทุน และดึงข้อมูล
# =============================================================
def get_sub_recipe_unit_cost(conn, parent_id):
    """คำนวณต้นทุนต่อหน่วยของสูตรย่อย (recipe_items) โดยคิดจากราคาวัตถุดิบตั้งต้น (child_id)"""
    query = """
        SELECT ri.child_id, ri.quantity, i.cost_perunit
        FROM recipe_items ri
        LEFT JOIN ingredient i ON ri.child_id = i.ingredient_id
        WHERE ri.parent_id = ?
    """
    df = pd.read_sql_query(query, conn, params=[parent_id])
    if df.empty:
        return 0.0

    total_cost = (df["quantity"] * df["cost_perunit"].fillna(0.0)).sum()
    return total_cost


def get_menu_recipe_details(conn, menu_id):
    """ดึงรายการวัตถุดิบทั้งหมดในสูตรเมนูหลัก (ทั้งวัตถุดิบดิบ และสูตรผสมย่อย)"""
    # 1. วัตถุดิบหลักตรงๆ จากตาราง ingredient
    query_ing = """
        SELECT 
            r.recipe_id,
            r.ingredient_id,
            i.ingredient_name AS item_name,
            r.qty,
            i.stock_unit AS unit,
            i.cost_perunit AS unit_cost,
            'วัตถุดิบหลัก' AS item_type
        FROM recipe r
        JOIN ingredient i ON r.ingredient_id = i.ingredient_id
        WHERE r.menu_id = ?
    """
    df_ing = pd.read_sql_query(query_ing, conn, params=[menu_id])

    # 2. ส่วนผสมที่เป็นสูตรย่อย จากตาราง recipe_items
    query_sub = """
        SELECT DISTINCT
            r.recipe_id,
            r.ingredient_id,
            ri.recipe_item_name AS item_name,
            r.qty,
            ri.unit AS unit,
            'สูตรผสมย่อย' AS item_type
        FROM recipe r
        JOIN recipe_items ri ON r.ingredient_id = ri.parent_id
        WHERE r.menu_id = ?
    """
    df_sub = pd.read_sql_query(query_sub, conn, params=[menu_id])

    # คำนวณต้นทุนของสูตรย่อย
    if not df_sub.empty:
        df_sub["unit_cost"] = df_sub["ingredient_id"].apply(
            lambda pid: get_sub_recipe_unit_cost(conn, pid)
        )
    else:
        df_sub["unit_cost"] = pd.Series(dtype=float)

    # รวมตารางวัตถุดิบหลัก + สูตรย่อย
    df_all = pd.concat([df_ing, df_sub], ignore_index=True)

    if not df_all.empty:
        df_all["total_cost"] = df_all["qty"] * df_all["unit_cost"].fillna(0.0)
    else:
        df_all = pd.DataFrame(
            columns=[
                "recipe_id",
                "ingredient_id",
                "item_name",
                "qty",
                "unit",
                "unit_cost",
                "item_type",
                "total_cost",
            ]
        )

    return df_all


# =============================================================
# Main Render Function (เรียกใช้งานจาก app.py)
# =============================================================
def render():
    st.title("📝 จัดการสูตรเครื่องดื่ม (Menu Recipe)")
    st.caption("ระบบคำนวณต้นทุนวัตถุดิบและกำไรขั้นต้นต่อแก้วสำหรับ Grizzly Cafe")

    with get_db() as conn:
        # ดึงรายการเมนูขายทั้งหมด
        df_menus = pd.read_sql_query(
            """
            SELECT m.menu_id, m.menu_name, m.price, c.category_name 
            FROM menu m
            LEFT JOIN category c ON m.category_id = c.category_id
            ORDER BY m.menu_id
        """,
            conn,
        )

        if df_menus.empty:
            st.warning(
                "⚠️ ยังไม่มีข้อมูลเมนูในระบบ กรุณาเพิ่มรายการเมนูก่อนที่หน้า '🥤 เมนู'"
            )
            return

        # -------------------------------------------------------------
        # 1. เลือกเมนู (แสดง ID + ชื่อเมนู + ราคา + หมวดหมู่)
        # -------------------------------------------------------------
        menu_dict = {
            f"[{row['menu_id']}] {row['menu_name']} ({row['category_name'] or 'ไม่ระบุหมวด'}) - ฿{row['price']:.2f}": row[
                "menu_id"
            ]
            for _, row in df_menus.iterrows()
        }

        selected_label = st.selectbox(
            "🎯 เลือกเมนูที่ต้องการผูกสูตร:", list(menu_dict.keys())
        )
        selected_menu_id = menu_dict[selected_label]
        selected_menu_info = df_menus[
            df_menus["menu_id"] == selected_menu_id
        ].iloc[0]

        st.markdown("---")

        # ดึงข้อมูลสูตรปัจจุบัน
        df_recipe = get_menu_recipe_details(conn, selected_menu_id)

        # -------------------------------------------------------------
        # 2. สรุปต้นทุนและ Margin (แสดงแนวยาวด้านบน Top-Down)
        # -------------------------------------------------------------
        total_cost = (
            df_recipe["total_cost"].sum() if not df_recipe.empty else 0.0
        )
        price = float(selected_menu_info["price"])
        profit = price - total_cost
        cost_pct = (total_cost / price * 100) if price > 0 else 0.0
        margin_pct = (profit / price * 100) if price > 0 else 0.0

        st.subheader(
            f"📊 สรุปต้นทุน & กำไร: [{selected_menu_info['menu_id']}] {selected_menu_info['menu_name']}"
        )

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("ราคาขาย", f"฿{price:,.2f}")
        with m2:
            st.metric(
                "ต้นทุนวัตถุดิบรวม",
                f"฿{total_cost:,.2f}",
                delta=f"{cost_pct:.1f}% ของราคาขาย",
                delta_color="inverse",
            )
        with m3:
            st.metric(
                "กำไรขั้นต้น (Margin)",
                f"฿{profit:,.2f}",
                delta=f"{margin_pct:.1f}% Margin",
            )

        st.markdown("---")

        # -------------------------------------------------------------
        # 3. ตารางส่วนผสมในสูตรปัจจุบัน (แสดงเต็มความกว้างหน้าจอ)
        # -------------------------------------------------------------
        st.subheader("📋 รายการวัตถุดิบในสูตรปัจจุบัน")

        if not df_recipe.empty:
            df_show = df_recipe[
                [
                    "ingredient_id",
                    "item_name",
                    "item_type",
                    "qty",
                    "unit",
                    "unit_cost",
                    "total_cost",
                ]
            ].copy()
            df_show.columns = [
                "รหัสวัตถุดิบ/สูตรย่อย",
                "ชื่อวัตถุดิบ / สูตรย่อย",
                "ประเภท",
                "ปริมาณที่ใช้",
                "หน่วย",
                "ต้นทุน/หน่วย",
                "ต้นทุนรวม (บาท)",
            ]

            st.dataframe(
                df_show.style.format(
                    {
                        "ปริมาณที่ใช้": "{:,.2f}",
                        "ต้นทุน/หน่วย": "฿{:,.3f}",
                        "ต้นทุนรวม (บาท)": "฿{:,.2f}",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

            # ปุ่มลบส่วนผสมออกจากสูตร
            with st.expander("🗑️ ลบส่วนผสมออกจากสูตร"):
                del_recipe_id = st.selectbox(
                    "เลือกรายการที่จะลบ:",
                    options=df_recipe["recipe_id"].tolist(),
                    format_func=lambda x: f"[{df_recipe[df_recipe['recipe_id']==x]['ingredient_id'].values[0]}] {df_recipe[df_recipe['recipe_id']==x]['item_name'].values[0]} ({df_recipe[df_recipe['recipe_id']==x]['qty'].values[0]} {df_recipe[df_recipe['recipe_id']==x]['unit'].values[0]})",
                )
                if st.button("ยืนยันลบรายการ", type="primary"):
                    cur = conn.cursor()
                    cur.execute(
                        "DELETE FROM recipe WHERE recipe_id = ?",
                        (del_recipe_id,),
                    )
                    conn.commit()
                    st.success("ลบส่วนผสมออกจากสูตรเรียบร้อยแล้ว!")
                    st.rerun()
        else:
            st.info(
                "💡 เมนูนี้ยังไม่มีการผูกส่วนผสม สามารถเพิ่มส่วนผสมใหม่ได้จากฟอร์มด้านล่าง"
            )

        st.markdown("---")

        # -------------------------------------------------------------
        # 4. ฟอร์มเพิ่มส่วนผสมเข้าสูตร (วางเรียงต่อลงมาด้านล่าง)
        # -------------------------------------------------------------
        st.subheader("➕ เพิ่มส่วนผสมเข้าสูตร")

        # ดึงรายชื่อวัตถุดิบดิบจากตาราง ingredient
        df_ings = pd.read_sql_query(
            "SELECT ingredient_id, ingredient_name, stock_unit FROM ingredient ORDER BY ingredient_id",
            conn,
        )

        # ดึงรายชื่อสูตรย่อยจากตาราง recipe_items
        df_subs = pd.read_sql_query(
            "SELECT DISTINCT parent_id, recipe_item_name, unit FROM recipe_items ORDER BY parent_id",
            conn,
        )

        # รวมตัวเลือกทั้งหมดเข้าด้วยกัน โดยโชว์ ID นำหน้า
        item_options = {}
        for _, r in df_ings.iterrows():
            item_options[
                f"📦 [วัตถุดิบ - {r['ingredient_id']}] {r['ingredient_name']} ({r['stock_unit']})"
            ] = (r["ingredient_id"], r["stock_unit"])

        for _, r in df_subs.iterrows():
            item_options[
                f"🧪 [สูตรย่อย - {r['parent_id']}] {r['recipe_item_name']} ({r['unit']})"
            ] = (r["parent_id"], r["unit"])

        if item_options:
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                sel_item_key = st.selectbox(
                    "เลือกวัตถุดิบ/สูตรย่อยที่ต้องการเพิ่ม:",
                    list(item_options.keys()),
                )
                item_id, item_unit = item_options[sel_item_key]
            with c2:
                add_qty = st.number_input(
                    f"ปริมาณที่ใช้ ({item_unit}):",
                    min_value=0.001,
                    value=1.0,
                    step=0.5,
                    format="%.2f",
                )
            with c3:
                st.markdown(
                    "<div style='height: 28px;'></div>",
                    unsafe_allow_html=True,
                )
                if st.button(
                    "➕ บันทึกเข้าสูตร",
                    use_container_width=True,
                    type="primary",
                ):
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO recipe (menu_id, ingredient_id, qty) VALUES (?, ?, ?)",
                        (selected_menu_id, item_id, add_qty),
                    )
                    conn.commit()
                    st.success(
                        f"เพิ่มส่วนผสมเข้าสูตร [{selected_menu_id}] {selected_menu_info['menu_name']} เรียบร้อย!"
                    )
                    st.rerun()
        else:
            st.warning(
                "ยังไม่มีข้อมูลวัตถุดิบในระบบ กรุณาเพิ่มวัตถุดิบที่หน้า '🛒 วัตถุดิบ' ก่อน"
            )

        # -------------------------------------------------------------
        # 5. Section นำเข้าข้อมูลสูตรจากไฟล์ CSV (ล่างสุด)
        # -------------------------------------------------------------
        st.markdown("---")
        st.subheader("📥 นำเข้าสูตรอาหาร/เครื่องดื่มจาก CSV")

        with st.expander("ℹ️ ดูโครงสร้างไฟล์ CSV ที่รองรับ & ดาวน์โหลด Template"):
            st.markdown("""
            **คอลัมน์ที่จำเป็นต้องมีในไฟล์ CSV:**
            * `menu_id` : รหัสเมนู (ต้องตรงกับรหัสในตาราง `menu` เช่น `M001`)
            * `ingredient_id` : รหัสวัตถุดิบหรือสูตรย่อย (ต้องตรงกับตาราง `ingredient` หรือ `recipe_items` เช่น `ING001` หรือ `SUB_001`)
            * `qty` : ปริมาณที่ใช้ต่อแก้ว/เสิร์ฟ (เช่น `18.0`, `120.0`)
            """)

            # สร้างตัวอย่าง DataFrame สำหรับดาวน์โหลด Template
            sample_df = pd.DataFrame(
                [
                    {"menu_id": "M001", "ingredient_id": "ING001", "qty": 18.0},
                    {"menu_id": "M001", "ingredient_id": "ING002", "qty": 120.0},
                    {
                        "menu_id": "M002",
                        "ingredient_id": "SUB_001",
                        "qty": 30.0,
                    },
                ]
            )
            st.dataframe(sample_df, hide_index=True)

            csv_sample_data = sample_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 ดาวน์โหลดไฟล์ CSV ตัวอย่าง (Template)",
                data=csv_sample_data,
                file_name="recipe_import_template.csv",
                mime="text/csv",
            )

        uploaded_file = st.file_uploader(
            "เลือกไฟล์ CSV เพื่ออัปโหลดสูตรจำนวนมาก:",
            type=["csv"],
            key="recipe_csv_uploader",
        )

        if uploaded_file is not None:
            try:
                df_upload = pd.read_csv(uploaded_file)
                st.write("🔍 **ตัวอย่างข้อมูลที่จะนำเข้า:**")
                st.dataframe(df_upload, use_container_width=True)

                required_cols = {"menu_id", "ingredient_id", "qty"}
                if not required_cols.issubset(df_upload.columns):
                    st.error(
                        f"❌ โครงสร้าง CSV ไม่ถูกต้อง! ไฟล์ต้องมีคอลัมน์: {', '.join(required_cols)}"
                    )
                else:
                    if st.button(
                        "💾 ยืนยันการนำเข้าข้อมูลจาก CSV", type="primary"
                    ):
                        cur = conn.cursor()
                        success_count = 0
                        for _, row in df_upload.iterrows():
                            m_id = str(row["menu_id"]).strip()
                            i_id = str(row["ingredient_id"]).strip()
                            qty = float(row["qty"])

                            cur.execute(
                                "INSERT INTO recipe (menu_id, ingredient_id, qty) VALUES (?, ?, ?)",
                                (m_id, i_id, qty),
                            )
                            success_count += 1

                        conn.commit()
                        st.success(
                            f"🎉 นำเข้าข้อมูลสูตรสำเร็จทั้งหมด {success_count} รายการ!"
                        )
                        st.rerun()
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์ CSV: {e}")