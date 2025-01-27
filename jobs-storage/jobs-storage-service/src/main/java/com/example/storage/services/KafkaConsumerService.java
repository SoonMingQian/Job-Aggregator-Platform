package com.example.storage.services;

import java.util.HashSet;
import java.util.Set;
import java.util.Optional;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

import com.example.storage.models.Jobs;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Service
public class KafkaConsumerService {

	private static final Logger logger = LoggerFactory.getLogger(KafkaConsumerService.class);
	
	@Autowired
	private JobsService jobsService;
	
	@Autowired
	private SkillCleaningService skillCleaningService;
	
	@Autowired
	private RedisService redisService;
	
	private final ObjectMapper objectMapper = new ObjectMapper();
	
    private String cleanJobId(String jobId) {
        return jobId.startsWith("job:") ? jobId.substring(4) : jobId;
    }

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
            String source = rootNode.path("source").asText();
            String jobId = rootNode.path("jobId").asText();
            String cleanedJobId = cleanJobId(jobId);
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
            
            Set<String> cleanedSkills = skillCleaningService.cleanSkills(skills);
            
            // Store in redis
            redisService.storeSkills(cleanedJobId, cleanedSkills, source);
            
            // Store in mysql
            if ("job".equals(source)) {
                String mysqlJobId = "job:" + cleanedJobId;
                logger.info("Attempting to store skills in MySQL for job: {} (MySQL ID: {})", cleanedJobId, mysqlJobId);
                Optional<Jobs> jobOptional = jobsService.findJobById(mysqlJobId);
                
                if (jobOptional.isPresent()) {
                    Jobs job = jobOptional.get();
                    job.setSkills(cleanedSkills);
                    jobsService.saveJobs(job);
                    logger.info("Successfully stored skills for job: {}", cleanedJobId);
                } else {
                    logger.error("Job not found in MySQL: {} (MySQL ID: {})", cleanedJobId, mysqlJobId);
                }
            } else {
                logger.info("Skipping MySQL storage for non-job source: {}", source);
            }         
        } catch (Exception e) {
        	logger.error("Error processing skills message: {}", e.getMessage(), e);
        }
    }
}
