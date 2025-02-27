package com.example.user.repositories;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

import com.example.user.models.ERole;
import com.example.user.models.Role;

public interface RoleRepository extends JpaRepository<Role, Long> {

	Optional<Role> findByName(ERole name);
	
	boolean existsByName(ERole name);
}
