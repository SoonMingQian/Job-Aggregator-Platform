package com.example.user.controllers;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.context.annotation.Import;

import com.example.user.TestConfig;
import com.example.user.models.PasswordResetToken;
import com.example.user.models.User;
import com.example.user.payload.PasswordDto;
import com.example.user.repositories.PasswordResetTokenRepository;
import com.example.user.services.SecurityUserService;
import com.example.user.services.UserProfileService;
import com.fasterxml.jackson.databind.ObjectMapper;

@SpringBootTest
@AutoConfigureMockMvc
@Import(TestConfig.class)
public class ChangePasswordControllerTest {

    @Autowired
    private MockMvc mockMvc;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    @MockBean
    private SecurityUserService securityUserService;
    
    @MockBean
    private UserProfileService userProfileService;
    
    @MockBean
    private PasswordResetTokenRepository passwordResetTokenRepository;
    
    private User testUser;
    private PasswordResetToken testToken;
    
    @BeforeEach
    public void setup() {
        testUser = new User();
        testUser.setId("user123");
        testUser.setEmail("test@example.com");
        testUser.setFirstName("Test");
        testUser.setLastName("User");
        
        testToken = new PasswordResetToken();
        testToken.setToken("valid-token-123");
        testToken.setUser(testUser);
    }
    
    @Test
    public void testSavePassword_Success() throws Exception {
        // Create password DTO
        PasswordDto passwordDto = new PasswordDto();
        passwordDto.setEmail("test@example.com");
        passwordDto.setToken("valid-token-123");
        passwordDto.setNewPassword("newPassword123");
        
        // Mock behavior
        when(passwordResetTokenRepository.findByToken("valid-token-123")).thenReturn(testToken);
        when(securityUserService.validatePasswordResetToken(testUser.getId(), "valid-token-123")).thenReturn(null); // null means valid
        doNothing().when(userProfileService).changeUserPassword(any(User.class), anyString());
        
        // Perform request
        mockMvc.perform(post("/api/user/savePassword")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(passwordDto)))
                .andExpect(status().isOk())
                .andExpect(content().string("Password successfully updated"));
    }
    
    @Test
    public void testSavePassword_InvalidToken() throws Exception {
        // Create password DTO
        PasswordDto passwordDto = new PasswordDto();
        passwordDto.setEmail("test@example.com");
        passwordDto.setToken("invalid-token");
        passwordDto.setNewPassword("newPassword123");
        
        // Mock behavior
        when(passwordResetTokenRepository.findByToken("invalid-token")).thenReturn(null);
        
        // Perform request
        mockMvc.perform(post("/api/user/savePassword")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(passwordDto)))
                .andExpect(status().isBadRequest())
                .andExpect(content().string("Error: Invalid token"));
    }
    
    @Test
    public void testSavePassword_ExpiredToken() throws Exception {
        // Create password DTO
        PasswordDto passwordDto = new PasswordDto();
        passwordDto.setEmail("test@example.com");
        passwordDto.setToken("expired-token");
        passwordDto.setNewPassword("newPassword123");
        
        // Mock behavior
        when(passwordResetTokenRepository.findByToken("expired-token")).thenReturn(testToken);
        when(securityUserService.validatePasswordResetToken(testUser.getId(), "expired-token")).thenReturn("expired");
        
        // Perform request
        mockMvc.perform(post("/api/user/savePassword")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(passwordDto)))
                .andExpect(status().isBadRequest())
                .andExpect(content().string("Error: Token has expired"));
    }
}