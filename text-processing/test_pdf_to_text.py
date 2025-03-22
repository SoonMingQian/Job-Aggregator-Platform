import unittest
from unittest.mock import MagicMock, patch
import os
from kafka.errors import NoBrokersAvailable
import pdfplumber
import time

# Import the PDFProcessor class
from pdf_to_text import PDFProcessor

class SimplifiedTest(unittest.TestCase):
    """
    Simplified test suite for PDFProcessor with focused tests
    """
    
    def test_pdf_to_text_direct(self):
        """Test pdf_to_text method with direct mocking approach"""
        # Create test instance
        processor = PDFProcessor()
        
        # Create a custom context manager mock that returns a PDF with pages
        cm_mock = MagicMock()
        pdf_mock = MagicMock()
        pdf_mock.pages = [
            MagicMock(extract_text=lambda: "Page 1"),
            MagicMock(extract_text=lambda: "Page 2")
        ]
        cm_mock.__enter__ = MagicMock(return_value=pdf_mock)
        cm_mock.__exit__ = MagicMock(return_value=None)
        
        # Replace pdfplumber.open with our mock
        original_open = pdfplumber.open
        try:
            pdfplumber.open = MagicMock(return_value=cm_mock)
            
            # Call the method
            result = processor.pdf_to_text('test.pdf')
            
            # Verify
            self.assertEqual(result, "Page 1Page 2")
            pdfplumber.open.assert_called_once_with('test.pdf')
        finally:
            # Restore original function
            pdfplumber.open = original_open
    
    def test_create_kafka_producer_direct(self):
        """Test create_kafka_producer by replacing KafkaProducer directly"""
        # Create test instance
        processor = PDFProcessor(bootstrap_servers=['test:9092'])
        
        # Create a real mock
        from kafka import KafkaProducer
        original_producer = KafkaProducer
        mock_producer = MagicMock()
        
        try:
            # Replace the actual KafkaProducer class
            from kafka import KafkaProducer as KP
            KP.__new__ = MagicMock(return_value=mock_producer)
            
            # Call the method
            result = processor.create_kafka_producer()
            
            # Verify
            self.assertEqual(result, mock_producer)
        finally:
            # Clean up
            from kafka import KafkaProducer as KP
            KP.__new__ = original_producer.__new__
    
    def test_send_text_to_analysis_direct(self):
        """Test send_text_to_analysis method directly"""
        # Create processor with a mock producer
        processor = PDFProcessor()
        processor.producer = MagicMock()
        
        # Call the method
        message = {'userId': 'test123', 'text': 'Test content'}
        processor.send_text_to_analysis(message)
        
        # Verify
        expected = {
            'source': 'cv',
            'userId': 'test123',
            'cvContent': 'Test content'
        }
        processor.producer.send.assert_called_once_with('analysis', value=expected)
        processor.producer.flush.assert_called_once()
    
    def test_process_upload_mocked_methods(self):
        """Test process_upload by mocking its dependent methods"""
        # Create processor and mock its methods
        processor = PDFProcessor()
        processor.pdf_to_text = MagicMock(return_value="Extracted Text")
        processor.send_text_to_analysis = MagicMock()
        
        # Mock file operations
        os.path.exists = MagicMock(return_value=True)
        os.remove = MagicMock()
        
        # Create mock file
        mock_file = MagicMock()
        mock_file.filename = "test.pdf"
        
        # Call the method
        result, status = processor.process_upload(mock_file, 'user123')
        
        # Verify
        self.assertEqual(status, 200)
        self.assertEqual(result['text'], "Extracted Text")
        mock_file.save.assert_called_once_with(processor.temp_file_path)
        processor.pdf_to_text.assert_called_once_with(processor.temp_file_path)
        processor.send_text_to_analysis.assert_called_once()
        os.remove.assert_called_once_with(processor.temp_file_path)
        
        # Restore originals
        import builtins
        builtins.__import__('os').path.exists = os.path.exists
        builtins.__import__('os').remove = os.remove

if __name__ == '__main__':
    unittest.main()