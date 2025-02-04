package com.example.matching.controllers;

import java.util.Collections;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.matching.services.RedisService;

@RestController
@RequestMapping("/api/redis")
@CrossOrigin(origins = "*")
public class RedisController {

	@Autowired
    private RedisService redisService;
	
	@GetMapping("/match/{userId}")
	public ResponseEntity<?> getMatchScores(@PathVariable String userId) {
		try {
			Map<String, Double> scores = redisService.getMatchScores(userId);
            return ResponseEntity.ok(scores);
		} catch (Exception e) {
			return ResponseEntity.badRequest()
	                .body(Collections.singletonMap("error", e.getMessage())); 
		}
	}
}
