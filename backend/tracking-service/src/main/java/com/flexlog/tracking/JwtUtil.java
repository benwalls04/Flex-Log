package com.flexlog.tracking;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import java.util.UUID;

@Component
public class JwtUtil {

    @Value("${supabase.jwt.secret}")
    private String jwtSecret;

    public UUID extractUserIdFromToken(String authHeader) {
        // Remove "Bearer " prefix
        String token = authHeader.replace("Bearer ", "");

        // Parse and validate the JWT
        Claims claims = Jwts.parser()
                .verifyWith(Keys.hmacShaKeyFor(jwtSecret.getBytes()))
                .build()
                .parseSignedClaims(token)
                .getPayload();

        // Extract 'sub' claim (user ID)
        String userId = claims.getSubject();
        return UUID.fromString(userId);
    }
}

