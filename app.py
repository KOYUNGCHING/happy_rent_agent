import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from agent_service import run_agent, chat_with_agent, chat_with_agent_gemini, analyze_listing
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection, init_db, seed_sample_data
app = Flask(__name__)
# Flask session 需要 secret_key 才能運作
# session 可以用來記錄目前登入的使用者是誰
# 注意：正式上線時不要把 secret key 寫死在程式裡，應該放在 .env
app.secret_key = os.getenv("FLASK_SECRET_KEY", "happy-rent-dev-secret-key")
init_db()

seed_sample_data()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/listings")
def listings():
    """
    找房者房源列表頁。

    這個 route 的任務：
    1. 連接 SQLite 資料庫
    2. 查詢目前 status = 'available' 的房源
    3. 把房源資料傳給 listings.html
    """

    # 建立資料庫連線
    conn = get_db_connection()

    # 從 listings table 查詢目前可租的房源
    # ORDER BY created_at DESC 代表最新上架的房源排最前面
    rows = conn.execute("""
        SELECT *
        FROM listings
        WHERE status = 'available'
        ORDER BY created_at DESC
    """).fetchall()

    # 關閉資料庫連線
    conn.close()

    # sqlite3.Row 雖然可以像 dict 一樣使用，
    # 但轉成真正的 dict 後，在 template 裡比較直覺
    listing_list = [dict(row) for row in rows]

    # 把 listing_list 傳給前端 HTML
    return render_template("listings.html", listings=listing_list)

@app.route("/listings/<int:listing_id>")
def listing_detail(listing_id):
    """
    房源詳細頁。

    這個 route 的任務：
    1. 根據 listing_id 從 SQLite 找出單一房源
    2. 如果找不到房源，就回傳 404
    3. 使用房源地址呼叫 run_agent()
    4. 把房源資料與 AI 分析結果傳給 listing_detail.html
    """

    # 建立資料庫連線
    conn = get_db_connection()

    # 根據房源 id 查詢單一房源
    listing = conn.execute("""
        SELECT *
        FROM listings
        WHERE id = ?
    """, (listing_id,)).fetchone()

    # 查詢完就先關閉資料庫連線
    conn.close()

    # 如果找不到房源，回傳簡單錯誤訊息
    # 之後可以改成漂亮的 404 頁面
    if listing is None:
        return "找不到這筆房源資料", 404

    # 把 sqlite3.Row 轉成 dict，template 比較好使用
    listing_data = dict(listing)

    # 用房源地址呼叫 AI Agent
    # 這裡等於讓 Agent 分析「這間房所在的位置」
    #
    # 例如：
    # address = 桃園市中壢區中央大學後門附近
    # run_agent() 會做：
    # Geocoding -> Weather -> Commute -> Rental -> Summary
    try:
        # 使用新版 analyze_listing()
        # 它不只分析地址，還會分析租金、房型、設備、水電與看房風險
        listing_analysis = analyze_listing(listing_data)
    except Exception as e:
        print("Listing AI analysis error:", e)
        listing_analysis = None

    return render_template(
        "listing_detail.html",
        listing=listing_data,
        listing_analysis=listing_analysis
    )

@app.route("/landlord/new", methods=["GET", "POST"])
def new_listing():
    # 房東上架前，必須先登入
    if "user_id" not in session:
        return redirect(url_for("login"))

    # 只有房東身份可以上架房源
    if session.get("user_role") != "landlord":
        return "你不是房東身份，無法上架房源。", 403
    """
    房東新增房源頁。

    這個 route 同時處理兩種情況：

    1. GET request：
       使用者第一次打開 /landlord/new
       → 顯示新增房源表單

    2. POST request：
       使用者填完表單並送出
       → 從 request.form 取得表單資料
       → 寫入 SQLite listings table
       → 導回 /listings 房源列表頁
    """

    # 如果是 GET，代表只是要顯示表單頁面
    if request.method == "GET":
        return render_template("new_listing.html")

    # 從表單取得基本文字欄位
    title = request.form.get("title", "").strip()
    area = request.form.get("area", "").strip()
    address = request.form.get("address", "").strip()
    room_type = request.form.get("room_type", "").strip()

    # 租金與押金是數字欄位
    # 如果使用者沒有填押金，就先設成 0
    rent = int(request.form.get("rent", 0))
    deposit = int(request.form.get("deposit", 0) or 0)

    # 房間細節
    size = request.form.get("size", "").strip()
    floor = request.form.get("floor", "").strip()

    # checkbox 如果有勾選，request.form 會收到 "on"
    # 如果沒勾選，request.form.get() 會是 None
    # 所以這裡用 == "on" 判斷，再轉成 1 或 0 存進資料庫
    has_window = 1 if request.form.get("has_window") == "on" else 0
    can_cook = 1 if request.form.get("can_cook") == "on" else 0
    pet_allowed = 1 if request.form.get("pet_allowed") == "on" else 0
    internet_included = 1 if request.form.get("internet_included") == "on" else 0

    # 費用與描述
    water_fee = request.form.get("water_fee", "").strip()
    electricity_fee = request.form.get("electricity_fee", "").strip()
    description = request.form.get("description", "").strip()

    # 聯絡資訊
    contact_name = request.form.get("contact_name", "").strip()
    contact_phone = request.form.get("contact_phone", "").strip()

    # 目前 MVP 先用圖片 URL，不處理圖片上傳
    # 之後可以升級成上傳圖片到 static/uploads
    image_url = request.form.get("image_url", "").strip()

    # 如果房東沒有填圖片，給一張預設圖
    if not image_url:
        image_url = "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267"


    if not title or not area or not address or not room_type or rent <= 0:
        return render_template(
            "new_listing.html",
            error="請填寫房源名稱、地區、地址、房型與租金。"
        )

    conn = get_db_connection()

    # 目前還沒有正式登入系統，所以 landlord_id 先用 1
    # 之後做登入後，會改成 session["user_id"]
    # 使用目前登入的房東 user_id 作為 landlord_id
    # 這樣每筆房源都會知道是誰上架的
    landlord_id = session["user_id"]

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
            image_url,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
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
        image_url,
        "available"
    ))

    # commit 代表真的把新增房源存進資料庫
    conn.commit()

    # 關閉資料庫連線
    conn.close()

    # 新增成功後，導回房源列表頁
    return redirect(url_for("listings"))


@app.route("/api/analyze", methods=["POST"])
def analyze_area():
    data = request.get_json()
    user_input = data.get("query", "")

    if not user_input.strip():
        return jsonify({"error": "Please enter a location."}), 400

    try:
        result = run_agent(user_input)
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    except Exception as e:
        print("Analyze error:", e)
        return jsonify({"error": "分析時發生錯誤，請稍後再試。"}), 500

@app.route("/register", methods=["GET", "POST"])
def register():
    """
    使用者註冊頁。

    GET：
    - 顯示註冊表單

    POST：
    - 取得使用者填寫的 name / email / password / role
    - 檢查 email 是否已經存在
    - 將密碼加密後存入 users table
    - 註冊成功後導到 login 頁
    """

    # GET request：顯示註冊頁面
    if request.method == "GET":
        return render_template("register.html")

    # POST request：處理註冊資料
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    role = request.form.get("role", "").strip()

    # 基本欄位檢查
    if not name or not email or not password or not role:
        return render_template(
            "register.html",
            error="請完整填寫姓名、Email、密碼與身份。"
        )

    # 只允許 student / landlord 兩種身份
    if role not in ["student", "landlord"]:
        return render_template(
            "register.html",
            error="身份選擇不正確。"
        )

    conn = get_db_connection()

    # 檢查 email 是否已經被註冊
    existing_user = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    if existing_user:
        conn.close()
        return render_template(
            "register.html",
            error="這個 Email 已經被註冊過了。"
        )

    # 密碼不要明文存進資料庫
    # generate_password_hash 會把密碼轉成 hash
    password_hash = generate_password_hash(password)

    # 寫入 users table
    conn.execute("""
        INSERT INTO users (name, email, password, role)
        VALUES (?, ?, ?, ?)
    """, (name, email, password_hash, role))

    conn.commit()
    conn.close()

    # 註冊成功後導到登入頁
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    使用者登入頁。

    GET：
    - 顯示登入表單

    POST：
    - 根據 email 找使用者
    - 檢查密碼是否正確
    - 登入成功後，把 user_id / role / name 存進 session
    - 根據身份導到不同頁面
    """

    # GET request：顯示登入頁面
    if request.method == "GET":
        return render_template("login.html")

    # POST request：處理登入資料
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()

    if not email or not password:
        return render_template(
            "login.html",
            error="請輸入 Email 和密碼。"
        )

    conn = get_db_connection()

    # 根據 email 查使用者
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    conn.close()

    # 如果找不到使用者
    if user is None:
        return render_template(
            "login.html",
            error="Email 或密碼錯誤。"
        )

    # 檢查密碼
    # check_password_hash(資料庫裡的 hash, 使用者輸入的密碼)
    if not check_password_hash(user["password"], password):
        return render_template(
            "login.html",
            error="Email 或密碼錯誤。"
        )

    # 登入成功，把使用者資訊存進 session
    # session 可以讓後端知道目前是誰登入
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_role"] = user["role"]

    # 根據身份導向不同頁面
    if user["role"] == "landlord":
        return redirect(url_for("landlord_dashboard"))

    return redirect(url_for("listings"))
@app.route("/logout")
def logout():
    """
    使用者登出。

    session.clear() 會清掉所有登入狀態。
    """

    session.clear()
    return redirect(url_for("home"))

@app.route("/landlord/listings/<int:listing_id>/edit", methods=["GET", "POST"])
def edit_listing(listing_id):
    """
    房東編輯房源頁。

    這個 route 有兩種情況：

    1. GET：
       顯示目前房源資料，讓房東修改。

    2. POST：
       接收表單資料，更新資料庫中的房源。

    權限限制：
    - 必須登入
    - 必須是 landlord
    - 只能編輯自己上架的房源
    """

    # 檢查是否登入
    if "user_id" not in session:
        return redirect(url_for("login"))

    # 檢查身份是否為房東
    if session.get("user_role") != "landlord":
        return "你不是房東身份，無法編輯房源。", 403

    conn = get_db_connection()

    # 查詢這筆房源，並確認 landlord_id 是目前登入的房東
    listing = conn.execute("""
        SELECT *
        FROM listings
        WHERE id = ? AND landlord_id = ?
    """, (listing_id, session["user_id"])).fetchone()

    # 如果找不到，代表房源不存在，或不是這個房東的房源
    if listing is None:
        conn.close()
        return "找不到房源，或你沒有權限編輯這筆房源。", 404

    # GET：顯示編輯頁
    if request.method == "GET":
        conn.close()
        return render_template("edit_listing.html", listing=dict(listing))

    # --------------------------------------------------------
    # POST：更新房源資料
    # --------------------------------------------------------

    title = request.form.get("title", "").strip()
    area = request.form.get("area", "").strip()
    address = request.form.get("address", "").strip()
    room_type = request.form.get("room_type", "").strip()

    rent = int(request.form.get("rent", 0))
    deposit = int(request.form.get("deposit", 0) or 0)

    size = request.form.get("size", "").strip()
    floor = request.form.get("floor", "").strip()

    has_window = 1 if request.form.get("has_window") == "on" else 0
    can_cook = 1 if request.form.get("can_cook") == "on" else 0
    pet_allowed = 1 if request.form.get("pet_allowed") == "on" else 0
    internet_included = 1 if request.form.get("internet_included") == "on" else 0

    water_fee = request.form.get("water_fee", "").strip()
    electricity_fee = request.form.get("electricity_fee", "").strip()
    description = request.form.get("description", "").strip()

    contact_name = request.form.get("contact_name", "").strip()
    contact_phone = request.form.get("contact_phone", "").strip()
    image_url = request.form.get("image_url", "").strip()

    if not image_url:
        image_url = listing["image_url"]

    # 基本驗證
    if not title or not area or not address or not room_type or rent <= 0:
        conn.close()
        return render_template(
            "edit_listing.html",
            listing=dict(listing),
            error="請填寫房源名稱、地區、地址、房型與租金。"
        )

    # 更新資料庫
    conn.execute("""
        UPDATE listings
        SET
            title = ?,
            area = ?,
            address = ?,
            room_type = ?,
            rent = ?,
            deposit = ?,
            size = ?,
            floor = ?,
            has_window = ?,
            can_cook = ?,
            pet_allowed = ?,
            water_fee = ?,
            electricity_fee = ?,
            internet_included = ?,
            description = ?,
            contact_name = ?,
            contact_phone = ?,
            image_url = ?
        WHERE id = ? AND landlord_id = ?
    """, (
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
        image_url,
        listing_id,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("landlord_dashboard"))
@app.route("/landlord/listings/<int:listing_id>/deactivate", methods=["POST"])
def deactivate_listing(listing_id):
    """
    房東下架房源。

    這裡不是刪除資料，而是把 status 改成 'inactive'。

    為什麼不直接 DELETE？
    因為正式平台通常會保留歷史資料，
    例如之後可以查詢：
    - 房東曾經上架過哪些房源
    - 哪些房源已出租
    - 房源歷史紀錄
    """

    # 檢查是否登入
    if "user_id" not in session:
        return redirect(url_for("login"))

    # 檢查身份
    if session.get("user_role") != "landlord":
        return "你不是房東身份，無法下架房源。", 403

    conn = get_db_connection()

    # 只允許房東下架自己的房源
    conn.execute("""
        UPDATE listings
        SET status = 'inactive'
        WHERE id = ? AND landlord_id = ?
    """, (listing_id, session["user_id"]))

    conn.commit()
    conn.close()

    return redirect(url_for("landlord_dashboard"))

@app.route("/landlord/dashboard")
def landlord_dashboard():
    """
    房東後台。

    功能：
    - 只有房東可以進入
    - 顯示目前登入房東自己上架的房源
    """

    # 檢查是否登入
    if "user_id" not in session:
        return redirect(url_for("login"))

    # 檢查身份是否為房東
    if session.get("user_role") != "landlord":
        return "你不是房東身份，無法進入房東後台。", 403

    conn = get_db_connection()

    # 只查目前登入房東自己的房源
    rows = conn.execute("""
        SELECT *
        FROM listings
        WHERE landlord_id = ?
        ORDER BY created_at DESC
    """, (session["user_id"],)).fetchall()

    conn.close()

    listings = [dict(row) for row in rows]

    return render_template(
        "landlord_dashboard.html",
        listings=listings
    )

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "")
    current_area_data = data.get("current_area_data")

    if not message.strip():
        return jsonify({"error": "Please enter a message."}), 400

    # 使用 Gemini Chat Agent 回覆
    # 如果 Gemini 失敗，chat_with_agent_gemini() 內部會 fallback 到規則式回覆
    reply = chat_with_agent_gemini(message, current_area_data)
    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True)