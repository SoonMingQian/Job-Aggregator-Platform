package com.example.user.repositories;

import org.springframework.data.jpa.repository.JpaRepository;

import com.example.user.models.PasswordResetToken;
import com.example.user.models.User;

public interface PasswordResetTokenRepository extends JpaRepository<PasswordResetToken, Long>{

	PasswordResetToken findByToken(String token);
	
	PasswordResetToken findByUser(User user);
}
