import config


def seed_data():
  config.init_db()
  conn = config.get_db()
  cur = conn.cursor()

  # 1. ข้อมูลทดสอบ: category
  categories = [
      ("CAT-ING-01", "เมล็ดกาแฟ & ชา", "Ingredient"),
      ("CAT-ING-02", "นม & ไซรัป", "Ingredient"),
      ("CAT-MNU-01", "กาแฟร้อน", "Menu"),
      ("CAT-MNU-02", "กาแฟเย็น", "Menu"),
  ]
  cur.executemany(
      "INSERT OR REPLACE INTO category VALUES (?, ?, ?)", categories
  )

  # 2. ข้อมูลทดสอบ: ingredient
  ingredients = [
      (
          "ING-001",
          "CAT-ING-01",
          "เมล็ดกาแฟ Arabica",
          "g",
          0.70,
          5000.0,
          1000.0,
          "",
      ),
      ("ING-002", "CAT-ING-02", "นมสดสดพาสเจอร์ไรส์", "ml", 0.08, 10000.0, 2000.0, ""),
      ("ING-003", "CAT-ING-02", "ไซรัปวานิลลา", "ml", 0.35, 1000.0, 200.0, ""),
  ]
  cur.executemany(
      "INSERT OR REPLACE INTO ingredient VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
      ingredients,
  )

  # 3. ข้อมูลทดสอบ: menu
  menus = [
      ("HOT-001", "CAT-MNU-01", "เอสเพรสโซ่ร้อน", 55.0, "ช็อตเข้มข้น", ""),
      ("HOT-002", "CAT-MNU-01", "ลาเต้ร้อน", 65.0, "ฟองนมนุ่ม", ""),
      ("ICE-001", "CAT-MNU-02", "อเมริกาโน่เย็น", 60.0, "เข้มข้นสดชื่น", ""),
  ]
  cur.executemany(
      "INSERT OR REPLACE INTO menu VALUES (?, ?, ?, ?, ?, ?)", menus
  )

  # 4. ข้อมูลทดสอบ: recipe
  # ล้างข้อมูล recipe เก่าก่อนกันซ้ำ
  cur.execute("DELETE FROM recipe")
  recipes = [
      ("HOT-001", "ING-001", 18.0),  # เอสเพรสโซ่ร้อน ใช้กาแฟ 18g
      ("HOT-002", "ING-001", 18.0),  # ลาเต้ร้อน ใช้กาแฟ 18g
      ("HOT-002", "ING-002", 150.0),  # ลาเต้ร้อน ใช้นมสด 150ml
      ("ICE-001", "ING-001", 36.0),  # อเมริกาโน่เย็น ใช้กาแฟ 36g
  ]
  cur.executemany(
      "INSERT INTO recipe (menu_id, ingredient_id, qty) VALUES (?, ?, ?)",
      recipes,
  )

  # 5. ข้อมูลทดสอบ: purchase_log
  purchases = [
      (
          "PUR-001",
          "2026-08-10T09:00:00Z",
          "ING-001",
          "เมล็ดกาแฟ Arabica",
          1000.0,
          "g",
          700.0,
      ),
      (
          "PUR-002",
          "2026-08-10T09:30:00Z",
          "ING-002",
          "นมสดสดพาสเจอร์ไรส์",
          5000.0,
          "ml",
          400.0,
      ),
  ]
  cur.executemany(
      "INSERT OR REPLACE INTO purchase_log VALUES (?, ?, ?, ?, ?, ?, ?)",
      purchases,
  )

  conn.commit()
  conn.close()
  print("✅ สร้างข้อมูลทดสอบสำเร็จครบทั้ง 5 ตารางเรียบร้อยแล้ว!")


if __name__ == "__main__":
  seed_data()