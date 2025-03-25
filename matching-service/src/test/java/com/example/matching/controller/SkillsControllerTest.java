package com.example.matching.controller;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.HashSet;
import java.util.Set;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import com.example.matching.controllers.SkillsController;
import com.example.matching.services.RedisService;

@WebMvcTest(SkillsController.class)
public class SkillsControllerTest {

	@Autowired
	private MockMvc mockMvc;

	@MockBean
	private RedisService redisService;

	private Set<String> sampleSkills;

	@BeforeEach
	public void setup() {
		sampleSkills = new HashSet<>();
		sampleSkills.add("java");
		sampleSkills.add("spring");
		sampleSkills.add("microservices");
	}

	@Test
	public void testGetSkillsByJobId_Found() throws Exception {
		String jobId = "123";
		String key = "job:123:skills";

		// Setup mocks
		when(redisService.hasKey(key)).thenReturn(true);
		when(redisService.getJobSkills(jobId)).thenReturn(sampleSkills);

		// Execute and verify
		mockMvc.perform(get("/api/skills/job/{jobId}", jobId).contentType(MediaType.APPLICATION_JSON))
				.andExpect(status().isOk()).andExpect(jsonPath("$[0]").exists()).andExpect(jsonPath("$[1]").exists())
				.andExpect(jsonPath("$[2]").exists());

		// Verify service calls
		verify(redisService).hasKey(key);
		verify(redisService).getJobSkills(jobId);
	}
	
	@Test
    public void testGetSkillsByJobId_NotFound() throws Exception {
        String jobId = "nonexistent";
        String key = "job:nonexistent:skills";
        
        // Setup mocks
        when(redisService.hasKey(key)).thenReturn(false);
        
        // Execute and verify
        mockMvc.perform(get("/api/skills/job/{jobId}", jobId)
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isNotFound());
        
        // Verify service calls
        verify(redisService).hasKey(key);
        verify(redisService, never()).getJobSkills(anyString()); // Should not be called
    }
	
	@Test
    public void testGetSkillsByUserId_Found() throws Exception {
        String userId = "user123";
        String key = "cv:cv_user123:skills";
        
        // Setup mocks
        when(redisService.hasKey(key)).thenReturn(true);
        when(redisService.getUserSkills(userId)).thenReturn(sampleSkills);
        
        // Execute and verify
        mockMvc.perform(get("/api/skills/user/{userId}", userId)
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0]").exists())
                .andExpect(jsonPath("$[1]").exists())
                .andExpect(jsonPath("$[2]").exists());
        
        // Verify service calls
        verify(redisService).hasKey(key);
        verify(redisService).getUserSkills(userId);
    }
	
	@Test
    public void testGetSkillsByUserId_NotFound() throws Exception {
        String userId = "nonexistent";
        String key = "cv:cv_nonexistent:skills";
        
        // Setup mocks
        when(redisService.hasKey(key)).thenReturn(false);
        
        // Execute and verify
        mockMvc.perform(get("/api/skills/user/{userId}", userId)
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isNotFound());
        
        // Verify service calls
        verify(redisService).hasKey(key);
        verify(redisService, never()).getUserSkills(anyString()); // Should not be called
    }
	
	@Test
    public void testSearchJobs_Found() throws Exception {
        String title = "software engineer";
        String location = "dublin";
        
        Set<String> jobIds = new HashSet<>();
        jobIds.add("job1");
        jobIds.add("job2");
        
        // Setup mocks
        when(redisService.getJobIdFromSearchKey(title, location)).thenReturn(jobIds);
        
        // Execute and verify
        mockMvc.perform(get("/api/skills/jobs")
                .param("title", title)
                .param("location", location)
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0]").exists())
                .andExpect(jsonPath("$[1]").exists());
        
        // Verify service calls
        verify(redisService).getJobIdFromSearchKey(title, location);
    }
    
    @Test
    public void testSearchJobs_NotFound() throws Exception {
        String title = "nonexistent";
        String location = "nowhere";
        
        // Setup mocks - return empty set
        when(redisService.getJobIdFromSearchKey(title, location)).thenReturn(new HashSet<>());
        
        // Execute and verify - should still return 200 OK with empty array
        mockMvc.perform(get("/api/skills/jobs")
                .param("title", title)
                .param("location", location)
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$").isArray())
                .andExpect(jsonPath("$").isEmpty());
        
        // Verify service calls
        verify(redisService).getJobIdFromSearchKey(title, location);
    }
    
    @Test
    public void testSearchJobs_MissingParameters() throws Exception {
        // Execute and verify - missing required parameters
        mockMvc.perform(get("/api/skills/jobs")
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isBadRequest());
        
        // Verify no service calls
        verify(redisService, never()).getJobIdFromSearchKey(anyString(), anyString());
    }
}
