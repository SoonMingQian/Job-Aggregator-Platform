package com.example.matching.services;

import java.util.HashSet;
import java.util.Set;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

@Service
public class RedisService {
    
    @Autowired
    private RedisTemplate<String, String> redisTemplate;
    
    public Set<String> getJobSkills(String jobId) {
        String key = "job:job:" + jobId + ":skills";
        Set<String> members = redisTemplate.opsForSet().members(key);
        return members != null ? members : new HashSet<>();
    }
    
    public Set<String> getUserSkills(String userId) {
    	String key = "cv:cv_" + userId + ":skills";
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
}
