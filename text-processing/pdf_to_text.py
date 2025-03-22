import pdfplumber
from kafka import KafkaProducer
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
import logging
from kafka.errors import NoBrokersAvailable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFProcessor:

    def __init__(self, bootstrap_servers=None, temp_file_path='temp.pdf'):
        
        if bootstrap_servers is None:
            bootstrap_servers = ['kafka1:9092', 'kafka2:9093', 'kafka3:9094']
            
        self.bootstrap_servers = bootstrap_servers
        self.temp_file_path = temp_file_path
        self.producer = None


    def create_kafka_producer(self, retries=5):
        for attempt in range(retries):
            try:
                return KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    acks='all',  # Wait for all replicas
                    retries=3,
                    max_in_flight_requests_per_connection=1
                )
            except NoBrokersAvailable:
                if attempt < retries - 1:
                    logger.warning(f"Failed to connect to Kafka. Retrying in 5 seconds... (Attempt {attempt + 1}/{retries})")
                    time.sleep(5)
                else:
                    raise
    
    # Connect to Kafka by creating a producer
    def connect(self):
        if self.producer is None:
            logger.info("Connecting to Kafka...")
            self.producer = self.create_kafka_producer()
            logger.info("Connected to Kafka successfully")

    # Disconnect from Kafka
    def disconnect(self):
        if self.producer:
            logger.info("Disconnecting from Kafka...")
            try:
                self.producer.flush()
                self.producer.close()
                logger.info("Disconnected from Kafka")
            except Exception as e:
                logger.error(f"Error closing Kafka producer: {e}")
            finally:
                self.producer = None

    # Extract text from a PDF file
    def pdf_to_text(self, pdf_path):
        with pdfplumber.open(pdf_path) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text()
        return text
    
    # Send extracted text to Kafka for analysis
    def send_text_to_analysis(self, message):
        if self.producer is None:
            self.connect()
            
        # Restructure message to match expected format
        analysis_message = {
            'source': 'cv',
            'userId': message['userId'],
            'cvContent': message['text']
        }

        logger.info(f"Sending text to analysis for user: {message['userId']}")
        self.producer.send('analysis', value=analysis_message)
        self.producer.flush()
        logger.info("Text sent to analysis")

    # Process an uploaded file
    def process_upload(self, file, user_id):
        if file.filename == '':
            return {"error": "No selected file"}, 400
            
        # Save the file temporarily
        file.save(self.temp_file_path)

        try:
            # Extract text from PDF
            text = self.pdf_to_text(self.temp_file_path)
            
            # Send to Kafka for analysis
            message = {
                'userId': user_id,
                'text': text
            }
            self.send_text_to_analysis(message)
            
            # Clean up
            if os.path.exists(self.temp_file_path):
                os.remove(self.temp_file_path)
                
            return {'text': text}, 200
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            # Clean up on error
            if os.path.exists(self.temp_file_path):
                os.remove(self.temp_file_path)
            return {"error": f"Error extracting text: {str(e)}"}, 500
        
app = Flask(__name__)
CORS(app)

pdf_processor = PDFProcessor()

@app.route('/extract-text', methods=['POST'])
def extract_text():
    """Flask route to handle PDF uploads and text extraction"""
    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    # Check if user ID was provided
    user_id = request.form.get('userId')
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    
    # Process the uploaded file
    file = request.files['file']
    result, status_code = pdf_processor.process_upload(file, user_id)
    
    return jsonify(result), status_code

if __name__ == '__main__':
    # Connect to Kafka before starting the server
    try:
        pdf_processor.connect()
        app.run(host='0.0.0.0', debug=True, port=5000)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
    finally:
        pdf_processor.disconnect()

# Initialize Kafka producers with retry mechanism
# producerText = create_kafka_producer()

# def pdf_to_text(pdf_path):
#     with pdfplumber.open(pdf_path) as pdf:
#         text = ''
#         for page in pdf.pages:
#             text += page.extract_text()
#     return text

# @app.route('/extract-text', methods=['POST'])
# def extract_text():
#     if 'file' not in request.files:
#         return jsonify({"error": "No file uploaded"}), 400
    
#     user_id = request.form.get('userId')
#     if not user_id:
#         return jsonify({"error": "User ID required"}), 400
    
#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({"error": "No selected file"}), 400
    
#     temp_path = 'temp.pdf'
#     file.save(temp_path)

#     try:
#         text = pdf_to_text(temp_path)
#         message = {
#             'userId': user_id,
#             'text': text
#         }
#         send_text_to_analysis(message)
#         os.remove(temp_path)  # Clean up temp file
#         return jsonify({'text': text})
#     except Exception as e:
#         if os.path.exists(temp_path):
#             os.remove(temp_path)
#         return jsonify({"error": f"Error extracting text: {e}"}), 500
    
# def send_text_to_analysis(message):
#     # Restructure message to match job format but with CV identifier
#     analysis_message = {
#         'source': 'cv',
#         'userId': message['userId'],  # Keep userId as is
#         'cvContent': message['text']  # Rename text to cvContent
#     }

#     print(f"Sending text to analysis: {analysis_message}")
#     producerText.send('analysis', value=analysis_message)
#     producerText.flush()
#     print("Text sent to analysis")

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', debug=True, port=5000)
