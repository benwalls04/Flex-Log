# Workout Recommendation & Tracking App

## Overview

This project is a **personalized workout tracking and recommendation system** designed to help users log workouts, track progress, and receive exercise recommendations based on prior activity.

The system leverages:

- **Ridge Regression** for predicting next-exercise features  
- **Weighted recommendation** based on similarity and user preferences  
- **Frontend ML inference** for real-time recommendations  
- **Backend microservices** for secure logging, user management, and exercise catalog  
- **Batch training service** for per-user model updates  

---

## Architecture

Frontend (React Native)
├─ Stores JWT from Auth Service
├─ Stores ML model parameters
├─ Computes recommendations locally
└─ Displays streaks / stats fetched from backend

Backend (Spring Boot)
├─ Auth Service (JWT login / user management)
├─ Exercise Catalog Service (CRUD for exercises)
└─ Workout Logging Service (CRUD for user logs)
└─ Indexed by user + timestamp
└─ Emits events for derived metrics (optional)

Batch ML (Python + FastAPI)
└─ Model Training & Scheduler Service
├─ Runs weekly for offline users
├─ Pulls logs from database
├─ Trains ridge regression model per user
└─ Updates model parameters in DB

## Data Models

### Exercises
- Static features for each exercise (muscle group, machine type, etc.)

### Logs
- User workout logs, indexed by `user_id` and `timestamp`

### User Parameters
- Stores model parameters, last retraining timestamp, and weight/frequency adjustment for recommendations

### Streaks (optional)
- Tracks progressive overload per exercise

---

## Features

- Log workouts and track progress over time  
- Per-user ML models predicting the next exercise features  
- Real-time recommendations on the frontend  
- Weighted recommendation system (similarity + user frequency)  
- Batch retraining weekly when users are offline  
- Streak tracking for progressive overload  

---

## Tech Stack

- **Frontend:** React Native  
- **Backend Microservices:** Spring Boot (Auth, Logging, Catalog)  
- **ML Training Service:** Python + FastAPI  
- **Database:** SQLite (development), PostgreSQL (production)  
- **Authentication:** JWT or third-party (Firebase/Auth0)  
- **Optional Messaging:** RabbitMQ / Kafka for async events  