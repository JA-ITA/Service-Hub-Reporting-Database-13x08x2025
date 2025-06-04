from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import jwt
import bcrypt
import csv
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import shutil

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create uploads directory
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Settings
JWT_SECRET = "your-secret-key-here"
JWT_ALGORITHM = "HS256"
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI(title="CLIENT SERVICES Platform")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    password_hash: str
    role: str  # 'admin', 'manager', 'data_entry'
    assigned_location: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    assigned_location: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class ServiceLocation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class ServiceLocationCreate(BaseModel):
    name: str
    description: Optional[str] = None

class FormTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    fields: List[Dict[str, Any]]  # Dynamic field definitions
    assigned_locations: List[str] = []
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class FormTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    fields: List[Dict[str, Any]]
    assigned_locations: List[str] = []

class DataSubmission(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    template_id: str
    submitted_by: str
    service_location: str
    month_year: str  # Format: "YYYY-MM"
    form_data: Dict[str, Any]
    attachments: List[str] = []  # File paths
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "submitted"  # submitted, reviewed, approved

class DataSubmissionCreate(BaseModel):
    template_id: str
    service_location: str
    month_year: str
    form_data: Dict[str, Any]

# Helper functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, username: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["user_id"]})
        if user:
            return User(**user)
        raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# Initialize default data
async def initialize_default_data():
    # Create default admin if not exists
    admin_exists = await db.users.find_one({"username": "admin"})
    if not admin_exists:
        admin_user = User(
            username="admin",
            password_hash=hash_password("admin123"),
            role="admin"
        )
        await db.users.insert_one(admin_user.dict())
        
    # Create sample locations if not exist
    locations_count = await db.service_locations.count_documents({})
    if locations_count == 0:
        sample_locations = [
            ServiceLocation(name="Central Hub", description="Main service location in city center"),
            ServiceLocation(name="North Branch", description="Northern district service hub"),
            ServiceLocation(name="South Branch", description="Southern district service hub"),
            ServiceLocation(name="East Branch", description="Eastern district service hub"),
            ServiceLocation(name="West Branch", description="Western district service hub")
        ]
        for location in sample_locations:
            await db.service_locations.insert_one(location.dict())

# Authentication Routes
@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"username": credentials.username})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user["is_active"]:
        raise HTTPException(status_code=401, detail="Account is disabled")
    
    token = create_jwt_token(user["id"], user["username"], user["role"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "assigned_location": user.get("assigned_location")
        }
    }

@api_router.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "assigned_location": current_user.assigned_location
    }

# User Management Routes (Admin only)
@api_router.post("/users", response_model=User)
async def create_user(user_data: UserCreate, current_user: User = Depends(require_role(["admin"]))):
    # Check if username already exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        assigned_location=user_data.assigned_location
    )
    await db.users.insert_one(user.dict())
    return user

@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(require_role(["admin"]))):
    users = await db.users.find({"is_active": True}).to_list(1000)
    return [User(**user) for user in users]

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, user_data: dict, current_user: User = Depends(require_role(["admin"]))):
    if "password" in user_data:
        user_data["password_hash"] = hash_password(user_data["password"])
        del user_data["password"]
    
    await db.users.update_one({"id": user_id}, {"$set": user_data})
    return {"message": "User updated successfully"}

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(require_role(["admin"]))):
    await db.users.update_one({"id": user_id}, {"$set": {"is_active": False}})
    return {"message": "User deleted successfully"}

# Service Location Routes
@api_router.post("/locations", response_model=ServiceLocation)
async def create_location(location_data: ServiceLocationCreate, current_user: User = Depends(require_role(["admin"]))):
    location = ServiceLocation(**location_data.dict())
    await db.service_locations.insert_one(location.dict())
    return location

@api_router.get("/locations", response_model=List[ServiceLocation])
async def get_locations(current_user: User = Depends(get_current_user)):
    locations = await db.service_locations.find({"is_active": True}).to_list(1000)
    return [ServiceLocation(**location) for location in locations]

@api_router.put("/locations/{location_id}")
async def update_location(location_id: str, location_data: dict, current_user: User = Depends(require_role(["admin"]))):
    await db.service_locations.update_one({"id": location_id}, {"$set": location_data})
    return {"message": "Location updated successfully"}

@api_router.delete("/locations/{location_id}")
async def delete_location(location_id: str, current_user: User = Depends(require_role(["admin"]))):
    await db.service_locations.update_one({"id": location_id}, {"$set": {"is_active": False}})
    return {"message": "Location deleted successfully"}

# Form Template Routes
@api_router.post("/templates", response_model=FormTemplate)
async def create_template(template_data: FormTemplateCreate, current_user: User = Depends(require_role(["admin"]))):
    template = FormTemplate(**template_data.dict(), created_by=current_user.id)
    await db.form_templates.insert_one(template.dict())
    return template

@api_router.get("/templates", response_model=List[FormTemplate])
async def get_templates(current_user: User = Depends(get_current_user)):
    if current_user.role == "admin":
        templates = await db.form_templates.find({"is_active": True}).to_list(1000)
    else:
        # For managers and data entry, only show templates assigned to their location
        templates = await db.form_templates.find({
            "is_active": True,
            "assigned_locations": {"$in": [current_user.assigned_location]}
        }).to_list(1000)
    return [FormTemplate(**template) for template in templates]

@api_router.get("/templates/{template_id}")
async def get_template(template_id: str, current_user: User = Depends(require_role(["admin"]))):
    template = await db.form_templates.find_one({"id": template_id})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Remove ObjectId for JSON serialization
    if "_id" in template:
        del template["_id"]
    
    return template

@api_router.put("/templates/{template_id}")
async def update_template(template_id: str, template_data: FormTemplateCreate, current_user: User = Depends(require_role(["admin"]))):
    # Check if template exists
    existing_template = await db.form_templates.find_one({"id": template_id})
    if not existing_template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Update template with new data
    update_data = template_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    update_data["updated_by"] = current_user.id
    
    await db.form_templates.update_one({"id": template_id}, {"$set": update_data})
    return {"message": "Template updated successfully"}

@api_router.delete("/templates/{template_id}")
async def delete_template(template_id: str, current_user: User = Depends(require_role(["admin"]))):
    await db.form_templates.update_one({"id": template_id}, {"$set": {"is_active": False}})
    return {"message": "Template deleted successfully"}

# Data Submission Routes
@api_router.post("/submissions")
async def create_submission(submission_data: DataSubmissionCreate, current_user: User = Depends(get_current_user)):
    # Validate user can submit to this location
    if current_user.role in ["manager", "data_entry"] and current_user.assigned_location != submission_data.service_location:
        raise HTTPException(status_code=403, detail="Cannot submit data for this location")
    
    submission = DataSubmission(**submission_data.dict(), submitted_by=current_user.id)
    await db.data_submissions.insert_one(submission.dict())
    return {"message": "Data submitted successfully", "id": submission.id}

@api_router.get("/submissions")
async def get_submissions(
    location: Optional[str] = None,
    month_year: Optional[str] = None,
    template_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    query = {}
    
    # Role-based filtering
    if current_user.role in ["manager", "data_entry"]:
        query["service_location"] = current_user.assigned_location
    elif location:
        query["service_location"] = location
    
    if month_year:
        query["month_year"] = month_year
    if template_id:
        query["template_id"] = template_id
    
    submissions = await db.data_submissions.find(query).to_list(1000)
    
    # Convert ObjectIds to strings for JSON serialization
    for submission in submissions:
        if "_id" in submission:
            del submission["_id"]
    
    return submissions

@api_router.put("/submissions/{submission_id}")
async def update_submission(submission_id: str, submission_data: dict, current_user: User = Depends(get_current_user)):
    # Check if user can edit this submission
    submission = await db.data_submissions.find_one({"id": submission_id})
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    if current_user.role in ["manager", "data_entry"] and submission["service_location"] != current_user.assigned_location:
        raise HTTPException(status_code=403, detail="Cannot edit this submission")
    
    await db.data_submissions.update_one({"id": submission_id}, {"$set": submission_data})
    return {"message": "Submission updated successfully"}

# File Upload Routes
@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    # Validate file type
    allowed_types = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf', 'application/msword', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/csv'
    }
    
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not allowed")
    
    # Create unique filename
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"filename": unique_filename, "original_name": file.filename}

@api_router.get("/files/{filename}")
async def get_file(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

# Report Generation Routes
@api_router.get("/reports/csv")
async def export_csv(
    location: Optional[str] = None,
    month_year: Optional[str] = None,
    template_id: Optional[str] = None,
    current_user: User = Depends(require_role(["admin", "manager"]))
):
    # Get submissions based on filters
    query = {}
    if current_user.role == "manager":
        query["service_location"] = current_user.assigned_location
    elif location:
        query["service_location"] = location
    
    if month_year:
        query["month_year"] = month_year
    if template_id:
        query["template_id"] = template_id
    
    submissions = await db.data_submissions.find(query).to_list(1000)
    
    # Remove ObjectIds for CSV processing
    for submission in submissions:
        if "_id" in submission:
            del submission["_id"]
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    if submissions:
        headers = ["ID", "Template", "Location", "Month/Year", "Submitted By", "Submitted At"]
        # Add dynamic form field headers
        if submissions[0].get("form_data"):
            headers.extend(submissions[0]["form_data"].keys())
        writer.writerow(headers)
        
        # Write data
        for submission in submissions:
            row = [
                submission["id"],
                submission["template_id"],
                submission["service_location"],
                submission["month_year"],
                submission["submitted_by"],
                submission["submitted_at"]
            ]
            if submission.get("form_data"):
                row.extend(submission["form_data"].values())
            writer.writerow(row)
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=report.csv"}
    )

@api_router.get("/")
async def root():
    return {"message": "CLIENT SERVICES Platform API"}

# Initialize data on startup
@app.on_event("startup")
async def startup_event():
    await initialize_default_data()

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
