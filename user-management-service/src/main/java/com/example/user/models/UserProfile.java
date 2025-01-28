package com.example.user.models;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.Lob;
import jakarta.persistence.MapsId;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "user_profiles")	
public class UserProfile {

	@Id
    private String id;

    @OneToOne(fetch = FetchType.LAZY)
    @MapsId
    @JoinColumn(name = "user_id")
    private User user;
    
    private String phoneNumber;
    private String address;
    private String education;
    private String jobTitle;
    private String company;
    
    @Lob
    @Column(name = "cv_data", columnDefinition = "LONGBLOB")
    private byte[] cvData;
    
    @Column(name = "cv_name")
    private String cvName;
    
    @Column(name = "is_complete")
    private boolean isComplete = false;

	public UserProfile(String id, User user, String phoneNumber, String address, String education, String jobTitle,
			String company, byte[] cvData, String cvName, boolean isComplete) {
		super();
		this.id = id;
		this.user = user;
		this.phoneNumber = phoneNumber;
		this.address = address;
		this.education = education;
		this.jobTitle = jobTitle;
		this.company = company;
		this.cvData = cvData;
		this.cvName = cvName;
		this.isComplete = isComplete;
	}
	
	

	public UserProfile() {
		super();
	}



	public String getId() {
		return id;
	}

	public void setId(String id) {
		this.id = id;
	}

	public User getUser() {
		return user;
	}

	public void setUser(User user) {
		this.user = user;
	}

	public String getPhoneNumber() {
		return phoneNumber;
	}

	public void setPhoneNumber(String phoneNumber) {
		this.phoneNumber = phoneNumber;
	}

	public String getAddress() {
		return address;
	}

	public void setAddress(String address) {
		this.address = address;
	}

	public String getEducation() {
		return education;
	}

	public void setEducation(String education) {
		this.education = education;
	}

	public String getJobTitle() {
		return jobTitle;
	}

	public void setJobTitle(String jobTitle) {
		this.jobTitle = jobTitle;
	}

	public String getCompany() {
		return company;
	}

	public void setCompany(String company) {
		this.company = company;
	}

	public byte[] getCvData() {
		return cvData;
	}

	public void setCvData(byte[] cvData) {
		this.cvData = cvData;
	}

	public String getCvName() {
		return cvName;
	}

	public void setCvName(String cvName) {
		this.cvName = cvName;
	}

	public boolean isComplete() {
		return isComplete;
	}

	public void setComplete(boolean isComplete) {
		this.isComplete = isComplete;
	}

	

	

    
	
    
    
}
