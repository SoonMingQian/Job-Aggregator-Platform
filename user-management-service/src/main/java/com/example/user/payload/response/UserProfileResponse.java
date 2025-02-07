package com.example.user.payload.response;

import lombok.Data;

@Data
public class UserProfileResponse {
	private String userId;
	private String firstName;
	private String lastName;
	private String email;
	private ProfileDetails profile;

	// Main class getters and setters
	public String getUserId() {
		return userId;
	}

	public void setUserId(String userId) {
		this.userId = userId;
	}

	public String getFirstName() {
		return firstName;
	}

	public void setFirstName(String firstName) {
		this.firstName = firstName;
	}

	public String getLastName() {
		return lastName;
	}

	public void setLastName(String lastName) {
		this.lastName = lastName;
	}

	public String getEmail() {
		return email;
	}

	public void setEmail(String email) {
		this.email = email;
	}

	public ProfileDetails getProfile() {
		return profile;
	}

	public void setProfile(ProfileDetails profile) {
		this.profile = profile;
	}

	public static class ProfileDetails {
		private String phoneNumber;
		private String address;
		private String education;
		private String jobTitle;
		private String company;
		private String cvName;

		// ProfileDetails getters and setters
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

		public String getCvName() {
			return cvName;
		}

		public void setCvName(String cvName) {
			this.cvName = cvName;
		}
	}

}
