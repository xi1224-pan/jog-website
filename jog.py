from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3 # 💡 改用 Python 內建輕量資料庫，完全免費
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 💡 初始化資料庫：如果檔案不存在，會自動在雲端開好資料表
def init_db():
    conn = sqlite3.connect('running.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS running_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TEXT UNIQUE NOT NULL,              
            distance_km REAL NOT NULL,
            duration_text TEXT NOT NULL,
            avg_pace_text TEXT NOT NULL,
            speed_kmh REAL NOT NULL,            
            tag_text TEXT DEFAULT 'as usual',     
            cadence_spm INTEGER,
            steps_count INTEGER,               
            calories_burned INTEGER,           
            nausea_percentage INTEGER DEFAULT 0,
            status_note TEXT,
            photo_base64 TEXT,                      
            temperature INTEGER,
            wind_speed REAL,
            wind_dir TEXT,
            humidity INTEGER,
            km_splits TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

class RunLog(BaseModel):
    run_date: str
    dist: str
    dur: str
    pace: str
    speed: str
    tag: Optional[str] = "as usual"
    cad: Optional[str] = ""
    steps: Optional[str] = ""     
    calories: Optional[str] = ""  
    nau: Optional[str] = "0"
    note: Optional[str] = ""
    photo: Optional[List[str]] = []
    temperature: Optional[int] = None
    wind_speed: Optional[float] = None
    wind_dir: Optional[str] = None
    humidity: Optional[int] = None
    km_splits: Optional[str] = ""

@app.get("/api/logs")
def get_all_logs():
    try:
        conn = sqlite3.connect('running.db')
        conn.row_factory = sqlite3.Row # 讓資料可以用欄位名讀取
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM running_logs ORDER BY run_date ASC")
        rows = cursor.fetchall()
        
        result = {}
        for row in rows:
            d_str = row['run_date']
            photo_list = json.loads(row['photo_base64']) if row['photo_base64'] else []
            
            result[d_str] = {
                "dist": str(row['distance_km']),
                "dur": row['duration_text'],
                "pace": row['avg_pace_text'],
                "speed": str(row['speed_kmh']),
                "tag": row['tag_text'],
                "cad": str(row['cadence_spm']) if row['cadence_spm'] else "",
                "steps": str(row['steps_count']) if row['steps_count'] else "",      
                "calories": str(row['calories_burned']) if row['calories_burned'] else "",  
                "nau": str(row['nausea_percentage']),
                "note": row['status_note'],
                "photo": photo_list,
                "temperature": row['temperature'],
                "wind_speed": row['wind_speed'],
                "wind_dir": row['wind_dir'],
                "humidity": row['humidity'],
                "km_splits": row['km_splits'] if row['km_splits'] else ""
            }
        conn.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/logs")
def save_log(log: RunLog):
    try:
        conn = sqlite3.connect('running.db')
        cursor = conn.cursor()
        
        # 使用 SQLite 的 INSERT OR REPLACE 語法達到原本 ON DUPLICATE KEY UPDATE 的效果
        sql = """
            INSERT OR REPLACE INTO running_logs 
            (run_date, distance_km, duration_text, avg_pace_text, speed_kmh, tag_text, 
             cadence_spm, steps_count, calories_burned, nausea_percentage, status_note, photo_base64,
             temperature, wind_speed, wind_dir, humidity, km_splits)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cadence = int(log.cad) if log.cad and log.cad.isdigit() else None
        steps = int(log.steps) if log.steps and log.steps.isdigit() else None      
        calories = int(log.calories) if log.calories and log.calories.isdigit() else None  
        nausea = int(log.nau) if log.nau and log.nau.isdigit() else 0
        photo_json = json.dumps(log.photo)
        
        val = (log.run_date, float(log.dist), log.dur, log.pace, float(log.speed), log.tag, 
               cadence, steps, calories, nausea, log.note, photo_json,
               log.temperature, log.wind_speed, log.wind_dir, log.humidity, log.km_splits)
        
        cursor.execute(sql, val)
        conn.commit()
        conn.close()
        return {"status": "success", "message": "儲存成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/logs/{run_date}")
def delete_log(run_date: str):
    try:
        conn = sqlite3.connect('running.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM running_logs WHERE run_date = ?", (run_date,))
        conn.commit()
        conn.close()
        return {"status": "success", "message": "已刪除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))