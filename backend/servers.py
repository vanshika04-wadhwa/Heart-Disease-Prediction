from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta

from models import (
    User, UserCreate, UserLogin, UserResponse, Token,
    PatientProfile, DoctorProfile, DoctorCreate, DoctorResponse,
    HeartPredictionInput, HeartPrediction, PredictionResponse,
    Feedback, FeedbackCreate, PasswordChange
)
from auth import (
    verify_password, get_password_hash, create_access_token, decode_token
)
from ml_model import ml_model

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'health_prediction')]

# Collections
users_collection = db.users
patients_collection = db.patients
doctors_collection = db.doctors
predictions_collection = db.predictions
feedback_collection = db.feedback

# Create the main app
app = FastAPI(title="Smart Health Disease Prediction System")

# Create a router with /api prefix
api_router = APIRouter(prefix="/api")

security = HTTPBearer()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize ML model on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up the application...")
    ml_model.load_model()
    
    # Create admin user if not exists
    admin = await users_collection.find_one({"username": "admin"})
    if not admin:
        admin_user = User(
            username="admin",
            email="admin@health.com",
            first_name="Admin",
            last_name="User",
            contact="1234567890",
            address="Admin Office",
            role="admin",
            hashed_password=get_password_hash("admin123")
        )
        await users_collection.insert_one(admin_user.model_dump())
        logger.info("Admin user created")

# Helper function to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await users_collection.find_one({"username": username}, {"_id": 0})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

# Authentication Routes
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    """Register a new user (patient or doctor)"""
    # Check if user exists
    existing_user = await users_collection.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    existing_email = await users_collection.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        **user_data.model_dump(exclude={'password'}),
        hashed_password=get_password_hash(user_data.password)
    )
    
    await users_collection.insert_one(user.model_dump())
    
    # Create profile based on role
    if user_data.role == "patient":
        patient_profile = PatientProfile(
            user_id=user.id,
            date_of_birth=user_data.date_of_birth,
            image_url=user_data.image_url
        )
        await patients_collection.insert_one(patient_profile.model_dump())
    elif user_data.role == "doctor":
        doctor_profile = DoctorProfile(
            user_id=user.id,
            specialization="Cardiologist",
            image_url=user_data.image_url,
            status=0  # pending approval
        )
        await doctors_collection.insert_one(doctor_profile.model_dump())
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**user.model_dump())
    )

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login user"""
    user = await users_collection.find_one({"username": credentials.username}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account is inactive")
    
    # Check if doctor is approved
    if user["role"] == "doctor":
        doctor = await doctors_collection.find_one({"user_id": user["id"]}, {"_id": 0})
        if doctor and doctor.get("status", 0) == 0:
            raise HTTPException(status_code=401, detail="Your account is pending approval")
    
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**user)
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse(**current_user)

@api_router.post("/auth/change-password")
async def change_password(password_data: PasswordChange, current_user: dict = Depends(get_current_user)):
    """Change user password"""
    if not verify_password(password_data.old_password, current_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    new_hashed_password = get_password_hash(password_data.new_password)
    await users_collection.update_one(
        {"id": current_user["id"]},
        {"$set": {"hashed_password": new_hashed_password}}
    )
    
    return {"message": "Password changed successfully"}

# Doctor Management Routes
@api_router.post("/doctors", response_model=DoctorResponse)
async def create_doctor(doctor_data: DoctorCreate, current_user: dict = Depends(get_current_user)):
    """Create a new doctor (Admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create doctors")
    
    # Check if username exists
    existing_user = await users_collection.find_one({"username": doctor_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create user
    user = User(
        username=doctor_data.username,
        email=doctor_data.email,
        first_name=doctor_data.first_name,
        last_name=doctor_data.last_name,
        contact=doctor_data.contact,
        address=doctor_data.address,
        role="doctor",
        hashed_password=get_password_hash(doctor_data.password)
    )
    await users_collection.insert_one(user.model_dump())
    
    # Create doctor profile
    doctor_profile = DoctorProfile(
        user_id=user.id,
        specialization=doctor_data.specialization,
        image_url=doctor_data.image_url,
        status=1  # auto-approve admin-created doctors
    )
    await doctors_collection.insert_one(doctor_profile.model_dump())
    
    return DoctorResponse(
        id=doctor_profile.id,
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        contact=user.contact,
        address=user.address,
        specialization=doctor_profile.specialization,
        image_url=doctor_profile.image_url,
        status=doctor_profile.status,
        created_at=doctor_profile.created_at
    )

@api_router.get("/doctors", response_model=List[DoctorResponse])
async def get_doctors(current_user: dict = Depends(get_current_user)):
    """Get all doctors"""
    doctors = await doctors_collection.find({}, {"_id": 0}).to_list(1000)
    
    doctor_responses = []
    for doctor in doctors:
        user = await users_collection.find_one({"id": doctor["user_id"]}, {"_id": 0})
        if user:
            doctor_responses.append(DoctorResponse(
                id=doctor["id"],
                user_id=doctor["user_id"],
                first_name=user["first_name"],
                last_name=user["last_name"],
                email=user["email"],
                contact=user["contact"],
                address=user["address"],
                specialization=doctor["specialization"],
                image_url=doctor.get("image_url"),
                status=doctor["status"],
                created_at=doctor["created_at"]
            ))
    
    return doctor_responses

@api_router.get("/doctors/approved", response_model=List[DoctorResponse])
async def get_approved_doctors():
    """Get approved doctors (public endpoint)"""
    doctors = await doctors_collection.find({"status": 1}, {"_id": 0}).to_list(1000)
    
    doctor_responses = []
    for doctor in doctors:
        user = await users_collection.find_one({"id": doctor["user_id"]}, {"_id": 0})
        if user:
            doctor_responses.append(DoctorResponse(
                id=doctor["id"],
                user_id=doctor["user_id"],
                first_name=user["first_name"],
                last_name=user["last_name"],
                email=user["email"],
                contact=user["contact"],
                address=user["address"],
                specialization=doctor["specialization"],
                image_url=doctor.get("image_url"),
                status=doctor["status"],
                created_at=doctor["created_at"]
            ))
    
    return doctor_responses

@api_router.put("/doctors/{doctor_id}/status")
async def update_doctor_status(doctor_id: str, current_user: dict = Depends(get_current_user)):
    """Toggle doctor approval status (Admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update doctor status")
    
    doctor = await doctors_collection.find_one({"id": doctor_id}, {"_id": 0})
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    new_status = 0 if doctor["status"] == 1 else 1
    await doctors_collection.update_one(
        {"id": doctor_id},
        {"$set": {"status": new_status}}
    )
    
    return {"message": "Doctor status updated", "status": new_status}

@api_router.delete("/doctors/{doctor_id}")
async def delete_doctor(doctor_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a doctor (Admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete doctors")
    
    doctor = await doctors_collection.find_one({"id": doctor_id}, {"_id": 0})
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Delete doctor profile
    await doctors_collection.delete_one({"id": doctor_id})
    
    # Delete user
    await users_collection.delete_one({"id": doctor["user_id"]})
    
    return {"message": "Doctor deleted successfully"}

# Prediction Routes
@api_router.post("/predict", response_model=PredictionResponse)
async def predict_heart_disease(prediction_input: HeartPredictionInput, current_user: dict = Depends(get_current_user)):
    """Predict heart disease"""
    if current_user["role"] != "patient":
        raise HTTPException(status_code=403, detail="Only patients can make predictions")
    
    # Get patient profile
    patient = await patients_collection.find_one({"user_id": current_user["id"]}, {"_id": 0})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    
    # Prepare features for ML model
    features = [
        prediction_input.age,
        prediction_input.sex,
        prediction_input.cp,
        prediction_input.trestbps,
        prediction_input.chol,
        prediction_input.fbs,
        prediction_input.restecg,
        prediction_input.thalach,
        prediction_input.exang,
        prediction_input.oldpeak,
        prediction_input.slope,
        prediction_input.ca,
        prediction_input.thal
    ]
    
    # Make prediction
    result = ml_model.predict(features)
    
    # Save prediction
    prediction = HeartPrediction(
        patient_id=patient["id"],
        patient_name=f"{current_user['first_name']} {current_user['last_name']}",
        input_values=prediction_input.model_dump(),
        result=result['prediction'],
        accuracy=result['accuracy'],
        probability=result['probability']
    )
    
    await predictions_collection.insert_one(prediction.model_dump())
    
    message = "You are healthy" if result['prediction'] == 0 else "You may have heart disease. Please consult a doctor."
    
    return PredictionResponse(
        id=prediction.id,
        result=result['prediction'],
        accuracy=result['accuracy'],
        probability=result['probability'],
        message=message,
        created_at=prediction.created_at
    )

@api_router.get("/predictions", response_model=List[HeartPrediction])
async def get_predictions(current_user: dict = Depends(get_current_user)):
    """Get all predictions"""
    if current_user["role"] == "patient":
        # Get patient's own predictions
        patient = await patients_collection.find_one({"user_id": current_user["id"]}, {"_id": 0})
        if not patient:
            return []
        predictions = await predictions_collection.find({"patient_id": patient["id"]}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    else:
        # Admin and doctors can see all predictions
        predictions = await predictions_collection.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    return predictions

@api_router.delete("/predictions/{prediction_id}")
async def delete_prediction(prediction_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a prediction"""
    prediction = await predictions_collection.find_one({"id": prediction_id}, {"_id": 0})
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    # Check authorization
    if current_user["role"] == "patient":
        patient = await patients_collection.find_one({"user_id": current_user["id"]}, {"_id": 0})
        if not patient or prediction["patient_id"] != patient["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to delete this prediction")
    
    await predictions_collection.delete_one({"id": prediction_id})
    return {"message": "Prediction deleted successfully"}

# Feedback Routes
@api_router.post("/feedback")
async def submit_feedback(feedback_data: FeedbackCreate, current_user: dict = Depends(get_current_user)):
    """Submit feedback"""
    feedback = Feedback(
        user_id=current_user["id"],
        user_name=f"{current_user['first_name']} {current_user['last_name']}",
        email=current_user["email"],
        message=feedback_data.message
    )
    
    await feedback_collection.insert_one(feedback.model_dump())
    return {"message": "Feedback submitted successfully"}

@api_router.get("/feedback", response_model=List[Feedback])
async def get_feedback(current_user: dict = Depends(get_current_user)):
    """Get all feedback (Admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view feedback")
    
    feedback_list = await feedback_collection.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return feedback_list

# Patient Routes
@api_router.get("/patients")
async def get_patients(current_user: dict = Depends(get_current_user)):
    """Get all patients (Admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view patients")
    
    patients = await patients_collection.find({}, {"_id": 0}).to_list(1000)
    
    patient_list = []
    for patient in patients:
        user = await users_collection.find_one({"id": patient["user_id"]}, {"_id": 0})
        if user:
            patient_list.append({
                "id": patient["id"],
                "user_id": patient["user_id"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "email": user["email"],
                "contact": user["contact"],
                "address": user["address"],
                "date_of_birth": patient.get("date_of_birth"),
                "image_url": patient.get("image_url"),
                "created_at": patient["created_at"]
            })
    
    return patient_list

# Stats Route
@api_router.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view stats")
    
    total_patients = await patients_collection.count_documents({})
    total_doctors = await doctors_collection.count_documents({})
    total_predictions = await predictions_collection.count_documents({})
    total_feedback = await feedback_collection.count_documents({})
    
    healthy_predictions = await predictions_collection.count_documents({"result": 0})
    disease_predictions = await predictions_collection.count_documents({"result": 1})
    
    return {
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "total_predictions": total_predictions,
        "total_feedback": total_feedback,
        "healthy_predictions": healthy_predictions,
        "disease_predictions": disease_predictions
    }

# Test Route
@api_router.get("/")
async def root():
    return {"message": "Smart Health Disease Prediction System API", "status": "active"}

# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
