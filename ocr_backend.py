from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import vision
import os
import mimetypes
import base64

app = Flask(__name__)
CORS(app)

@app.route('/api/ocr', methods=['POST'])
def ocr():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    content = file.read()
    filename = file.filename
    mime_type, _ = mimetypes.guess_type(filename)

    client = vision.ImageAnnotatorClient()

    # Check if the file is a PDF
    if mime_type == 'application/pdf' or filename.lower().endswith('.pdf'):
        # For PDFs, use DOCUMENT_TEXT_DETECTION
        encoded_pdf = base64.b64encode(content).decode('utf-8')
        requests = [
            {
                "input_config": {
                    "content": encoded_pdf,
                    "mime_type": "application/pdf"
                },
                "features": [{"type": vision.Feature.Type.DOCUMENT_TEXT_DETECTION}]
            }
        ]
        response = client.batch_annotate_files(requests=requests)
        # Extract text from the response
        text = ""
        for resp in response.responses:
            for annotation in resp.responses:
                if annotation.full_text_annotation.text:
                    text += annotation.full_text_annotation.text
        return jsonify({'text': text})
    else:
        # For images, use TEXT_DETECTION
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        texts = response.text_annotations
        if not texts:
            return jsonify({'text': ''})
        extracted_text = texts[0].description
        return jsonify({'text': extracted_text})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
