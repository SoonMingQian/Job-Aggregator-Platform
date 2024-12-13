package com.example.storage.repositories;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.example.storage.models.Jobs;

@Repository
public interface JobsRepository extends JpaRepository<Jobs, String>{
	Jobs findByJobId(String jobId);
}
