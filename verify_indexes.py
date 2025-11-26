import time
import random
from datetime import datetime, timedelta
from sqlalchemy import text
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import json


app = Flask(__name__)

db_url = os.environ.get('DATABASE_URL', 'postgresql://admin:securepassword123@localhost:5432/meeting_room_db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def verify_room_index():
    print("\n" + "="*50)
    print("   Test 1: rooms indexing (Location)")
    print("="*50)
    
    # Raw SQL to check if data exists
    count = db.session.execute(text("SELECT count(*) FROM rooms")).scalar()
    
    if count < 10000:
        print("Generating 10,000 dummy rooms...")

        values = []
        for i in range(10000):
            values.append(f"('Room {i}', {10 + (i%50)}, 'Projector', 'Building {i%100}')")
        

        chunk_size = 1000
        for i in range(0, len(values), chunk_size):
            chunk = values[i:i+chunk_size]
            sql = f"INSERT INTO rooms (name, capacity, equipment, location) VALUES {','.join(chunk)}"
            db.session.execute(text(sql))
        db.session.commit()
        print("Done.")
    
    print("Running Query: SELECT * FROM rooms WHERE location = 'Building 50'")
    result = db.session.execute(text("EXPLAIN ANALYZE SELECT * FROM rooms WHERE location = 'Building 50'"))
    
    print("\n--- EXECUTION PLAN ---")
    for row in result:
        line = row[0]
        if "Index Scan" in line or "Bitmap Heap Scan" in line:
            print(f"Success: {line.strip()}")
        elif "Seq Scan" in line:
            print(f"Warning: {line.strip()}")

def verify_booking_index():
    print("\n" + "="*50)
    print("   Test 2: bookings indexing (Start Time)")
    print("="*50)
    
    count = db.session.execute(text("SELECT count(*) FROM bookings")).scalar()
    
    if count < 10000:
        print("Generating 10,000 dummy bookings...")
        values = []
        base_time = datetime.now()
        for i in range(10000):
            start = base_time + timedelta(days=random.randint(0, 1000))
            end = start + timedelta(hours=1)

            start_str = start.strftime('%Y-%m-%d %H:%M:%S')
            end_str = end.strftime('%Y-%m-%d %H:%M:%S')
            values.append(f"(1, {random.randint(1,50)}, '{start_str}', '{end_str}')")
            
        chunk_size = 1000
        for i in range(0, len(values), chunk_size):
            chunk = values[i:i+chunk_size]
            sql = f"INSERT INTO bookings (user_id, room_id, start_time, end_time) VALUES {','.join(chunk)}"
            db.session.execute(text(sql))
        db.session.commit()
        print("Done.")

    target_date = (datetime.now() + timedelta(days=500)).strftime('%Y-%m-%d')
    print(f"Running Query: SELECT * FROM bookings WHERE start_time > '{target_date}'")
    
    result = db.session.execute(text(f"EXPLAIN ANALYZE SELECT * FROM bookings WHERE start_time > '{target_date}'"))
    
    print("Execution plan")
    for row in result:
        line = row[0]
        if "Index Scan" in line or "Bitmap Heap Scan" in line:
            print(f"Success: {line.strip()}")
        elif "Seq Scan" in line:
            print(f"Warning: {line.strip()}")


if __name__ == "__main__":
    with app.app_context():
        
        try:
            db.create_all()
        except:
            pass 
            
        verify_room_index()
        verify_booking_index()


