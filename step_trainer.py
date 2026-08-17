import re
import streamlit as st
import streamlit.components.v1 as components


def _extract_number(value) -> float:
    """Helper function: ดึงเฉพาะตัวเลขจากข้อความ ป้องกัน ValueError"""
    if isinstance(value, (int, float)):
        return float(value)
    if not value:
        return 0.0
    match = re.search(r"[-+]?\d*\.\d+|\d+", str(value))
    if match:
        try:
            return float(match.group())
        except ValueError:
            return 0.0
    return 0.0


def render_step_by_step_guide(
    menu_id: str,
    menu_name: str,
    base_recipe: list,
    key_prefix: str = "trainee",
):
    """Component สำหรับแสดงขั้นตอนการฝึกชงแบบ Full Width อยู่ Section ด้านล่าง"""

    clean_id = (
        str(menu_id)
        .replace("-", "_")
        .replace(" ", "_")
        .replace(".", "_")
        .lower()
    )
    unique_tag = f"{key_prefix}_{clean_id}"

    # 1. เช็กประเภทเมนู (ร้อน/เย็น)
    is_hot = any(
        kw in menu_name.lower() or kw in str(menu_id).lower()
        for kw in ["ร้อน", "hot", "espresso", "เอสเพรสโซ่"]
    )
    options = ["4 oz", "8 oz"] if is_hot else ["8 oz", "12 oz", "16 oz"]

    # 2. Header Bar
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; background: #0F172A; color: white; padding: 10px 18px; border-radius: 10px 10px 0 0; margin-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.1rem;">☕</span>
                <span style="font-size: 1rem; font-weight: 700;">โหมดฝึกชง: {menu_name}</span>
                <span style="background: {'#EF4444' if is_hot else '#3B82F6'}; font-size: 0.68rem; padding: 2px 8px; border-radius: 8px; font-weight: 600;">
                    {'HOT' if is_hot else 'ICED'}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ตัวเลือกขนาดแก้ว
    c_space, c_radio = st.columns([1, 1.5])
    with c_space:
        st.caption("🥤 ปรับสูตรตามขนาดแก้ว:")
    with c_radio:
        radio_key = f"radio_cup_{unique_tag}_{'hot' if is_hot else 'iced'}"
        cup_size = st.radio(
            label="ขนาดแก้ว",
            options=options,
            horizontal=True,
            label_visibility="collapsed",
            key=radio_key,
        )

    # 3. Spec ทรงแก้ว
    CUP_SPECS = {
        "4 oz": {
            "capacity_ml": 120,
            "y_top": 95,
            "y_bot": 180,
            "x_tl": 35,
            "x_tr": 105,
            "x_bl": 45,
            "x_br": 95,
            "rx": 35,
            "ry": 5,
        },
        "8 oz": {
            "capacity_ml": 240,
            "y_top": 70,
            "y_bot": 180,
            "x_tl": 30,
            "x_tr": 110,
            "x_bl": 42,
            "x_br": 98,
            "rx": 40,
            "ry": 5,
        },
        "12 oz": {
            "capacity_ml": 360,
            "y_top": 50,
            "y_bot": 180,
            "x_tl": 28,
            "x_tr": 112,
            "x_bl": 40,
            "x_br": 100,
            "rx": 42,
            "ry": 6,
        },
        "16 oz": {
            "capacity_ml": 480,
            "y_top": 30,
            "y_bot": 180,
            "x_tl": 25,
            "x_tr": 115,
            "x_bl": 40,
            "x_br": 100,
            "rx": 45,
            "ry": 6,
        },
    }

    fallback_key = "4 oz" if is_hot else "16 oz"
    spec = CUP_SPECS.get(cup_size, CUP_SPECS[fallback_key])
    max_capacity = spec["capacity_ml"]

    multiplier = 1.0
    if "4" in cup_size:
        multiplier = 1.0
    elif "8" in cup_size:
        multiplier = 1.0 if is_hot else 0.5
    elif "12" in cup_size:
        multiplier = 0.75
    elif "16" in cup_size:
        multiplier = 1.0

    # 4. State ขั้นตอนการชง
    step_key = f"step_idx_{unique_tag}"
    if step_key not in st.session_state:
        st.session_state[step_key] = 0

    total_steps = len(base_recipe)
    if total_steps == 0:
        st.warning("⚠️ ไม่พบข้อมูลขั้นตอนส่วนผสม")
        return

    if st.session_state[step_key] >= total_steps:
        st.session_state[step_key] = 0

    current_step = st.session_state[step_key]

    # คำนวณปริมาตรสะสม
    accumulated_liquid_ml = 0.0
    for i in range(current_step + 1):
        raw_q = base_recipe[i].get("qty", 0)
        accumulated_liquid_ml += _extract_number(raw_q) * multiplier

    fill_percent = min((accumulated_liquid_ml / max_capacity), 1.0)
    cup_height_px = spec["y_bot"] - spec["y_top"]
    liquid_height_px = fill_percent * cup_height_px
    liquid_y = spec["y_bot"] - liquid_height_px

    colors = ["#78350F", "#D97706", "#FBBF24", "#38BDF8", "#10B981"]
    current_color = colors[current_step % len(colors)]

    # 5. ข้อมูลขั้นตอนปัจจุบัน
    item = base_recipe[current_step]
    num_val = _extract_number(item.get("qty", 0)) * multiplier
    display_qty = (
        f"{int(num_val)}" if num_val.is_integer() else f"{round(num_val, 1)}"
    )
    unit_str = item.get("unit", "")

    # 6. BANNER CARD (แสดงผลเต็มความกว้าง)
    clip_id = f"clip_{unique_tag}"
    banner_html = f"""
    <div style="font-family: system-ui, -apple-system, sans-serif; display: flex; flex-direction: row; align-items: center; justify-content: space-between; background: #F8FAFC; border-left: 6px solid {current_color}; padding: 12px 20px; border-radius: 12px; border: 1px solid #E2E8F0; min-height: 110px; box-sizing: border-box;">
        
        <div style="display: flex; align-items: center; gap: 16px;">
            <svg width="60" height="90" viewBox="0 0 140 200" style="flex-shrink: 0;">
                <defs>
                    <clipPath id="{clip_id}">
                        <polygon points="{spec['x_tl']},{spec['y_top']} {spec['x_tr']},{spec['y_top']} {spec['x_br']},{spec['y_bot']} {spec['x_bl']},{spec['y_bot']}" />
                    </clipPath>
                </defs>
                <rect x="0" y="{liquid_y}" width="140" height="{liquid_height_px + 10}" fill="{current_color}" clip-path="url(#{clip_id})" style="transition: all 0.4s ease-in-out;" />
                <polygon points="{spec['x_tl']},{spec['y_top']} {spec['x_tr']},{spec['y_top']} {spec['x_br']},{spec['y_bot']} {spec['x_bl']},{spec['y_bot']}" fill="none" stroke="#64748B" stroke-width="3.5" stroke-linejoin="round" />
                <ellipse cx="70" cy="{spec['y_top']}" rx="{spec['rx']}" ry="{spec['ry']}" fill="none" stroke="#475569" stroke-width="2.5" />
            </svg>
            
            <div style="display: flex; flex-direction: column;">
                <div style="font-size: 0.72rem; color: #64748B; font-weight: 700; text-transform: uppercase;">ทรงแก้ว {cup_size}</div>
                <div style="font-weight: 800; color: #0F172A; font-size: 1.1rem; margin-top: 2px;">
                    {round(accumulated_liquid_ml, 1)} <span style="font-size: 0.85rem; font-weight: 500; color: #64748B;">/ {max_capacity} ml</span>
                </div>
                <div style="color: #475569; font-size: 0.78rem; margin-top: 2px;">
                    เติมแล้ว <b style="color: #0F172A;">{int(fill_percent * 100)}%</b>
                </div>
            </div>
        </div>

        <div style="width: 1px; height: 60px; background-color: #CBD5E1; margin: 0 16px;"></div>

        <div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: center;">
            <div style="color: #64748B; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.5px;">
                STEP {current_step + 1} OF {total_steps}
            </div>
            <div style="color: #0F172A; font-weight: 700; font-size: 1.1rem; margin-top: 2px;">
                เติม {item.get('ingredient', 'ส่วนผสม')}
            </div>
            <div style="display: flex; align-items: baseline; gap: 6px; margin-top: 2px;">
                <span style="color: #166534; font-size: 2rem; font-weight: 800; line-height: 1;">{display_qty}</span>
                <span style="font-size: 1rem; color: #475569; font-weight: 600;">{unit_str}</span>
            </div>
        </div>

    </div>
    """
    components.html(banner_html, height=130, scrolling=False)

    # 7. Progress & Controls
    st.markdown("<div style='margin-top: 4px;'></div>", unsafe_allow_html=True)
    st.progress(
        (current_step + 1) / total_steps,
        text=f"ขั้นตอนที่ {current_step + 1} จาก {total_steps}",
    )

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button(
            "⬅️ ย้อนกลับ",
            key=f"btn_prev_{unique_tag}",
            disabled=(current_step == 0),
            use_container_width=True,
        ):
            st.session_state[step_key] -= 1
            st.rerun()

    with col_next:
        if current_step < total_steps - 1:
            if st.button(
                "ถัดไป ➡️",
                key=f"btn_next_{unique_tag}",
                type="primary",
                use_container_width=True,
            ):
                st.session_state[step_key] += 1
                st.rerun()
        else:
            if st.button(
                "✅ ชงเสร็จเรียบร้อย!",
                key=f"btn_finish_{unique_tag}",
                type="primary",
                use_container_width=True,
            ):
                st.balloons()
                st.session_state[step_key] = 0
                st.rerun()