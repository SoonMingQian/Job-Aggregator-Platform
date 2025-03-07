package com.example.storage.repositories;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import com.example.storage.models.Jobs;

@Repository
public interface JobsRepository extends JpaRepository<Jobs, String> {
	Jobs findByJobId(String jobId);

	List<Jobs> findAllByOrderByTimestampDesc();

	@Query("SELECT j FROM Jobs j WHERE " +
			"(LOWER(j.searchTitle) = LOWER(:title) OR :title IS NULL)")
	List<Jobs> findRelevantJobs(@Param("title") String title);

}
