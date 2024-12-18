import pdfplumber
from kafka import KafkaProducer
import json
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

producerText = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def pdf_to_text(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()
    return text

@app.route('/extract-text', methods=['POST'])
def extract_text():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    user_id = request.form.get('userId')
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    temp_path = 'temp.pdf'
    file.save(temp_path)

    try:
        text = pdf_to_text(temp_path)
        message = {
            'userId': user_id,
            'text': text
        }
        send_text_to_analysis(message)
        os.remove(temp_path)  # Clean up temp file
        return jsonify({'text': text})
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"error": f"Error extracting text: {e}"}), 500
    
def send_text_to_analysis(message):
    # Restructure message to match job format but with CV identifier
    analysis_message = {
        'jobId': f"cv_{message['userId']}", # Prefix with cv_ to differentiate
        'jobDescription': message['text'],
        'source': 'cv'
    }
    producerText.send('analysis', value=analysis_message)
    producerText.flush()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
