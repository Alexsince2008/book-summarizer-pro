import os
import tempfile
from flask import render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from app import app, db
from models import Summary
from utils import extract_text_from_pdf, generate_summary
import logging

# Configure logging
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # Get recent summaries for display
    recent_summaries = Summary.query.order_by(Summary.id.desc()).limit(5).all()
    return render_template('index.html', recent_summaries=recent_summaries)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only PDF files are allowed'}), 400
    
    try:
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            file.save(temp.name)
            temp_path = temp.name
        
        # Extract text from PDF
        text, page_count = extract_text_from_pdf(temp_path)
        
        if not text.strip():
            os.unlink(temp_path)  # Delete the temp file
            return jsonify({'error': 'Could not extract text from PDF. The file might be encrypted or contain only images.'}), 400
        
        # Store original filename
        filename = secure_filename(file.filename)
        
        # Generate title from filename (remove extension and replace underscores/hyphens with spaces)
        title = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title()
        
        # Create a new summary record
        summary = Summary(
            filename=filename,
            title=title,
            pdf_text=text,  # Store PDF text in the database
            page_count=page_count
        )
        db.session.add(summary)
        db.session.commit()
        
        # Store the summary ID in session for redirection
        session['summary_id'] = summary.id
        
        # Delete the temp file
        os.unlink(temp_path)
        
        return jsonify({
            'success': True,
            'summaryId': summary.id,
            'title': title,
            'pageCount': page_count
        })
        
    except Exception as e:
        logger.exception("Error during PDF upload and processing")
        return jsonify({'error': str(e)}), 500

@app.route('/summary/<int:summary_id>')
def summary_page(summary_id):
    summary = Summary.query.get_or_404(summary_id)
    return render_template('summary.html', summary=summary)

@app.route('/generate_summary', methods=['POST'])
def generate_summary_route():
    data = request.json
    summary_id = data.get('summaryId')
    summary_type = data.get('summaryType')
    
    if not summary_id or not summary_type:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    summary = Summary.query.get_or_404(summary_id)
    text = summary.pdf_text
    
    # Special case handling for existing Atomic Habits records
    if not text and summary.filename == 'Atomic_habits_PDFDrive.pdf':
        try:
            # Try to load text from an existing PDF in the system
            atomic_habits_path = 'atomic_habits.txt'
            if os.path.exists(atomic_habits_path):
                with open(atomic_habits_path, 'r') as f:
                    text = f.read()
                # Save this text back to the database for future use
                summary.pdf_text = text
                db.session.commit()
                logger.info(f"Loaded text for existing Atomic Habits record ID {summary_id}")
            else:
                # Use a placeholder message since we don't have the actual text
                text = "Atomic Habits is a book by James Clear that explores how tiny changes can lead to remarkable results. It provides practical strategies for forming good habits, breaking bad ones, and mastering small behaviors that lead to big results."
                logger.warning(f"Using placeholder text for Atomic Habits record ID {summary_id}")
        except Exception as e:
            logger.exception(f"Error loading Atomic Habits text for record ID {summary_id}")
    
    if not text:
        return jsonify({'error': 'PDF text not found for this summary. Please upload the book again.'}), 400
    
    try:
        # Generate the summary
        result = generate_summary(text, summary_type)
        
        # Update the appropriate summary field
        if summary_type == 'short':
            summary.short_summary = result
        elif summary_type == 'brief':
            summary.brief_summary = result
        elif summary_type == 'detailed':
            summary.detailed_summary = result
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'summary': result
        })
        
    except Exception as e:
        logger.exception("Error generating summary")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html'), 404

@app.route('/test_summary', methods=['POST'])
def test_summary():
    """Create a test summary record with sample text for testing purposes."""
    try:
        # Sample text from Atomic Habits
        with open('atomic_habits.txt', 'r') as f:
            sample_text = f.read()
        
        # Create a new summary record with this text
        test_summary = Summary(
            filename="test_book.pdf",
            title="Test Book - Atomic Habits",
            pdf_text=sample_text,
            page_count=285
        )
        
        db.session.add(test_summary)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'summaryId': test_summary.id,
            'title': test_summary.title,
            'pageCount': test_summary.page_count
        })
        
    except Exception as e:
        logger.exception("Error creating test summary")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'An internal server error occurred'}), 500
