# Job-Aggregator-Platform
A comprehensive microservices-based platform that aggregates job listings from multiple sources, allowing users to search across various platforms simultaneously. The platform features skills matching, personalized recommendations, and a unified interface for job seekers.

## Table of Contents
- [Overview](#-overview)
- [Architecture](#-architecture)
- [Technologies](#-technologies)
- [Setup Instructions](#-setup-instructions)
  - [Local Development](#local-development)
  - [Using Pre-built Docker Images](#using-pre-built-docker-images)
- [Usage Guide](#-usage-guide)
- [Services](#-services)
- [Frontend](#-frontend)
- [System Requirements](#system-requirements)
- [Acknowledgements](#acknowledgements)

## Overview

This platform addresses the fragmentation in job search by consolidating listings from multiple sources including **Jobs.ie** and **IrishJobs.ie**. It features sophisticated skills matching, CV parsing, and personalized recommendations based on user profiles.

## Architecture

The system follows a microservices architecture with:

- **Frontend**: React application
- **Backend services**: User management, job storage, and matching
- **Scrapers**: Real-time job collection from various job platforms
- **Kafka**: Message broker for asynchronous communication
- **Redis**: In-memory caching
- **MySQL**: Persistent storage

---

## Technologies

- **Frontend**: React, TypeScript
- **Backend**: Spring Boot, Python Flask
- **Data Storage**: MySQL, Redis
- **Message Broker**: Kafka
- **Containerization**: Docker
- **Authentication**: JWT, Google OAuth

---

## Prerequisites

This project requires Docker and Docker Compose to run.

## Setup Instructions

### Local Development

1. **Clone the repository**
    ```bash
    git clone https://github.com/SoonMingQian/Job-Aggregator-Platform.git
    cd Job-Aggregator-Platform

2. **Start the services**
    ```bash
    docker-compose up -d

3. **Run the frontend**
    ```bash
    cd frontend/frontend-job-aggregator
    npm install
    npm run dev

### Using Pre-built Docker Images
For instructors or reviewers who want to run the complete system quickly:

1. **Clone the repository**
    ```bash
    git clone https://github.com/SoonMingQian/Job-Aggregator-Platform.git
    cd Job-Aggregator-Platform

2. **Pull and run the containers**
    ```bash
    docker-compose -f docker-compose.dist.yaml pull
    docker-compose -f docker-compose.dist.yaml up -d

3. **Access the application**
- Live frontend: https://soonmingqian.github.io/Job-Aggregator-Platform/
- Or run the frontend locally as described above.

## Usage Guide
1. Create an account or log in via Google.

2. Complete your profile.

3. Upload your CV for automatic skills extraction.

4. Search for jobs across multiple platforms.

5. View suitable jobs.

## Services
| Service              | Description                             | Port       |
|:---------------------|:----------------------------------------|:------------|
| **User Service**       | Authentication, profile management       | 8081       |
| **Jobs Storage Service** | Job listings database and search        | 8080       |
| **Matching Service**    | Skills matching algorithms               | 8082       |
| **Text Processing**     | CV parsing and analysis                  | 5000       |
| **Scrapers**            | Real-time job collection                 | 3002, 3003 |

## Demo Video
[Demo video here](https://atlantictu-my.sharepoint.com/:v:/g/personal/g00438454_atu_ie/EQyqR5hOEKpIt6VWF4pBxOsBZl6qp8MSpy6oxgARl_gsYA?nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJPbmVEcml2ZUZvckJ1c2luZXNzIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXciLCJyZWZlcnJhbFZpZXciOiJNeUZpbGVzTGlua0NvcHkifX0&e=RlssQH)

## Acknowledgements
Developed as part of Final Year Project at Atlantic Technological University
