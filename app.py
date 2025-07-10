from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os
import uuid

try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# simple in-memory database for verifying PO numbers
VALID_POS = {'12345', '98765'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text(path):
    if pytesseract is None:
        return 'OCR engine not installed'
    ext = os.path.splitext(path)[1].lower()
    if ext == '.pdf':
        if convert_from_path is None:
            return 'PDF support not installed'
        images = convert_from_path(path, first_page=1, last_page=1)
        image = images[0]
    else:
        image = Image.open(path)
    text = pytesseract.image_to_string(image)
    return text

def verify_po(text):
    # very naive PO extraction and validation
    for line in text.splitlines():
        if line.lower().startswith('po'):
            parts = line.split(':')
            if len(parts) > 1:
                po = parts[1].strip()
                return po in VALID_POS
    return False

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        files = request.files.getlist('files')
        results = []
        for f in files:
            if f and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                unique_name = str(uuid.uuid4()) + '_' + filename
                path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
                f.save(path)
                text = extract_text(path)
                results.append({'file': unique_name, 'text': text})
        return render_template('edit.html', results=results)
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    entries = []
    for key in request.form:
        if key.startswith('text_'):
            idx = key.split('_')[1]
            text = request.form[key]
            valid = verify_po(text)
            # simulate sending to Oracle and getting SO number
            so_number = 'SO-' + str(uuid.uuid4())[:8]
            entries.append({'text': text, 'valid': valid, 'so': so_number})
    return render_template('success.html', entries=entries)

if __name__ == '__main__':
    app.run(debug=True)
