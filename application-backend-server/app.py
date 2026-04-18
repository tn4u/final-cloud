from flask import Flask, jsonify, request
import json
import os
import time
import requests
import pymysql
from jose import jwt

app = Flask(__name__)

ISSUER = os.getenv("OIDC_ISSUER", "http://localhost:8081/realms/realm_final_cloud")
AUDIENCE = os.getenv("OIDC_AUDIENCE", "flask-app")
JWKS_URL = os.getenv(
    "OIDC_JWKS_URL",
    "http://authentication-identity-server:8080/realms/realm_final_cloud/protocol/openid-connect/certs"
)
DB_HOST = os.getenv("DB_HOST", "relational-database-server")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_NAME = os.getenv("DB_NAME", "studentdb")

_JWKS = None
_TS = 0

def get_jwks():
    global _JWKS, _TS
    now = time.time()
    if not _JWKS or now - _TS > 600:
        r = requests.get(JWKS_URL, timeout=5)
        print("JWKS_URL =", JWKS_URL)
        print("Status =", r.status_code)
        print("Body =", r.text)
        _JWKS = r.json()
        _TS = now
    return _JWKS

@app.get("/hello")
def hello():
    return jsonify({
        "message": "Hello from Application Backend Server!",
        "service": "application-backend-server",
        "project": "final-cloud"
    })

@app.get("/student")
def student():
    try:
        with open("students.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({
            "source": "students.json",
            "count": len(data),
            "students": data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/students-db")
def students_db():
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, student_id, fullname, dob, major FROM students")
                rows = cursor.fetchall()
        return jsonify({
            "source": "database",
            "count": len(rows),
            "students": rows
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/secure")
def secure():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "Missing Bearer token"}), 401

    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(
            token,
            get_jwks(),
            algorithms=["RS256"],
            issuer=ISSUER,
            options={"verify_aud": False}
        )
        return jsonify({
            "message": "Secure resource OK",
            "preferred_username": payload.get("preferred_username"),
            "realm": ISSUER
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)