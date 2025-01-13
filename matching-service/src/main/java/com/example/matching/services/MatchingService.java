package com.example.matching.services;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.example.matching.dto.JobMatch;

@Service
public class MatchingService {

	@Autowired
	private RedisService redisService;

	private static final double SIMILARITY_THRESHOLD = 0.6;

	public List<JobMatch> findMatchingJobs(String userId, String jobTitle, String location) {
		try {
			Set<String> userSkills = redisService.getUserSkills(userId);
			Set<String> jobIds = redisService.getJobIdFromSearchKey(jobTitle, location);
			System.out.println(jobIds);
			List<JobMatch> matches = new ArrayList<>();

			if (jobIds == null || jobIds.isEmpty()) {
				return matches;
			}

			System.out.println("User skills: " + userSkills);

			for (String jobId : jobIds) {
				if (jobId != null) {
					Set<String> jobSkills = redisService.getJobSkills(jobId);
					System.out.println("Job " + jobId + " skills: " + jobSkills);

					if (!jobSkills.isEmpty()) {
	                    double fuzzyScore = calculateFuzzyMatchScore(userSkills, jobSkills);
	                    System.out.println("Score for " + jobId + ": " + fuzzyScore);
	                    matches.add(new JobMatch(jobId, fuzzyScore));
	                }
				}
			}

			// Safe sorting with defensive checks
			if (!matches.isEmpty()) {
				matches.sort((a, b) -> {
					if (a == null || b == null) return 0;
					try {
						return Double.compare(b.getScore(), a.getScore());
					} catch (Exception e) {
						return 0;
					}
				});
			}
			
			return matches;

		} catch (Exception e) {
			System.err.println("Error in findMatchingJobs: " + e.getMessage());
			e.printStackTrace();
			return new ArrayList<>();
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
				System.out.println(String.format("Comparing '%s' with '%s': %.2f", 
                jobSkill, userSkill, similarity));
				bestMatch = Math.max(bestMatch, similarity);
			}

			if (bestMatch >= SIMILARITY_THRESHOLD) {
				totalMatches += bestMatch;
				System.out.println("Match found for '" + jobSkill + "' with score: " + bestMatch);
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
	                dp[i][j] = 1 + Math.min(dp[i - 1][j - 1],
	                            Math.min(dp[i - 1][j], dp[i][j - 1]));
	            }
	        }
	    }

	    return dp[s1.length()][s2.length()];
	}
}
