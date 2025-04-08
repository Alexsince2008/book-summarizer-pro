import os
import PyPDF2
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

# Configure the Google Generative AI API
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    logger.warning("GOOGLE_API_KEY not set. Summarization will not work.")

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file."""
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            page_count = len(pdf_reader.pages)
            
            # Extract text from each page
            for page_num in range(page_count):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n\n"
                
        return text, page_count
    except Exception as e:
        logger.exception("Error extracting text from PDF")
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

def generate_summary(text, summary_type):
    """Generate a summary of the provided text using Google's Generative AI."""
    if not GOOGLE_API_KEY:
        return "API key not configured. Please set the GOOGLE_API_KEY environment variable."
    
    try:
        # Limit text length if needed (API may have limits)
        max_length = 30000  # Characters
        if len(text) > max_length:
            text = text[:max_length] + "... (text truncated)"
        
        # Configure the prompt based on summary type
        prompts = {
            'short': "Create a very concise summary of this book in about 100-150 words. Focus only on the most important points:",
            'brief': "Create a brief summary of this book in about 300-400 words. Include the main themes and key points:",
            'detailed': "Create a detailed summary of this book in about 800-1000 words. Include all major themes, key events, and conclusions:"
        }
        
        prompt = prompts.get(summary_type, prompts['brief'])
        full_prompt = f"{prompt}\n\n{text}"
        
        # Generate the summary using Gemini
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(full_prompt)
        
        return response.text
    except Exception as e:
        logger.exception("Error generating summary with GenAI")
        raise Exception(f"Failed to generate summary: {str(e)}")
