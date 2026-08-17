import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "database.db")


def get_db():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        cur = conn.cursor()

        # 1. category
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS category (
                category_id TEXT PRIMARY KEY,
                category_name TEXT NOT NULL,
                type TEXT NOT NULL
            );
        """
        )

        # 2. ingredient
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ingredient (
                ingredient_id TEXT PRIMARY KEY,
                category_id TEXT,
                ingredient_name TEXT NOT NULL,
                stock_unit TEXT,
                cost_perunit REAL DEFAULT 0,
                current_stock REAL DEFAULT 0,
                min_stock REAL DEFAULT 0,
                img_url TEXT
            );
        """
        )

        # 3. menu
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS menu (
                menu_id TEXT PRIMARY KEY,
                category_id TEXT,
                menu_name TEXT NOT NULL,
                price REAL DEFAULT 0,
                note TEXT,
                img_url TEXT
            );
        """
        )

        # 4. recipe
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS recipe (
                recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
                menu_id TEXT NOT NULL,
                ingredient_id TEXT NOT NULL,
                qty REAL NOT NULL
            );
        """
        )

        # 5. purchase_log
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS purchase_log (
                purchase_id TEXT PRIMARY KEY,
                date TEXT,
                ingredient_id TEXT,
                ingredient_name TEXT,
                qty_bought REAL DEFAULT 0,
                unit TEXT,
                total_price REAL DEFAULT 0
            );
        """
        )

        # 6. coffee_shot
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS coffee_shot (
                shot_id TEXT PRIMARY KEY,
                shot_name TEXT NOT NULL,
                dose_weight REAL NOT NULL,
                yield_vol REAL NOT NULL,
                extraction_time INTEGER NOT NULL
            );
        """
        )

        # 7. recipe_items (สูตรผสมย่อย / Sub-recipe)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS recipe_items (
                recipe_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_item_name TEXT NOT NULL,
                parent_id TEXT NOT NULL,
                child_id TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL
            );
        """
        )

    

        conn.commit()


# เรียกใช้งานทันที
init_db()