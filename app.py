import os
import cv2
from datetime import datetime
from deepface import DeepFace
import mysql.connector

# Database connection
conn = mysql.connector.connect(
    host="localhost",      
    user="root",           
    password="12345678",   
    database="face_attendance"  
)
cursor = conn.cursor()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "images")
os.makedirs(IMG_DIR, exist_ok=True)



# โหลดรายชื่อจากโฟลเดอร์
known_people = [
    os.path.splitext(f)[0]
    for f in os.listdir(IMG_DIR)
    if f.lower().endswith((".jpg", ".jpeg", ".png"))
]
print(" โหลดฐานข้อมูลภาพ:", known_people if known_people else "(ยังไม่พบรูปใน 'static/uploads/' folder)")


#  DATABASE FUNCTIONS 
def get_user_id_by_name(name):
    cursor.execute("SELECT user_id FROM users WHERE name = %s", (name,))
    result = cursor.fetchone()
    return result[0] if result else None


def mark_attendance(user_id, status="เช็กชื่อเรียบร้อย"):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    # ดึงชื่อจาก users
    cursor.execute("SELECT name FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    user_name = user[0] if user else f"ID {user_id}"

    # ตรวจว่ามีบันทึกแล้วหรือยัง
    cursor.execute("""
        SELECT * FROM attendance 
        WHERE user_id = %s AND date = %s
    """, (user_id, date))
    result = cursor.fetchone()

    if result:
        print(f"วันนี้คุณ {user_name} เช็กชื่อไปแล้ว ")
        return

    cursor.execute("""
        INSERT INTO attendance (user_id, date, time, status)
        VALUES (%s, %s, %s, %s)
    """, (user_id, date, time, status))
    conn.commit()
    print(f"บันทึกเช็กชื่อ {user_name} (user_id={user_id}) เวลา {time} ")
    




# ฟังก์ชันเปิดกล้อง
def open_camera():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        for idx in [1, 2]:
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                print(f"📷 เปิดกล้อง (index {idx}) สำเร็จ")
                return cap
        print(" ไม่พบกล้อง")
        return None
    print(" เปิดกล้องสำเร็จ")
    return cap


#  MAIN LOOP 
cap = open_camera()
if cap is None or not cap.isOpened():
    exit(1)

FRAME_INTERVAL = 5
frame_count = 0
recognized_today = set()
current_date = datetime.now().strftime("%Y-%m-%d")

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        today = datetime.now().strftime("%Y-%m-%d")
        if today != current_date:
            current_date = today
            recognized_today.clear()

        display_text = "Scanning..."

        if frame_count % FRAME_INTERVAL == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            if len(faces) > 0:
                for (x, y, w, h) in faces:
                    face_roi = frame[y:y+h, x:x+w]

                    try:
                        results = DeepFace.find(
                            img_path=face_roi,
                            db_path=IMG_DIR,
                            enforce_detection=False,  #  ป้องกัน error ถ้าไม่เจอหน้า
                            silent=True
                        )

                        if isinstance(results, list) and len(results) > 0 and not results[0].empty:
                            top = results[0].iloc[0]
                            identity_path = top["identity"]
                            name = os.path.splitext(os.path.basename(identity_path))[0]

                            display_text = f"Detected: {name}"

                            if name not in recognized_today:
                                user_id = get_user_id_by_name(name)
                                if user_id:
                                    mark_attendance(user_id)
                                    recognized_today.add(name)
                                else:
                                    print(f" ไม่พบ {name} ในตาราง users")

                            # วาดกรอบสีเขียวรอบใบหน้า
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        else:
                            display_text = "No match found"

                    except Exception as e:
                        display_text = "Error"
                        print(" Error:", e)

            else:
                display_text = "No face detected"

        cv2.putText(
            frame,
            display_text,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0) if display_text.startswith("Detected") else (0, 0, 255),
            2,
            cv2.LINE_AA,
        )

        cv2.imshow("Face Attendance (DeepFace + OpenCV + MySQL)", frame)
        frame_count += 1

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    cursor.close()
    conn.close()
