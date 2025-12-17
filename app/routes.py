import os
import uuid
import pandas as pd
from flask import Blueprint, request, jsonify, send_file, current_app, render_template
from werkzeug.utils import secure_filename
from .models import db, Receipt, Item
from .services.ocr_engine import process_image
from .services.parser import parse_receipt_text
from sqlalchemy import func, desc
from datetime import datetime

bp = Blueprint('main', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

@bp.route('/')
def index():
    # FIX: Use render_template instead of send_static_file
    return render_template('index.html')

@bp.route('/api/upload', methods=['POST'])
def upload_receipt():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file format. Use JPG or PNG."}), 400

    # Securely save the file
    filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)

    # 1. OCR Processing
    raw_text_lines = process_image(save_path)
    
    # 2. Text Parsing
    items_data, total_amt = parse_receipt_text(raw_text_lines)

    # 3. Database Storage
    new_receipt = Receipt(filename=filename, total_amount=total_amt)
    db.session.add(new_receipt)
    db.session.flush() # Flush to generate the Receipt ID

    for item in items_data:
        db_item = Item(
            receipt_id=new_receipt.id,
            product_name=item['name'],
            quantity=item['qty'],
            unit_price=item['unit_price'],
            subtotal=item['subtotal']
        )
        db.session.add(db_item)
    
    db.session.commit()

    return jsonify({"message": "Success", "receipt": new_receipt.to_dict()}), 201

@bp.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    current_month = datetime.now().strftime('%Y-%m')
    
    # Analytics Queries
    monthly_total = db.session.query(func.sum(Receipt.total_amount))\
        .filter(func.strftime('%Y-%m', Receipt.upload_date) == current_month).scalar() or 0

    highest_item = Item.query.order_by(desc(Item.unit_price)).first()
    highest_item_dict = highest_item.to_dict() if highest_item else None

    recents = Receipt.query.order_by(desc(Receipt.upload_date)).limit(5).all()

    return jsonify({
        "monthly_total": monthly_total,
        "highest_item": highest_item_dict,
        "recent_receipts": [r.to_dict() for r in recents]
    })

@bp.route('/api/export', methods=['GET'])
def export_csv():
    query = db.session.query(
        Receipt.upload_date, 
        Receipt.filename, 
        Item.product_name, 
        Item.subtotal
    ).join(Item).all()

    data = [{
        "Date": r[0], 
        "File": r[1], 
        "Item": r[2], 
        "Price (IDR)": r[3]
    } for r in query]

    df = pd.DataFrame(data)
    csv_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'report.csv')
    df.to_csv(csv_path, index=False)

    return send_file(csv_path, as_attachment=True, download_name='monthly_expense_report.csv')