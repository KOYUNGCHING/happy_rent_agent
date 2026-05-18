from flask import Flask, render_template, request, jsonify, redirect, url_for
from agent_service import run_agent, chat_with_agent
from database import get_db_connection

app = Flask(__name__)


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
        ai_result = run_agent(listing_data["address"])
    except Exception as e:
        # 如果 AI 分析失敗，不要讓整個房源頁壞掉
        # 先印出錯誤，然後前端顯示資料不足
        print("Listing AI analysis error:", e)
        ai_result = None

    return render_template(
        "listing_detail.html",
        listing=listing_data,
        ai_result=ai_result
    )

@app.route("/landlord/new", methods=["GET", "POST"])
def new_listing():
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
    landlord_id = 1

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

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "")
    current_area_data = data.get("current_area_data")

    if not message.strip():
        return jsonify({"error": "Please enter a message."}), 400

    reply = chat_with_agent(message, current_area_data)
    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True)