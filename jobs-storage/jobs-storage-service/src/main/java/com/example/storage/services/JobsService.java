package com.example.storage.services;

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
}
