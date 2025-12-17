from . import db
from datetime import datetime

class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, default=0.0)
    merchant_name = db.Column(db.String(100), nullable=True)
    
    # Relationship to items
    items = db.relationship('Item', backref='receipt', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'date': self.upload_date.strftime('%Y-%m-%d %H:%M'),
            'total_amount': self.total_amount,
            'merchant': self.merchant_name,
            'items': [item.to_dict() for item in self.items]
        }

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey('receipt.id'), nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, default=0.0)
    subtotal = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            'product_name': self.product_name,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'subtotal': self.subtotal
        }