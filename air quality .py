# =========================================================
# 🌍 AIR QUALITY PREDICTION & HEALTH ALERT SYSTEM
# FULL STACK (FRONTEND + BACKEND + ML + DB) IN ONE FILE
# ERROR-SAFE VERSION FOR MAJOR PROJECT
# =========================================================

# ===================== IMPORTS ===========================
from flask import Flask, request, render_template_string
import sqlite3
import os
import pickle
import numpy as np

from sklearn.linear_model import LinearRegression

app = Flask(__name__)

MODEL_FILE = "aqi_model.pkl"
DB_FILE = "aqi.db"

# =========================================================
# 🗄️ DATABASE SECTION
# =========================================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pm25 REAL,
        pm10 REAL,
        no2 REAL,
        co REAL,
        aqi REAL,
        category TEXT,
        advice TEXT
    )
    """)

    conn.commit()
    conn.close()

# =========================================================
# 🧠 MACHINE LEARNING SECTION
# =========================================================
def train_model():
    # Sample dataset
    X = np.array([
        [30, 40, 20, 0.5],
        [80, 90, 40, 1.0],
        [150, 160, 80, 1.5],
        [250, 300, 120, 2.0],
        [400, 450, 200, 3.0]
    ])

    y = np.array([50, 100, 200, 300, 400])

    model = LinearRegression()
    model.fit(X, y)

    with open(MODEL_FILE, "wb") as f:
        pickle.dump(model, f)

def load_model():
    if not os.path.exists(MODEL_FILE):
        train_model()

    with open(MODEL_FILE, "rb") as f:
        model = pickle.load(f)

    return model

# =========================================================
# 🧪 AQI LOGIC (HEALTH ALERT SYSTEM)
# =========================================================
def get_category_and_advice(aqi):
    if aqi <= 50:
        return "Good", "Air quality is satisfactory. Enjoy outdoor activities."
    elif aqi <= 100:
        return "Moderate", "Sensitive people should limit outdoor exertion."
    elif aqi <= 200:
        return "Poor", "Wear a mask. Reduce outdoor activities."
    elif aqi <= 300:
        return "Very Poor", "Avoid outdoor exposure. Use air purifier."
    else:
        return "Hazardous", "Stay indoors. Seek medical advice if needed."

# Initialize system
init_db()
model = load_model()

# =========================================================
# 🌐 FRONTEND SECTION (GUI - HTML + CSS)
# =========================================================
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Air Quality System</title>
    <style>
        body {
            font-family: Arial;
            background: linear-gradient(to right, #00c6ff, #0072ff);
            color: white;
            text-align: center;
            padding: 40px;
        }

        input {
            padding: 10px;
            margin: 5px;
            width: 120px;
            border-radius: 5px;
            border: none;
        }

        button {
            padding: 10px 20px;
            background: #00e676;
            border: none;
            color: black;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
        }

        button:hover {
            background: #00c853;
        }

        .result {
            margin-top: 20px;
            font-size: 20px;
            font-weight: bold;
        }

        .card {
            background: white;
            color: black;
            padding: 15px;
            border-radius: 10px;
            margin-top: 30px;
            width: 60%;
            margin-left: auto;
            margin-right: auto;
            text-align: left;
        }
    </style>
</head>
<body>

<h1>🌍 Air Quality Prediction & Health Alert</h1>

<form method="POST">
    <input type="number" step="any" name="pm25" placeholder="PM2.5" required>
    <input type="number" step="any" name="pm10" placeholder="PM10" required><br>
    <input type="number" step="any" name="no2" placeholder="NO2" required>
    <input type="number" step="any" name="co" placeholder="CO" required><br><br>

    <button type="submit">Predict AQI</button>
</form>

{% if result %}
<div class="result">
    AQI: {{ result.aqi }} <br>
    Category: {{ result.category }} <br>
    Advice: {{ result.advice }}
</div>
{% endif %}

{% if logs %}
<div class="card">
    <h3>📜 Recent Records</h3>
    <ul>
    {% for row in logs %}
        <li>
            AQI {{ row[5] | round(2) }} → {{ row[6] }} <br>
            <small>{{ row[7] }}</small>
        </li>
    {% endfor %}
    </ul>
</div>
{% endif %}

</body>
</html>
"""

# =========================================================
# ⚙️ BACKEND SECTION (FLASK ROUTES)
# =========================================================
@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    logs = []

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        if request.method == "POST":
            # Safe input handling
            pm25 = float(request.form.get("pm25", 0))
            pm10 = float(request.form.get("pm10", 0))
            no2 = float(request.form.get("no2", 0))
            co = float(request.form.get("co", 0))

            features = np.array([[pm25, pm10, no2, co]])

            aqi = model.predict(features)[0]
            category, advice = get_category_and_advice(aqi)

            result = {
                "aqi": round(aqi, 2),
                "category": category,
                "advice": advice
            }

            # Save to DB
            cursor.execute("""
                INSERT INTO records (pm25, pm10, no2, co, aqi, category, advice)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (pm25, pm10, no2, co, aqi, category, advice))

            conn.commit()

        # Fetch logs
        cursor.execute("SELECT * FROM records ORDER BY id DESC LIMIT 5")
        logs = cursor.fetchall()

    except Exception as e:
        result = {
            "aqi": "Error",
            "category": "Invalid",
            "advice": "Please enter valid numeric values"
        }

    finally:
        conn.close()

    return render_template_string(HTML_PAGE, result=result, logs=logs)

# =========================================================
# ▶️ RUN APPLICATION
# =========================================================
if __name__ == "__main__":
    app.run(debug=True)