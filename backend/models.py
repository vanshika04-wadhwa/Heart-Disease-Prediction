from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
import uuid

class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    contact: str
    address: str
    role: str  # 'admin', 'doctor', 'patient'

class UserCreate(UserBase):
    password: str
    date_of_birth: Optional[str] = None
    image_url: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: datetime

class PatientProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    date_of_birth: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DoctorProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    specialization: str
    image_url: Optional[str] = None
    status: int = 0  # 0: pending, 1: approved
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DoctorCreate(BaseModel):
    first_name: str
    last_name: str
    username: str
    password: str
    email: EmailStr
    contact: str
    address: str
    specialization: str
    image_url: Optional[str] = None

class DoctorResponse(BaseModel):
    id: str
    user_id: str
    first_name: str
    last_name: str
    email: str
    contact: str
    address: str
    specialization: str
    image_url: Optional[str] = None
    status: int
    created_at: datetime

class HeartPredictionInput(BaseModel):
    age: int
    sex: int  # 0: female, 1: male
    cp: int  # chest pain type (0-3)
    trestbps: int  # resting blood pressure
    chol: int  # cholesterol
    fbs: int  # fasting blood sugar
    restecg: int  # resting electrocardiographic results (0-2)
    thalach: int  # maximum heart rate achieved
    exang: int  # exercise induced angina
    oldpeak: float  # ST depression
    slope: int  # slope of peak exercise ST segment
    ca: int  # number of major vessels (0-3)
    thal: int  # thalassemia (0-3)

class HeartPrediction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    patient_name: str
    input_values: dict
    result: int  # 0: healthy, 1: disease
    accuracy: float
    probability: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PredictionResponse(BaseModel):
    id: str
    result: int
    accuracy: float
    probability: float
    message: str
    created_at: datetime

class Feedback(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    email: str
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FeedbackCreate(BaseModel):
    message: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class PasswordChange(BaseModel):
    old_password: str
    new_password: str
