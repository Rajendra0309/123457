# app.py
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
import os
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from magic import Magic  # for file type detection

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

def get_file_extension(filename):
    return os.path.splitext(filename)[1][1:].lower()

def detect_language(content, filename):
    try:
        # First try to guess based on file extension
        ext = get_file_extension(filename)
        if ext:
            try:
                return get_lexer_by_name(ext)
            except:
                pass
        
        # If that fails, try to guess based on content
        return guess_lexer(content)
    except:
        # Default to plain text if we can't detect the language
        return get_lexer_by_name('text')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400

    try:
        # Read file content
        content = file.read().decode('utf-8')
        
        # Detect language and highlight code
        lexer = detect_language(content, file.filename)
        formatter = HtmlFormatter(style='monokai', cssclass='highlight')
        highlighted_code = highlight(content, lexer, formatter)
        
        # Get CSS for syntax highlighting
        css = formatter.get_style_defs('.highlight')
        
        return jsonify({
            'status': 'success',
            'filename': file.filename,
            'content': content,
            'highlighted_code': highlighted_code,
            'css': css,
            'language': lexer.name
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error processing file: {str(e)}'
        }), 500

@app.route('/get_response', methods=['POST'])
def get_response():
    try:
        user_message = request.json['message']
        
        # Generate response from Gemini
        response = model.generate_content(
            f"You are a coding assistant. Please help with this query: {user_message}"
        )
        
        return jsonify({
            'status': 'success',
            'response': response.text
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)