package com.example.user.services;

import java.util.Calendar;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.example.user.models.PasswordResetToken;
import com.example.user.models.User;
import com.example.user.repositories.PasswordResetTokenRepository;

@Service
public class SecurityUserService {

	@Autowired
	private PasswordResetTokenRepository passwordResetTokenRepository;

	public String validatePasswordResetToken(String userId, String token) {
	    try {
	        PasswordResetToken passToken = passwordResetTokenRepository.findByToken(token);
	        
	        if (passToken == null) {
	            return "invalidToken";
	        }
	        
	        User user = passToken.getUser();
	        if (user == null || !user.getId().equals(userId)) {
	            return "invalidToken";
	        }
	        
	        // Check expiry date
	        if (passToken.getExpiryDate() == null) {
	            return "expiryDateNotFound";
	        }
	        
	        Calendar cal = Calendar.getInstance();
	        if ((passToken.getExpiryDate().getTime() - cal.getTime().getTime()) <= 0) {
	            passwordResetTokenRepository.delete(passToken);
	            return "expired";
	        }
	        
	        return null; // Valid token
	    } catch (Exception e) {
	        System.err.println("Error validating token: " + e.getMessage());
	        e.printStackTrace();
	        return "error: " + e.getMessage();
	    }
	}
}
