package com.example.matching.services;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

import com.example.matching.dto.JobMatch;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@Service
public class MatchingService {

	@Autowired
	private RedisService redisService;

	private static final double SIMILARITY_THRESHOLD = 0.2;
	private static final Logger logger = LoggerFactory.getLogger(MatchingService.class);
	
	@KafkaListener(topics = "matching", groupId = "matching-group")
	public void onSkillExtractionComplete(String message) {
		try {
			ObjectMapper mapper = new ObjectMapper();
			JsonNode node = mapper.readTree(message);
			String jobId = node.get("jobId").asText();
			String userId = node.get("userId").asText();
			
			logger.info("Skills extraction completed for job: {} and user: {}", jobId, userId);
			Set<String> userSkills = redisService.getUserSkills(userId);
            Set<String> jobSkills = redisService.getJobSkills(jobId);
            
            if(jobSkills == null || jobSkills.isEmpty()) {
            	logger.warn("No skills found for job: {}" + jobId );
            }
            
            double score = calculateFuzzyMatchScore(userSkills, jobSkills);
            logger.info("Match score for job {} and user {}: {}", jobId, userId, score);
	        // Store match score in Redis
	        redisService.saveMatchScore(userId, jobId, score);
        } catch (Exception e) {
            logger.error("Error processing matching message: {}", e);
        }
	}

	private double calculateFuzzyMatchScore(Set<String> userSkills, Set<String> jobSkills) {
		if (jobSkills.isEmpty() || userSkills.isEmpty()) { // Add check for empty user skills
			System.out.println("User skills: " + userSkills);
			System.out.println("Job skills: " + jobSkills);
			return 0.0;
		}

		System.out.println("\nMatching skills:");
		System.out.println("User skills: " + userSkills);
		System.out.println("Job skills: " + jobSkills);

		double totalMatches = 0.0;
		for (String jobSkill : jobSkills) {
			double bestMatch = 0.0;
			for (String userSkill : userSkills) {
				double similarity = calculateSimilarity(jobSkill.toLowerCase(), userSkill.toLowerCase());
				System.out.println(String.format("Comparing '%s' with '%s': %.2f", jobSkill, userSkill, similarity));
				bestMatch = Math.max(bestMatch, similarity);
			}

			if (bestMatch >= SIMILARITY_THRESHOLD) {
				totalMatches += bestMatch;
				System.out.println("Match found for '" + jobSkill + "' with score: " + bestMatch);
			} else if (bestMatch >= 0.2) {  // Add partial matches
				totalMatches += bestMatch * 0.5;  // Count as half value
				System.out.println("Partial match found for '" + jobSkill + "' with score: " + bestMatch + " (counted as " + (bestMatch * 0.5) + ")");
			}
		}

		double finalScore = (totalMatches / jobSkills.size()) * 100.0;
		System.out.println("Final score: " + finalScore + "%");
		return finalScore;
	}

	private double calculateSimilarity(String s1, String s2) {
		int levenshteinDistance = levenshteinDistance(s1, s2);
		int maxLength = Math.max(s1.length(), s2.length());
		return 1.0 - ((double) levenshteinDistance / maxLength);
	}

	private int levenshteinDistance(String s1, String s2) {
		if (s1 == null || s2 == null) {
			return 0;
		}

		s1 = s1.trim();
		s2 = s2.trim();

		if (s1.isEmpty() || s2.isEmpty()) {
			return 0;
		}

		int[][] dp = new int[s1.length() + 1][s2.length() + 1];

		for (int i = 0; i <= s1.length(); i++) {
			dp[i][0] = i;
		}

		for (int j = 0; j <= s2.length(); j++) {
			dp[0][j] = j;
		}

		for (int i = 1; i <= s1.length(); i++) {
			for (int j = 1; j <= s2.length(); j++) {
				if (s1.charAt(i - 1) == s2.charAt(j - 1)) {
					dp[i][j] = dp[i - 1][j - 1];
				} else {
					dp[i][j] = 1 + Math.min(dp[i - 1][j - 1], Math.min(dp[i - 1][j], dp[i][j - 1]));
				}
			}
		}

		return dp[s1.length()][s2.length()];
	}
}
