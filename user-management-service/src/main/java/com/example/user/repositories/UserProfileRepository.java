package com.example.user.repositories;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

import com.example.user.models.User;
import com.example.user.models.UserProfile;

public interface UserProfileRepository extends JpaRepository<UserProfile, String>{
	Optional<UserProfile> findByUser(User user);
}
