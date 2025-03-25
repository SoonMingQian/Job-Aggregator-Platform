package com.example.storage.controllers;

import static org.mockito.Mockito.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import java.util.List;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Arrays;
import java.util.Date;
import java.util.Optional;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import com.example.storage.models.Jobs;
import com.example.storage.services.JobsService;
import com.example.storage.services.RedisService;
import com.fasterxml.jackson.databind.ObjectMapper;

@WebMvcTest(JobsController.class)
public class JobsControllerTest {

	@Autowired
	private MockMvc mockMvc;
	
	@Autowired
	private ObjectMapper objectMapper;
	
    @MockBean 
    private JobsService jobsService;
    
    @MockBean
    private RedisService redisService;
    
    private Jobs job1;
    private Jobs job2;
    
    @BeforeEach
    public void setup() {
    	job1 = new Jobs();
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
        
        job2 = new Jobs();
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
        job2.setSearchLocation("Cork");
    }
    
    @Test	
    public void testGetAllJobs() throws Exception {
    	List<Jobs> jobs = Arrays.asList(job1, job2);
        when(jobsService.getAllJobs()).thenReturn(jobs);
        
        mockMvc.perform(get("/api/jobs/all")
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].jobId").value("1"))
                .andExpect(jsonPath("$[0].title").value("Software Engineer"))
                .andExpect(jsonPath("$[1].jobId").value("2"))
                .andExpect(jsonPath("$[1].title").value("Data Scientist"));	
    }
    
    @Test
    public void testGetRelevantJobs() throws Exception {
    	List<Jobs> jobs = Arrays.asList(job1, job2);
        when(jobsService.getRelevantJobs("engineer", "dublin")).thenReturn(jobs);
        
        mockMvc.perform(get("/api/jobs/relevant")
                .param("title", "engineer")
                .param("location", "dublin")
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].jobId").value("1"))
                .andExpect(jsonPath("$[0].title").value("Software Engineer"));
    }
}
