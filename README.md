# 🎵 Music Recommendation System

## Overview

A data-driven music recommendation platform designed to improve music discovery and user engagement through behavioral analytics and recommendation workflows.

The system combines transactional services, recommendation processing, search infrastructure, and user activity analytics to support scalable recommendation and search operations.

---

# System Goals

- Improve user music discovery experience through personalized recommendations
- Process and analyze large-scale listening data
- Track user behavior for analytical and recommendation purposes
- Separate transactional workloads from search and analytics infrastructure
- Support scalable and modular multi-service deployment

---

# Core Features

## User & Playlist Management

- User authentication and authorization
- Playlist creation and management
- Track organization workflows

## Recommendation System

- Behavior-based recommendation workflows using association analysis
- Personalized track and artist suggestions
- Recommendation generation from listening patterns

## Search & Analytics

- Real-time search for tracks and artists
- User activity tracking (click/view events)
- Behavioral analytics and monitoring dashboards

## Data Processing

- ETL workflows for ingesting and transforming large CSV datasets
- Structured data pipelines for recommendation and analytical operations

---

# System Architecture

## Backend Services

- API service for authentication, playlists, search, recommendations, and events
- Relational database for transactional operations
- Search and analytics infrastructure for behavioral tracking
- Monitoring and visualization services

## Architecture Highlights

- Separation between transactional storage and search analytics workflows
- Modular multi-service deployment using containerized architecture
- Scalable data-processing and recommendation pipeline design

---

# Data & Analytics Workflow

```text
Raw CSV Data
        ↓
ETL Processing
        ↓
Structured Storage
        ↓
Recommendation Engine
        ↓
Search & Analytics
        ↓
User Interaction Tracking
```

---

# Recommendation Workflow

```text
User Listening Behavior
        ↓
Behavior Analysis
        ↓
Association Rule Generation
        ↓
Personalized Recommendations
```

---

# Tech Stack

## Backend

- Python
- FastAPI

## Data & Analytics

- PostgreSQL
- Elasticsearch
- Kibana

## Deployment

- Docker
- Docker Compose

## Frontend

- HTML
- CSS
- JavaScript

---

# Deployment

The system is deployed using a containerized multi-service architecture to simplify:

- Local development
- Service orchestration
- Scalability
- Environment consistency

---

# Setup Guide

## Requirements

- Docker
- Docker Compose
- Python 3.8+

---

## Start Services

```bash
docker-compose up -d
```

### Services

- Backend API
- PostgreSQL
- Elasticsearch
- Kibana

---

## Initialize Analytics Index

```bash
bash es-init/bootstrap.sh
```

---

## Load Dataset

Example:

```bash
python backend/app/loaders/loader.py tracks backend/app/data/track.csv
```

---

## Run ETL Workflow

```sql
CALL full_load_from_staging();
```

---

# API Documentation

After starting the system:

- Swagger UI: `/docs`
- ReDoc: `/redoc`

## Core APIs

- Authentication
- Playlist Management
- Search
- Recommendations
- User Activity Events

---

# Development Mode

Run backend locally:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```
