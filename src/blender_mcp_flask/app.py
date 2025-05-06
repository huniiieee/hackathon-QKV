from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json["message"]

    # 테스트 응답
    return jsonify({"reply": "hi"})

if __name__ == "__main__":
    app.run(debug=True)
