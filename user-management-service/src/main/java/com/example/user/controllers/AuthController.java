package com.example.user.controllers;

import java.io.IOException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.user.models.ERole;
import com.example.user.models.Role;
import com.example.user.models.User;
import com.example.user.payload.LoginRequest;
import com.example.user.payload.SignupRequest;
import com.example.user.payload.response.JwtResponse;
import com.example.user.payload.response.MessageResponse;
import com.example.user.repositories.RoleRepository;
import com.example.user.repositories.UserRepository;
import com.example.user.security.jwt.JwtUtils;
import com.example.user.security.service.UserDetailsImpl;
import com.example.user.services.OAuthService;
import com.google.gson.JsonObject;

import jakarta.servlet.http.HttpServletResponse;

@CrossOrigin(origins = "*")
@RestController
@RequestMapping("/api/auth")
public class AuthController {
	private static final Logger logger = LoggerFactory.getLogger(AuthController.class);

	@Autowired
	AuthenticationManager authenticationManager;

	@Autowired
	UserRepository userRepository;

	@Autowired
	RoleRepository roleRepository;

	@Autowired
	PasswordEncoder encoder;

	@Autowired
	JwtUtils jwtUtils;

	@Autowired
	OAuthService oAuthService;

	@PostMapping("/login")
	public ResponseEntity<?> authenticateUser(@RequestBody LoginRequest loginRequest) {
		// Authentication process
		Authentication authentication = authenticationManager.authenticate(
				new UsernamePasswordAuthenticationToken(loginRequest.getEmail(), loginRequest.getPassword()));

		UserDetailsImpl userDetailss = (UserDetailsImpl) authentication.getPrincipal();

		// Check user status
		Optional<User> optionalUser = userRepository.findOptionalByEmail(userDetailss.getEmail());
		if (!optionalUser.isPresent()) {
			throw new RuntimeException("Error: User not found.");
		}

		// Set authentication in SecurityContextHolder
		SecurityContextHolder.getContext().setAuthentication(authentication);
		String jwt = jwtUtils.generateJwtToken(authentication);

		// Get user details and roles
		UserDetailsImpl userDetails = (UserDetailsImpl) authentication.getPrincipal();
		List<String> roles = userDetails.getAuthorities().stream().map(item -> item.getAuthority())
				.collect(Collectors.toList());

		// Respond with JWT and user details
		return ResponseEntity.ok(new JwtResponse(jwt, userDetails.getId(), userDetails.getEmail(), roles));
	}

	@PostMapping("/register")
	public ResponseEntity<?> registerUser(@RequestBody SignupRequest signUpRequest) {
		// Check if email already exists
		if (userRepository.existsByEmail(signUpRequest.getEmail())) {
			return ResponseEntity.badRequest().body(new MessageResponse("Error: Username is already taken!"));
		}

		// Create new user's account
		if (userRepository.existsByEmail(signUpRequest.getEmail())) {
			return ResponseEntity.badRequest().body(new MessageResponse("Error: Email is already in use!"));
		}

		// Create new user's account
		User user = new User(signUpRequest.getFirstName(), signUpRequest.getLastName(), signUpRequest.getEmail(),
				encoder.encode(signUpRequest.getPassword()));

		Set<String> strRoles = signUpRequest.getRole();
		System.out.println(strRoles);
		Set<Role> roles = new HashSet<>();

		// Assign roles based on signup request
		if (strRoles == null) {
			Role userRole = roleRepository.findByName(ERole.ROLE_USER)
					.orElseThrow(() -> new RuntimeException("Error: Role is not found."));
			roles.add(userRole);
		}

		user.setRoles(roles);
		userRepository.save(user);

		return ResponseEntity.ok(new MessageResponse("User registered successfully!"));
	}

	@GetMapping("/grantcode")
	public void handleGoogleCallback(@RequestParam("code") String code, HttpServletResponse response) throws IOException {
		try {
			JsonObject googleUser = oAuthService.handleGoogleAuth(code);
			String email = googleUser.get("email").getAsString();

			User user;
			String googlePassword = "GOOGLE_AUTH_" + email; // Create consistent password for Google users

			if (!userRepository.existsByEmail(email)) {
				// Create new user if doesn't exist
				user = new User();
				user.setEmail(email);
				user.setPassword(encoder.encode(java.util.UUID.randomUUID().toString()));

				if (googleUser.has("given_name")) {
					user.setFirstName(googleUser.get("given_name").getAsString());
				}
				if (googleUser.has("family_name")) {
					user.setLastName(googleUser.get("family_name").getAsString());
				}

				Set<Role> roles = new HashSet<>();
				Role userRole = roleRepository.findByName(ERole.ROLE_USER)
						.orElseThrow(() -> new RuntimeException("Error: Role is not found."));
				roles.add(userRole);
				user.setRoles(roles);

				user = userRepository.save(user);
			} else {
				user = userRepository.findOptionalByEmail(email)
						.orElseThrow(() -> new RuntimeException("Error: User not found."));
			}

			// Create UserDetails directly without password authentication
	        UserDetailsImpl userDetails = UserDetailsImpl.build(user);
	        
	        // Create authentication token without password verification
	        Authentication authentication = new UsernamePasswordAuthenticationToken(
	            userDetails,
	            null,
	            userDetails.getAuthorities()
	        );

			SecurityContextHolder.getContext().setAuthentication(authentication);
			String jwt = jwtUtils.generateJwtToken(authentication);

			List<String> roles = userDetails.getAuthorities().stream().map(item -> item.getAuthority())
					.collect(Collectors.toList());

			// Redirect to frontend with token
	        String redirectUrl = String.format("http://localhost:5173/oauth/callback?token=%s&email=%s",
	                URLEncoder.encode(jwt, StandardCharsets.UTF_8),
	                URLEncoder.encode(userDetails.getEmail(), StandardCharsets.UTF_8));
	        
	        response.sendRedirect(redirectUrl);

		} catch (Exception e) {
			logger.error("Error in Google callback: ", e);
	        response.sendRedirect("http://localhost:5173/?error=" + 
	            URLEncoder.encode("Authentication failed", StandardCharsets.UTF_8));
		}
	}
}