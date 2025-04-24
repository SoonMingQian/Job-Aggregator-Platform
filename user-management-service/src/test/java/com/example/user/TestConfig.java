package com.example.user;

import org.mockito.Mockito;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.test.util.ReflectionTestUtils;

import com.example.user.security.jwt.JwtUtils;
import com.example.user.services.EmailService;
import com.example.user.services.PasswordResetService;

@TestConfiguration
public class TestConfig {

    @Bean
    public JavaMailSender javaMailSender() {
        return Mockito.mock(JavaMailSender.class);
    }
    
    @Bean
    public EmailService emailService() {
        return Mockito.mock(EmailService.class);
    }
    
    @Bean
    public PasswordResetService passwordResetService() {
        return Mockito.mock(PasswordResetService.class);
    }
    
    @Bean
    public JwtUtils jwtUtils() {
        JwtUtils jwtUtils = new JwtUtils();
        ReflectionTestUtils.setField(jwtUtils, "jwtSecret", 
                "testSecretKeyHasToBeVeryLongForAlgorithmSecurity123456789");
        ReflectionTestUtils.setField(jwtUtils, "jwtExpirationMs", 86400000);
        return jwtUtils;
    }
}