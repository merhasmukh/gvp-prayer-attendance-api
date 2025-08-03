from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime, time

app = Flask(__name__)
CORS(app)  # Enable CORS if frontend is hosted separately

# Constants
PRAYER_LAT = 23.110917   # Replace with actual latitude of prayer area
PRAYER_LONG = 72.526056 # Replace with actual longitude
ALLOWED_RADIUS = 0.0015  # Roughly 50 meters
TIME_START = time(10, 15)
TIME_END = time(23, 35)

# SQLite setup
def init_db():
    conn = sqlite3.connect("attendance.db")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_number TEXT NOT NULL,
        device_id TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        UNIQUE(roll_number, date),
        UNIQUE(device_id, date)
    )
    """)
    conn.commit()
    conn.close()

init_db()

# Helper functions
def is_within_time():
    now = datetime.now().time()
    return TIME_START <= now <= TIME_END

def is_within_location(lat, long):
    return abs(lat - PRAYER_LAT) < ALLOWED_RADIUS and abs(long - PRAYER_LONG) < ALLOWED_RADIUS

@app.route('/api/mark-attendance', methods=['POST'])
def mark_attendance():
    try:
        data = request.get_json()
        roll_number = data['roll_number'].strip().upper()
        device_id = data['device_id']
        lat = float(data['lat'])
        long = float(data['long'])
        today = datetime.now().date()
        now = datetime.now().time()

        if not is_within_time():
            return "Attendance allowed only between 10:25 and 10:35 AM", 400

        if not is_within_location(lat, long):
            return "You are not at the prayer location", 400

        conn = sqlite3.connect("attendance.db")
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO attendance (roll_number, device_id, date, time, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (roll_number, device_id, str(today), now.strftime('%H:%M:%S'), lat, long))
        conn.commit()
        conn.close()

        return "✅ Attendance marked successfully"

    except sqlite3.IntegrityError:
        return "❌ You have already marked attendance today", 400
    except Exception as e:
        print("Error:", e)
        return "❌ Something went wrong", 500

@app.route('/')
def health():
    return "Attendance API running"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
