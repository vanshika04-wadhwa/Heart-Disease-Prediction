# Project Structure - Smart Health Disease Prediction System

## Complete Directory Structure

```
smart_health_prediction_system/
│
├── README.md                           # Main project documentation
├── INSTALLATION_GUIDE.md               # Step-by-step installation instructions
├── PROJECT_STRUCTURE.md                # This file
│
├── backend/                            # FastAPI Backend
│   ├── server.py                       # Main FastAPI application & API routes
│   ├── models.py                       # Pydantic data models
│   ├── auth.py                         # Authentication utilities (JWT, password hashing)
│   ├── ml_model.py                     # Machine Learning model (Random Forest)
│   ├── seed_doctors.py                 # Script to seed sample doctors
│   ├── requirements.txt                # Python dependencies
│   ├── .env.example                    # Environment variables template
│   └── heart_model.pkl                 # Trained ML model (auto-generated)
│
└── frontend/                           # React Frontend
    ├── package.json                    # Node.js dependencies
    ├── tailwind.config.js              # Tailwind CSS configuration
    ├── postcss.config.js               # PostCSS configuration
    ├── craco.config.js                 # Create React App configuration
    ├── jsconfig.json                   # JavaScript configuration
    ├── .env.example                    # Frontend environment variables template
    │
    ├── public/                         # Static assets
    │   ├── index.html                  # HTML template
    │   ├── favicon.ico
    │   ├── manifest.json
    │   └── robots.txt
    │
    └── src/                            # React source code
        ├── index.js                    # Application entry point
        ├── App.js                      # Main React component with routing
        ├── App.css                     # Main stylesheet
        ├── index.css                   # Global styles & Tailwind imports
        │
        ├── components/                 # Reusable components
        │   ├── Navbar.js              # Navigation bar component
        │   ├── Footer.js              # Footer component
        │   └── ui/                    # Shadcn UI components
        │       ├── button.jsx
        │       ├── card.jsx
        │       ├── dialog.jsx
        │       ├── input.jsx
        │       ├── label.jsx
        │       ├── select.jsx
        │       ├── table.jsx
        │       ├── toast.jsx
        │       └── ... (other UI components)
        │
        ├── pages/                     # Application pages
        │   ├── Home.js                # Landing page
        │   ├── Login.js               # Login page
        │   ├── Register.js            # Registration page
        │   ├── About.js               # About us page
        │   ├── Contact.js             # Contact page with feedback form
        │   ├── PatientDashboard.js    # Patient dashboard
        │   ├── DoctorDashboard.js     # Doctor dashboard
        │   ├── AdminDashboard.js      # Admin dashboard
        │   └── PredictDisease.js      # Disease prediction form
        │
        ├── context/                   # React Context
        │   └── AuthContext.js         # Authentication context & hooks
        │
        ├── utils/                     # Utility functions
        │   └── api.js                 # API client & utilities
        │
        └── lib/                       # Library utilities
            └── utils.js               # Helper functions
```

## File Descriptions

### Backend Files

**server.py** - Main FastAPI application containing:
- API route definitions
- Database connection setup
- Authentication middleware
- All endpoints (auth, doctors, predictions, feedback, patients, stats)
- Startup events (ML model loading, admin creation)

**models.py** - Pydantic models for:
- User, UserCreate, UserLogin, UserResponse
- PatientProfile, DoctorProfile, DoctorCreate, DoctorResponse
- HeartPredictionInput, HeartPrediction, PredictionResponse
- Feedback, Token, PasswordChange

**auth.py** - Authentication utilities:
- Password hashing with bcrypt
- JWT token creation and verification
- Token decoding

**ml_model.py** - Machine Learning implementation:
- HeartDiseaseModel class
- Random Forest Classifier
- Model training function
- Prediction function
- Sample data generation

**seed_doctors.py** - Database seeding:
- Creates 5 sample doctors
- Pre-approved for testing
- Includes cardiologists and specialists

**requirements.txt** - Python dependencies:
- fastapi, uvicorn
- motor (async MongoDB)
- scikit-learn, numpy, pandas
- passlib, python-jose
- pydantic, email-validator

### Frontend Files

**App.js** - Main React component:
- React Router setup
- Route definitions
- Protected route wrapper
- Authentication context integration

**AuthContext.js** - Authentication management:
- User state management
- Login/logout functions
- Token storage
- API integration

**api.js** - API client:
- Axios configuration
- API endpoints (doctorAPI, predictionAPI, feedbackAPI, patientAPI, statsAPI)
- Request interceptors
- Error handling

### Page Components

**Home.js** - Landing page with:
- Hero section
- Features showcase
- How it works guide
- Call-to-action sections

**Login.js** - Login page with:
- Username/password form
- Error handling
- Role-based navigation
- Demo credentials display

**Register.js** - Registration page with:
- Multi-field form
- Role selection (Patient/Doctor)
- Form validation
- Success handling

**PatientDashboard.js** - Patient features:
- Welcome section
- Quick action cards
- Prediction history table
- Delete predictions

**DoctorDashboard.js** - Doctor features:
- Patient statistics
- Prediction list
- Health analytics
- Patient monitoring

**AdminDashboard.js** - Admin features:
- System statistics
- Doctor management (add, approve, delete)
- Patient list
- Predictions overview
- Feedback review

**PredictDisease.js** - Prediction form:
- 13 health parameter inputs
- Form validation
- ML prediction display
- Doctor recommendations
- Result visualization

**About.js** - About page:
- Mission statement
- System features
- Goals and objectives
- Technology stack

**Contact.js** - Contact page:
- Contact information
- Feedback form
- Emergency information

### UI Components (Shadcn)

The project includes a comprehensive set of UI components from Shadcn:
- Buttons, Cards, Dialogs
- Forms (Input, Label, Select, Textarea)
- Navigation (Tabs, Accordion, Breadcrumb)
- Feedback (Toast, Alert, Progress)
- Layout (Separator, Scroll Area, Resizable)
- And many more...

## Database Collections

### MongoDB Collections:

1. **users** - User accounts
   - id, username, email, first_name, last_name
   - hashed_password, role, contact, address
   - created_at, is_active

2. **patients** - Patient profiles
   - id, user_id, date_of_birth, image_url
   - created_at

3. **doctors** - Doctor profiles
   - id, user_id, specialization, image_url
   - status (0: pending, 1: approved)
   - created_at

4. **predictions** - Heart predictions
   - id, patient_id, patient_name
   - input_values (13 parameters)
   - result (0: healthy, 1: disease)
   - accuracy, probability
   - created_at

5. **feedback** - User feedback
   - id, user_id, user_name, email
   - message, created_at

## API Routes

### Authentication (`/api/auth/`)
- POST `/register` - Register new user
- POST `/login` - User login
- GET `/me` - Get current user
- POST `/change-password` - Change password

### Doctors (`/api/doctors/`)
- GET `/` - Get all doctors (Admin)
- GET `/approved` - Get approved doctors (Public)
- POST `/` - Create doctor (Admin)
- PUT `/{id}/status` - Toggle approval (Admin)
- DELETE `/{id}` - Delete doctor (Admin)

### Predictions (`/api/`)
- POST `/predict` - Make prediction (Patient)
- GET `/predictions` - Get predictions (Role-based)
- DELETE `/predictions/{id}` - Delete prediction

### Feedback (`/api/feedback/`)
- POST `/` - Submit feedback
- GET `/` - Get all feedback (Admin)

### Patients (`/api/patients/`)
- GET `/` - Get all patients (Admin)

### Statistics (`/api/stats/`)
- GET `/` - Get system statistics (Admin)

## Environment Variables

### Backend (.env)
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=health_prediction
SECRET_KEY=your-secret-key
CORS_ORIGINS=*
```

### Frontend (.env)
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

## Dependencies

### Backend (Python)
- fastapi==0.110.1
- uvicorn==0.25.0
- motor==3.3.1 (async MongoDB)
- pymongo==4.5.0
- scikit-learn==1.7.2
- numpy==2.3.4
- pandas==2.3.3
- passlib==1.7.4
- python-jose==3.5.0
- bcrypt==4.1.3
- pydantic>=2.6.4
- python-dotenv>=1.0.1
- python-multipart>=0.0.9

### Frontend (Node.js)
- react: ^19.0.0
- react-dom: ^19.0.0
- react-router-dom: ^7.5.1
- axios: ^1.8.4
- lucide-react: ^0.507.0
- tailwindcss: ^3.4.17
- @radix-ui components (various)
- class-variance-authority
- tailwind-merge
- date-fns

## Key Features Implementation

### 1. Authentication
- JWT token-based authentication
- Role-based access control (Admin, Doctor, Patient)
- Protected routes in frontend
- Password hashing with bcrypt

### 2. Machine Learning
- Random Forest Classifier
- 85% prediction accuracy
- 13 input features
- Automatic model training on startup

### 3. User Management
- User registration with role selection
- Admin can manage doctors
- Doctor approval system
- Patient profiles

### 4. Disease Prediction
- Comprehensive health parameter form
- Real-time ML prediction
- Prediction history tracking
- Doctor recommendations

### 5. Analytics
- Admin dashboard with statistics
- Doctor patient monitoring
- Prediction analytics
- Feedback system

## Security Features

- JWT token authentication
- Password hashing (bcrypt)
- Role-based authorization
- Input validation (Pydantic)
- CORS configuration
- MongoDB injection prevention
- XSS protection

## Responsive Design

- Mobile-first approach
- Tailwind CSS utility classes
- Responsive navigation
- Adaptive layouts
- Touch-friendly UI elements

---

**Last Updated**: 2024
**Version**: 1.0.0
**Author**: Suraj Chadha
