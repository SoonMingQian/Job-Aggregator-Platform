package com.example.user.services;

import java.util.Calendar;
import java.util.Date;
import java.util.Locale;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.stereotype.Service;

import com.example.user.models.PasswordResetToken;
import com.example.user.models.User;
import com.example.user.repositories.PasswordResetTokenRepository;

@Service
public class PasswordResetService {

    @Autowired
    private PasswordResetTokenRepository passwordResetTokenRepository;
    
    @Autowired
    private EmailService emailService;
    
    public void createPasswordResetTokenForUser(User user, String token) {
        try {
            // First check if a token already exists for this user
            PasswordResetToken existingToken = passwordResetTokenRepository.findByUser(user);
            if (existingToken != null) {
                // Delete the existing token
                passwordResetTokenRepository.delete(existingToken);
            }
            
            // Create a new token with expiry date
            PasswordResetToken myToken = new PasswordResetToken(token, user);
            
            // Add extra logging to debug
            System.out.println("Creating token: " + token + " for user: " + user.getEmail());
            System.out.println("Token expiry date: " + myToken.getExpiryDate());
            
            passwordResetTokenRepository.save(myToken);
        } catch (Exception e) {
            System.err.println("Error creating password reset token: " + e.getMessage());
            e.printStackTrace();
            throw e;
        }
    }
    
    public void sendPasswordResetEmail(String appUrl, Locale locale, String token, User user) {
        try {
            // Create a direct reset URL
            String resetUrl = appUrl + "/reset-password?token=" + token;
            
            // Create the email content directly without using message resources
            String subject = "Password Reset Request";
            String message = "Hello " + user.getFirstName() + ",\n\n" +
                    "You have requested to reset your password. \n\n" +
                    "Click the following link to reset your password: \n" +
                    resetUrl + "\n\n" +
                    "If you did not request a password reset, please ignore this email.\n\n" +
                    "This link will expire in 24 hours.\n\n" +
                    "Regards,\n" +
                    "Your Application Team";
            
            // For testing, print to console
            System.out.println("Password reset email would be sent to: " + user.getEmail());
            System.out.println("Subject: " + subject);
            System.out.println("Message: " + message);
            System.out.println("Reset URL: " + resetUrl);
            
            // Create a simple mail message
            SimpleMailMessage email = new SimpleMailMessage();
            email.setTo(user.getEmail());
            email.setSubject(subject);
            email.setText(message);
            
            // Send the email
            // Comment this out if you don't have email configured
            emailService.sendSimpleMessage(user.getEmail(), subject, message);
            
        } catch (Exception e) {
            System.err.println("Error sending password reset email: " + e.getMessage());
            e.printStackTrace();
            // Don't throw the exception to avoid breaking the password reset flow
        }
    }
    
    // Add this method to get the token for a user (for testing)
    public PasswordResetToken getPasswordResetToken(User user) {
        return passwordResetTokenRepository.findByUser(user);
    }
    
    public PasswordResetToken validatePasswordResetToken(String token) {
        PasswordResetToken passToken = passwordResetTokenRepository.findByToken(token);
        
        if (passToken == null) {
            return null;
        }
        
        Calendar cal = Calendar.getInstance();
        if ((passToken.getExpiryDate().getTime() - cal.getTime().getTime()) <= 0) {
            passwordResetTokenRepository.delete(passToken);
            return null;
        }
        
        return passToken;
    }
}
