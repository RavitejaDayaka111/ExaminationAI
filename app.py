from flask import Flask, render_template, request, jsonify
import os, json, fitz
import google.generativeai as genai

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
HISTORY_FILE = "history.json"

#  Set your Gemini API Key
genai.configure(api_key="AIzaSyBdqjnf_BeBwO1fWs-LMSPgkm3Z1qdpNwk")
model = genai.GenerativeModel(model_name="models/gemini-2.5-pro")

# Load saved chat history
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

# Save chat history
def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    question = request.json.get("message", "")
    try:
        prompt = f"""
You are an AI tutor. Respond in two parts:
1. 📌 Key Point (1‑2 lines)
2. 📚 Detailed Explanation

Question: {question}
"""
        response = model.generate_content(prompt)
        answer = response.text.strip()

        history = load_history()
        history.insert(0, {"question": question, "answer": answer})
        save_history(history)

        return jsonify({"response": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/history", methods=["GET"])
def get_history():
    history = load_history()
    short_history = [{"id": i, "key": h["answer"].split("\n")[0][:60], "question": h["question"], "answer": h["answer"]} for i, h in enumerate(history)]
    return jsonify(short_history)

@app.route("/delete/<int:index>", methods=["DELETE"])
def delete_history(index):
    history = load_history()
    if 0 <= index < len(history):
        history.pop(index)
        save_history(history)
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Invalid index"}), 400

@app.route("/upload", methods=["POST"])
def upload_pdf():
    pdf_file = request.files.get("pdf")
    if pdf_file:
        path = os.path.join(app.config["UPLOAD_FOLDER"], pdf_file.filename)
        pdf_file.save(path)
        text = extract_text_from_pdf(path)
        return jsonify({"text": text[:2000] + "..." if len(text) > 2000 else text})
    return jsonify({"error": "No file uploaded"}), 400

def extract_text_from_pdf(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text.strip()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render provides PORT environment variable
    app.run(host="0.0.0.0", port=port)
