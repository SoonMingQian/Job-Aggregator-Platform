package com.example.storage.services;

import java.util.List;
import java.util.Optional;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.example.storage.models.Jobs;
import com.example.storage.repositories.JobsRepository;

@Service
public class JobsService {

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
}
