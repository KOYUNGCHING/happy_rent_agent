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