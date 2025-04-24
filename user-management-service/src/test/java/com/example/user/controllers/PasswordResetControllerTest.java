package com.example.user.controllers;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.Locale;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import com.example.user.models.User;
import com.example.user.services.PasswordResetService;
import com.example.user.services.UserProfileService;

@SpringBootTest
@AutoConfigureMockMvc
public class PasswordResetControllerTest {

    @Autowired
    private MockMvc mockMvc;
    
    @MockBean
    private UserProfileService userProfileService;
    
    @MockBean
    private PasswordResetService passwordResetService;
    
    private User testUser;
    
    @BeforeEach
    public void setup() {
        testUser = new User();
        testUser.setId("user123");
        testUser.setEmail("test@example.com");
        testUser.setFirstName("Test");
        testUser.setLastName("User");
    }
    
    @Test
    public void testResetPasswordExistingUser() throws Exception {
        // Mock behavior
        when(userProfileService.findUserByEmail("test@example.com")).thenReturn(testUser);
        doNothing().when(passwordResetService).createPasswordResetTokenForUser(any(User.class), anyString());
        doNothing().when(passwordResetService).sendPasswordResetEmail(anyString(), any(Locale.class), anyString(), any(User.class));
        
        // Perform request
        mockMvc.perform(post("/api/reset-password")
                .param("email", "test@example.com"))
                .andExpect(status().isOk())
                .andExpect(content().string(
                        "We've sent an email to test@example.com with further instructions to reset your password."));
    }
    
    @Test
    public void testResetPasswordNonExistingUser() throws Exception {
        // Mock behavior for non-existent user
        when(userProfileService.findUserByEmail("nonexistent@example.com")).thenReturn(null);
        
        // Perform request
        mockMvc.perform(post("/api/reset-password")
                .param("email", "nonexistent@example.com"))
                .andExpect(status().isNotFound())
                .andExpect(content().string(
                        "We couldn't find an account with that email address."));
    }
    
    @Test
    public void testResendResetTokenExistingUser() throws Exception {
        // Mock behavior
        when(userProfileService.findUserByEmail("test@example.com")).thenReturn(testUser);
        doNothing().when(passwordResetService).createPasswordResetTokenForUser(any(User.class), anyString());
        doNothing().when(passwordResetService).sendPasswordResetEmail(anyString(), any(Locale.class), anyString(), any(User.class));
        
        // Perform request
        mockMvc.perform(post("/api/resend-reset-token")
                .param("email", "test@example.com"))
                .andExpect(status().isOk())
                .andExpect(content().string(
                        "We've sent a new email to test@example.com with instructions to reset your password."));
    }
}