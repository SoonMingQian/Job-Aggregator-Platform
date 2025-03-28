package com.example.user.repositories;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

import com.example.user.models.User;

public interface UserRepository extends JpaRepository<User, String> {

	Optional<User> findOptionalByEmail(String email);
	
	Boolean existsByEmail(String email);
	
	User findByEmail(String email);
}
