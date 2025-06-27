from flask import Flask, request, jsonify
from google.cloud import vision
import os

app = Flask(__name__)

@app.route('/api/ocr', methods=['POST'])
def ocr():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    content = file.read()

    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if not texts:
        return jsonify({'text': ''})

    extracted_text = texts[0].description
    return jsonify({'text': extracted_text})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)