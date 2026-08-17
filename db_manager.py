import streamlit as st
import os
from datetime import datetime
from config import get_db

def backup_database():
    """สร้างไฟล์สำรองข้อมูล (Backup) พร้อมระบุวันที่-เวลา"""
    try:
        # กำหนดโฟลเดอร์สำหรับเก็บไฟล์ Backup
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # ชื่อไฟล์ต้นทาง (เปลี่ยนเป็นชื่อไฟล์ DB ของคุณถ้าไม่ได้ใช้ database.db)
        db_file = "database.db" 
        
        if not os.path.exists(db_file):
            return False, "❌ ไม่พบไฟล์ฐานข้อมูลต้นทาง"

        # ตั้งชื่อไฟล์สำรองตาม วันที่_เวลา (เช่น backup_20260813_191500.db)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)

        # ใช้ SQLite Online Backup (ปลอดภัยกว่าการ copy ตรงๆ ขณะที่มีคนใช้งาน)
        src_conn = get_db()
        dest_conn = sqlite3.connect(backup_path)
        with dest_conn:
            src_conn.backup(dest_conn)
        
        dest_conn.close()
        src_conn.close()

        return True, backup_path
    except Exception as e:
        return False, f"❌ เกิดข้อผิดพลาดในการ Backup: {e}"

def render_backup_ui():
    st.subheader("💾 สำรองและดาวน์โหลดฐานข้อมูล (Database Backup)", divider="blue")

    col1, col2 = st.columns([2, 2], vertical_alignment="center")

    # 1. ปุ่มสร้างไฟล์ Backup ไว้ในเครื่อง Server
    with col1:
        if st.button("📦 สร้างไฟล์ Backup บนเซิร์ฟเวอร์", type="primary", use_container_width=True):
            success, result = backup_database()
            if success:
                st.success(f"✅ สำรองข้อมูลเรียบร้อยแล้ว!\nเก็บไว้ที่: `{result}`")
            else:
                st.error(result)

    # 2. ปุ่มดาวน์โหลดไฟล์ DB ลงเครื่องคอมพิวเตอร์ของคุณทันที
    with col2:
        db_file = "database.db"  # เปลี่ยนชื่อไฟล์ให้ตรงกับที่ตั้งไว้ใน config
        if os.path.exists(db_file):
            with open(db_file, "rb") as f:
                st.download_button(
                    label="📥 ดาวน์โหลดไฟล์ DB ลงเครื่อง",
                    data=f,
                    file_name=f"backup_{datetime.now().strftime('%Y%m%d_%H%M')}.db",
                    mime="application/x-sqlite3",
                    use_container_width=True
                )