package com.example.storage.controllers;

import java.text.Format;
import java.util.HashSet;
import java.util.Optional;
import java.util.Set;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.kafka.annotation.KafkaListener;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.type.TypeReference;
import com.example.storage.models.Jobs;
import com.example.storage.services.JobsService;

@Controller
public class JobsController {

	
}
