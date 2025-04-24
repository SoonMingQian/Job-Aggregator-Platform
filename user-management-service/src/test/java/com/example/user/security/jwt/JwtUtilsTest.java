package com.example.user.security.jwt;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.test.util.ReflectionTestUtils;

import com.example.user.security.service.UserDetailsImpl;

@ExtendWith(MockitoExtension.class)
public class JwtUtilsTest {

    @InjectMocks
    private JwtUtils jwtUtils;
    
    @Mock
    private Authentication authentication;
    
    private UserDetailsImpl userDetails;
    
    @BeforeEach
    public void setup() {
        // Set JWT secret and expiration via reflection (normally from application.properties)
        ReflectionTestUtils.setField(jwtUtils, "jwtSecret", "testSecretKeyTestSecretKeyTestSecretKeyTestSecretKey");
        ReflectionTestUtils.setField(jwtUtils, "jwtExpirationMs", 86400000); // 24 hours
        
        // Create user details
        Collection<GrantedAuthority> authorities = new ArrayList<>();
        authorities.add(() -> "ROLE_USER");
        
        userDetails = new UserDetailsImpl(
            "user123", 
            "Test", 
            "User", 
            "test@example.com",
            "password", 
            authorities
        );
    }
    
    @Test
    public void testGenerateAndValidateJwtToken() {
        // Arrange
        when(authentication.getPrincipal()).thenReturn(userDetails);
        
        // Act
        String jwtToken = jwtUtils.generateJwtToken(authentication);
        boolean isValid = jwtUtils.validateJwtToken(jwtToken);
        
        // Assert
        assertNotNull(jwtToken);
        assertTrue(isValid);
        
        // Verify
        verify(authentication).getPrincipal();
    }
    
    @Test
    public void testGetUserNameFromJwtToken() {
        // Arrange
        when(authentication.getPrincipal()).thenReturn(userDetails);
        String jwtToken = jwtUtils.generateJwtToken(authentication);
        
        // Act
        String email = jwtUtils.getUserNameFromJwtToken(jwtToken);
        
        // Assert
        assertEquals("test@example.com", email);
    }
    
    @Test
    public void testValidateJwtToken_InvalidToken() {
        // Arrange
        String invalidToken = "invalid.jwt.token";
        
        // Act
        boolean isValid = jwtUtils.validateJwtToken(invalidToken);
        
        // Assert
        assertFalse(isValid);
    }
    
    @Test
    public void testValidateJwtToken_EmptyToken() {
        // Act & Assert
        assertFalse(jwtUtils.validateJwtToken(""));
        assertFalse(jwtUtils.validateJwtToken(null));
    }
}