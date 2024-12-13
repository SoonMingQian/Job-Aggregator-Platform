package com.example.storage.controllers;

import java.text.Format;
import java.util.HashSet;
import java.util.Optional;
import java.util.Set;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.kafka.annotation.KafkaListener;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.type.TypeReference;
import com.example.storage.models.Jobs;
import com.example.storage.services.JobsService;

@Controller
public class JobsController {

	@Autowired
	private JobsService jobsService;
	
	private final ObjectMapper objectMapper = new ObjectMapper();
	
	@KafkaListener(topics = "storage", groupId = "storage-group")
	public void listenJobs(String message) {
		try {
			Jobs job = objectMapper.readValue(message, Jobs.class);
			jobsService.saveJobs(job);
		} catch (Exception e) {
			System.err.println("Error processing message: " + e.getMessage());
		}
	}
	
	@KafkaListener(topics = "skill", groupId = "storage-group")
	public void listenSkills(String message) {
	    try {
	        // Remove escape characters and quotes if present
	        if (message.startsWith("\"") && message.endsWith("\"")) {
	            message = message.substring(1, message.length() - 1);
	        }
	        message = message.replace("\\\"", "\"");
	        
	        System.out.println("Processing message: " + message);
	        
	        // Parse JSON
	        JsonNode rootNode = objectMapper.readTree(message);
	        System.out.println("Parsed JSON: " + rootNode);
	        
	        String jobId = rootNode.path("jobId").asText();
	        JsonNode skillsNode = rootNode.path("skills");
	        
	        if (jobId.isEmpty()) {
	            throw new IllegalArgumentException("jobId is missing or empty");
	        }
	        
	        if (!skillsNode.isArray()) {
	            throw new IllegalArgumentException("skills must be an array");
	        }
	        
	        // Convert skills array to Set
	        Set<String> skills = new HashSet<>();
	        skillsNode.forEach(skill -> {
	            String skillText = skill.asText().trim();
	            if (!skillText.isEmpty()) {
	                skills.add(skillText);
	            }
	        });
	        
	        // Update job
	        Optional<Jobs> jobOptional = jobsService.findJobById(jobId);
	        if (jobOptional.isPresent()) {
	            Jobs job = jobOptional.get();
	            job.setSkills(skills);
	            jobsService.saveJobs(job);
	            System.out.println("Successfully updated skills for job " + jobId + ": " + skills);
	        } else {
	            System.err.println("Job not found: " + jobId);
	        }
	        
	    } catch (Exception e) {
	        System.err.println("Error processing message: " + message);
	        System.err.println("Error: " + e.getMessage());
	        e.printStackTrace();
	    }
	}
}
