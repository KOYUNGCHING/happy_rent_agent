from flask import Flask, render_template, request, jsonify
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