import os
import shutil
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from app.database import init_db, get_db_connection
from app.ocr_engine import extract_text
from app.parser import parse_receipt_lines

# Load Env
load_dotenv()
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Init App
app = FastAPI(title="RupiahReceipts")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize DB on startup
@app.on_event("startup")
def startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_receipt(file: UploadFile = File(...)):
    # 1. Save File
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 2. OCR Processing
    raw_lines = extract_text(file_path)
    
    # 3. Parse Data
    items = parse_receipt_lines(raw_lines)
    total_amount = sum(item['price'] for item in items)
    
    # 4. Save to DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO receipts (filename, total_amount) VALUES (?, ?)", (file.filename, total_amount))
    receipt_id = cursor.lastrowid
    
    for item in items:
        cursor.execute("INSERT INTO items (receipt_id, item_name, price) VALUES (?, ?, ?)", 
                       (receipt_id, item['name'], item['price']))
    
    conn.commit()
    conn.close()
    
    return JSONResponse({"status": "success", "receipt_id": receipt_id, "items": items, "total": total_amount})

@app.get("/api/analytics")
async def get_analytics():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Monthly Summary
    cursor.execute("""
        SELECT strftime('%Y-%m', upload_date) as month, SUM(total_amount) as total
        FROM receipts
        GROUP BY month
        ORDER BY month DESC
    """)
    monthly_stats = cursor.fetchall()
    
    # Highest Item
    cursor.execute("""
        SELECT item_name, price, strftime('%Y-%m', receipts.upload_date) as month
        FROM items
        JOIN receipts ON items.receipt_id = receipts.id
        ORDER BY price DESC
        LIMIT 1
    """)
    highest_item = cursor.fetchone()
    
    # Recent Transactions
    cursor.execute("SELECT * FROM receipts ORDER BY upload_date DESC LIMIT 5")
    recent = cursor.fetchall()
    
    conn.close()
    
    return {
        "monthly": [dict(row) for row in monthly_stats],
        "highest": dict(highest_item) if highest_item else None,
        "recent": [dict(row) for row in recent]
    }