import pytest
from unittest.mock import patch, MagicMock, call
import threading
from analysis import SkillsExtractor

class TestSkillsExtractor:
    
    def setup_method(self):
        """Set up a fresh instance for each test"""
        self.extractor = SkillsExtractor(
            bootstrap_servers=['localhost:9092'],  # Use test servers
            consumer_group='test-group'
        )
    
    #--------------------------------------------------------------------------
    # Test 1: extract_skills - Core Functionality
    #--------------------------------------------------------------------------
    def test_extract_skills_basic(self):
        """Test basic skill extraction functionality"""
        # Patch the NLP components
        with patch.object(self.extractor, '_load_models') as mock_load:
            # Set up mocks for NLP pipeline
            self.extractor._token_skill_classifier = MagicMock()
            self.extractor._token_knowledge_classifier = MagicMock()
            self.extractor._tokenizer = MagicMock()
            
            # Configure mock responses
            self.extractor._tokenizer.return_value = {"input_ids": [[1, 2, 3]]}
            self.extractor._tokenizer.decode.return_value = "test text"
            
            self.extractor._token_skill_classifier.return_value = [
                {"entity_group": "SKILL", "word": "Python"},
                {"entity_group": "SKILL", "word": "SQL"}
            ]
            
            self.extractor._token_knowledge_classifier.return_value = [
                {"entity_group": "KNOWLEDGE", "word": "Machine Learning"}
            ]
            
            # Call the function
            result = self.extractor.extract_skills("Sample text with skills")
            
            # Check results
            assert result == {"Python", "SQL", "Machine Learning"}
            mock_load.assert_called_once()
    
    def test_extract_skills_empty_text(self):
        """Test handling of empty text"""
        with patch.object(self.extractor, '_load_models'):
            self.extractor._token_skill_classifier = MagicMock(return_value=[])
            self.extractor._token_knowledge_classifier = MagicMock(return_value=[])
            self.extractor._tokenizer = MagicMock()
            self.extractor._tokenizer.return_value = {"input_ids": [[]]}
            self.extractor._tokenizer.decode.return_value = ""
            
            result = self.extractor.extract_skills("")
            
            assert result == set()
    
    def test_extract_skills_error_handling(self):
        """Test error handling during skill extraction"""
        with patch.object(self.extractor, '_load_models'):
            self.extractor._tokenizer = MagicMock()
            self.extractor._tokenizer.side_effect = Exception("Tokenizer error")
            
            # Should return empty set on error rather than crashing
            result = self.extractor.extract_skills("Sample text")
            assert result == set()
    
    #--------------------------------------------------------------------------
    # Test 2: process_cv_message - Process CV Messages
    #--------------------------------------------------------------------------
    def test_process_cv_message(self):
        """Test CV message processing"""
        # Mock extract_skills to return known skills
        with patch.object(self.extractor, 'extract_skills', return_value={"Python", "SQL"}) as mock_extract:
            # Create test message
            message = {
                'userId': 'user123',
                'cvContent': 'Sample CV mentioning Python and SQL'
            }
            
            # Process the message
            result = self.extractor.process_cv_message(message)
            
            # Verify results
            assert result['source'] == 'cv'
            assert result['userId'] == 'user123'
            assert set(result['skills']) == {"Python", "SQL"}
            
            # Verify extract_skills called correctly
            mock_extract.assert_called_once_with('Sample CV mentioning Python and SQL')
    
    #--------------------------------------------------------------------------
    # Test 3: process_job_message - Process Job Messages
    #--------------------------------------------------------------------------
    def test_process_job_message(self):
        """Test job message processing"""
        # Mock extract_skills to return known skills
        with patch.object(self.extractor, 'extract_skills', return_value={"JavaScript", "React"}) as mock_extract:
            # Create test message
            message = {
                'jobId': 'job456',
                'userId': 'user123',
                'jobDescription': 'Job requiring JavaScript and React'
            }
            
            # Process the message
            skills_message, matching_message = self.extractor.process_job_message(message)
            
            # Verify skills message
            assert skills_message['source'] == 'job'
            assert skills_message['jobId'] == 'job456'
            assert set(skills_message['skills']) == {"JavaScript", "React"}
            
            # Verify matching message
            assert matching_message['jobId'] == 'job456'
            assert matching_message['userId'] == 'user123'
            
            # Verify extract_skills called correctly
            mock_extract.assert_called_once_with('Job requiring JavaScript and React')
    
    #--------------------------------------------------------------------------
    # Test 4: connect and disconnect - Kafka Connection Management
    #--------------------------------------------------------------------------
    def test_connect_disconnect(self):
        """Test connection and disconnection functionality"""
        # Mock Kafka client creation
        with patch.object(self.extractor, 'create_kafka_consumer') as mock_create_consumer:
            with patch.object(self.extractor, 'create_kafka_producer') as mock_create_producer:
                # Set mock returns
                mock_consumer = MagicMock()
                mock_producer = MagicMock()
                mock_create_consumer.return_value = mock_consumer
                mock_create_producer.return_value = mock_producer
                
                # Test connect
                self.extractor.connect()
                
                # Verify connections
                assert self.extractor.consumer == mock_consumer
                assert self.extractor.producer == mock_producer
                mock_create_consumer.assert_called_once()
                mock_create_producer.assert_called_once()
                
                # Test disconnect
                self.extractor.disconnect()
                
                # Verify disconnections
                mock_consumer.close.assert_called_once()
                mock_producer.flush.assert_called_once()
                mock_producer.close.assert_called_once()
    
    #--------------------------------------------------------------------------
    # Test 5: start_analysis - Main Processing Loop
    #--------------------------------------------------------------------------
    def test_start_analysis_cv_message(self):
        """Test main processing loop with CV message"""
        # Create mock objects
        mock_consumer = MagicMock()
        mock_producer = MagicMock()
        mock_message = MagicMock()
        
        # Set message value
        mock_message.value = {
            'source': 'cv',
            'userId': 'user789',
            'cvContent': 'I know Python and JavaScript'
        }
        
        # Set up the test to exit after one poll
        processed_messages = 0
        
        # Custom side effect to exit after one message
        def poll_side_effect(*args, **kwargs):
            nonlocal processed_messages
            if processed_messages == 0:
                processed_messages += 1
                return {('analysis', 0): [mock_message]}
            else:
                return {}  # Return empty batch after first message
        
        mock_consumer.poll.side_effect = poll_side_effect
        
        # Mock connect to use our mocks
        with patch.object(self.extractor, 'connect') as mock_connect:
            self.extractor.consumer = mock_consumer
            self.extractor.producer = mock_producer
            
            # Mock CV processing
            with patch.object(self.extractor, 'process_cv_message') as mock_process_cv:
                mock_process_cv.return_value = {
                    'source': 'cv',
                    'userId': 'user789',
                    'skills': ['Python', 'JavaScript']
                }
                
                # Use a thread with timeout to run the analysis without blocking
                def run_with_timeout():
                    thread = threading.Thread(target=self.extractor.start_analysis)
                    thread.daemon = True
                    thread.start()
                    thread.join(timeout=1.0)  # Wait for 1 second max
                    
                # Run the function
                run_with_timeout()
                
                # Verify processing
                mock_connect.assert_called_once()
                mock_process_cv.assert_called_once_with(mock_message.value)
                
                # Verify message sent
                mock_producer.send.assert_called_once_with('skill', value={
                    'source': 'cv',
                    'userId': 'user789',
                    'skills': ['Python', 'JavaScript']
                })
                mock_producer.flush.assert_called()
    
    def test_start_analysis_job_message(self):
        """Test main processing loop with job message"""
        # Create mock objects
        mock_consumer = MagicMock()
        mock_producer = MagicMock()
        mock_message = MagicMock()
        
        # Set message value (job message has no 'source' field)
        mock_message.value = {
            'jobId': 'job456',
            'userId': 'user123',
            'jobDescription': 'Need React developer'
        }
        
        # Set up the test to exit after one poll
        processed_messages = 0
        
        # Custom side effect to exit after one message
        def poll_side_effect(*args, **kwargs):
            nonlocal processed_messages
            if processed_messages == 0:
                processed_messages += 1
                return {('analysis', 0): [mock_message]}
            else:
                return {}  # Return empty batch after first message
        
        mock_consumer.poll.side_effect = poll_side_effect
        
        # Mock connect to use our mocks
        with patch.object(self.extractor, 'connect') as mock_connect:
            self.extractor.consumer = mock_consumer
            self.extractor.producer = mock_producer
            
            # Mock job processing
            with patch.object(self.extractor, 'process_job_message') as mock_process_job:
                mock_process_job.return_value = (
                    {
                        'source': 'job',
                        'jobId': 'job456',
                        'skills': ['React']
                    },
                    {
                        'jobId': 'job456',
                        'userId': 'user123'
                    }
                )
                
                # Use a thread with timeout to run the analysis without blocking
                def run_with_timeout():
                    thread = threading.Thread(target=self.extractor.start_analysis)
                    thread.daemon = True
                    thread.start()
                    thread.join(timeout=1.0)  # Wait for 1 second max
                
                # Run the function
                run_with_timeout()
                
                # Verify processing
                mock_connect.assert_called_once()
                mock_process_job.assert_called_once_with(mock_message.value)
                
                # Verify messages sent (check both messages)
                skill_call = call('skill', value={
                    'source': 'job',
                    'jobId': 'job456',
                    'skills': ['React']
                })
                matching_call = call('matching', value={
                    'jobId': 'job456',
                    'userId': 'user123'
                })
                mock_producer.send.assert_has_calls([skill_call, matching_call], any_order=False)
                mock_producer.flush.assert_called()
    def test_start_analysis_error_handling(self):
        """Test error handling in main loop"""
        # Create mock objects
        mock_consumer = MagicMock()
        mock_producer = MagicMock()
        mock_message = MagicMock()
        
        # Set message value that will cause an error
        mock_message.value = {
            'source': 'cv',
            # Missing required field 'cvContent' will cause error
            'userId': 'user789'
        }
        
        # Set up the test to exit after one poll
        processed_messages = 0
        
        # Custom side effect to exit after one message
        def poll_side_effect(*args, **kwargs):
            nonlocal processed_messages
            if processed_messages == 0:
                processed_messages += 1
                return {('analysis', 0): [mock_message]}
            else:
                return {}  # Return empty batch after first message
        
        mock_consumer.poll.side_effect = poll_side_effect
        
        # Mock connect to use our mocks
        with patch.object(self.extractor, 'connect') as mock_connect:
            self.extractor.consumer = mock_consumer
            self.extractor.producer = mock_producer
            
            # Mock CV processing to raise exception
            with patch.object(self.extractor, 'process_cv_message', 
                            side_effect=Exception("Missing cvContent field")) as mock_process_cv:
                
                # Use a thread with timeout to run the analysis without blocking
                def run_with_timeout():
                    thread = threading.Thread(target=self.extractor.start_analysis)
                    thread.daemon = True
                    thread.start()
                    thread.join(timeout=1.0)  # Wait for 1 second max
                
                # Run the function
                run_with_timeout()
                
                # Verify processing was attempted
                mock_connect.assert_called_once()
                mock_process_cv.assert_called_once_with(mock_message.value)
                
                # Verify no messages sent on error
                assert mock_producer.send.call_count == 0, "send() should not be called on error"
                # The flush may be called as part of disconnect, so we don't assert on it