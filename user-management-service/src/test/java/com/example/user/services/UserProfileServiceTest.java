package com.example.user.services;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.Optional;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.web.multipart.MultipartFile;

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
		testProfile.setId("profile123");
		testProfile.setId("user123");
		testProfile.setPhoneNumber("1234567890");
		testProfile.setAddress("Test Address");
		testProfile.setEducation("Test Education");
		testProfile.setJobTitle("Software Engineer");
		testProfile.setCompany("Test Company");

		// Set up test profile DTO
		testProfileDTO = new UserProfileDTO("1234567890", "Test Address", "Test Education", "Software Engineer",
				"Test Company");

		// Mock CV file
		when(mockCv.getOriginalFilename()).thenReturn("test_cv.pdf");
		when(mockCv.getContentType()).thenReturn("application/pdf");
	}

	@Test
	public void testFindProfileByUserId_ProfileExists() {
		// Arrange
		User testUser = new User(); // Create a test user with id "user123"
		testUser.setId("user123");

		when(userRepository.findById("user123")).thenReturn(Optional.of(testUser));
		when(userProfileRepository.findByUser(testUser)).thenReturn(Optional.of(testProfile));

		// Act
		UserProfile result = userProfileService.findProfileByUserId("user123");

		// Assert
		assertNotNull(result);
		assertEquals("user123", result.getId());
		assertEquals("1234567890", result.getPhoneNumber());

		// Verify
		verify(userRepository).findById("user123");
		verify(userProfileRepository).findByUser(testUser);
	}
}
