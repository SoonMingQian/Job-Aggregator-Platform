package com.example.storage.services;

import java.util.List;
import java.util.Optional;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.example.storage.models.Jobs;
import com.example.storage.repositories.JobsRepository;

@Service
public class JobsService {

	private static final Logger logger = LoggerFactory.getLogger(JobsService.class);
	
	@Autowired
	private JobsRepository jobsRepository;

	public Jobs saveJobs(Jobs jobs) {
		return jobsRepository.save(jobs);
	}

	public Optional<Jobs> findJobById(String jobId) {
		return jobsRepository.findById(jobId);
	}

	public List<Jobs> findAllJobs() {
		return jobsRepository.findAll();
	}

	public List<Jobs> getAllJobs() {
		return jobsRepository.findAllByOrderByTimestampDesc();
	}

	public List<Jobs> getRelevantJobs(String searchTitle, String searchLocation) {
		// If no search parameters provided, return all jobs sorted by timestamp
		if ((searchTitle == null || searchTitle.isEmpty())) {
			return getAllJobs();
		}

		// Get jobs with matching searchTitle and searchLocation
		List<Jobs> relevantJobs = jobsRepository.findRelevantJobs(searchTitle != null && !searchTitle.isEmpty() ? searchTitle : null);

		if (relevantJobs.isEmpty()) {
			logger.info("No jobs found matching search criteria, returning all jobs");
			return getAllJobs();
		}
		// If we found relevant jobs, sort them by calculated score
		if (!relevantJobs.isEmpty()) {
			// Create final variables for use in the lambda
			final String finalSearchTitle = searchTitle != null ? searchTitle.toLowerCase() : "";
			final String finalSearchLocation = searchLocation != null ? searchLocation.toLowerCase() : "";

			// Sort jobs by their calculated relevance score (DESCENDING - highest score
			// first)
			relevantJobs.sort((job1, job2) -> {
				int score1 = calculateJobScore(job1, finalSearchTitle, finalSearchLocation);
				int score2 = calculateJobScore(job2, finalSearchTitle, finalSearchLocation);
				// Sort by score (descending)
				return Integer.compare(score2, score1); // Changed from score1, score2 to score2, score1
			});
		}

		return relevantJobs;
	}

	private int calculateJobScore(Jobs job, String searchTitle, String searchLocation) {
		int score = 0;

		// Score based on job title matching the search title
		if (!searchTitle.isEmpty() && job.getTitle() != null) {
			String jobTitle = job.getTitle().toLowerCase();

			// Exact title match
			if (jobTitle.equals(searchTitle)) {
				score += 100;
			}
			// Title contains search term
			else if (jobTitle.contains(searchTitle)) {
				score += 70;
			}
			// Words in search term appear in title (for multi-word searches)
			else {
				String[] searchWords = searchTitle.split("\\s+");
				for (String word : searchWords) {
					if (word.length() > 2 && jobTitle.contains(word)) {
						score += 30;
					}
				}
			}
		}

		// Score based on job location matching the search location
		if (!searchLocation.isEmpty() && job.getLocation() != null) {
			String jobLocation = job.getLocation().toLowerCase();

			// Exact location match
			if (jobLocation.equals(searchLocation)) {
				score += 80;
			}
			// Location contains search term
			else if (jobLocation.contains(searchLocation)) {
				score += 60;
			}
			// Search location contains job location
			else if (searchLocation.contains(jobLocation)) {
				score += 40;
			}
		}

		// Recency bonus: newer jobs get more points (max 30 points for jobs from today)
		if (job.getTimestamp() != null) {
			long daysSincePosted = java.time.temporal.ChronoUnit.DAYS.between(
					job.getTimestamp().toInstant().atZone(java.time.ZoneId.systemDefault()).toLocalDate(),
					java.time.LocalDate.now());

			int recencyScore = (int) Math.max(0, 30 - (daysSincePosted * 2));
			score += recencyScore;
		}
		return score;
	}
}
