package com.flexlog.tracking;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
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
        String token = authHeader.replace("Bearer ", "");
        Claims claims = parseToken(token);
        String userId = claims.getSubject();
        return UUID.fromString(userId);
    }

    public Claims parseToken(String token) {
        try {
            return Jwts.parser()
                    .verifyWith(Keys.hmacShaKeyFor(jwtSecret.getBytes()))
                    .build()
                    .parseSignedClaims(token)
                    .getPayload();
        } catch (JwtException e) {
            throw new RuntimeException("Invalid or expired JWT token", e);
        }
    }

    public String extractEmail(String token) {
        Claims claims = parseToken(token);
        return claims.get("email", String.class);
    }

    public String extractRole(String token) {
        Claims claims = parseToken(token);
        return claims.get("role", String.class);
    }
}