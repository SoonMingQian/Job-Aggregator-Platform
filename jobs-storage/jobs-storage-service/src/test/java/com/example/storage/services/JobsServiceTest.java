package com.example.storage.services;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.List;
import java.util.Optional;
import java.util.Date;
import java.text.SimpleDateFormat;
import java.text.ParseException;

import java.util.Arrays;
import java.util.Calendar;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import com.example.storage.models.Jobs;
import com.example.storage.repositories.JobsRepository;

public class JobsServiceTest {

	@Mock
	private JobsRepository jobsRepository;
	
	@InjectMocks
	private JobsService jobsService;
	
	@BeforeEach
	public void setup() {
		MockitoAnnotations.openMocks(this);
	}
	
	@Test
    public void testGetAllJobs() {
        // Create job1 with complete data
        Jobs job1 = new Jobs();
        job1.setJobId("1");
        job1.setTitle("Software Engineer"); // Added missing title
        job1.setCompany("Company A"); // Added missing company
        job1.setLocation("Dublin"); // Added location to match searchLocation
        job1.setApplyLink("Apply Link A");
        job1.setJobDescription("Description A");
        job1.setPlatform("JobsIE");
        try {
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSSSSS");
            Date timestamp = sdf.parse("2025-03-07 20:17:29.638000");
            job1.setTimestamp(timestamp);
        } catch (ParseException e) {
            e.printStackTrace();
        }
        job1.setSearchTitle("Software Engineer"); // Fixed to match title
        job1.setSearchLocation("Dublin");
        
        // Create job2 with complete data
        Jobs job2 = new Jobs();
        job2.setJobId("2");
        job2.setTitle("Data Scientist");
        job2.setCompany("Company B");
        job2.setLocation("Location B");
        job2.setApplyLink("Apply Link B");
        job2.setJobDescription("Description B");
        job2.setPlatform("JobsIE");
        try {
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSSSSS");
            Date timestamp = sdf.parse("2025-03-07 20:17:29.638000");
            job2.setTimestamp(timestamp);
        } catch (ParseException e) {
            e.printStackTrace();
        }
        job2.setSearchTitle("Data Scientist"); // Fixed to match title
        job2.setSearchLocation("Dublin");
        
        // Mock the repository - make sure you're using the right method
        List<Jobs> mockJobs = Arrays.asList(job1, job2);
        
        // Check which repository method is actually used in getAllJobs
        // If it's findAllByOrderByTimestampDesc(), use that instead
        when(jobsRepository.findAllByOrderByTimestampDesc()).thenReturn(mockJobs);

        when(jobsRepository.findAll()).thenReturn(mockJobs);
        
        // Execute the test
        List<Jobs> result = jobsService.getAllJobs();
        
        // Verify results
        assertEquals(2, result.size());
        assertEquals("Software Engineer", result.get(0).getTitle());
        assertEquals("Data Scientist", result.get(1).getTitle());
    }
	
	@Test
	public void testGetJobById() {
		Jobs mockJob = new Jobs();
		mockJob.setJobId("1");
		mockJob.setTitle("Software Engineer");
		mockJob.setCompany("Company A");
		mockJob.setLocation("Dublin");
		mockJob.setApplyLink("Apply Link A");
		mockJob.setJobDescription("Description A");
		mockJob.setPlatform("JobsIE");
		try {
			SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSSSSS");
			Date timestamp = sdf.parse("2025-03-07 20:17:29.638000");
			mockJob.setTimestamp(timestamp);
		} catch (ParseException e) {
			e.printStackTrace();
		}
		mockJob.setSearchTitle("Software Engineer");
		mockJob.setSearchLocation("Dublin");
        when(jobsRepository.findById("1")).thenReturn(Optional.of(mockJob));
        
        // Act
        Optional<Jobs> result = jobsService.findJobById("1");
        
        // Assert
        assertTrue(result.isPresent());
        assertEquals("Software Engineer", result.get().getTitle());
    }

	@Test
    public void testGetRelevantJobs_WithTitleAndLocation() {
        // Arrange
        String searchTitle = "Software Engineer";
        String searchLocation = "Dublin";
        
        Jobs job1 = new Jobs();
        job1.setJobId("1");
        job1.setTitle("Software Engineer"); // Added missing title
        job1.setCompany("Company A"); // Added missing company
        job1.setLocation("Dublin"); // Added location to match searchLocation
        job1.setApplyLink("Apply Link A");
        job1.setJobDescription("Description A");
        job1.setPlatform("JobsIE");
        try {
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSSSSS");
            Date timestamp = sdf.parse("2025-03-07 20:17:29.638000");
            job1.setTimestamp(timestamp);
        } catch (ParseException e) {
            e.printStackTrace();
        }
        job1.setSearchTitle("Software Engineer"); // Fixed to match title
        job1.setSearchLocation("Dublin");

		Jobs job2 = new Jobs();
        job2.setJobId("2");
        job2.setTitle("Internship"); // Added missing title
        job2.setCompany("Company B"); // Added missing company
        job2.setLocation("Galway"); // Added location to match searchLocation
        job2.setApplyLink("Apply Link B");
        job2.setJobDescription("Description B");
        job2.setPlatform("JobsIE");
        try {
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSSSSS");
            Date timestamp = sdf.parse("2025-02-07 20:17:29.638000");
            job2.setTimestamp(timestamp);
        } catch (ParseException e) {
            e.printStackTrace();
        }
        job2.setSearchTitle("Software Engineer"); // Fixed to match title
        job2.setSearchLocation("Dublin");
        
        List<Jobs> relevantJobs = Arrays.asList(job1, job2);
        
        when(jobsRepository.findRelevantJobs(searchTitle)).thenReturn(relevantJobs);
        
        // Act
        List<Jobs> result = jobsService.getRelevantJobs(searchTitle, searchLocation);
        
        // Assert
        assertEquals(2, result.size());
        // job1 should be first because it matches both title and location
        assertEquals("1", result.get(0).getJobId());
        verify(jobsRepository, times(1)).findRelevantJobs(searchTitle);
    }
	
	@Test
	public void testCalculateJobScore() throws Exception {
		// Use reflection to access the private method
		java.lang.reflect.Method calculateJobScoreMethod = JobsService.class.getDeclaredMethod(
				"calculateJobScore", Jobs.class, String.class, String.class);
		calculateJobScoreMethod.setAccessible(true);
		
		// Create test jobs with different scenarios
		Jobs exactMatchJob = new Jobs();
		exactMatchJob.setTitle("Software Engineer");
		exactMatchJob.setLocation("Dublin");
		exactMatchJob.setTimestamp(new Date()); // Today's date
		
		Jobs partialMatchJob = new Jobs();
		partialMatchJob.setTitle("Senior Software Developer");
		partialMatchJob.setLocation("Dublin City");
		// Set date to 5 days ago
		Calendar cal = Calendar.getInstance();
		cal.add(Calendar.DATE, -5);
		partialMatchJob.setTimestamp(cal.getTime());
		
		Jobs wordMatchJob = new Jobs();
		wordMatchJob.setTitle("Java Engineer");
		wordMatchJob.setLocation("Remote");
		// Set date to 10 days ago
		cal = Calendar.getInstance();
		cal.add(Calendar.DATE, -10);
		wordMatchJob.setTimestamp(cal.getTime());
		
		// Test different scoring scenarios
		int exactMatchScore = (int) calculateJobScoreMethod.invoke(
				jobsService, exactMatchJob, "software engineer", "dublin");
		int partialMatchScore = (int) calculateJobScoreMethod.invoke(
				jobsService, partialMatchJob, "software engineer", "dublin");
		int wordMatchScore = (int) calculateJobScoreMethod.invoke(
				jobsService, wordMatchJob, "software engineer", "dublin");
		
		// Verify exact match has highest score (title exact: 100, location exact: 80, recency: ~30)
		assertTrue(exactMatchScore > 200);
		
		// Partial match should have lower score than exact match but higher than word match
		assertTrue(partialMatchScore < exactMatchScore);
		assertTrue(partialMatchScore > wordMatchScore);
		
		// Word match should have lowest score
		assertTrue(wordMatchScore > 0);
		
		// Test with empty search terms
		int emptySearchScore = (int) calculateJobScoreMethod.invoke(
				jobsService, exactMatchJob, "", "");
		assertEquals(30, emptySearchScore, 5); // Should only get recency points
	}
}
