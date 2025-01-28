package com.example.storage.controllers;

import java.util.List;
import java.util.Set;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.storage.models.Jobs;
import com.example.storage.services.JobsService;
import com.example.storage.services.RedisService;

@RestController
@RequestMapping("/api/redis")
@CrossOrigin(origins = "*")
public class JobsController {

	@Autowired
    private RedisService redisService;
	
	@Autowired
	private JobsService jobsService;

    @PostMapping("/skills/{jobId}")
    public ResponseEntity<?> storeSkills(
            @PathVariable String jobId,
            @RequestParam(defaultValue = "job") String source,
            @RequestBody Set<String> skills) {
        try {
            redisService.storeSkills(jobId, skills, source);
            return ResponseEntity.ok()
                .body("Skills stored successfully for " + jobId);
        } catch (Exception e) {
            return ResponseEntity.badRequest()
                .body("Error storing skills: " + e.getMessage());
        }
    }
    
    @GetMapping("jobs/all")
    public ResponseEntity<List<Jobs>> getAllJobs() {
    	List<Jobs> jobs = jobsService.getAllJobs();
    	return ResponseEntity.ok(jobs);
    }
}
