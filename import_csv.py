import pandas as pd
from config import get_db

# 1. อ่านไฟล์ CSV ที่ดาวน์โหลดมาจาก Google Sheets
csv_file = "ingredients.csv"  # เปลี่ยนเป็นชื่อไฟล์ของคุณ
df = pd.read_csv(csv_file)

# ล้างช่องว่างในชื่อคอลัมน์
df.columns = df.columns.str.strip()

# 2. เชื่อมต่อฐานข้อมูลและบันทึกข้อมูล
conn = get_db()
try:
    # df.to_sql จะทำการ Insert ข้อมูลเข้าตาราง ingredient ให้อัตโนมัติ
    # if_exists='append' คือการเพิ่มข้อมูลต่อจากที่มีอยู่ (ถ้าต้องการทับของเดิมให้ใช้ 'replace')
    df.to_sql("ingredient", conn, if_exists="append", index=False)
    print(f"✅ นำเข้าข้อมูลวัตถุดิบสำเร็จจำนวน {len(df)} รายการ!")
except Exception as e:
    print(f"❌ เกิดข้อผิดพลาด: {e}")
finally:
    conn.close()