import pandas as pd
import streamlit as st
from config import get_db
from step_trainer import render_step_by_step_guide


# -------------------------------------------------------------------
# CUSTOM CSS FOR NORDIC EXPANDER LIST VIEW
# -------------------------------------------------------------------
def apply_trainee_styles():
    st.markdown(
        """
        <style>
        /* ===================================================
           1. กรอบนอกและพื้นหลังรวม (Container)
           =================================================== */
        div[data-testid="stExpander"] {
            background-color: #E0D6CD !important;  /* สีพื้นหลังกล่อง */
            border: 1px solid #D1C5B8 !important;  /* สีเส้นขอบ */
            border-radius: 14px !important;        /* ความโค้งมน */
            margin-bottom: 12px !important;
            overflow: hidden;
            box-shadow: 0 2px 6px rgba(0,0,0,0.03);
            transition: all 0.2s ease-in-out;
        }

        /* ===================================================
           2. แถบหัวข้อ (Header Bar)
           =================================================== */
        div[data-testid="stExpander"] summary {
            background-color: #DFD8D0 !important;  /* สีพื้นหลังแถบหัวข้อ */
            border-radius: 2px !important;
            padding: 12px 18px !important;
        }

        /* สีแถบหัวข้อขณะเอาเมาส์ไปชี้ (Hover) */
        div[data-testid="stExpander"] summary:hover {
            background-color: #D5CCC3 !important;
            cursor: pointer;
        }

        /* ===================================================
           3. ตัวหนังสือในแถบหัวข้อ (Header Text)
           =================================================== */
        div[data-testid="stExpander"] summary p {
            color: #0F172A !important;             /* สีตัวหนังสือหัวข้อ */
            font-weight: 600 !important;           /* ความหนาตัวหนังสือ */
            font-size: 1.05rem !important;
        }

        /* ===================================================
           4. ลูกศรเปิด/ปิด (Icon Arrow)
           =================================================== */
        div[data-testid="stExpander"] summary svg {
            color: #64748B !important;             /* สีลูกศร */
        }

        /* ===================================================
           5. พื้นหลังเนื้อหาด้านในเมื่อเปิดออก (Content Details)
           =================================================== */
        div[data-testid="stExpanderDetails"] {
            background-color: #E0D6CD !important;  /* สีพื้นหลังเนื้อหาด้านใน */
            border-top: 1px solid #D5CCC3 !important; /* เส้นคั่นระหว่างหัวข้อกับเนื้อหา */
            padding: 18px !important;
        }

        /* ---------------------------------------------------
           คลาสอื่นๆ สำหรับตกแต่งภายใน Expander
           --------------------------------------------------- */
        .category-header {
            font-size: 1.15rem;
            font-weight: 700;
            color: #0F172A;
            background: #F1F5F9;
            padding: 10px 16px;
            border-radius: 10px;
            border-left: 5px solid #475569;
            margin-top: 24px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .recipe-box {
            background-color: #F8FAFC !important;
            border-left: 4px solid #8C6A5C; /* สีน้ำตาลกาแฟ */
            border-radius: 8px;
            padding: 14px 16px;
            margin-top: 8px;
            margin-bottom: 12px;
            font-size: 0.92rem;
            color: #334155;
            line-height: 1.6;
            white-space: pre-line;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        }

        .recipe-title {
            font-weight: 700;
            font-size: 0.85rem;
            color: #6B4E3D;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            margin-bottom: 6px;
            display: block;
        }

        .info-pill-container {
            display: flex;
            gap: 8px;
            margin-bottom: 10px;
            align-items: center;
            flex-wrap: wrap;
        }

        .info-pill-id {
            background-color: #475569;
            color: #FFFFFF;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .info-pill-price {
            background-color: #8C6A5C;
            color: #FFFFFF;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .no-image-box {
            background-color: #D8CEC5;
            border: 2px dashed #B8AAA0;
            border-radius: 10px;
            height: 180px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #64748B;
            font-size: 0.9rem;
            font-weight: 500;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# -------------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------------


def get_beverage_menus() -> pd.DataFrame:
    """ดึงข้อมูลเมนูเครื่องดื่ม สูตร และส่วนผสมจาก Database (รองรับ Dynamic Schema)"""
    conn = get_db()
    try:
        recipe_cols = []
        try:
            recipe_info = pd.read_sql_query(
                "PRAGMA table_info(recipe)", conn
            )
            recipe_cols = (
                recipe_info["name"].tolist() if not recipe_info.empty else []
            )
        except Exception:
            pass

        instructions_select = (
            "MAX(r.instructions) AS instructions"
            if "instructions" in recipe_cols
            else "'' AS instructions"
        )
        recipe_note_select = (
            "MAX(r.note) AS recipe_note"
            if "note" in recipe_cols
            else "'' AS recipe_note"
        )

        query = f"""
            SELECT 
                m.menu_id, 
                m.category_id, 
                c.category_name,
                m.menu_name, 
                m.price, 
                m.note AS menu_note,
                m.img_url,
                {instructions_select},
                {recipe_note_select},
                GROUP_CONCAT(
                    COALESCE(i.ingredient_name, r.ingredient_id) || ' : ' || r.qty || ' ' || COALESCE(i.stock_unit, ''), 
                    x'0A'
                ) AS ingredients
            FROM menu m
            LEFT JOIN category c ON m.category_id = c.category_id
            LEFT JOIN recipe r ON m.menu_id = r.menu_id
            LEFT JOIN ingredient i ON r.ingredient_id = i.ingredient_id
            GROUP BY m.menu_id
            ORDER BY m.category_id, m.menu_id
        """
        df = pd.read_sql_query(query, conn)

        if not df.empty and "category_id" in df.columns:
            df_filtered = df[
                df["category_id"]
                .astype(str)
                .str.upper()
                .str.startswith("CAT-1")
            ]
            if not df_filtered.empty:
                return df_filtered
            return df

    except Exception as e:
        st.error(f"Error fetching menus: {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
    return df


def get_categories_dict() -> dict:
    """ดึงข้อมูลหมวดหมู่มาทำเป็น Dictionary {category_id: category_name}"""
    conn = get_db()
    cat_dict = {}
    try:
        df_cat = pd.read_sql_query("SELECT * FROM category", conn)
        for _, row in df_cat.iterrows():
            c_id = str(row["category_id"]).strip()
            c_name = (
                str(row["category_name"]).strip()
                if "category_name" in row and pd.notna(row["category_name"])
                else c_id
            )
            cat_dict[c_id] = c_name
    except Exception:
        pass
    finally:
        conn.close()
    return cat_dict


def get_recipe_safe(menu_id: str) -> list:
    """ดึงสูตรแบบปลอดภัย ถ้ามีข้อผิดพลาดจะไม่ crash แต่จะคืนค่าว่างแทน"""
    try:
        conn = get_db()
        query = """
            SELECT 
                i.ingredient_name AS ingredient,
                r.qty AS qty,
                COALESCE(i.stock_unit, '') AS unit
            FROM recipe r
            JOIN ingredient i ON r.ingredient_id = i.ingredient_id
            WHERE r.menu_id = ?
        """
        df = pd.read_sql_query(query, conn, params=(menu_id,))
        conn.close()

        if not df.empty:
            return df.to_dict(orient="records")
    except Exception as e:
        print(f"Error fetching recipe for {menu_id}: {e}")

    return []


# -------------------------------------------------------------------
# MAIN RENDER FUNCTION
# -------------------------------------------------------------------


def render():
    apply_trainee_styles()

    st.header("📚 เรียนรู้ (Trainee Guide)")
    st.caption("คู่มือสูตรเครื่องดื่มสำหรับบาริสต้า (Nordic Expander List View)")

    df_menus = get_beverage_menus()
    cat_dict = get_categories_dict()

    if df_menus.empty:
        st.warning("⚠️ ไม่พบข้อมูลเมนูเครื่องดื่มในระบบ")
        return

    # ---------------------------------------------------------------
    # 1. โซน ค้นหา & ตัวกรอง (Search & Filter)
    # ---------------------------------------------------------------
    col_search, col_filter = st.columns([2, 1])

    with col_search:
        search_kw = st.text_input(
            "🔍 ค้นหาเมนู / ส่วนผสม",
            placeholder="พิมพ์ชื่อเมนู เช่น มัจฉะ, ลาเต้...",
        )

    available_cats = sorted(
        df_menus["category_id"].dropna().unique().tolist()
    )
    cat_filter_options = ["ทั้งหมด (All Categories)"] + [
        f"{c_id} - {cat_dict.get(c_id, c_id)}" for c_id in available_cats
    ]

    with col_filter:
        selected_cat_filter = st.selectbox(
            "📂 กรองตามหมวดหมู่", cat_filter_options
        )

    # กรองข้อมูล
    filtered_df = df_menus.copy()

    if search_kw.strip():
        kw = search_kw.strip().lower()
        filtered_df = filtered_df[
            filtered_df["menu_name"].astype(str).str.lower().str.contains(kw)
            | filtered_df["menu_id"].astype(str).str.lower().str.contains(kw)
            | filtered_df["ingredients"]
            .astype(str)
            .str.lower()
            .str.contains(kw)
            | filtered_df["menu_note"].astype(str).str.lower().str.contains(kw)
        ]

    if selected_cat_filter != "ทั้งหมด (All Categories)":
        target_cat_id = selected_cat_filter.split(" - ")[0].strip()
        filtered_df = filtered_df[filtered_df["category_id"] == target_cat_id]

    st.markdown("---")

    # ---------------------------------------------------------------
    # 2. โซน แสดงผลลิสต์เมนูด้วย st.expander
    # ---------------------------------------------------------------
    if filtered_df.empty:
        st.info("🔍 ไม่พบเมนูที่ตรงกับเงื่อนไขการค้นหา")
        return

    grouped = filtered_df.groupby("category_id")

    for cat_id, group_df in grouped:
        cat_name = cat_dict.get(cat_id, "เครื่องดื่ม")

        # Header ประจำหมวดหมู่
        st.markdown(
            f"""
            <div class="category-header">
                <span>🏷️ {cat_id} : {cat_name}</span>
                <span style="font-size: 0.85rem; font-weight: normal; color: #64748B;">({len(group_df)} รายการ)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for _, row in group_df.iterrows():
            m_id = str(row.get("menu_id", ""))
            m_name = str(row.get("menu_name", ""))
            m_price = (
                float(row.get("price")) if pd.notna(row.get("price")) else 0.0
            )
            m_img = (
                str(row.get("img_url", "")).strip()
                if pd.notna(row.get("img_url"))
                else ""
            )

            ingredients = (
                str(row.get("ingredients", "")).strip()
                if pd.notna(row.get("ingredients"))
                else ""
            )
            instructions = (
                str(row.get("instructions", "")).strip()
                if pd.notna(row.get("instructions"))
                else ""
            )
            recipe_note = (
                str(row.get("recipe_note", "")).strip()
                if pd.notna(row.get("recipe_note"))
                else ""
            )
            menu_note = (
                str(row.get("menu_note", "")).strip()
                if pd.notna(row.get("menu_note"))
                else ""
            )

            # Label ของ Expander แสดง ชื่อเมนู | รหัส | ราคา
            expander_label = f"🥤 {m_name}  —  [{m_id}]  (฿{m_price:,.0f})"

            with st.expander(expander_label, expanded=True):
                # -----------------------------------------------------------
                # ส่วนที่ 1 (ด้านบน): แบ่ง 2 คอลัมน์ (รูปภาพฝั่งซ้าย | ข้อมูลฝั่งขวา)
                # -----------------------------------------------------------
                col_left, col_right = st.columns([1, 2.2])

                # ฝั่งซ้าย: แสดงรูปภาพ
                with col_left:
                    if m_img:
                        try:
                            st.image(m_img, use_container_width=True)
                        except Exception:
                            st.markdown(
                                '<div class="no-image-box">⚠️ ไม่สามารถแสดงรูปภาพได้</div>',
                                unsafe_allow_html=True,
                            )
                    else:
                        st.markdown(
                            '<div class="no-image-box">📷 ไม่มีรูปภาพประกอบ</div>',
                            unsafe_allow_html=True,
                        )

                # ฝั่งขวา: แสดง Badge, ส่วนผสม, ขั้นตอนการทำ และหมายเหตุ
                with col_right:
                    # แสดง Badge รหัส และ ราคา
                    st.markdown(
                        f"""
                        <div class="info-pill-container">
                            <span class="info-pill-id">ID: {m_id}</span>
                            <span class="info-pill-price">฿{m_price:,.0f}.-</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # ส่วนผสม
                    display_ingredients = (
                        ingredients or menu_note or "ยังไม่ได้ระบุส่วนผสม"
                    )
                    st.markdown(
                        f"""
                        <div class="recipe-box">
                            <span class="recipe-title">🧪 ส่วนผสม:</span>
                            {display_ingredients}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # ขั้นตอนการทำ (ถ้ามี)
                    if instructions:
                        st.markdown("**🥣 ขั้นตอนการชง:**")
                        st.write(instructions)

                    # หมายเหตุ (ถ้ามี)
                    if recipe_note:
                        st.caption(f"📌 **หมายเหตุ:** {recipe_note}")

                # -----------------------------------------------------------
                # ส่วนที่ 2 (ด้านล่าง): โหมดฝึกชง Step Trainer (แสดงแบบ Full Width)
                # -----------------------------------------------------------
                recipe_data = get_recipe_safe(m_id)
                if recipe_data:
                    st.markdown("---")
                    st.markdown("##### 🎯 โหมดฝึกชง (Step Trainer)")
                    render_step_by_step_guide(
                        menu_id=m_id,
                        menu_name=m_name,
                        base_recipe=recipe_data,
                        key_prefix=f"trainee_{m_id}",
                    )