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
    
    public Set<String> getSkills(String jobId) {
        String key = "job:job:" + jobId + ":skills";
        Set<String> members = redisTemplate.opsForSet().members(key);
        return members != null ? members : new HashSet<>();
    }

    public boolean hasKey(String key) {
        return redisTemplate.hasKey(key);
    }
}
