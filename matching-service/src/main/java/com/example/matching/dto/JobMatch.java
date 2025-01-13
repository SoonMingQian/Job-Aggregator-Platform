package com.example.matching.dto;

public class JobMatch {
	
	private String jobId;
	private double score;
	
	public JobMatch(String jobId, double score) {
		super();
		this.jobId = jobId;
		this.score = score;
	}

	public String getJobId() {
		return jobId;
	}

	public void setJobId(String jobId) {
		this.jobId = jobId;
	}

	public double getScore() {
		return score;
	}

	public void setScore(double score) {
		this.score = score;
	}
	
	
	
	
}
