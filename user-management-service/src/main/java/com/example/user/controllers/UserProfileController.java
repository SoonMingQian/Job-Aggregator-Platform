package com.example.user.controllers;

import java.util.HashMap;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.example.user.models.User;
import com.example.user.models.UserProfile;
import com.example.user.payload.ContactInfoRequest;
import com.example.user.payload.PersonalInfoRequest;
import com.example.user.payload.ProfessionalInfoRequest;
import com.example.user.payload.UserProfileDTO;
import com.example.user.payload.response.CVUpdateResponse;
import com.example.user.payload.response.MessageResponse;
import com.example.user.payload.response.UserProfileResponse;
import com.example.user.security.service.UserDetailsImpl;
import com.example.user.services.UserProfileService;

@CrossOrigin(origins = "*")
@RestController
@RequestMapping("/api/user")
public class UserProfileController {

	@Autowired
	private UserProfileService userProfileService;

	@PostMapping("/complete-profile")
	public ResponseEntity<?> completeProfile(@RequestParam("phoneNumber") String phoneNumber,
			@RequestParam("address") String address, @RequestParam("education") String education,
			@RequestParam("jobTitle") String jobTitle, @RequestParam("company") String company,
			@RequestParam("cv") MultipartFile cv, @AuthenticationPrincipal UserDetailsImpl userDetails) {

		try {
			UserProfileDTO profileDTO = new UserProfileDTO(phoneNumber, address, education, jobTitle, company);

			UserProfile profile = userProfileService.completeProfile(userDetails.getId(), profileDTO, cv);
			Map<String, String> response = new HashMap<>();
			response.put("message", "Profile completed successfully");
			response.put("userId", userDetails.getId());

			return ResponseEntity.ok(response);
		} catch (Exception e) {
			return ResponseEntity.badRequest().body(new MessageResponse("Error: " + e.getMessage()));
		}
	}

	@GetMapping("/profile-status")
	public ResponseEntity<?> checkProfileStatus(@AuthenticationPrincipal UserDetailsImpl userDetails) {
		try {
			boolean isComplete = userProfileService.isProfileComplete(userDetails.getId());
			return ResponseEntity.ok(new MessageResponse(String.valueOf(isComplete)));
		} catch (Exception e) {
			return ResponseEntity.badRequest().body(new MessageResponse("Error: " + e.getMessage()));
		}
	}

	@GetMapping("/userId")
	public ResponseEntity<?> getCurrentUserProfile(@AuthenticationPrincipal UserDetailsImpl userDetails) {
		try {
			UserProfile profile = userProfileService.findProfileByUserId(userDetails.getId());
			Map<String, String> response = new HashMap<>();
			response.put("userId", userDetails.getId());
			return ResponseEntity.ok(response);
		} catch (Exception e) {
			return ResponseEntity.badRequest().body(new MessageResponse("Error: " + e.getMessage()));
		}
	}

	@GetMapping("/profile")
	public ResponseEntity<?> getUserProfile(@AuthenticationPrincipal UserDetailsImpl userDetails) {
		try {
			UserProfile profile = userProfileService.findProfileByUserId(userDetails.getId());
			UserProfileResponse response = new UserProfileResponse();

			// Set user details
			response.setUserId(userDetails.getId());
			response.setFirstName(userDetails.getFirstName());
			response.setLastName(userDetails.getLastName());
			response.setEmail(userDetails.getEmail());

			// Set profile details
			UserProfileResponse.ProfileDetails profileDetails = new UserProfileResponse.ProfileDetails();
			profileDetails.setPhoneNumber(profile.getPhoneNumber());
			profileDetails.setAddress(profile.getAddress());
			profileDetails.setEducation(profile.getEducation());
			profileDetails.setJobTitle(profile.getJobTitle());
			profileDetails.setCompany(profile.getCompany());
			profileDetails.setCvName(profile.getCvName());

			response.setProfile(profileDetails);

			return ResponseEntity.ok(response);
		} catch (Exception e) {
			return ResponseEntity.badRequest().body(new MessageResponse("Error: " + e.getMessage()));
		}
	}

	@PutMapping("/profile/personal")
	public ResponseEntity<?> updatePersonalInfo(@AuthenticationPrincipal UserDetailsImpl userDetails,
			@RequestBody PersonalInfoRequest request) {
		try {
			User updateUser = userProfileService.updatePersonalInfo(userDetails.getId(), request.getFirstName(),
					request.getLastName());
			return ResponseEntity.ok(new MessageResponse("Personal information updated successfully"));
		} catch (Exception e) {
			return ResponseEntity.badRequest().body(new MessageResponse("Error: " + e.getMessage()));
		}
	}

	@PutMapping("/profile/professional")
	public ResponseEntity<?> updateProfessionalInfo(@AuthenticationPrincipal UserDetailsImpl userDetails,
			@RequestBody ProfessionalInfoRequest request) {
		try {
			UserProfile updatedProfile = userProfileService.updateProfessionalInfo(userDetails.getId(),
					request.getJobTitle(), request.getCompany(), request.getEducation());

			return ResponseEntity.ok(new MessageResponse("Professional information updated successfully"));
		} catch (Exception e) {
			return ResponseEntity.badRequest().body(new MessageResponse("Error: " + e.getMessage()));
		}
	}

	@PutMapping("/profile/contact")
	public ResponseEntity<?> updateProfessionalInfo(@AuthenticationPrincipal UserDetailsImpl userDetails,
			@RequestBody ContactInfoRequest request) {
		try {
			UserProfile updatedProfile = userProfileService.updateContactInfo(userDetails.getId(),
					request.getPhoneNumber(), request.getAddress());

			return ResponseEntity.ok(new MessageResponse("Contact information updated successfully"));
		} catch (Exception e) {
			return ResponseEntity.badRequest().body(new MessageResponse("Error: " + e.getMessage()));
		}
	}

	@PutMapping("/profile/cv")
	public ResponseEntity<?> updateCV(@AuthenticationPrincipal UserDetailsImpl userDetails,
			@RequestParam("cv") MultipartFile cv) {
		try {
			if (cv.isEmpty()) {
				return ResponseEntity.badRequest().body(new MessageResponse("Error: Please select a file"));
			}

			String contentType = cv.getContentType();
			if (contentType == null || !(contentType.equals("application/pdf"))) {
				return ResponseEntity.badRequest().body(new MessageResponse("Error: Only PDF document is allowed"));
			}

			UserProfile updateProfile = userProfileService.updateCV(userDetails.getId(), cv);
			
			return ResponseEntity.ok(new CVUpdateResponse("CV updated successfully", userDetails.getId()));
		} catch (Exception e) {
			return ResponseEntity.badRequest().body(new MessageResponse("Error: " + e.getMessage()));
		}
	}
}
