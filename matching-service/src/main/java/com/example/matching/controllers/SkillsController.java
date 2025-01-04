package com.example.matching.controllers;

import java.util.Collections;
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

import com.example.matching.services.RedisService;

@CrossOrigin(origins = "*")
@RestController
@RequestMapping("/api/skills")
public class SkillsController {

	@Autowired
	private RedisService redisService;
	
	@GetMapping("/job/{jobId}")
    public ResponseEntity<Set<String>> getSkillsByJobId(@PathVariable String jobId) {
        String key = "job:job:" + jobId + ":skills";
        if (!redisService.hasKey(key)) {
            return ResponseEntity.notFound().build();
        }
        Set<String> skills = redisService.getJobSkills(jobId);
        return ResponseEntity.ok(skills);
    }
	
	@GetMapping("/user/{userId}")
	public ResponseEntity<Set<String>> getSkillsByUserId(@PathVariable String userId){
		String key = "cv:cv_" + userId + ":skills";
		if (!redisService.hasKey(key)) {
            return ResponseEntity.notFound().build();
        }
        Set<String> skills = redisService.getUserSkills(userId);
        return ResponseEntity.ok(skills);
	}	
}
