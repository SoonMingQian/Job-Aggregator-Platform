package com.example.user.controllers;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors;
import org.springframework.test.web.servlet.MockMvc;

import com.example.user.models.User;
import com.example.user.models.UserProfile;
import com.example.user.payload.PersonalInfoRequest;
import com.example.user.payload.ProfessionalInfoRequest;
import com.example.user.security.service.UserDetailsImpl;
import com.example.user.services.UserProfileService;
import com.fasterxml.jackson.databind.ObjectMapper;

@SpringBootTest
@AutoConfigureMockMvc
public class UserProfileControllerTest {

    @Autowired
    private MockMvc mockMvc;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    @MockBean
    private UserProfileService userProfileService;
    
    private User testUser;
    private UserProfile testProfile;
    private UserDetailsImpl userDetails;
    
    @BeforeEach
    public void setup() {
        // Set up test user
        testUser = new User();
        testUser.setId("user123");
        testUser.setEmail("test@example.com");
        testUser.setFirstName("Test");
        testUser.setLastName("User");

        // Set up test profile
        testProfile = new UserProfile();
        testProfile.setId("user123");
        testProfile.setUser(testUser);
        testProfile.setPhoneNumber("1234567890");
        testProfile.setAddress("Test Address");
        testProfile.setEducation("Test Education");
        testProfile.setJobTitle("Software Engineer");
        testProfile.setCompany("Test Company");
        
        // Create UserDetailsImpl
        userDetails = new UserDetailsImpl(
            testUser.getId(),
            testUser.getFirstName(),
            testUser.getLastName(),
            testUser.getEmail(),
            "password",
            java.util.Collections.emptyList()
        );
    }
    
    @Test
    @WithMockUser
    public void testGetUserProfile() throws Exception {
        // Mock behavior
        when(userProfileService.findProfileByUserId(any())).thenReturn(testProfile);
        
        // Perform request with authentication
        mockMvc.perform(get("/api/user/profile")
                .with(SecurityMockMvcRequestPostProcessors.user(userDetails)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.userId").value(testUser.getId()))
                .andExpect(jsonPath("$.firstName").value(testUser.getFirstName()))
                .andExpect(jsonPath("$.lastName").value(testUser.getLastName()))
                .andExpect(jsonPath("$.email").value(testUser.getEmail()))
                .andExpect(jsonPath("$.profile.phoneNumber").value(testProfile.getPhoneNumber()))
                .andExpect(jsonPath("$.profile.address").value(testProfile.getAddress()))
                .andExpect(jsonPath("$.profile.education").value(testProfile.getEducation()))
                .andExpect(jsonPath("$.profile.jobTitle").value(testProfile.getJobTitle()))
                .andExpect(jsonPath("$.profile.company").value(testProfile.getCompany()));
    }
    
    @Test
    @WithMockUser
    public void testUpdatePersonalInfo() throws Exception {
        // Create request
        PersonalInfoRequest request = new PersonalInfoRequest();
        request.setFirstName("Updated");
        request.setLastName("Name");
        
        // Mock behavior
        when(userProfileService.updatePersonalInfo(anyString(), anyString(), anyString())).thenReturn(testUser);
        
        // Perform request
        mockMvc.perform(put("/api/user/profile/personal")
                .with(SecurityMockMvcRequestPostProcessors.user(userDetails))
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("Personal information updated successfully"));
    }
    
    @Test
    @WithMockUser
    public void testUpdateProfessionalInfo() throws Exception {
        // Create request
        ProfessionalInfoRequest request = new ProfessionalInfoRequest();
        request.setJobTitle("Senior Developer");
        request.setCompany("New Company");
        request.setEducation("Masters Degree");
        
        // Mock behavior
        when(userProfileService.updateProfessionalInfo(anyString(), anyString(), anyString(), anyString()))
            .thenReturn(testProfile);
        
        // Perform request
        mockMvc.perform(put("/api/user/profile/professional")
                .with(SecurityMockMvcRequestPostProcessors.user(userDetails))
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("Professional information updated successfully"));
    }
    
    @Test
    @WithMockUser
    public void testCheckProfileStatus() throws Exception {
        // Mock behavior
        when(userProfileService.isProfileComplete(anyString())).thenReturn(true);
        
        // Perform request
        mockMvc.perform(get("/api/user/profile-status")
                .with(SecurityMockMvcRequestPostProcessors.user(userDetails)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("true"));
    }
}