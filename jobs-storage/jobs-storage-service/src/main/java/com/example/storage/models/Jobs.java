package com.example.storage.models;

import java.util.Date;

import jakarta.persistence.*;

@Entity
public class Jobs {
	
	@Id
	private String jobId;
	
	private String title;
	
	private String company;
	
	private String location;
	
	@Lob
	private String applyLink;
	
	@Lob 
	private String jobDescription;
	
	@Temporal(TemporalType.TIMESTAMP)
	private Date timestamp;

	public String getJobId() {
		return jobId;
	}

	public void setJobId(String jobId) {
		this.jobId = jobId;
	}

	public String getTitle() {
		return title;
	}

	public void setTitle(String title) {
		this.title = title;
	}

	public String getCompany() {
		return company;
	}

	public void setCompany(String company) {
		this.company = company;
	}

	public String getLocation() {
		return location;
	}

	public void setLocation(String location) {
		this.location = location;
	}

	public String getApplyLink() {
		return applyLink;
	}

	public void setApplyLink(String applyLink) {
		this.applyLink = applyLink;
	}

	public String getJobDescription() {
		return jobDescription;
	}

	public void setJobDescription(String jobDescription) {
		this.jobDescription = jobDescription;
	}

	public Date getTimestamp() {
		return timestamp;
	}

	public void setTimestamp(Date timestamp) {
		this.timestamp = timestamp;
	}
}
