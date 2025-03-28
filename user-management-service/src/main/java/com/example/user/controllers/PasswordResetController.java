package com.example.user.controllers;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.user.models.PasswordResetToken;
import com.example.user.models.User;
import com.example.user.repositories.UserRepository;
import com.example.user.services.PasswordResetService;
import com.example.user.services.UserProfileService;

import jakarta.servlet.http.HttpServletRequest;

@RestController
@CrossOrigin(origins = "*")
@RequestMapping("/api")
public class PasswordResetController {

	@Autowired
	private PasswordResetService passwordResetService;

	@Autowired
	private UserProfileService userProfileService;

	@Autowired
	private UserRepository userRepository;

	@PostMapping("/reset-password")
	public ResponseEntity<?> resetPassword(HttpServletRequest request, @RequestParam("email") String userEmail) {
		try {
			User user = userProfileService.findUserByEmail(userEmail);
			if (user == null) {
				// Log the exact email that was used for debugging
				System.out.println("Failed password reset attempt for email: " + userEmail);
				return ResponseEntity.status(HttpStatus.NOT_FOUND)
						.body("We couldn't find an account with that email address.");
			}

			// Generate a unique token
			String token = UUID.randomUUID().toString();
			passwordResetService.createPasswordResetTokenForUser(user, token);
			// Get the application URL
			String appUrl = getAppUrl(request);
			passwordResetService.sendPasswordResetEmail(appUrl, request.getLocale(), token, user);

			return ResponseEntity
					.ok("We've sent an email to " + userEmail + " with further instructions to reset your password.");
		} catch (Exception e) {
			// Log the exception for debugging
			e.printStackTrace();
			return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
					.body("An error occurred during the password reset process: " + e.getMessage());
		}
	}

	// Add to PasswordResetController
	@PostMapping("/resend-reset-token")
	public ResponseEntity<?> resendResetToken(HttpServletRequest request, @RequestParam("email") String userEmail) {
		try {
			User user = userProfileService.findUserByEmail(userEmail);
			if (user == null) {
				System.out.println("Failed token resend attempt for email: " + userEmail);
				return ResponseEntity.status(HttpStatus.NOT_FOUND)
						.body("We couldn't find an account with that email address.");
			}

			// Generate a new token (this will replace any existing token)
			String token = UUID.randomUUID().toString();
			passwordResetService.createPasswordResetTokenForUser(user, token);

			// Get the application URL
			String appUrl = getAppUrl(request);
			passwordResetService.sendPasswordResetEmail(appUrl, request.getLocale(), token, user);

			return ResponseEntity
					.ok("We've sent a new email to " + userEmail + " with instructions to reset your password.");
		} catch (Exception e) {
			e.printStackTrace();
			return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
					.body("An error occurred while resending the reset token: " + e.getMessage());
		}
	}

	@GetMapping("/test/get-reset-token")
	public ResponseEntity<?> getResetToken(@RequestParam("email") String email) {
		try {
			// Find the user
			User user = userProfileService.findUserByEmail(email);
			if (user == null) {
				return ResponseEntity.status(HttpStatus.NOT_FOUND)
						.body("User not found with email: " + email);
			}

			// Get the token for this user
			PasswordResetToken token = passwordResetService.getPasswordResetToken(user);
			if (token == null) {
				return ResponseEntity.status(HttpStatus.NOT_FOUND)
						.body("No token found for user. Please request a password reset first.");
			}

			return ResponseEntity.ok("Token: " + token.getToken());
		} catch (Exception e) {
			e.printStackTrace();
			return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
					.body("Error retrieving token: " + e.getMessage());
		}
	}

	private String getAppUrl(HttpServletRequest request) {
		return "http://localhost:8081";
	}
}
