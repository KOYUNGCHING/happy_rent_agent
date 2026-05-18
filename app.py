from flask import Flask, render_template, request, jsonify
from agent_service import run_agent, chat_with_agent

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze_area():
    data = request.get_json()
    user_input = data.get("query", "")

    if not user_input.strip():
        return jsonify({"error": "Please enter a location."}), 400

    result = run_agent(user_input)
    return jsonify(result)


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