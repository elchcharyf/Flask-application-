from flask import Flask, render_template, request
import pickle
import numpy as np
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# Chargement du modèle et du scaler
model = pickle.load(open("model.pkl", "rb"))
scaler = pickle.load(open("scaler.pkl", "rb"))

# Fonction de connexion à la base MySQL
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="ahmed2001",
        database="ma_base_de_donnees"
    )
# Initialisation de la table "visits"
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visits (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ip VARCHAR(100),
            page VARCHAR(255),
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()

# Fonction pour enregistrer une visite
def log_visit(ip, page):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO visits (ip, page, timestamp) VALUES (%s, %s, %s)",
        (ip, page, datetime.now())
    )
    conn.commit()
    conn.close()

@app.route("/health", methods=["GET"])
def health_check():
    return "OK", 200

@app.route("/", methods=["GET", "POST"])
def index():
    prediction = None

    if request.method == "POST":
        geo = request.form["Geography"]
        germany = 1 if geo == "Allemagne" else 0
        spain = 1 if geo == "Espagne" else 0
        france = 1 if geo == "France" else 0

        gender = 1 if request.form["Gender"] == "Homme" else 0

        data = [
            float(request.form["CreditScore"]),
            gender,
            float(request.form["Age"]),
            float(request.form["Tenure"]),
            float(request.form["Balance"]),
            float(request.form["NumOfProducts"]),
            float(request.form["HasCrCard"]),
            float(request.form["IsActiveMember"]),
            float(request.form["EstimatedSalary"]),
            germany,
            spain,
            france
        ]

        # Vérifie s’il manque des colonnes pour le scaler
        if len(data) < scaler.n_features_in_:
            missing_features = scaler.n_features_in_ - len(data)
            data.extend([0] * missing_features)

        data = scaler.transform([data])
        result = model.predict(data)[0]
        prediction = "🚨 Le client risque de partir." if result == 1 else "✅ Le client restera."

    # Enregistrer la visite
    log_visit(request.remote_addr, '/')

    return render_template("cours.html", prediction=prediction)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)