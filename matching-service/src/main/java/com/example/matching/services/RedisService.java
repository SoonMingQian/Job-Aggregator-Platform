package com.example.matching.services;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

@Service
public class RedisService {
    
    @Autowired
    private RedisTemplate<String, String> redisTemplate;
    
    public Set<String> getJobSkills(String jobId) {
    	String cleanJobId = jobId.startsWith("job:") ? jobId.substring(4) : jobId;
        String key = "job:" + cleanJobId + ":skills";
        Set<String> members = redisTemplate.opsForSet().members(key);
        return members != null ? members : new HashSet<>();
    }
    
    public Set<String> getUserSkills(String userId) {
    	String key = "cv:" + userId + ":skills";
    	Set<String> members = redisTemplate.opsForSet().members(key);
        return members != null ? members : new HashSet<>();
    }
    
    public Set<String> getJobIdFromSearchKey(String jobTitle, String location) {
    	String jobsIESearchKey = "search:" + jobTitle + ":" + location + ":jobsIE";
    	String indeedSearchKey = "search:" + jobTitle + ":" + location + ":indeed";
    	
    	Set<String> jobsIEResults = redisTemplate.opsForSet().members(jobsIESearchKey);
        Set<String> indeedResults = redisTemplate.opsForSet().members(indeedSearchKey);
        
        Set<String> combinedResults = new HashSet<>();
        
        if (jobsIEResults != null) {
            combinedResults.addAll(jobsIEResults);
        }
        
        if (indeedResults != null) {
            combinedResults.addAll(indeedResults);
        }
        
        return combinedResults;
    }

    public boolean hasKey(String key) {
        return redisTemplate.hasKey(key);
    }
    
    public void saveMatchScore(String userId, String jobId, double score) {
    	redisTemplate.opsForHash().put(
    	        "match:" + userId,
    	        jobId,
    	        String.valueOf(score)
    	    );
    }
    
    public Map<String, Double> getMatchScores(String userId) {
    	Map<Object, Object> rawScores = redisTemplate.opsForHash().entries("match:" + userId);
    	Map<String, Double> scores = new HashMap<>();
    	
    	for (Map.Entry<Object, Object> entry : rawScores.entrySet()) {
    		String jobId = entry.getKey().toString();
    		Double score = Double.parseDouble(entry.getValue().toString());
    		scores.put(jobId, score);
    	}
    	
    	return scores;
    }
}
