from flask import Flask, render_template, jsonify
import mysql.connector
import os

app = Flask(__name__)

# Database config
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "12345678",   # แก้ตามจริง
    "database": "face_attendance"
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/attendance_api")
def attendance_api():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.attendance_id, u.name, a.date, a.time, a.status, u.image_path
        FROM attendance AS a
        INNER JOIN users AS u ON a.user_id = u.user_id
        ORDER BY a.date DESC, a.time DESC
    """)

    records = []
    for (attendance_id, name, date, time, status, image_path) in cursor:
        # เอาเฉพาะชื่อไฟล์จาก path
        filename = os.path.basename(image_path) if image_path else "default.png"
        records.append({
            "id": attendance_id,
            "name": name,
            "date": str(date),
            "time": str(time),
            "status": status,
            "image_url": f"/static/uploads/{filename}"
        })

    cursor.close()
    conn.close()

    return jsonify(records)

if __name__ == "__main__":
    app.run(debug=True)
