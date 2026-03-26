# =========================================================
# 📧 EMAIL SPAM RECTIFIER (FULL STACK - ERROR SAFE VERSION)
# =========================================================

from flask import Flask, request, render_template_string
import sqlite3
import os
import pickle

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

app = Flask(__name__)

MODEL_FILE = "model.pkl"
VECTORIZER_FILE = "vectorizer.pkl"
DB_FILE = "spam.db"

# ===================== DATABASE ==========================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT,
        prediction TEXT
    )
    """)

    conn.commit()
    conn.close()

# ===================== MODEL TRAINING ====================
def train_model():
    messages = [
        "Win money now", "Free prize claim", "Limited offer hurry",
        "Hello friend", "Let's meet tomorrow", "Project update",
        "Congratulations you won lottery", "Call me later", "Important meeting"
    ]

    labels = [1,1,1,0,0,0,1,0,0]

    vectorizer = CountVectorizer()
    X = vectorizer.fit_transform(messages)

    model = MultinomialNB()
    model.fit(X, labels)

    with open(MODEL_FILE, "wb") as f:
        pickle.dump(model, f)

    with open(VECTORIZER_FILE, "wb") as f:
        pickle.dump(vectorizer, f)

# ===================== SAFE LOAD =========================
def load_model():
    if not os.path.exists(MODEL_FILE) or not os.path.exists(VECTORIZER_FILE):
        train_model()

    with open(MODEL_FILE, "rb") as f:
        model = pickle.load(f)

    with open(VECTORIZER_FILE, "rb") as f:
        vectorizer = pickle.load(f)

    return model, vectorizer

# Initialize DB and model
init_db()
model, vectorizer = load_model()

# ===================== FRONTEND ==========================
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Spam Rectifier</title>
    <style>
        body {
            font-family: Arial;
            background: linear-gradient(to right, #667eea, #764ba2);
            color: white;
            text-align: center;
            padding: 50px;
        }

        textarea {
            width: 60%;
            height: 120px;
            border-radius: 10px;
            padding: 10px;
            font-size: 16px;
        }

        button {
            padding: 10px 20px;
            font-size: 16px;
            border: none;
            border-radius: 5px;
            background-color: #00c9a7;
            color: white;
            cursor: pointer;
        }

        button:hover {
            background-color: #00a389;
        }

        .result {
            margin-top: 20px;
            font-size: 22px;
            font-weight: bold;
        }

        .logs {
            margin-top: 40px;
            background: white;
            color: black;
            padding: 15px;
            border-radius: 10px;
            width: 60%;
            margin-left: auto;
            margin-right: auto;
            text-align: left;
        }
    </style>
</head>
<body>

    <h1>📧 Email Spam Rectifier</h1>

    <form method="POST">
        <textarea name="message" placeholder="Enter your email text here..." required></textarea>
        <br><br>
        <button type="submit">Check Spam</button>
    </form>

    {% if result %}
        <div class="result">
            Result: {{ result }}
        </div>
    {% endif %}

    {% if logs %}
        <div class="logs">
            <h3>📜 History (Last 5)</h3>
            <ul>
                {% for log in logs %}
                    <li><b>{{ log[1] }}</b> → {{ log[2] }}</li>
                {% endfor %}
            </ul>
        </div>
    {% endif %}

</body>
</html>
"""

# ===================== ROUTES ============================
@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    logs = []

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        if request.method == "POST":
            message = request.form.get("message", "").strip()

            if message:  # avoid empty input crash
                vec = vectorizer.transform([message])
                prediction = model.predict(vec)[0]

                result = "🚫 Spam" if prediction == 1 else "✅ Not Spam"

                cursor.execute(
                    "INSERT INTO logs (message, prediction) VALUES (?, ?)",
                    (message, result)
                )
                conn.commit()

        cursor.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 5")
        logs = cursor.fetchall()

    except Exception as e:
        result = "⚠️ Error occurred"

    finally:
        conn.close()

    return render_template_string(HTML_PAGE, result=result, logs=logs)

# ===================== RUN ===============================
if __name__ == "__main__":
    app.run(debug=True)