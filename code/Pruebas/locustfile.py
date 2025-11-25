"""
PredictHealth Microservices Load Testing Suite

Usage:
    # Run with Web UI
    locust -f locustfile.py

    # Run specific test class
    locust -f locustfile.py BaselineTest

    # Headless mode (smoke test example)
    locust -f locustfile.py SmokeTest --headless --users 10 --spawn-rate 2 --run-time 2m

    # CSV test with data
    locust -f locustfile.py CSVTest --headless --users 50 --spawn-rate 10 --run-time 5m

Note: Services use absolute URLs with specific ports (8001-8011), so --host flag is not needed.

Test Scenarios:
    - BaselineTest: Normal load (50 users, steady)
    - SmokeTest: Minimal load verification (10 users, 2 min)
    - ReadHeavyTest: 80% reads, 20% writes
    - WriteHeavyTest: 80% writes, 20% reads
    - RampUpTest: Gradual increase 10→100 users
    - RampDownTest: Gradual decrease 100→10 users
    - SpikeTest: Sudden burst to 200 users
    - SoakTest: Extended duration (1+ hours) at medium load
    - BreakpointTest: Find system limits (progressive load increase)
    - CSVTest: Data-driven testing with CSV users
"""

import csv
import json
import random
import time
from typing import Optional
from locust import HttpUser, TaskSet, task, between, constant, constant_pacing  # LoadTestShape disabled for now
# from locust import LoadTestShape  # Uncomment to enable custom load shapes
from locust.exception import StopUser


# =============================================================================
# Configuration & Test Data
# =============================================================================

# Service ports
SERVICES = {
    "auth": 8001,
    "register": 8002,
    "patient": 8003,
    "health": 8004,
    "diabetes": 8008,
    "hypertension": 8009,
    "data": 8010,
    "recommendations": 8011,
}

# Test users (from init.sql - 200 users with complete patient data in database)
# All users use password: password123
# 100 users from cdc-diabetes dataset + 100 users from hypertension dataset
TEST_USERS = [
    # Generate all 200 users programmatically to avoid huge list
    # Pattern: user_1@cdc-diabetes.com through user_100@cdc-diabetes.com
    #         user_1@hypertension-risk.com through user_100@hypertension-risk.com
    *[{"email": f"user_{i}@cdc-diabetes.com", "password": "password123"} for i in range(1, 101)],
    *[{"email": f"user_{i}@hypertension-risk.com", "password": "password123"} for i in range(1, 101)],
]

# Sample patient data
SAMPLE_PATIENT = {
    "nombre": "Juan",
    "apellido": "Pérez",
    "fecha_nacimiento": "1985-05-15",
    "sexo": "M",
}

# Sample lifestyle data
SAMPLE_LIFESTYLE = {
    "frutas": "true",
    "verduras": "true",
    "fuma": "false",
    "alcohol": "false",
    "movilidad": "false",
    "sal": "5.0",
    "horas_sueno": "7",
    "nivel_estres": "5",
    "salud_mental": "2",
    "actividad_fisica": "3",
    "actividad_frecuente": "true",
    "salud_fisica": "1",
}

# Sample hypertension prediction data
SAMPLE_HYPERTENSION = {
    "age": 45,
    "salt_intake": 7.5,
    "stress_score": 6,
    "sleep_duration": 6.5,
    "bmi": 28.5,
    "medication": 0,
    "family_history": 1,
    "exercise_level": 2,
}

# Sample full history data for /guardar_historial endpoint
SAMPLE_FULL_HISTORY = {
    "nombre": "LoadTest",
    "apellido": "User",
    "fecha_nacimiento": "1990-01-01",
    "sexo": "M",
    "diabetes": False,
    "hipertension": False,
    "colesterol": "Normal",
    "colesterol_alto": "No",
    "bmi": 25.5,
    "presion": "Normal",
    "salud_general": "Buena",
    "acv": "No",
    "problemas_corazon": "No",
    "medicamentos": ["Ninguno"],
    "estilo_vida": {
        "frutas": "true",
        "verduras": "true",
        "fuma": "false",
        "alcohol": "false",
        "movilidad": "false",
        "sal": "5.0",
        "horas_sueno": "7",
        "nivel_estres": "5",
        "salud_mental": "2",
        "actividad_fisica": "3",
        "actividad_frecuente": "true",
        "salud_fisica": "1",
    }
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_service_url(service_name: str) -> str:
    """Build service URL from base host and port"""
    port = SERVICES.get(service_name, 8000)
    return f"http://localhost:{port}"


# =============================================================================
# Base User Behavior
# =============================================================================

class PredictHealthUser(HttpUser):
    """Base user class with authentication and common tasks"""
    
    abstract = True  # Don't run this directly
    host = "http://localhost"  # Base host (services use absolute URLs with specific ports)
    access_token: Optional[str] = None
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    
    def on_start(self):
        """Called when a simulated user starts - perform login"""
        self.login()
    
    def login(self):
        """Authenticate and get access token"""
        # Pick random test user
        user_creds = random.choice(TEST_USERS)
        
        response = self.client.post(
            f"{get_service_url('auth')}/auth/login",
            json={
                "username": user_creds["email"],
                "password": user_creds["password"]
            },
            name="/auth/login"
        )
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            self.user_email = user_creds["email"]
            
            # Get user ID from /auth/me
            if self.access_token:
                me_response = self.client.get(
                    f"{get_service_url('auth')}/auth/me",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    name="/auth/me"
                )
                if me_response.status_code == 200:
                    me_data = me_response.json()
                    self.user_id = int(me_data.get("sub", 1))
        else:
            # If login fails, use fallback
            self.user_id = 1
            self.access_token = None
    
    def get_auth_headers(self):
        """Return Authorization header dict"""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}


# =============================================================================
# Task Sets
# =============================================================================

class ReadTasks(TaskSet):
    """Read-heavy operations (GET endpoints)"""
    
    @task(5)
    def get_patient(self):
        """Get patient data"""
        if self.user.user_id:
            self.client.get(
                f"{get_service_url('patient')}/paciente/{self.user.user_id}",
                name="/paciente/{id} [GET]"
            )
    
    @task(5)
    def get_diabetes_prediction(self):
        """Get diabetes prediction"""
        if self.user.user_id and self.user.access_token:
            self.client.get(
                f"{get_service_url('diabetes')}/predict_diabetes/{self.user.user_id}",
                headers=self.user.get_auth_headers(),
                name="/predict_diabetes/{id} [GET]"
            )
    
    @task(3)
    def get_latest_diabetes(self):
        """Get latest diabetes prediction"""
        if self.user.user_id and self.user.access_token:
            self.client.get(
                f"{get_service_url('diabetes')}/prediccion/latest/diabetes/{self.user.user_id}",
                headers=self.user.get_auth_headers(),
                name="/prediccion/latest/diabetes/{id} [GET]"
            )
    
    @task(3)
    def get_latest_hypertension(self):
        """Get latest hypertension prediction"""
        if self.user.user_id and self.user.access_token:
            self.client.get(
                f"{get_service_url('hypertension')}/prediccion/latest/hypertension/{self.user.user_id}",
                headers=self.user.get_auth_headers(),
                name="/prediccion/latest/hypertension/{id} [GET]"
            )
    
    @task(4)
    def get_recommendations(self):
        """Get personalized recommendations"""
        if self.user.user_id and self.user.access_token:
            self.client.get(
                f"{get_service_url('recommendations')}/recommendations/{self.user.user_id}",
                headers=self.user.get_auth_headers(),
                name="/recommendations/{id} [GET]"
            )
    
    @task(2)
    def health_checks(self):
        """Check service health"""
        service = random.choice(["auth", "register"])
        self.client.get(
            f"{get_service_url(service)}/{service}/health",
            name=f"/{service}/health [GET]"
        )


class WriteTasks(TaskSet):
    """Write-heavy operations (POST endpoints)"""
    
    @task(4)
    def create_patient(self):
        """Create/update patient data"""
        if self.user.user_id and self.user.access_token:
            patient_data = SAMPLE_PATIENT.copy()
            patient_data["id_usuario"] = self.user.user_id
            
            self.client.post(
                f"{get_service_url('patient')}/paciente",
                json=patient_data,
                headers=self.user.get_auth_headers(),
                name="/paciente [POST]"
            )
    
    @task(4)
    def create_lifestyle(self):
        """Create lifestyle data"""
        if self.user.user_id and self.user.access_token:
            lifestyle_data = SAMPLE_LIFESTYLE.copy()
            lifestyle_data["id_usuario"] = self.user.user_id
            
            self.client.post(
                f"{get_service_url('health')}/estilo_vida",
                json=lifestyle_data,
                headers=self.user.get_auth_headers(),
                name="/estilo_vida [POST]"
            )
    
    @task(3)
    def predict_hypertension(self):
        """Request hypertension prediction"""
        if self.user.user_id and self.user.access_token:
            hyp_data = SAMPLE_HYPERTENSION.copy()
            hyp_data["id_usuario"] = self.user.user_id
            
            self.client.post(
                f"{get_service_url('hypertension')}/predict_hypertension",
                json=hyp_data,
                headers=self.user.get_auth_headers(),
                name="/predict_hypertension [POST]"
            )
    
    @task(5)
    def save_full_history(self):
        """Save complete patient history"""
        if self.user.user_id and self.user.access_token:
            history_data = SAMPLE_FULL_HISTORY.copy()
            history_data["id_usuario"] = self.user.user_id
            
            self.client.post(
                f"{get_service_url('data')}/guardar_historial",
                json=history_data,
                headers=self.user.get_auth_headers(),
                name="/guardar_historial [POST]"
            )


class MixedTasks(TaskSet):
    """Balanced mix of read and write operations"""
    
    @task(10)
    def read_operations(self):
        """Execute read tasks"""
        read_task = ReadTasks(self.user)
        read_task.execute_task(random.choice([
            read_task.get_patient,
            read_task.get_diabetes_prediction,
            read_task.get_recommendations,
        ]))
    
    @task(5)
    def write_operations(self):
        """Execute write tasks"""
        write_task = WriteTasks(self.user)
        write_task.execute_task(random.choice([
            write_task.create_patient,
            write_task.create_lifestyle,
            write_task.predict_hypertension,
        ]))


# =============================================================================
# Test Scenarios
# =============================================================================

class BaselineTest(PredictHealthUser):
    """
    Baseline Test: Normal expected load
    - 50 concurrent users
    - Mixed read/write operations
    - Steady state for performance baseline
    """
    wait_time = between(1, 3)
    tasks = [MixedTasks]


class SmokeTest(PredictHealthUser):
    """
    Smoke Test: Minimal load to verify system works
    - 10 concurrent users
    - Quick verification (2-5 min)
    - All endpoints touched
    """
    wait_time = between(2, 5)
    tasks = [MixedTasks]


class ReadHeavyTest(PredictHealthUser):
    """
    Read-Heavy Test: 80% reads, 20% writes
    - Simulates typical CMS usage
    - Emphasis on GET endpoints
    """
    wait_time = between(1, 2)
    
    @task(80)
    def read_operations(self):
        # Pick a random read operation
        operation = random.choice([
            self.get_patient,
            self.get_diabetes_prediction,
            self.get_latest_diabetes,
            self.get_recommendations,
        ])
        operation()
    
    @task(20)
    def write_operations(self):
        # Pick a random write operation
        operation = random.choice([
            self.create_patient,
            self.create_lifestyle,
        ])
        operation()
    
    # Read operations
    def get_patient(self):
        if self.user_id:
            self.client.get(
                f"{get_service_url('patient')}/paciente/{self.user_id}",
                name="/paciente/{id} [GET]"
            )
    
    def get_diabetes_prediction(self):
        if self.user_id and self.access_token:
            self.client.get(
                f"{get_service_url('diabetes')}/predict_diabetes/{self.user_id}",
                headers=self.get_auth_headers(),
                name="/predict_diabetes/{id} [GET]"
            )
    
    def get_latest_diabetes(self):
        if self.user_id and self.access_token:
            self.client.get(
                f"{get_service_url('diabetes')}/prediccion/latest/diabetes/{self.user_id}",
                headers=self.get_auth_headers(),
                name="/prediccion/latest/diabetes/{id} [GET]"
            )
    
    def get_recommendations(self):
        if self.user_id and self.access_token:
            self.client.get(
                f"{get_service_url('recommendations')}/recommendations/{self.user_id}",
                headers=self.get_auth_headers(),
                name="/recommendations/{id} [GET]"
            )
    
    # Write operations
    def create_patient(self):
        if self.user_id and self.access_token:
            patient_data = SAMPLE_PATIENT.copy()
            patient_data["id_usuario"] = self.user_id
            self.client.post(
                f"{get_service_url('patient')}/paciente",
                json=patient_data,
                headers=self.get_auth_headers(),
                name="/paciente [POST]"
            )
    
    def create_lifestyle(self):
        if self.user_id and self.access_token:
            lifestyle_data = SAMPLE_LIFESTYLE.copy()
            lifestyle_data["id_usuario"] = self.user_id
            self.client.post(
                f"{get_service_url('health')}/estilo_vida",
                json=lifestyle_data,
                headers=self.get_auth_headers(),
                name="/estilo_vida [POST]"
            )


class WriteHeavyTest(PredictHealthUser):
    """
    Write-Heavy Test: 80% writes, 20% reads
    - Simulates data entry/update scenarios
    - Emphasis on POST endpoints
    - Tests database write capacity
    """
    wait_time = between(1, 3)
    
    @task(20)
    def read_operations(self):
        self.get_patient()
    
    @task(80)
    def write_operations(self):
        # Pick a random write operation
        operation = random.choice([
            self.create_patient,
            self.create_lifestyle,
            self.predict_hypertension,
            self.save_full_history,
        ])
        operation()
    
    # Read operation
    def get_patient(self):
        if self.user_id:
            self.client.get(
                f"{get_service_url('patient')}/paciente/{self.user_id}",
                name="/paciente/{id} [GET]"
            )
    
    # Write operations
    def create_patient(self):
        if self.user_id and self.access_token:
            patient_data = SAMPLE_PATIENT.copy()
            patient_data["id_usuario"] = self.user_id
            self.client.post(
                f"{get_service_url('patient')}/paciente",
                json=patient_data,
                headers=self.get_auth_headers(),
                name="/paciente [POST]"
            )
    
    def create_lifestyle(self):
        if self.user_id and self.access_token:
            lifestyle_data = SAMPLE_LIFESTYLE.copy()
            lifestyle_data["id_usuario"] = self.user_id
            self.client.post(
                f"{get_service_url('health')}/estilo_vida",
                json=lifestyle_data,
                headers=self.get_auth_headers(),
                name="/estilo_vida [POST]"
            )
    
    def predict_hypertension(self):
        if self.user_id and self.access_token:
            hypertension_data = SAMPLE_HYPERTENSION.copy()
            hypertension_data["id_usuario"] = self.user_id
            self.client.post(
                f"{get_service_url('hypertension')}/predict_hypertension",
                json=hypertension_data,
                headers=self.get_auth_headers(),
                name="/predict_hypertension [POST]"
            )
    
    def save_full_history(self):
        if self.user_id and self.access_token:
            full_data = SAMPLE_FULL_HISTORY.copy()
            full_data["id_usuario"] = self.user_id
            self.client.post(
                f"{get_service_url('data')}/guardar_historial",
                json=full_data,
                headers=self.get_auth_headers(),
                name="/guardar_historial [POST]"
            )

# Custom LoadTestShape classes are disabled for now
# Uncomment when you need progressive/custom load patterns
# class SpikeTestShape(LoadTestShape):
#     """
#     Spike Test Shape: Sudden traffic burst
#     - Normal: 50 users
#     - Spike: 200 users (sudden)
#     - Duration: 5 minutes
#     """
#     
#     def tick(self):
#         run_time = self.get_run_time()
#         
#         if run_time < 120:
#             # First 2 min: baseline 50 users
#             return (50, 10)
#         elif run_time < 180:
#             # Spike: jump to 200 users instantly
#             return (200, 50)
#         elif run_time < 240:
#             # Hold spike for 1 min
#             return (200, 50)
#         elif run_time < 300:
#             # Drop back to baseline
#             return (50, 50)
#         else:
#             return None


class SpikeTest(PredictHealthUser):
    """
    Spike Test: Sudden traffic burst
    - Use custom LoadTestShape for spike pattern
    - Tests system elasticity
    """
    wait_time = between(0.5, 1.5)
    tasks = [MixedTasks]


class SoakTest(PredictHealthUser):
    """
    Soak Test: Extended duration testing
    - Medium load over 1+ hours
    - Detects memory leaks, resource exhaustion
    - Run with: --run-time 1h or --run-time 4h
    """
    wait_time = between(2, 5)
    tasks = [MixedTasks]


# class BreakpointTestShape(LoadTestShape):
#     """
#     Breakpoint Test Shape: Progressive load increase
#     - Increments: +50 users every 2 minutes
#     - Continues until failure or manual stop
#     """
#     
#     def tick(self):
#         run_time = self.get_run_time()
#         
#         # Calculate user count based on elapsed time
#         step = int(run_time / 120)  # Every 2 minutes
#         user_count = 50 + (step * 50)  # Start at 50, add 50 every step
#         
#         # Cap at 1000 users (safety limit)
#         if user_count > 1000:
#             return None
#         
#         return (user_count, 10)


class BreakpointTest(PredictHealthUser):
    """
    Breakpoint Test: Find system limits
    - Use custom LoadTestShape for progressive load
    - Identify maximum capacity
    """
    wait_time = constant(1)
    tasks = [MixedTasks]


class CSVTest(PredictHealthUser):
    """
    CSV Test: Data-driven testing
    - Reads user credentials from users.csv
    - Each virtual user uses unique credentials
    
    Create users.csv:
        email,password
        user1@test.com,pass123
        user2@test.com,pass456
    """
    wait_time = between(1, 3)
    tasks = [MixedTasks]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.csv_data = self.load_csv_data()
    
    @staticmethod
    def load_csv_data():
        """Load users from CSV file"""
        import os
        # Try multiple possible locations for users.csv
        possible_paths = [
            'testing/users.csv',  # From repo root
            'users.csv',          # From testing/ directory
            os.path.join(os.path.dirname(__file__), 'users.csv'),  # Relative to locustfile
        ]
        
        for csv_path in possible_paths:
            try:
                with open(csv_path, 'r') as f:
                    reader = csv.DictReader(f)
                    data = list(reader)
                    print(f"Loaded {len(data)} users from {csv_path}")
                    return data
            except FileNotFoundError:
                continue
        
        print("Warning: users.csv not found in any location, using default test users")
        return TEST_USERS
    
    def on_start(self):
        """Override login to use CSV data"""
        if self.csv_data:
            user_creds = random.choice(self.csv_data)
            
            response = self.client.post(
                f"{get_service_url('auth')}/auth/login",
                json={
                    "username": user_creds["email"],
                    "password": user_creds["password"]
                },
                name="/auth/login [CSV]"
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.user_email = user_creds["email"]
                
                if self.access_token:
                    me_response = self.client.get(
                        f"{get_service_url('auth')}/auth/me",
                        headers={"Authorization": f"Bearer {self.access_token}"},
                        name="/auth/me [CSV]"
                    )
                    if me_response.status_code == 200:
                        me_data = me_response.json()
                        self.user_id = int(me_data.get("sub", 1))
        else:
            super().on_start()


# =============================================================================
# Combined Test Classes with Shapes (SHAPES DISABLED)
# =============================================================================

# class RampUpTestShape(LoadTestShape):
#     """Ramp-Up Test: Gradual load increase"""
#     def tick(self):
#         run_time = self.get_run_time()
#         if run_time < 60: return (10, 5)
#         elif run_time < 120: return (20, 5)
#         elif run_time < 180: return (30, 5)
#         elif run_time < 240: return (40, 5)
#         elif run_time < 300: return (50, 5)
#         elif run_time < 360: return (60, 5)
#         elif run_time < 420: return (70, 5)
#         elif run_time < 480: return (80, 5)
#         elif run_time < 540: return (90, 5)
#         elif run_time < 600: return (100, 5)
#         else: return None


class RampUpTest(PredictHealthUser):
    """Ramp-up test (shapes disabled, use --users parameter)"""
    wait_time = between(1, 3)
    tasks = [MixedTasks]


# class RampDownTestShape(LoadTestShape):
#     """Ramp-Down Test: Gradual load decrease"""
#     def tick(self):
#         run_time = self.get_run_time()
#         if run_time < 60: return (100, 5)
#         elif run_time < 120: return (90, 5)
#         elif run_time < 180: return (80, 5)
#         elif run_time < 240: return (70, 5)
#         elif run_time < 300: return (60, 5)
#         elif run_time < 360: return (50, 5)
#         elif run_time < 420: return (40, 5)
#         elif run_time < 480: return (30, 5)
#         elif run_time < 540: return (20, 5)
#         elif run_time < 600: return (10, 5)
#         else: return None


class RampDownTest(PredictHealthUser):
    """Ramp-down test (shapes disabled, use --users parameter)"""
    wait_time = between(1, 3)
    tasks = [MixedTasks]


# =============================================================================
# Usage Examples
# =============================================================================

"""
Run Examples (Services use absolute URLs on ports 8001-8011):

1. Baseline Test (50 users, 10 min):
   locust -f locustfile.py BaselineTest --headless --users 50 --spawn-rate 5 --run-time 10m

2. Smoke Test (10 users, 2 min):
   locust -f locustfile.py SmokeTest --headless --users 10 --spawn-rate 2 --run-time 2m

3. Read-Heavy Test (100 users, 15 min):
   locust -f locustfile.py ReadHeavyTest --headless --users 100 --spawn-rate 10 --run-time 15m

4. Write-Heavy Test (50 users, 10 min):
   locust -f locustfile.py WriteHeavyTest --headless --users 50 --spawn-rate 5 --run-time 10m

5. Ramp-Up Test (with custom shape):
   locust -f locustfile.py RampUpTest --headless

6. Ramp-Down Test (with custom shape):
   locust -f locustfile.py RampDownTest --headless

7. Spike Test (with custom shape):
   locust -f locustfile.py SpikeTest --headless

8. Soak Test (100 users, 2 hours):
   locust -f locustfile.py SoakTest --headless --users 100 --spawn-rate 10 --run-time 2h

9. Breakpoint Test (progressive load):
   locust -f locustfile.py BreakpointTest --headless

10. CSV Test (data-driven):
    locust -f locustfile.py CSVTest --headless --users 50 --spawn-rate 10 --run-time 10m

11. Web UI (interactive):
    locust -f locustfile.py --host http://localhost
    # Then open http://localhost:8089

Generate HTML report:
    locust -f locustfile.py BaselineTest --headless --users 50 --spawn-rate 5 --run-time 5m --html report.html --host http://localhost
"""