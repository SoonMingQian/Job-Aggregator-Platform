package com.example.user.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import com.example.user.models.ERole;
import com.example.user.models.Role;
import com.example.user.repositories.RoleRepository;

@Component
public class RoleInitializer implements CommandLineRunner {

	private static final Logger logger = LoggerFactory.getLogger(RoleInitializer.class);
	
	@Autowired
    private RoleRepository roleRepository;
	
	public void run(String... args) {
		logger.info("Initializing roles...");
		
		// Check if ROLE_USER exists
        if (!roleRepository.existsByName(ERole.ROLE_USER)) {
            logger.info("Creating ROLE_USER");
            roleRepository.save(new Role(ERole.ROLE_USER));
        }
        
        // Check if ROLE_ADMIN exists (if you added it)
        if (!roleRepository.existsByName(ERole.ROLE_ADMIN)) {
            logger.info("Creating ROLE_ADMIN");
            roleRepository.save(new Role(ERole.ROLE_ADMIN));
        }
        
        logger.info("Role initialization completed");
	}
}
