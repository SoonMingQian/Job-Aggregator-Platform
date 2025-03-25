package com.example.storage.services;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

public class SkillCleaningServiceTest {

	private SkillCleaningService skillCleaningService;

	@BeforeEach
	public void setup() {
		skillCleaningService = new SkillCleaningService();
	}

	@Test
	public void testCleanSkills_BasicCleaning() {
		Set<String> inputSkills = new HashSet<>(Arrays.asList("Java", "Python", "JavaScript"));
		Set<String> cleanedSkills = skillCleaningService.cleanSkills(inputSkills);
		Set<String> expectedSkills = new HashSet<>(Arrays.asList("java", "python", "javascript"));
		assertEquals(expectedSkills, cleanedSkills);
	}

	@Test
	public void testCleanSkills_TrimmingWhiteSpaces() {
		Set<String> inputSkills = new HashSet<>(Arrays.asList("  Java  ", "Spring Boot ", " Hibernate"));
		Set<String> cleanedSkills = skillCleaningService.cleanSkills(inputSkills);
		Set<String> expectedSkills = new HashSet<>(Arrays.asList("java", "spring boot", "hibernate"));
		assertEquals(expectedSkills, cleanedSkills);
	}
	
	@Test
    public void testCleanSkills_ExtraSpaces() {
        // Arrange
        Set<String> inputSkills = new HashSet<>(Arrays.asList(
            "Amazon  Web  Services",
            "Microsoft    Azure",
            "Google   Cloud   Platform"
        ));
        
        // Act
        Set<String> cleanedSkills = skillCleaningService.cleanSkills(inputSkills);
        
        // Assert
        Set<String> expectedSkills = new HashSet<>(Arrays.asList(
            "amazon web services",
            "microsoft azure",
            "google cloud platform"
        ));
        assertEquals(expectedSkills, cleanedSkills);
	}
	
	@Test
    public void testCleanSkills_EmptyStrings() {
        // Arrange
        Set<String> inputSkills = new HashSet<>(Arrays.asList(
            "",
            "  ",
            "Java"
        ));
        
        // Act
        Set<String> cleanedSkills = skillCleaningService.cleanSkills(inputSkills);
        
        // Assert
        Set<String> expectedSkills = new HashSet<>(Arrays.asList(
            "java"
        ));
        assertEquals(expectedSkills, cleanedSkills);
        assertEquals(1, cleanedSkills.size(), "Empty strings should be filtered out");
    }
	
	@Test
    public void testCleanSkills_NullValues() {
        // Arrange
        Set<String> inputSkills = new HashSet<>();
        inputSkills.add("Java");
        inputSkills.add(null);
        inputSkills.add("Python");
        
        // Act
        Set<String> cleanedSkills = skillCleaningService.cleanSkills(inputSkills);
        
        // Assert
        Set<String> expectedSkills = new HashSet<>(Arrays.asList(
            "java",
            "python"
        ));
        assertEquals(expectedSkills, cleanedSkills);
        assertEquals(2, cleanedSkills.size(), "Null values should be filtered out");
    }
	
	@Test
    public void testCleanSkills_Numbers() {
        // Arrange
        Set<String> inputSkills = new HashSet<>(Arrays.asList(
            "Java 11",
            "Python 3.9",
            "SQL Server 2019"
        ));
        
        // Act
        Set<String> cleanedSkills = skillCleaningService.cleanSkills(inputSkills);
        
        // Assert
        Set<String> expectedSkills = new HashSet<>(Arrays.asList(
            "java 11",
            "python 39",
            "sql server 2019"
        ));
        assertEquals(expectedSkills, cleanedSkills);
    }
	
	@Test
    public void testCleanSkills_EmptyInput() {
        // Arrange
        Set<String> inputSkills = new HashSet<>();
        
        // Act
        Set<String> cleanedSkills = skillCleaningService.cleanSkills(inputSkills);
        
        // Assert
        assertTrue(cleanedSkills.isEmpty(), "Cleaning an empty set should return an empty set");
    }
	
	@Test
    public void testCleanSkills_Deduplicate() {
        // Arrange - different casing but same after cleaning
        Set<String> inputSkills = new HashSet<>(Arrays.asList(
            "Java",
            "JAVA",
            "java"
        ));
        
        // Act
        Set<String> cleanedSkills = skillCleaningService.cleanSkills(inputSkills);
        
        // Assert
        Set<String> expectedSkills = new HashSet<>(Arrays.asList(
            "java"
        ));
        assertEquals(expectedSkills, cleanedSkills);
        assertEquals(1, cleanedSkills.size(), "Duplicate skills should be removed");
    }
}
