package com.example.user.services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

import com.example.user.exceptions.ResourceNotFoundException;
import com.example.user.models.User;
import com.example.user.models.UserProfile;
import com.example.user.payload.UserProfileDTO;
import com.example.user.repositories.UserProfileRepository;
import com.example.user.repositories.UserRepository;

import io.jsonwebtoken.io.IOException;

@Service
public class UserProfileService {

	@Autowired
	private UserProfileRepository userProfileRepository;

	@Autowired
	private PasswordEncoder passwordEncoder;

	@Autowired
	UserRepository userRepository;

	public UserProfile completeProfile(String userId, UserProfileDTO userProfileDTO, MultipartFile cv)
			throws IOException, Exception {
		User user = userRepository.findById(userId).orElseThrow(() -> new ResourceNotFoundException("User not found"));

		UserProfile profile = new UserProfile();
		profile.setUser(user);
		profile.setPhoneNumber(userProfileDTO.getPhoneNumber());
		profile.setAddress(userProfileDTO.getAddress());
		profile.setEducation(userProfileDTO.getEducation());
		profile.setJobTitle(userProfileDTO.getJobTitle());
		profile.setCompany(userProfileDTO.getCompany());
		profile.setCvData(cv.getBytes());
		profile.setCvName(cv.getOriginalFilename());
		profile.setComplete(true);

		return userProfileRepository.save(profile);
	}

	public boolean isProfileComplete(String userId) {
		User user = userRepository.findById(userId).orElseThrow(() -> new ResourceNotFoundException("User not found"));
		UserProfile profile = userProfileRepository.findByUser(user).orElse(null);

		return profile != null && profile.isComplete();
	}

	public UserProfile findProfileByUserId(String userId) {
		User user = userRepository.findById(userId).orElseThrow(() -> new ResourceNotFoundException("User not found"));

		return userProfileRepository.findByUser(user)
				.orElseThrow(() -> new ResourceNotFoundException("Profile not found for user"));
	}

	public User updatePersonalInfo(String userId, String firstName, String lastName) {
		User user = userRepository.findById(userId).orElseThrow(() -> new ResourceNotFoundException("User not found"));

		user.setFirstName(firstName);
		user.setLastName(lastName);

		return userRepository.save(user);
	}

	public UserProfile updateProfessionalInfo(String userId, String jobTitle, String company, String education) {
		User user = userRepository.findById(userId).orElseThrow(() -> new ResourceNotFoundException("User not found"));

		UserProfile profile = userProfileRepository.findByUser(user)
				.orElseThrow(() -> new ResourceNotFoundException("Profile not found"));

		profile.setJobTitle(jobTitle);
		profile.setCompany(company);
		profile.setEducation(education);

		return userProfileRepository.save(profile);
	}

	public UserProfile updateContactInfo(String userId, String phoneNumber, String address) {
		User user = userRepository.findById(userId).orElseThrow(() -> new ResourceNotFoundException("User not found"));

		UserProfile profile = userProfileRepository.findByUser(user)
				.orElseThrow(() -> new ResourceNotFoundException("Profile not found"));

		profile.setPhoneNumber(phoneNumber);
		profile.setAddress(address);

		return userProfileRepository.save(profile);
	}

	public UserProfile updateCV(String userId, MultipartFile cv) throws java.io.IOException {
		User user = userRepository.findById(userId).orElseThrow(() -> new ResourceNotFoundException("User not found"));

		UserProfile profile = userProfileRepository.findByUser(user)
				.orElseThrow(() -> new ResourceNotFoundException("Profile not found"));

		profile.setCvData(cv.getBytes());
		profile.setCvName(cv.getOriginalFilename());

		return userProfileRepository.save(profile);
	}

	public void changeUserPassword(User user, String newPassword) {
		System.out.println("Encoding password with BCryptPasswordEncoder");
		String encodedPassword = passwordEncoder.encode(newPassword);
		System.out.println("Password encoded, length: " + encodedPassword.length());
		user.setPassword(encodedPassword);
		userRepository.save(user);
		System.out.println("User saved with new password");

	}

	public User findUserByEmail(String userEmail) {
		return userRepository.findByEmail(userEmail);
	}
}
