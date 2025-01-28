package com.example.user.payload;

public class UserProfileDTO {
	private String phoneNumber;
    private String address;
    private String education;
    private String jobTitle;
    private String company;
    
    
	public UserProfileDTO(String phoneNumber, String address, String education, String jobTitle, String company) {
		super();
		this.phoneNumber = phoneNumber;
		this.address = address;
		this.education = education;
		this.jobTitle = jobTitle;
		this.company = company;
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
    
    
}
