package com.example.user.services;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import com.google.gson.Gson;
import com.google.gson.JsonObject;

import java.util.Collections;

@Service
public class OAuthService {

	private static final Logger logger = LoggerFactory.getLogger(OAuthService.class);

	@Value("${google.oauth2.client.id}")
	private String clientId;

	@Value("${google.oauth2.client.secret}")
	private String clientSecret;

	@Value("${google.oauth2.redirect.uri}")
	private String redirectUri;

	private String getOauthAccessTokenGoogle(String code) {
		logger.info("Attempting to get OAuth access token"); 
		try {
			RestTemplate restTemplate = new RestTemplate();
			HttpHeaders httpHeaders = new HttpHeaders();
			httpHeaders.setContentType(MediaType.APPLICATION_FORM_URLENCODED);
			httpHeaders.setAccept(Collections.singletonList(MediaType.APPLICATION_JSON));

			MultiValueMap<String, String> params = new LinkedMultiValueMap<>();
			params.add("code", code);
			params.add("redirect_uri", redirectUri);
			params.add("client_id", clientId);
			params.add("client_secret", clientSecret);
			params.add("grant_type", "authorization_code");

			HttpEntity<MultiValueMap<String, String>> requestEntity = new HttpEntity<>(params, httpHeaders);

			String url = "https://oauth2.googleapis.com/token";
			logger.info("Making token request with client_id: " + clientId.substring(0, 10) + "...");
			String response = restTemplate.postForObject(url, requestEntity, String.class);
			logger.info("Token request successful");
			return response;
		} catch (Exception e) {
			logger.error("Error getting OAuth token: " + e.getMessage(), e);  
	        throw e;
		}
		
	}

	private JsonObject getProfileDetailsGoogle(String accessToken) {
		try {
			RestTemplate restTemplate = new RestTemplate();
			HttpHeaders httpHeaders = new HttpHeaders();
			httpHeaders.setBearerAuth(accessToken);

			HttpEntity<String> requestEntity = new HttpEntity<>(httpHeaders);

			String url = "https://www.googleapis.com/oauth2/v2/userinfo";
			ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.GET, requestEntity, String.class);
			return new Gson().fromJson(response.getBody(), JsonObject.class);
		} catch (Exception e) {
			logger.error("Error getting Google profile details: ", e);
			throw new RuntimeException("Failed to get Google profile details", e);
		}
	}

	public JsonObject handleGoogleAuth(String code, String state) {
    	try {
    		// Get access token
    		String tokenResponse = getOauthAccessTokenGoogle(code);
    		JsonObject tokenJson = new Gson().fromJson(tokenResponse, JsonObject.class);
    		String accessToken = tokenJson.get("access_token").getAsString();
    		
    		// Get user profile
    		JsonObject userProfile = getProfileDetailsGoogle(accessToken);

			// Parse the stae parameter to determine if this is login or signup
			if (state != null && !state.isEmpty()) {
				try {
					JsonObject stateJson = new Gson().fromJson(java.net.URLDecoder.decode(state, "UTF-8"), JsonObject.class);
					if (stateJson.has("action")) {
						String action = stateJson.get("action").getAsString();
						userProfile.addProperty("oauth_action", action);
					}
				} catch (Exception e) {
					logger.warn("Failed to parse state paramenter" + e.getMessage());
				}
			}

			return userProfile;
    	} catch (Exception e) {
    		throw new RuntimeException("Failed to process Google authentication", e);
    	}
    }

}
