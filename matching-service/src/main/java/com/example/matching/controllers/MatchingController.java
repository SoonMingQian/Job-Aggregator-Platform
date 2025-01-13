package com.example.matching.controllers;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.matching.dto.JobMatch;
import com.example.matching.services.MatchingService;

@RestController
@RequestMapping("/api/matching")
@CrossOrigin(origins = "*")
public class MatchingController {

	@Autowired
    private MatchingService matchingService;
	
	@GetMapping("/jobs")
	public ResponseEntity<?> findMatchingJobs(@RequestParam String userId,
									          @RequestParam String jobTitle,
									          @RequestParam String location){
		try {
			List<JobMatch> matches = matchingService.findMatchingJobs(userId, jobTitle, location);
			if(matches.isEmpty()) {
				return ResponseEntity.ok().body("No matching jobs found");
			}
			
			return ResponseEntity.ok(matches);
		} catch (Exception e) {
			 return ResponseEntity.badRequest().body("Error finding matching jobs: " + e.getMessage());
		}
	}
}
