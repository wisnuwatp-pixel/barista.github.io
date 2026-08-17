import os
import streamlit as st


def apply_global_styles():
  """ฟังก์ชันอ่านไฟล์ style.css มาประยุกต์ใช้กับ Streamlit."""
  css_file_path = "style.css"

  # ตรวจสอบว่ามีไฟล์ style.css หรือไม่
  if os.path.exists(css_file_path):
    with open(css_file_path, "r", encoding="utf-8") as f:
      css_content = f.read()

    # ฝั่ง CSS เข้าไปใน Streamlit
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
  else:
    st.warning(
        f"⚠️ ไม่พบไฟล์ {css_file_path} กรุณาตรวจสอบว่าสร้างไฟล์ไว้ในโฟลเดอร์เดียวกันหรือยัง"
    )