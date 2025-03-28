package com.example.user.controllers;

import java.util.Optional;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.user.models.PasswordResetToken;
import com.example.user.models.User;
import com.example.user.payload.LoginRequest;
import com.example.user.payload.PasswordDto;
import com.example.user.repositories.PasswordResetTokenRepository;
import com.example.user.repositories.UserRepository;
import com.example.user.services.SecurityUserService;
import com.example.user.services.UserProfileService;
import org.springframework.security.crypto.password.PasswordEncoder;

@RestController
@CrossOrigin(origins = "*")
@RequestMapping("/api")
public class ChangePasswordController {

	@Autowired
	private PasswordResetTokenRepository passwordResetTokenRepository;

	@Autowired
	private SecurityUserService securityUserService;

	@Autowired
	private UserProfileService userProfileService;

	@PostMapping("/user/savePassword")
	public ResponseEntity<?> savePassword(@RequestBody PasswordDto passwordDto) {
	    System.out.println("Processing password reset for email: " + passwordDto.getEmail());
	    System.out.println("With token: " + passwordDto.getToken());
	    
	    try {
	        // Find the token
	        PasswordResetToken token = passwordResetTokenRepository.findByToken(passwordDto.getToken());
	        if (token == null) {
	            System.out.println("Token not found: " + passwordDto.getToken());
	            return new ResponseEntity<>("Error: Invalid token", HttpStatus.BAD_REQUEST);
	        }
	        
	        // Find the user
	        User user = token.getUser();
	        if (user == null) {
	            System.out.println("No user associated with token");
	            return new ResponseEntity<>("Error: Invalid token - no user associated", HttpStatus.BAD_REQUEST);
	        }
	        
	        System.out.println("Found user with ID: " + user.getId() + ", email: " + user.getEmail());
	        
	        if (!user.getEmail().equals(passwordDto.getEmail())) {
	            System.out.println("Email mismatch: token for " + user.getEmail() + 
	                              " but request for " + passwordDto.getEmail());
	            return new ResponseEntity<>("Error: No user found with email " + passwordDto.getEmail(),
	                    HttpStatus.NOT_FOUND);
	        }
	        
	        // Check token validity - FIXED: no parsing to Long
	        String result = securityUserService.validatePasswordResetToken(user.getId(), passwordDto.getToken());
	        if (result != null) {
	            System.out.println("Token validation failed: " + result);
	            
	            if (result.equals("expired")) {
	                return new ResponseEntity<>("Error: Token has expired", HttpStatus.BAD_REQUEST);
	            } else if (result.equals("invalidToken")) {
	                return new ResponseEntity<>("Error: Invalid token", HttpStatus.BAD_REQUEST);
	            } else {
	                return new ResponseEntity<>("Error: " + result, HttpStatus.BAD_REQUEST);
	            }
	        }
	        
	        // Change the password
	        System.out.println("Changing password for user: " + user.getEmail());
	        userProfileService.changeUserPassword(user, passwordDto.getNewPassword());
	        
	        // Delete the used token
	        passwordResetTokenRepository.delete(token);
	        System.out.println("Password successfully changed and token deleted");
	        
	        return ResponseEntity.ok("Password successfully updated");
	    } catch (Exception e) {
	        System.err.println("Error updating password: " + e.getMessage());
	        e.printStackTrace();
	        return new ResponseEntity<>("Error updating password: " + e.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR);
	    }
	}
}
