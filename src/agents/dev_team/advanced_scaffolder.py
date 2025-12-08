"""
Advanced Project Scaffolding for Phase 2 & 3

This module generates:
- Message queue integration (Kafka/RabbitMQ)
- Microservices structure
- Kubernetes deployment configs
- Docker Compose for multi-service setup
- Monitoring setup (Prometheus, Grafana)
- CI/CD pipeline templates
"""

from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

def generate_kafka_docker_compose() -> str:
    """Generate Docker Compose with Kafka and Zookeeper."""
    return """version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"
    networks:
      - app-network

  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
      - "9094:9094"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:9094
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    networks:
      - app-network

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-admin}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-admin123}
      POSTGRES_DB: ${POSTGRES_DB:-appdb}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network

  mongodb:
    image: mongo:7
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER:-admin}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD:-admin123}
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - app-network

  backend-api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER:-admin}:${POSTGRES_PASSWORD:-admin123}@postgres:5432/${POSTGRES_DB:-appdb}
      MONGO_URL: mongodb://${MONGO_USER:-admin}:${MONGO_PASSWORD:-admin123}@mongodb:27017/
      REDIS_URL: redis://redis:6379
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
    depends_on:
      - postgres
      - mongodb
      - redis
      - kafka
    networks:
      - app-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: http://localhost:8000
    depends_on:
      - backend-api
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
  mongo_data:
"""


def generate_rabbitmq_docker_compose() -> str:
    """Generate Docker Compose with RabbitMQ."""
    return """version: '3.8'

services:
  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER:-admin}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASS:-admin123}
    networks:
      - app-network

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-admin}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-admin123}
      POSTGRES_DB: ${POSTGRES_DB:-appdb}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network

  mongodb:
    image: mongo:7
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER:-admin}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD:-admin123}
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - app-network

  backend-api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER:-admin}:${POSTGRES_PASSWORD:-admin123}@postgres:5432/${POSTGRES_DB:-appdb}
      MONGO_URL: mongodb://${MONGO_USER:-admin}:${MONGO_PASSWORD:-admin123}@mongodb:27017/
      REDIS_URL: redis://redis:6379
      RABBITMQ_URL: amqp://${RABBITMQ_USER:-admin}:${RABBITMQ_PASS:-admin123}@rabbitmq:5672/
    depends_on:
      - postgres
      - mongodb
      - redis
      - rabbitmq
    networks:
      - app-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: http://localhost:8000
    depends_on:
      - backend-api
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
  mongo_data:
"""


def generate_kubernetes_deployment(service_name: str, port: int, image: str) -> str:
    """Generate Kubernetes deployment YAML for a service."""
    return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {service_name}
  labels:
    app: {service_name}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: {service_name}
  template:
    metadata:
      labels:
        app: {service_name}
    spec:
      containers:
      - name: {service_name}
        image: {image}
        ports:
        - containerPort: {port}
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: {port}
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: {port}
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: {service_name}-service
spec:
  selector:
    app: {service_name}
  ports:
  - protocol: TCP
    port: {port}
    targetPort: {port}
  type: ClusterIP
"""


def generate_kubernetes_ingress(domain: str, services: List[Dict[str, Any]]) -> str:
    """Generate Kubernetes Ingress for routing."""
    rules = []
    for svc in services:
        rules.append(f"""  - host: {svc['subdomain']}.{domain}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {svc['name']}-service
            port:
              number: {svc['port']}""")
    
    rules_yaml = "\n".join(rules)
    
    return f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - "*.{domain}"
    secretName: app-tls-secret
  rules:
{rules_yaml}
"""


def generate_prometheus_config() -> str:
    """Generate Prometheus monitoring configuration."""
    return """global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'backend-api'
    static_configs:
      - targets: ['backend-api:8000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'kafka'
    static_configs:
      - targets: ['kafka-exporter:9308']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - '/etc/prometheus/alerts.yml'
"""


def generate_grafana_dashboard() -> str:
    """Generate Grafana dashboard JSON for system monitoring."""
    return """{
  "dashboard": {
    "title": "Application Monitoring",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_activity_count"
          }
        ]
      }
    ]
  }
}"""


def generate_github_actions_ci() -> str:
    """Generate GitHub Actions CI/CD pipeline."""
    return """name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        cd backend
        pytest --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml

  test-frontend:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Run tests
      run: |
        cd frontend
        npm test -- --coverage
    
    - name: Build
      run: |
        cd frontend
        npm run build

  build-and-push:
    needs: [test-backend, test-frontend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Log in to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push backend
      uses: docker/build-push-action@v4
      with:
        context: ./backend
        push: true
        tags: ${{ secrets.DOCKER_USERNAME }}/app-backend:latest
    
    - name: Build and push frontend
      uses: docker/build-push-action@v4
      with:
        context: ./frontend
        push: true
        tags: ${{ secrets.DOCKER_USERNAME }}/app-frontend:latest

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to Kubernetes
      uses: azure/k8s-deploy@v4
      with:
        manifests: |
          k8s/deployment.yaml
          k8s/service.yaml
        images: |
          ${{ secrets.DOCKER_USERNAME }}/app-backend:latest
          ${{ secrets.DOCKER_USERNAME }}/app-frontend:latest
"""


def generate_gitlab_ci() -> str:
    """Generate GitLab CI/CD pipeline."""
    return """stages:
  - test
  - build
  - deploy

variables:
  POSTGRES_DB: testdb
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: postgres

test-backend:
  stage: test
  image: python:3.11
  services:
    - postgres:15
  variables:
    DATABASE_URL: postgresql://postgres:postgres@postgres:5432/testdb
  script:
    - cd backend
    - pip install -r requirements.txt
    - pip install pytest pytest-cov
    - pytest --cov=. --cov-report=term
  coverage: '/TOTAL.+ ([0-9]{1,3}%)/'

test-frontend:
  stage: test
  image: node:18
  script:
    - cd frontend
    - npm ci
    - npm test -- --coverage
    - npm run build
  artifacts:
    paths:
      - frontend/build/

build-backend:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE/backend:$CI_COMMIT_SHA ./backend
    - docker push $CI_REGISTRY_IMAGE/backend:$CI_COMMIT_SHA
  only:
    - main

build-frontend:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE/frontend:$CI_COMMIT_SHA ./frontend
    - docker push $CI_REGISTRY_IMAGE/frontend:$CI_COMMIT_SHA
  only:
    - main

deploy-staging:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl config use-context staging
    - kubectl set image deployment/backend backend=$CI_REGISTRY_IMAGE/backend:$CI_COMMIT_SHA
    - kubectl set image deployment/frontend frontend=$CI_REGISTRY_IMAGE/frontend:$CI_COMMIT_SHA
    - kubectl rollout status deployment/backend
    - kubectl rollout status deployment/frontend
  environment:
    name: staging
  only:
    - main

deploy-production:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl config use-context production
    - kubectl set image deployment/backend backend=$CI_REGISTRY_IMAGE/backend:$CI_COMMIT_SHA
    - kubectl set image deployment/frontend frontend=$CI_REGISTRY_IMAGE/frontend:$CI_COMMIT_SHA
    - kubectl rollout status deployment/backend
    - kubectl rollout status deployment/frontend
  environment:
    name: production
  when: manual
  only:
    - main
"""


def generate_microservice_template(service_name: str, port: int) -> str:
    """Generate a FastAPI microservice template."""
    return f"""\"\"\"
{service_name.replace('_', ' ').title()} Microservice

This service handles {service_name.replace('_', ' ')} operations.
\"\"\"

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime

# Message queue imports
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import asyncio

app = FastAPI(title="{service_name.replace('_', ' ').title()} Service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
SERVICE_TOPIC = "{service_name}_events"

# Kafka producer
producer: Optional[AIOKafkaProducer] = None

# Models
class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime

class EventMessage(BaseModel):
    event_type: str
    data: dict
    timestamp: datetime = datetime.now()

# Startup/Shutdown
@app.on_event("startup")
async def startup_event():
    \"\"\"Initialize Kafka producer on startup.\"\"\"
    global producer
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS
    )
    await producer.start()
    print(f"{{SERVICE_TOPIC}} service started - Kafka connected")

@app.on_event("shutdown")
async def shutdown_event():
    \"\"\"Close Kafka producer on shutdown.\"\"\"
    if producer:
        await producer.stop()

# Health endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    \"\"\"Health check endpoint for Kubernetes liveness probe.\"\"\"
    return HealthResponse(
        status="healthy",
        service="{service_name}",
        timestamp=datetime.now()
    )

@app.get("/ready", response_model=HealthResponse)
async def readiness_check():
    \"\"\"Readiness check endpoint for Kubernetes readiness probe.\"\"\"
    # Add checks for database, message queue, etc.
    return HealthResponse(
        status="ready",
        service="{service_name}",
        timestamp=datetime.now()
    )

# Service endpoints
@app.get("/")
async def root():
    return {{
        "service": "{service_name}",
        "version": "1.0.0",
        "status": "running"
    }}

# Message queue publishing
async def publish_event(event_type: str, data: dict):
    \"\"\"Publish event to Kafka.\"\"\"
    if producer:
        event = EventMessage(event_type=event_type, data=data)
        await producer.send(
            SERVICE_TOPIC,
            value=event.json().encode()
        )

# Add your service-specific endpoints here

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port={port})
"""


def generate_env_template() -> str:
    """Generate .env template file."""
    return """# Database Configuration
POSTGRES_USER=admin
POSTGRES_PASSWORD=change_me_in_production
POSTGRES_DB=appdb
DATABASE_URL=postgresql://admin:change_me_in_production@postgres:5432/appdb

# MongoDB Configuration
MONGO_USER=admin
MONGO_PASSWORD=change_me_in_production
MONGO_URL=mongodb://admin:change_me_in_production@mongodb:27017/

# Redis Configuration
REDIS_URL=redis://redis:6379

# Message Queue Configuration (choose one)
# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
# RabbitMQ
RABBITMQ_URL=amqp://admin:change_me_in_production@rabbitmq:5672/

# API Keys (External Services)
NEWS_API_KEY=your_news_api_key
MARKET_DATA_API_KEY=your_market_data_api_key

# JWT Configuration
SECRET_KEY=change_me_to_random_string_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Service Ports
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Environment
ENVIRONMENT=development
DEBUG=false
"""
