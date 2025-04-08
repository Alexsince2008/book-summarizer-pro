from app import db
from datetime import datetime

class Summary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255))
    pdf_text = db.Column(db.Text)  # Store the PDF text in the database
    short_summary = db.Column(db.Text)
    brief_summary = db.Column(db.Text)
    detailed_summary = db.Column(db.Text)
    page_count = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Summary {self.filename}>'
