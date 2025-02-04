package com.example.user.controllers;

import java.util.HashMap;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.example.user.models.UserProfile;
import com.example.user.payload.UserProfileDTO;
import com.example.user.payload.response.MessageResponse;
import com.example.user.security.service.UserDetailsImpl;
import com.example.user.services.UserProfileService;

@CrossOrigin(origins = "*")
@RestController
@RequestMapping("/api/user")
public class UserProfileController {

	@Autowired
	private UserProfileService userProfileService;

	@PostMapping("/complete-profile")
	public ResponseEntity<?> completeProfile(
			 	@RequestParam("phoneNumber") String phoneNumber,
	            @RequestParam("address") String address,
	            @RequestParam("education") String education,
	            @RequestParam("jobTitle") String jobTitle,
	            @RequestParam("company") String company,
	            @RequestParam("cv") MultipartFile cv,
	            @AuthenticationPrincipal UserDetailsImpl userDetails) {
		
		try {
			UserProfileDTO profileDTO = new UserProfileDTO(
					phoneNumber,
					address,
					education,
					jobTitle,
					company
			);
			
			UserProfile profile = userProfileService.completeProfile(userDetails.getId(), profileDTO, cv);
			Map<String, String> response = new HashMap<>();
	        response.put("message", "Profile completed successfully");
	        response.put("userId", userDetails.getId());
	        
	        return ResponseEntity.ok(response);	
		} catch (Exception e) {
			return ResponseEntity.badRequest()
                    .body(new MessageResponse("Error: " + e.getMessage()));
		}
	}
	
	@GetMapping("/profile-status")
	public ResponseEntity<?> checkProfileStatus(@AuthenticationPrincipal UserDetailsImpl userDetails) {
		try {
			boolean isComplete = userProfileService.isProfileComplete(userDetails.getId());
			return ResponseEntity.ok(new MessageResponse(String.valueOf(isComplete)));
		} catch (Exception e) {
			return ResponseEntity.badRequest()
					.body(new MessageResponse("Error: " + e.getMessage()));
		}
	}
	
	@GetMapping("/profile")
	public ResponseEntity<?> getCurrentUserProfile(@AuthenticationPrincipal UserDetailsImpl userDetails) {
		try {
			UserProfile profile = userProfileService.findProfileByUserId(userDetails.getId());
			Map<String, String> response = new HashMap<>();
	        response.put("userId", userDetails.getId());
	        return ResponseEntity.ok(response);
		} catch (Exception e) {
	        return ResponseEntity.badRequest()
	                .body(new MessageResponse("Error: " + e.getMessage()));
	    }
	}
}
