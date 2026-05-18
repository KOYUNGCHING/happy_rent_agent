import sqlite3

DATABASE_NAME = "happy_rent.db"


def get_db_connection():
    """
    建立並回傳 SQLite 資料庫連線。

    為什麼要包成 function？
    因為之後 app.py 裡很多地方都會需要連資料庫：
    - 查房源列表
    - 新增房源
    - 查使用者
    - 登入驗證

    每次需要資料庫時，就呼叫 get_db_connection()。
    """

    # 連接 SQLite 資料庫
    # 如果 happy_rent.db 不存在，SQLite 會自動建立這個檔案
    conn = sqlite3.connect(DATABASE_NAME)

    # 設定 row_factory
    # 預設 SQLite 查詢結果是 tuple，例如 row[0], row[1]
    # 設成 sqlite3.Row 後，可以用 row["title"] 這種方式讀資料，比較好懂
    conn.row_factory = sqlite3.Row

    return conn


def init_db():
    """
    初始化資料庫。

    這個 function 會建立兩張表：
    1. users：使用者資料，包含找房者與房東
    2. listings：房源資料，房東可以上架空房間

    IF NOT EXISTS 的意思是：
    如果資料表已經存在，就不要重複建立，避免程式報錯。
    """

    conn = get_db_connection()

    # 建立 users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 建立 listings table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- landlord_id 用來記錄這個房源是哪個房東上架的
            landlord_id INTEGER,

            -- 房源基本資訊
            title TEXT NOT NULL,
            area TEXT NOT NULL,
            address TEXT NOT NULL,
            room_type TEXT NOT NULL,

            -- 租金資訊
            rent INTEGER NOT NULL,
            deposit INTEGER,

            -- 房間細節
            size TEXT,
            floor TEXT,
            has_window INTEGER DEFAULT 1,
            can_cook INTEGER DEFAULT 0,
            pet_allowed INTEGER DEFAULT 0,

            -- 費用與設備
            water_fee TEXT,
            electricity_fee TEXT,
            internet_included INTEGER DEFAULT 1,

            -- 房源說明與聯絡方式
            description TEXT,
            contact_name TEXT,
            contact_phone TEXT,
            image_url TEXT,

            -- 房源狀態
            status TEXT DEFAULT 'available',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (landlord_id) REFERENCES users(id)
        )
    """)

    # commit 代表把剛剛的 SQL 變更真的存進資料庫
    conn.commit()

    # 關閉資料庫連線，避免資源浪費
    conn.close()


def seed_sample_data():
    """
    建立一些測試資料。

    為什麼需要 sample data？
    因為我們還沒做房東上架功能前，
    可以先用假房源測試「找房者看房源列表」功能。
    """

    conn = get_db_connection()

    # 先確認是否已經有房源資料
    # 如果已經有資料，就不要重複塞入 sample data
    existing_listing = conn.execute("SELECT id FROM listings LIMIT 1").fetchone()

    if existing_listing:
        conn.close()
        return

    # 建立一個測試房東
    conn.execute("""
        INSERT OR IGNORE INTO users (name, email, password, role)
        VALUES (?, ?, ?, ?)
    """, ("測試房東", "landlord@example.com", "123456", "landlord"))

    # 查出剛剛建立的房東 id
    landlord = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        ("landlord@example.com",)
    ).fetchone()

    landlord_id = landlord["id"] if landlord else None

    # 新增幾筆中央大學周邊測試房源
    sample_listings = [
        {
            "title": "中央後門溫馨套房",
            "area": "中央後門",
            "address": "桃園市中壢區中央大學後門附近",
            "room_type": "獨立套房",
            "rent": 6500,
            "deposit": 13000,
            "size": "7 坪",
            "floor": "3F",
            "has_window": 1,
            "can_cook": 0,
            "pet_allowed": 0,
            "water_fee": "包水",
            "electricity_fee": "電費每度 5 元",
            "internet_included": 1,
            "description": "近中央大學後門，適合學生，生活機能方便。",
            "contact_name": "王先生",
            "contact_phone": "0912-345-678",
            "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267"
        },
        {
            "title": "中壢車站生活機能套房",
            "area": "中壢車站",
            "address": "桃園市中壢區中壢車站附近",
            "room_type": "分租套房",
            "rent": 7200,
            "deposit": 14400,
            "size": "8 坪",
            "floor": "5F",
            "has_window": 1,
            "can_cook": 1,
            "pet_allowed": 0,
            "water_fee": "每月 200 元",
            "electricity_fee": "依台電計價",
            "internet_included": 1,
            "description": "生活機能佳，靠近車站，適合有機車或常搭火車的學生。",
            "contact_name": "李小姐",
            "contact_phone": "0922-888-999",
            "image_url": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85"
        },
        {
            "title": "青埔新大樓套房",
            "area": "青埔",
            "address": "桃園市中壢區青埔高鐵站附近",
            "room_type": "獨立套房",
            "rent": 9500,
            "deposit": 19000,
            "size": "10 坪",
            "floor": "8F",
            "has_window": 1,
            "can_cook": 1,
            "pet_allowed": 1,
            "water_fee": "依帳單",
            "electricity_fee": "依台電計價",
            "internet_included": 0,
            "description": "新大樓，環境佳，但距離中央大學較遠。",
            "contact_name": "陳先生",
            "contact_phone": "0933-222-111",
            "image_url": "https://images.unsplash.com/photo-1493809842364-78817add7ffb"
        }
    ]

    for listing in sample_listings:
        conn.execute("""
            INSERT INTO listings (
                landlord_id,
                title,
                area,
                address,
                room_type,
                rent,
                deposit,
                size,
                floor,
                has_window,
                can_cook,
                pet_allowed,
                water_fee,
                electricity_fee,
                internet_included,
                description,
                contact_name,
                contact_phone,
                image_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            landlord_id,
            listing["title"],
            listing["area"],
            listing["address"],
            listing["room_type"],
            listing["rent"],
            listing["deposit"],
            listing["size"],
            listing["floor"],
            listing["has_window"],
            listing["can_cook"],
            listing["pet_allowed"],
            listing["water_fee"],
            listing["electricity_fee"],
            listing["internet_included"],
            listing["description"],
            listing["contact_name"],
            listing["contact_phone"],
            listing["image_url"]
        ))

    conn.commit()
    conn.close()
