package com.example.storage.services;

import java.util.HashSet;
import java.util.Set;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

import com.example.storage.models.Jobs;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@Service
public class KafkaConsumerService {

	@Autowired
	private JobsService jobsService;
	
	private final ObjectMapper objectMapper = new ObjectMapper();
	
	@KafkaListener(topics = "storage", groupId = "${spring.kafka.consumer.group-id}")
	public void consumeJobs(String message) {
		try {
			Jobs job = objectMapper.readValue(message, Jobs.class);
			jobsService.saveJobs(job);
		} catch (Exception e) {
            System.err.println("Error processing job message: " + e.getMessage());
        }
	}
	
	@KafkaListener(topics = "skill", groupId = "${spring.kafka.consumer.group-id}")
    public void consumeSkills(String message) {
        try {
            if (message.startsWith("\"") && message.endsWith("\"")) {
                message = message.substring(1, message.length() - 1);
            }
            message = message.replace("\\\"", "\"");
            
            JsonNode rootNode = objectMapper.readTree(message);
            String jobId = rootNode.path("jobId").asText();
            JsonNode skillsNode = rootNode.path("skills");
            
            if (jobId.isEmpty()) {
                throw new IllegalArgumentException("jobId is missing or empty");
            }
            
            Set<String> skills = new HashSet<>();
            skillsNode.forEach(skill -> {
                String skillText = skill.asText().trim();
                if (!skillText.isEmpty()) {
                    skills.add(skillText);
                }
            });
            
            jobsService.findJobById(jobId).ifPresent(job -> {
                job.setSkills(skills);
                jobsService.saveJobs(job);
            });
        } catch (Exception e) {
            System.err.println("Error processing skills message: " + e.getMessage());
        }
    }
}
