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

    # Convert margin from mm to points (1 mm = 2.83465 pt)
    margin_pts = margin_mm * 2.83465
    a4_width, a4_height = 595, 842  # A4 size in points

    # Apply margin only to top and left
    content_w = a4_width - margin_pts
    content_h = a4_height - margin_pts

    page = input_pdf[0]
    width, height = page.rect.width, page.rect.height

    num_x = int(width / content_w) + (1 if width % content_w > 0 else 0)
    num_y = int(height / content_h) + (1 if height % content_h > 0 else 0)

    output_pdf = fitz.open()

    for y in range(num_y):
        for x in range(num_x):
            # Define crop area from the original page
            clip = fitz.Rect(
                x * content_w, y * content_h,
                (x + 1) * content_w, (y + 1) * content_h
            )

            # Create a new A4 page
            new_page = output_pdf.new_page(width=a4_width, height=a4_height)

            # Draw light gray margin guide lines (top and left)
            new_page.draw_line(
                p1=(0, margin_pts), p2=(a4_width, margin_pts),
                color=(0.8, 0.8, 0.8), width=0.5
            )
            new_page.draw_line(
                p1=(margin_pts, 0), p2=(margin_pts, a4_height),
                color=(0.8, 0.8, 0.8), width=0.5
            )

            # Define destination rectangle inside A4 with only top & left margin
            dest = fitz.Rect(margin_pts, margin_pts, a4_width, a4_height)

            # Place the clipped part into the new page
            new_page.show_pdf_page(dest, input_pdf, 0, clip=clip)

    # Prepare PDF for download
    output_stream = BytesIO()
    output_pdf.save(output_stream)
    output_stream.seek(0)

    return send_file(
        output_stream,
        as_attachment=True,
        download_name="tiled_a4.pdf",
        mimetype="application/pdf"
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
