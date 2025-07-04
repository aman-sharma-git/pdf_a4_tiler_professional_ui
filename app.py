from flask import Flask, render_template, request, send_file
import fitz  # PyMuPDF
import os
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_pdf():
    margin_mm = float(request.form['margin'])
    file = request.files['pdf_file']
    
    if not file:
        return "No file uploaded", 400

    filename = secure_filename(file.filename)
    input_pdf = fitz.open(stream=file.read(), filetype="pdf")

    if input_pdf.page_count != 1:
        return "Only 1-page PDF supported", 400

    margin_pts = margin_mm * 2.83465
    a4_width, a4_height = 595, 842
    content_w = a4_width - 2 * margin_pts
    content_h = a4_height - 2 * margin_pts
    page = input_pdf[0]
    width, height = page.rect.width, page.rect.height

    num_x = int(width / content_w) + (1 if width % content_w > 0 else 0)
    num_y = int(height / content_h) + (1 if height % content_h > 0 else 0)

    output_pdf = fitz.open()
    for y in range(num_y):
        for x in range(num_x):
            clip = fitz.Rect(x * content_w, y * content_h,
                             (x + 1) * content_w, (y + 1) * content_h)
            new_page = output_pdf.new_page(width=a4_width, height=a4_height)
            dest = fitz.Rect(margin_pts, margin_pts,
                             a4_width - margin_pts, a4_height - margin_pts)
            new_page.show_pdf_page(dest, input_pdf, 0, clip=clip)

    output_stream = BytesIO()
    output_pdf.save(output_stream)
    output_stream.seek(0)
    return send_file(output_stream, as_attachment=True,
                     download_name="tiled_a4.pdf", mimetype="application/pdf")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Default fallback port
    app.run(host='0.0.0.0', port=port)
