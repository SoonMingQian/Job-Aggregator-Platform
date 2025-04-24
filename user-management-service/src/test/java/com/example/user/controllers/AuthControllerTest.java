package com.example.user.controllers;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.HashSet;
import java.util.Optional;
import java.util.Set;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.web.servlet.MockMvc;

import com.example.user.models.ERole;
import com.example.user.models.Role;
import com.example.user.models.User;
import com.example.user.payload.LoginRequest;
import com.example.user.payload.SignupRequest;
import com.example.user.repositories.RoleRepository;
import com.example.user.repositories.UserRepository;
import com.example.user.security.jwt.JwtUtils;
import com.example.user.security.service.UserDetailsImpl;
import com.example.user.services.OAuthService;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.Collections;

import org.springframework.context.annotation.Import;
import com.example.user.TestConfig;
import org.mockito.Mockito;

@SpringBootTest
@AutoConfigureMockMvc
@Import(TestConfig.class) // Add this line to import the test configuration
public class AuthControllerTest {

    @Autowired
    private MockMvc mockMvc;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    @MockBean
    private AuthenticationManager authenticationManager;
    
    @MockBean
    private UserRepository userRepository;
    
    @MockBean
    private RoleRepository roleRepository;
    
    @MockBean
    private PasswordEncoder encoder;
    
    @MockBean
    private JwtUtils jwtUtils;
    
    @MockBean
    private OAuthService oAuthService;
    
    private User testUser;
    private Role testRole;
    
    @BeforeEach
    public void setup() {
        // Create test user
        testUser = new User();
        testUser.setId("testuser123");
        testUser.setEmail("test@example.com");
        testUser.setFirstName("Test");
        testUser.setLastName("User");
        testUser.setPassword("encodedPassword");
        
        // Create test role
        testRole = new Role();
        testRole.setId(1);
        testRole.setName(ERole.ROLE_USER);
        
        // Set up user roles
        Set<Role> roles = new HashSet<>();
        roles.add(testRole);
        testUser.setRoles(roles);
    }
    
    @Test
    public void testLoginSuccess() throws Exception {
        // Create login request
        LoginRequest loginRequest = new LoginRequest();
        loginRequest.setEmail("test@example.com");
        loginRequest.setPassword("password123");
        
        // Create a mock Authentication instead of a real one
        Authentication authentication = Mockito.mock(Authentication.class);
        UserDetailsImpl userDetails = new UserDetailsImpl(
                testUser.getId(), 
                testUser.getFirstName(),
                testUser.getLastName(),
                testUser.getEmail(),
                testUser.getPassword(),
                Collections.singletonList(new org.springframework.security.core.authority.SimpleGrantedAuthority("ROLE_USER"))
        );
        
        // Set up mock behavior
        when(authentication.getPrincipal()).thenReturn(userDetails);
        when(authenticationManager.authenticate(any(UsernamePasswordAuthenticationToken.class)))
            .thenReturn(authentication);
        when(jwtUtils.generateJwtToken(authentication)).thenReturn("testJwtToken");
        when(userRepository.findOptionalByEmail("test@example.com")).thenReturn(Optional.of(testUser));
        
        // Perform login request
        mockMvc.perform(post("/api/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(loginRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.token").value("testJwtToken"))
                .andExpect(jsonPath("$.id").value(testUser.getId()))
                .andExpect(jsonPath("$.email").value(testUser.getEmail()));
    }
    
    @Test
    public void testRegisterUserSuccess() throws Exception {
        // Create signup request
        SignupRequest signupRequest = new SignupRequest();
        signupRequest.setEmail("new@example.com");
        signupRequest.setFirstName("New");
        signupRequest.setLastName("User");
        signupRequest.setPassword("password123");
        
        // Mock behavior
        when(userRepository.existsByEmail(signupRequest.getEmail())).thenReturn(false);
        when(roleRepository.findByName(ERole.ROLE_USER)).thenReturn(Optional.of(testRole));
        when(encoder.encode(signupRequest.getPassword())).thenReturn("encodedPassword");
        
        // Perform register request
        mockMvc.perform(post("/api/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(signupRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.message").value("User registered successfully!"));
    }
    
    @Test
    public void testRegisterUserDuplicateEmail() throws Exception {
        // Create signup request with existing email
        SignupRequest signupRequest = new SignupRequest();
        signupRequest.setEmail("test@example.com");
        signupRequest.setFirstName("Test");
        signupRequest.setLastName("User");
        signupRequest.setPassword("password123");
        
        // Mock behavior to simulate duplicate email
        when(userRepository.existsByEmail(signupRequest.getEmail())).thenReturn(true);
        
        // Perform register request
        mockMvc.perform(post("/api/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(signupRequest)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.message").value("Error: Username is already taken!"));
    }
}