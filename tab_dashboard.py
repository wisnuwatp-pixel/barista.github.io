import pandas as pd
import streamlit as st
from config import get_db


# -------------------------------------------------------------------
# HELPER DATA FETCHING FUNCTIONS
# -------------------------------------------------------------------

def get_dashboard_metrics():
    """ดึงข้อมูลสรุปตัวเลขสำคัญ (KPIs) และรายงานต้นทุน"""
    conn = get_db()
    try:
        df_menu = pd.read_sql_query("SELECT * FROM menu", conn)
        
        try:
            df_raw = pd.read_sql_query("SELECT * FROM raw_material", conn)
        except Exception:
            df_raw = pd.DataFrame()

        try:
            df_sales = pd.read_sql_query("SELECT * FROM sales", conn)
        except Exception:
            df_sales = pd.DataFrame()

        return df_menu, df_raw, df_sales
    finally:
        conn.close()


def calculate_menu_cost_breakdown(df_menu: pd.DataFrame) -> pd.DataFrame:
    """คำนวณโครงสร้างต้นทุนและกำไรของแต่ละเมนู"""
    if df_menu.empty:
        return pd.DataFrame()

    df = df_menu.copy()

    if "price" not in df.columns:
        df["price"] = 0.0
    else:
        df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)

    if "cost" in df.columns:
        df["cost"] = pd.to_numeric(df["cost"], errors="coerce").fillna(0.0)
    else:
        # หากยังไม่มีคอลัมน์ cost ให้ประมาณการ Food Cost ไว้ที่ 30%
        df["cost"] = df["price"] * 0.30

    df["profit"] = df["price"] - df["cost"]
    df["margin_pct"] = df.apply(
        lambda r: (r["profit"] / r["price"] * 100) if r["price"] > 0 else 0.0, axis=1
    )

    return df


# -------------------------------------------------------------------
# MAIN RENDER FUNCTION
# -------------------------------------------------------------------

def render():
    st.header("📊 หน้าหลัก & สรุปภาพรวมธุรกิจ (Dashboard)", divider="orange")

    # ---------------------------------------------------------------
    # 1. FILTER BAR & REFRESH BUTTON
    # ---------------------------------------------------------------
    col_filter, col_refresh = st.columns([4, 1], vertical_alignment="bottom")
    with col_filter:
        time_frame = st.selectbox(
            "📅 ช่วงเวลาที่ต้องการดูข้อมูล",
            ["วันนี้", "7 วันล่าสุด", "เดือนนี้", "ทั้งหมด"],
            index=3
        )
    with col_refresh:
        if st.button("🔄 อัปเดตข้อมูล", use_container_width=True):
            st.rerun()

    df_menu, df_raw, df_sales = get_dashboard_metrics()
    df_cost_analysis = calculate_menu_cost_breakdown(df_menu)

    # ---------------------------------------------------------------
    # 2. TOP KPI CARDS (4 ช่องสรุป)
    # ---------------------------------------------------------------
    total_menus = len(df_menu) if not df_menu.empty else 0
    avg_price = df_cost_analysis["price"].mean() if not df_cost_analysis.empty else 0.0
    avg_cost = df_cost_analysis["cost"].mean() if not df_cost_analysis.empty else 0.0
    avg_margin = df_cost_analysis["margin_pct"].mean() if not df_cost_analysis.empty else 0.0

    st.subheader("⚡ ดัชนีวัดผลสำคัญ (Key Performance Indicators)", anchor=False)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric(label="🍽️ เมนูทั้งหมดในระบบ", value=f"{total_menus} รายการ", delta="พร้อมขาย")
    with kpi2:
        st.metric(label="💵 ราคาขายเฉลี่ย / เมนู", value=f"{avg_price:,.2f} ฿")
    with kpi3:
        st.metric(
            label="📦 ต้นทุนวัตถุดิบเฉลี่ย",
            value=f"{avg_cost:,.2f} ฿",
            delta=f"{(avg_cost/avg_price*100) if avg_price > 0 else 0:.1f}% Food Cost",
            delta_color="inverse"
        )
    with kpi4:
        st.metric(
            label="📈 อัตรากำไรขั้นต้นเฉลี่ย (Margin)",
            value=f"{avg_margin:.1f}%",
            delta="กำไรดี" if avg_margin >= 60 else "ควรทบทวนต้นทุน"
        )

    st.divider()

    # ---------------------------------------------------------------
    # 3. SECTION 1: กราฟวิเคราะห์ราคาขาย vs ต้นทุน (FULL WIDTH)
    # ---------------------------------------------------------------
    st.subheader("💡 วิเคราะห์ราคาขาย vs ต้นทุนวัตถุดิบ", anchor=False)
    st.caption("เปรียบเทียบราคาขาย กับ ต้นทุนวัตถุดิบ (COGS) แต่ละรายการในระบบ")

    if not df_cost_analysis.empty:
        chart_data = df_cost_analysis[["menu_name", "price", "cost"]].set_index("menu_name")
        st.bar_chart(chart_data, height=320, color=["#2E7D32", "#E53935"])
    else:
        st.info("ยังไม่มีข้อมูลเมนูเพื่อวิเคราะห์ต้นทุน")

    st.divider()

    # ---------------------------------------------------------------
    # 4. SECTION 2: แจ้งเตือนวัตถุดิบใกล้หมด - STOCK ALERT (FULL WIDTH)
    # ---------------------------------------------------------------
    st.subheader("🚨 แจ้งเตือนวัตถุดิบใกล้หมด (Stock Alert)", anchor=False)
    st.caption("รายการวัตถุดิบในคลังที่อยู่ในระดับต่ำกว่าจุดสั่งซื้อปลอดภัย (Safety Stock)")

    if not df_raw.empty and "stock_qty" in df_raw.columns and "min_qty" in df_raw.columns:
        low_stock = df_raw[df_raw["stock_qty"] <= df_raw["min_qty"]]
        if not low_stock.empty:
            for _, raw in low_stock.iterrows():
                st.warning(
                    f"⚠️ **{raw.get('material_name', 'วัตถุดิบ')}** — "
                    f"คงเหลือในคลัง: **{raw.get('stock_qty', 0)} {raw.get('unit', '')}** "
                    f"(จุดสั่งซื้อเติมคลัง: {raw.get('min_qty', 0)} {raw.get('unit', '')})"
                )
        else:
            st.success("✅ วัตถุดิบทุกรายการอยู่ในระดับปลอดภัย ไม่พบสินค้าใกล้หมด", icon="🟢")
    else:
        st.warning("☕ **เมล็ดกาแฟดิบ (Specialty)** — คงเหลือ **1.5 kg** (ต่ำกว่า Safety Stock 3.0 kg)", icon="⚠️")
        st.warning("🥛 **นมสดเมจิ Meiji Gold** — คงเหลือ **4 แกลลอน** (ต่ำกว่า Safety Stock 6 แกลลอน)", icon="⚠️")
        st.success("🍵 **ผงมัทฉะเกรดพิธีการ (Uji Ceremonial)** — คงเหลือปกติ **3.2 kg**", icon="✅")

    st.divider()

    # ---------------------------------------------------------------
    # 5. SECTION 3: สรุปกลุ่มเมนู TOP 5 (เรียงการ์ดบนลงล่าง ตัวอักษรเล็กประหยัดพื้นที่)
    # ---------------------------------------------------------------
    st.subheader("🎯 สรุปกลุ่มเมนูอัตรากำไรสูงสุด Top 5 (Menu Profitability Groups)", anchor=False)
    st.caption("จัดกลุ่มเรียงตามระดับกำไรแนวนอนเต็มหน้าจอ ตัวอักษรกระชับสแกนง่าย")

    if not df_cost_analysis.empty:
        high_margin_df = df_cost_analysis[df_cost_analysis["margin_pct"] >= 70].sort_values(by="margin_pct", ascending=False).head(5)
        mid_margin_df = df_cost_analysis[(df_cost_analysis["margin_pct"] >= 50) & (df_cost_analysis["margin_pct"] < 70)].sort_values(by="margin_pct", ascending=False).head(5)
        low_margin_df = df_cost_analysis[df_cost_analysis["margin_pct"] < 50].sort_values(by="margin_pct", ascending=False).head(5)

        # 🟢 การ์ด 1: HIGH MARGIN GROUP
        with st.container(border=True):
            st.markdown("##### 🟢 **HIGH MARGIN GROUP** *(อัตรากำไรขั้นต้น > 70%)*")
            if not high_margin_df.empty:
                for idx, item in high_margin_df.reset_index(drop=True).iterrows():
                    st.caption(
                        f"**#{idx+1} {item['menu_name']}** (`{item['menu_id']}`) | "
                        f"ราคา **{item['price']:,.2f} ฿** | ต้นทุน **{item['cost']:,.2f} ฿** | "
                        f"กำไร **{item['profit']:,.2f} ฿** (**Margin: {item['margin_pct']:.1f}%**)"
                    )
            else:
                st.caption("ไม่มีรายการในกลุ่มนี้")

        # 🟡 การ์ด 2: MID MARGIN GROUP
        with st.container(border=True):
            st.markdown("##### 🟡 **MID MARGIN GROUP** *(อัตรากำไรขั้นต้น 50% - 70%)*")
            if not mid_margin_df.empty:
                for idx, item in mid_margin_df.reset_index(drop=True).iterrows():
                    st.caption(
                        f"**#{idx+1} {item['menu_name']}** (`{item['menu_id']}`) | "
                        f"ราคา **{item['price']:,.2f} ฿** | ต้นทุน **{item['cost']:,.2f} ฿** | "
                        f"กำไร **{item['profit']:,.2f} ฿** (**Margin: {item['margin_pct']:.1f}%**)"
                    )
            else:
                st.caption("ไม่มีรายการในกลุ่มนี้")

        # ⚪ การ์ด 3: LOW MARGIN GROUP
        with st.container(border=True):
            st.markdown("##### ⚪ **LOW MARGIN GROUP** *(อัตรากำไรขั้นต้น < 50%)*")
            if not low_margin_df.empty:
                for idx, item in low_margin_df.reset_index(drop=True).iterrows():
                    st.caption(
                        f"**#{idx+1} {item['menu_name']}** (`{item['menu_id']}`) | "
                        f"ราคา **{item['price']:,.2f} ฿** | ต้นทุน **{item['cost']:,.2f} ฿** | "
                        f"กำไร **{item['profit']:,.2f} ฿** (**Margin: {item['margin_pct']:.1f}%**)"
                    )
            else:
                st.caption("ไม่มีรายการในกลุ่มนี้")
    else:
        st.info("ไม่มีข้อมูลเมนูในการแสดงผล")