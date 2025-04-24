package com.example.user.services;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

import java.util.Optional;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.multipart.MultipartFile;

import com.example.user.exceptions.ResourceNotFoundException;
import com.example.user.models.User;
import com.example.user.models.UserProfile;
import com.example.user.payload.UserProfileDTO;
import com.example.user.repositories.UserProfileRepository;
import com.example.user.repositories.UserRepository;

@ExtendWith(MockitoExtension.class)
public class UserProfileServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private UserProfileRepository userProfileRepository;
    
    @Mock
    private PasswordEncoder passwordEncoder;

    @Mock
    private MultipartFile mockCv;

    @InjectMocks
    private UserProfileService userProfileService;

    private User testUser;
    private UserProfile testProfile;
    private UserProfileDTO testProfileDTO;

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
        testProfile.setComplete(true);

        // Set up test profile DTO
        testProfileDTO = new UserProfileDTO("1234567890", "Test Address", "Test Education", "Software Engineer",
                "Test Company");

    }

    @Test
    public void testFindProfileByUserId_ProfileExists() {
        // Arrange
        when(userRepository.findById("user123")).thenReturn(Optional.of(testUser));
        when(userProfileRepository.findByUser(testUser)).thenReturn(Optional.of(testProfile));

        // Act
        UserProfile result = userProfileService.findProfileByUserId("user123");

        // Assert
        assertNotNull(result);
        assertEquals("user123", result.getId());
        assertEquals("1234567890", result.getPhoneNumber());
        assertEquals("Test Address", result.getAddress());
        assertEquals("Test Education", result.getEducation());
        assertEquals("Software Engineer", result.getJobTitle());
        assertEquals("Test Company", result.getCompany());
        assertTrue(result.isComplete());

        // Verify
        verify(userRepository).findById("user123");
        verify(userProfileRepository).findByUser(testUser);
    }
    
    @Test
    public void testFindProfileByUserId_UserNotFound() {
        // Arrange
        when(userRepository.findById("nonexistent")).thenReturn(Optional.empty());

        // Act & Assert
        assertThrows(ResourceNotFoundException.class, () -> {
            userProfileService.findProfileByUserId("nonexistent");
        });
        
        // Verify
        verify(userRepository).findById("nonexistent");
        verify(userProfileRepository, never()).findByUser(any(User.class));
    }
    
    @Test
    public void testFindProfileByUserId_ProfileNotFound() {
        // Arrange
        when(userRepository.findById("user123")).thenReturn(Optional.of(testUser));
        when(userProfileRepository.findByUser(testUser)).thenReturn(Optional.empty());

        // Act & Assert
        assertThrows(ResourceNotFoundException.class, () -> {
            userProfileService.findProfileByUserId("user123");
        });
        
        // Verify
        verify(userRepository).findById("user123");
        verify(userProfileRepository).findByUser(testUser);
    }
    
    @Test
    public void testUpdatePersonalInfo() {
        // Arrange
        when(userRepository.findById("user123")).thenReturn(Optional.of(testUser));
        when(userRepository.save(any(User.class))).thenReturn(testUser);
        
        // Act
        User updatedUser = userProfileService.updatePersonalInfo("user123", "Updated", "Name");
        
        // Assert
        assertEquals("Updated", updatedUser.getFirstName());
        assertEquals("Name", updatedUser.getLastName());
        
        // Verify
        verify(userRepository).findById("user123");
        verify(userRepository).save(testUser);
    }
    
    @Test
    public void testUpdateProfessionalInfo() {
        // Arrange
        when(userRepository.findById("user123")).thenReturn(Optional.of(testUser));
        when(userProfileRepository.findByUser(testUser)).thenReturn(Optional.of(testProfile));
        when(userProfileRepository.save(any(UserProfile.class))).thenReturn(testProfile);
        
        // Act
        UserProfile updatedProfile = userProfileService.updateProfessionalInfo(
                "user123", "Senior Dev", "New Company", "Masters");
        
        // Assert
        assertEquals("Senior Dev", updatedProfile.getJobTitle());
        assertEquals("New Company", updatedProfile.getCompany());
        assertEquals("Masters", updatedProfile.getEducation());
        
        // Verify
        verify(userRepository).findById("user123");
        verify(userProfileRepository).findByUser(testUser);
        verify(userProfileRepository).save(testProfile);
    }
    
    @Test
    public void testChangeUserPassword() {
        // Arrange
        String newPassword = "newPassword123";
        String encodedPassword = "encodedPassword123";
        
        when(passwordEncoder.encode(newPassword)).thenReturn(encodedPassword);
        
        // Act
        userProfileService.changeUserPassword(testUser, newPassword);
        
        // Assert
        assertEquals(encodedPassword, testUser.getPassword());
        
        // Verify
        verify(passwordEncoder).encode(newPassword);
        verify(userRepository).save(testUser);
    }
}