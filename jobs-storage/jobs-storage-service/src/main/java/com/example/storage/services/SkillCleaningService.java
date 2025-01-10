package com.example.storage.services;

import java.util.HashSet;
import java.util.Set;

import org.springframework.stereotype.Service;

@Service
public class SkillCleaningService {

	public Set<String> cleanSkills(Set<String> skills) {
		Set<String> cleanedSkills = new HashSet<>();
		for (String skill : skills) {
			if (skill != null) {
				String cleaned = skill.toLowerCase()
						.replaceAll("[^a-z0-9\\s]", "")
						.replaceAll("\\s+", " ")
						.trim();
				if (!cleaned.isEmpty()) {
					cleanedSkills.add(cleaned);
				}
			}
		}
		return cleanedSkills;
	}
}
