import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
from auth import get_password_hash
import uuid
from datetime import datetime

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def seed_doctors():
    # MongoDB connection
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'health_prediction')]
    
    users_collection = db.users
    doctors_collection = db.doctors
    
    # Sample doctors
    doctors_data = [
        {
            "first_name": "Sarah",
            "last_name": "Johnson",
            "username": "dr.sarah",
            "password": "doctor123",
            "email": "sarah.johnson@hospital.com",
            "contact": "555-0101",
            "address": "123 Medical Center, New York, NY 10001",
            "specialization": "Cardiologist"
        },
        {
            "first_name": "Michael",
            "last_name": "Chen",
            "username": "dr.michael",
            "password": "doctor123",
            "email": "michael.chen@hospital.com",
            "contact": "555-0102",
            "address": "456 Heart Clinic, Los Angeles, CA 90001",
            "specialization": "Cardiologist"
        },
        {
            "first_name": "Emily",
            "last_name": "Rodriguez",
            "username": "dr.emily",
            "password": "doctor123",
            "email": "emily.rodriguez@hospital.com",
            "contact": "555-0103",
            "address": "789 Cardiac Institute, Chicago, IL 60601",
            "specialization": "Cardiac Surgeon"
        },
        {
            "first_name": "David",
            "last_name": "Williams",
            "username": "dr.david",
            "password": "doctor123",
            "email": "david.williams@hospital.com",
            "contact": "555-0104",
            "address": "321 Health Plaza, Houston, TX 77001",
            "specialization": "Cardiologist"
        },
        {
            "first_name": "Lisa",
            "last_name": "Anderson",
            "username": "dr.lisa",
            "password": "doctor123",
            "email": "lisa.anderson@hospital.com",
            "contact": "555-0105",
            "address": "654 Medical District, Phoenix, AZ 85001",
            "specialization": "Cardiovascular Specialist"
        }
    ]
    
    print("Seeding sample doctors...")
    
    for doctor_data in doctors_data:
        # Check if doctor already exists
        existing_user = await users_collection.find_one({"username": doctor_data["username"]})
        if existing_user:
            print(f"Doctor {doctor_data['username']} already exists, skipping...")
            continue
        
        # Create user
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "username": doctor_data["username"],
            "email": doctor_data["email"],
            "first_name": doctor_data["first_name"],
            "last_name": doctor_data["last_name"],
            "contact": doctor_data["contact"],
            "address": doctor_data["address"],
            "role": "doctor",
            "hashed_password": get_password_hash(doctor_data["password"]),
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        await users_collection.insert_one(user)
        print(f"Created user for Dr. {doctor_data['first_name']} {doctor_data['last_name']}")
        
        # Create doctor profile
        doctor_profile = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "specialization": doctor_data["specialization"],
            "image_url": None,
            "status": 1,  # Approved
            "created_at": datetime.utcnow()
        }
        await doctors_collection.insert_one(doctor_profile)
        print(f"Created doctor profile for Dr. {doctor_data['first_name']} {doctor_data['last_name']}")
    
    print("\nDoctor seeding completed!")
    print(f"Total doctors in database: {await doctors_collection.count_documents({})}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_doctors())
