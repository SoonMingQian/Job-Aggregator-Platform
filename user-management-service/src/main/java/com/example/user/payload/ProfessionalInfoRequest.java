package com.example.user.payload;

public class ProfessionalInfoRequest {

	private String jobTitle;
    private String company;
    private String education;

    // Getters and Setters
    public String getJobTitle() { return jobTitle; }
    public void setJobTitle(String jobTitle) { this.jobTitle = jobTitle; }
    
    public String getCompany() { return company; }
    public void setCompany(String company) { this.company = company; }
    
    public String getEducation() { return education; }
    public void setEducation(String education) { this.education = education; }
}
