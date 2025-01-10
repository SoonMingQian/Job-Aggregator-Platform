package com.example.storage.services;

import java.util.Set;
import java.util.concurrent.TimeUnit;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

@Service
public class RedisService {

	@Autowired
    private RedisTemplate<String, String> redisTemplate;
	
	public void storeSkills(String jobId, Set<String> skills, String source) {
		try {
			String skillsKey = source + ":" + jobId + ":skills";
			
			redisTemplate.delete(skillsKey);
            if (!skills.isEmpty()) {
                redisTemplate.opsForSet().add(skillsKey, skills.toArray(new String[0]));
                if ("job".equals(source)) {
                    redisTemplate.expire(skillsKey, 24, TimeUnit.HOURS);
                }
            }
		} catch (Exception e) {
            System.err.println("Error storing skills in Redis: " + e);
        }
	}
    
}
