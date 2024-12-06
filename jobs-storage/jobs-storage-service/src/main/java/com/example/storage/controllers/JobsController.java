package com.example.storage.controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.kafka.annotation.KafkaListener;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.example.storage.models.Jobs;
import com.example.storage.services.JobsService;

@Controller
public class JobsController {

	@Autowired
	private JobsService jobsService;
	
	private final ObjectMapper objectMapper = new ObjectMapper();
	
	@KafkaListener(topics = "storage", groupId = "storage-group")
	public void listen(String message) {
		try {
			Jobs job = objectMapper.readValue(message, Jobs.class);
			jobsService.saveJobs(job);
			System.out.println(job);
		} catch (Exception e) {
			System.err.println("Error processing message: " + e.getMessage());
		}
	}
}
