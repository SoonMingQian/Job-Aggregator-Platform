import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import uuid
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Patch the required dependencies
mock_kafka_producer = MagicMock()
mock_redis_client = MagicMock()

# Apply the patches
kafka_patch = patch('kafka.KafkaProducer', return_value=mock_kafka_producer)
redis_patch = patch('redis.Redis', return_value=mock_redis_client)
logger_patch = patch('app.logger')

# Start the patches
kafka_patch.start()
redis_patch.start()
logger_patch.start()

# Now import the app (AFTER patching)
from app import IrishJobsScraper, app

class TestIrishJobsScraper(unittest.TestCase):

    def setUp(self):
        # Create fresh mocks for each test
        self.mock_kafka_producer = MagicMock()
        self.mock_redis_client = MagicMock()
        
        # Set up patch context managers for this test
        self.kafka_patcher = patch('kafka.KafkaProducer', return_value=self.mock_kafka_producer)
        self.redis_patcher = patch('redis.Redis', return_value=self.mock_redis_client)
        self.logger_patcher = patch('app.logger')
        
        # Start the patchers for this test
        self.kafka_mock = self.kafka_patcher.start()
        self.redis_mock = self.redis_patcher.start()
        self.logger_mock = self.logger_patcher.start()
        
        # Now we can safely create a scraper instance
        self.scraper = IrishJobsScraper()
        # Replace the scraper's Redis client with our mock
        self.scraper.redis_client = self.mock_redis_client
        # Replace Kafka producers with mocks
        self.scraper.producer_analysis = self.mock_kafka_producer
        self.scraper.producer_storage = self.mock_kafka_producer
        self.scraper.producer_matching = self.mock_kafka_producer
    
    def tearDown(self):
        # Stop all patches after the test
        self.kafka_patcher.stop()
        self.redis_patcher.stop()
        self.logger_patcher.stop()
    
    def test_init(self):
        self.assertEqual(self.scraper.MAX_JOBS, 100)
        self.assertEqual(self.scraper.base_url, "https://www.irishjobs.ie")
        self.assertIsInstance(self.scraper.processed_urls, set)
        self.assertEqual(len(self.scraper.processed_urls), 0)
    
    def test_generate_job_id(self):
        job_data = {
            'company': 'Test Company',
            'title': 'Software Engineer',
            'location': 'Dublin',
            'posted_date': '2023-01-01'
        }

        id1 = self.scraper.generate_job_id(job_data)
        id2 = self.scraper.generate_job_id(job_data)

        self.assertTrue(id1.startswith('job:'))
        self.assertEqual(id1, id2, "Job IDs should be deterministic")

        # Verify UUID is valid
        uuid_part = id1[4:]  # Remove 'job:' prefix
        try:
            uuid_obj = uuid.UUID(uuid_part)
            self.assertEqual(str(uuid_obj), uuid_part)
        except ValueError:
            self.fail("Job ID does not contain a valid UUID")

        # Test with different data
        different_data = job_data.copy()
        different_data['company'] = 'Another Company'
        different_id = self.scraper.generate_job_id(different_data)
        self.assertNotEqual(id1, different_id)

    def test_generate_cache_key(self):
        # Test with regular input
        result = self.scraper.generate_cache_key("Software Engineer", "Dublin")
        self.assertEqual(result, "search:software engineer:dublin:irishJobs")
        
        # Test with uppercase input
        result = self.scraper.generate_cache_key("SOFTWARE ENGINEER", "DUBLIN")
        self.assertEqual(result, "search:software engineer:dublin:irishJobs")
        
        # Test with mixed case and spaces
        result = self.scraper.generate_cache_key("  Data   Scientist  ", " Remote ")
        self.assertEqual(result, "search:  data   scientist  : remote :irishJobs")

    def test_get_cached_results_no_user_id(self):
        # Configure mock to return job keys
        self.mock_redis_client.smembers.return_value = ["job:123", "job:456"]
        
        # Configure mock to return job data for each key
        self.mock_redis_client.hgetall.side_effect = [
            {"jobId": "job:123", "title": "Developer", "company": "Tech Co"},
            {"jobId": "job:456", "title": "Engineer", "company": "Software Inc"}
        ]

        results = self.scraper.get_cached_results("developer", "dublin", None)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["jobId"], "job:123")
        self.assertEqual(results[1]["company"], "Software Inc")

        self.mock_redis_client.smembers.assert_called_once_with("search:developer:dublin:irishJobs")
        self.assertEqual(self.mock_redis_client.hgetall.call_count, 2)
    
    def test_get_cached_results_with_user_id_and_match(self):
        # Configure mock to return job keys
        self.mock_redis_client.smembers.return_value = ["job:123"]
        
        # Configure mock to return job data
        self.mock_redis_client.hgetall.return_value = {
            "jobId": "job:123", 
            "title": "Developer", 
            "company": "Tech Co"
        }

        # Configure mock to return match score
        self.mock_redis_client.hget.return_value = "0.85"

        results = self.scraper.get_cached_results("developer", "dublin", "user123")

        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["jobId"], "job:123")
        self.assertEqual(results[0]["matchScore"], 0.85)

        # Verify Redis calls
        self.mock_redis_client.hget.assert_called_with("match:user123", "job:123")

    def test_get_cached_result_with_user_id_no_match(self):
        self.mock_redis_client.smembers.return_value = ["job:789"]

        # Configure mock to return job data
        self.mock_redis_client.hgetall.return_value = {
            "jobId": "job:789", 
            "title": "DevOps", 
            "company": "Cloud Co"
        }

        # Configure mock to return None for match score
        self.mock_redis_client.hget.return_value = None
        
        # Call the method
        results = self.scraper.get_cached_results("devops", "remote", "user456")

        # Verify results
        self.assertEqual(len(results), 1)
        self.assertNotIn("matchScore", results[0])
        
        # Verify send to matching topic
        self.mock_kafka_producer.send.assert_called_with(
            'matching', 
            value={'jobId': 'job:789', 'userId': 'user456'}
        )
        self.mock_kafka_producer.flush.assert_called()

    def test_store_job_listing(self):
        job_data = {
            'jobId': 'job:xyz',
            'title': 'Software Engineer',
            'company': 'Test Company',
            'location': 'Dublin',
            'jobDescription': 'This is a job description',
            'applyLink': 'https://irishjobs.ie'
        }

        result = self.scraper.store_job_listing(job_data, "Software Engineer", "Dublin")
        self.assertEqual(result, 'job:xyz')
        
        # Verify Redis calls
        self.mock_redis_client.hmset.assert_called_once_with('job:xyz', job_data)
        self.mock_redis_client.sadd.assert_called_once_with(
            'search:software engineer:dublin:irishJobs', 
            'job:xyz'
        )
        self.assertEqual(self.mock_redis_client.expire.call_count, 2) 
    
    def test_store_job_listing_error(self):
        """Test error handling when storing a job listing"""
        # Configure mock to raise exception
        self.mock_redis_client.hmset.side_effect = Exception("Redis error")
        
        # Test data
        job_data = {
            'jobId': 'job:abc',
            'title': 'Developer',
            'company': 'Error Co'
        }
        
        # Call the method
        result = self.scraper.store_job_listing(job_data, "Developer", "Remote")
        
        # Verify result
        self.assertIsNone(result)
        
        # Verify logger called with error
        self.logger_mock.error.assert_called()

class TestFlaskApp(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Create mock for IrishJobsScraper
        self.mock_scraper = MagicMock()
        
        # Check if 'scraper' exists in the app's global space
        if hasattr(app, 'scraper'):
            # Save the original scraper
            self.original_scraper = app.scraper
            # Replace with our mock
            app.scraper = self.mock_scraper
        else:
            # If scraper doesn't exist as an attribute of app, create it
            self.original_scraper = None
            app.scraper = self.mock_scraper

    def tearDown(self):
        # Restore the original scraper only if it existed
        if self.original_scraper is not None:
            app.scraper = self.original_scraper
        else:
            # Remove the scraper attribute if it didn't exist before
            if hasattr(app, 'scraper'):
                delattr(app, 'scraper')

    @patch('app.IrishJobsScraper.get_cached_results')
    def test_irishjobs_endpoint_cached_results(self, mock_get_cached):
        # Prepare mock cached results
        mock_cached_jobs = [
            {'jobId': 'job:123', 'title': 'Developer', 'company': 'Tech Co'},
            {'jobId': 'job:456', 'title': 'Engineer', 'company': 'Software Inc'}
        ]
        mock_get_cached.return_value = mock_cached_jobs
        
        # Call the endpoint
        response = self.client.get('/irishjobs?title=Developer&job_location=Dublin&userId=user123')
        
        # Parse response
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['source'], 'cache')
        self.assertEqual(len(data['jobs']), 2)

    def test_irishjobs_endpoint_missing_params(self):
        # Call endpoint with missing parameters
        response = self.client.get('/irishjobs?title=Developer')
        
        # Parse response
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], 'Missing required parameters')
if __name__ == '__main__':
    unittest.main()