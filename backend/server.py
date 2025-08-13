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
    role: str  # 'admin', 'manager', 'data_entry', 'statistician'
    assigned_location: Optional[str] = None  # Keep for backward compatibility
    assigned_locations: List[str] = []  # New field for multiple locations
    has_all_locations: bool = False  # True if user has access to all locations
    page_permissions: List[str] = []  # List of allowed pages
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    status: str = "approved"  # "pending", "approved", "rejected"
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    assigned_location: Optional[str] = None  # Keep for backward compatibility
    assigned_locations: List[str] = []  # New field for multiple locations
    has_all_locations: bool = False
    page_permissions: List[str] = []

class UserRegister(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    email: Optional[str] = None

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

class AdminSetting(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    setting_key: str
    setting_value: str
    description: Optional[str] = None
    updated_by: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AdminSettingCreate(BaseModel):
    setting_key: str
    setting_value: str
    description: Optional[str] = None

class PasswordResetRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    user_id: str
    reset_token: Optional[str] = None
    status: str = "pending"  # pending, approved, used, expired
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True

class PasswordResetRequestCreate(BaseModel):
    username: str

class PasswordResetToken(BaseModel):
    token: str
    new_password: str

class PasswordResetInitiate(BaseModel):
    username: str

class PasswordResetComplete(BaseModel):
    username: str
    reset_code: str
    new_password: str

class UserApproval(BaseModel):
    user_id: str
    status: str  # "approved" or "rejected"
    assigned_location: Optional[str] = None
    role: str = "data_entry"

class UserRole(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    display_name: str
    description: Optional[str] = None
    permissions: List[str] = []  # List of allowed pages/actions
    is_system_role: bool = False  # Cannot be deleted if True
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class UserRoleCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    permissions: List[str] = []

class StatisticsQuery(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    locations: Optional[List[str]] = []
    user_roles: Optional[List[str]] = []
    templates: Optional[List[str]] = []
    status: Optional[List[str]] = []
    group_by: Optional[str] = "location"  # location, month, template, status, user_role, custom_field
    analyze_custom_fields: Optional[bool] = False
    custom_field_name: Optional[str] = None
    custom_field_analysis_type: Optional[str] = "frequency"  # frequency, numerical, trend

# Helper function to get default page permissions based on role
def get_default_permissions(role: str) -> List[str]:
    permissions_map = {
        "admin": ["dashboard", "users", "locations", "templates", "reports", "submit", "statistics"],
        "manager": ["dashboard", "submit", "reports"],
        "data_entry": ["dashboard", "submit"],
        "statistician": ["dashboard", "statistics", "reports"]
    }
    return permissions_map.get(role, [])

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
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication error")

def require_role(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# Initialize default data
async def initialize_default_data():
    # Create default roles if not exist
    default_roles = [
        UserRole(name="admin", display_name="Administrator", description="Full system access", 
                permissions=["dashboard", "users", "locations", "templates", "reports", "submit", "statistics", "roles"], 
                is_system_role=True, created_by="system"),
        UserRole(name="manager", display_name="Service Hub Manager", description="Manage assigned location", 
                permissions=["dashboard", "submit", "reports"], 
                is_system_role=True, created_by="system"),
        UserRole(name="data_entry", display_name="Data Entry Officer", description="Submit data only", 
                permissions=["dashboard", "submit"], 
                is_system_role=True, created_by="system"),
        UserRole(name="statistician", display_name="Statistician", description="View statistics and reports", 
                permissions=["dashboard", "statistics", "reports"], 
                is_system_role=True, created_by="system")
    ]
    
    for role in default_roles:
        existing_role = await db.user_roles.find_one({"name": role.name})
        if not existing_role:
            await db.user_roles.insert_one(role.dict())

    # Create default admin if not exists
    admin_exists = await db.users.find_one({"username": "admin"})
    if not admin_exists:
        admin_user = User(
            username="admin",
            password_hash=hash_password("admin123"),
            role="admin",
            page_permissions=get_default_permissions("admin"),
            status="approved"  # Admin is pre-approved
        )
        await db.users.insert_one(admin_user.dict())
    else:
        # Update existing admin with new permissions if needed
        await db.users.update_one(
            {"username": "admin"}, 
            {"$set": {"page_permissions": get_default_permissions("admin")}}
        )
        
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
    
    if user.get("status", "approved") == "pending":
        raise HTTPException(status_code=401, detail="Account is pending approval")
    
    if user.get("status", "approved") == "rejected":
        raise HTTPException(status_code=401, detail="Account has been rejected")
    
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

@api_router.post("/auth/register")
async def register(user_data: UserRegister):
    """Register a new user (requires admin approval)"""
    # Check if username already exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create new user with pending status
    user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role="data_entry",  # Default role for registered users
        page_permissions=get_default_permissions("data_entry"),
        status="pending",  # Requires admin approval
        is_active=False  # Inactive until approved
    )
    
    # Add additional fields if provided
    user_dict = user.dict()
    if user_data.full_name:
        user_dict["full_name"] = user_data.full_name
    if user_data.email:
        user_dict["email"] = user_data.email
    
    await db.users.insert_one(user_dict)
    
    return {
        "message": "Registration successful. Your account is pending admin approval.",
        "user_id": user.id,
        "status": "pending"
    }

@api_router.post("/auth/forgot-password")
async def forgot_password(request_data: PasswordResetInitiate):
    """Initiate password reset process"""
    user = await db.users.find_one({"username": request_data.username})
    if not user:
        # Don't reveal if user exists for security
        return {"message": "If the username exists, a reset code has been generated. Please contact your administrator."}
    
    # Generate a simple reset code (6-digit numeric)
    reset_code = str(uuid.uuid4().int)[:6]
    
    # Create password reset request
    reset_request = PasswordResetRequest(
        username=user["username"],
        user_id=user["id"],
        reset_token=reset_code,
        status="pending",
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    
    await db.password_reset_requests.insert_one(reset_request.dict())
    
    return {
        "message": "Password reset code generated. Please contact your administrator with this code.",
        "reset_code": reset_code,
        "username": user["username"]
    }

@api_router.post("/auth/reset-password")
async def reset_password(reset_data: PasswordResetComplete):
    """Complete password reset with code"""
    # Find the reset request
    reset_request = await db.password_reset_requests.find_one({
        "username": reset_data.username,
        "reset_token": reset_data.reset_code,
        "status": "pending",
        "is_active": True
    })
    
    if not reset_request:
        raise HTTPException(status_code=400, detail="Invalid reset code or username")
    
    # Check if expired
    if reset_request["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset code has expired")
    
    # Find user and update password
    user = await db.users.find_one({"username": reset_data.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate new password
    if len(reset_data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
    
    # Update password
    hashed_password = hash_password(reset_data.new_password)
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "password_hash": hashed_password,
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Mark reset request as used
    await db.password_reset_requests.update_one(
        {"id": reset_request["id"]},
        {"$set": {
            "status": "used",
            "used_at": datetime.utcnow(),
            "is_active": False
        }}
    )
    
    return {"message": "Password reset successfully"}

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
    
    # Set default permissions if not provided
    permissions = user_data.page_permissions if user_data.page_permissions else get_default_permissions(user_data.role)
    
    user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        assigned_location=user_data.assigned_location,
        page_permissions=permissions
    )
    await db.users.insert_one(user.dict())
    return user

@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(require_role(["admin"]))):
    users = await db.users.find({"is_active": True}).to_list(1000)
    return [User(**user) for user in users]

@api_router.get("/admin/pending-users")
async def get_pending_users(current_user: User = Depends(require_role(["admin"]))):
    """Get all pending user registrations"""
    pending_users = await db.users.find({"status": "pending"}).to_list(1000)
    
    # Remove password hashes and ObjectIds for security
    for user in pending_users:
        if "_id" in user:
            del user["_id"]
        if "password_hash" in user:
            del user["password_hash"]
    
    return pending_users

@api_router.post("/admin/approve-user")
async def approve_user(approval_data: UserApproval, current_user: User = Depends(require_role(["admin"]))):
    """Approve or reject a pending user"""
    # Find the pending user
    pending_user = await db.users.find_one({"id": approval_data.user_id, "status": "pending"})
    if not pending_user:
        raise HTTPException(status_code=404, detail="Pending user not found")
    
    update_data = {
        "status": approval_data.status,
        "approved_by": current_user.id,
        "approved_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    if approval_data.status == "approved":
        update_data.update({
            "is_active": True,
            "role": approval_data.role,
            "assigned_location": approval_data.assigned_location,
            "page_permissions": get_default_permissions(approval_data.role)
        })
    else:
        update_data["is_active"] = False
    
    await db.users.update_one({"id": approval_data.user_id}, {"$set": update_data})
    
    return {
        "message": f"User {approval_data.status} successfully",
        "user_id": approval_data.user_id,
        "username": pending_user["username"],
        "status": approval_data.status
    }

@api_router.get("/admin/password-reset-requests")
async def get_password_reset_requests(current_user: User = Depends(require_role(["admin"]))):
    """Get all pending password reset requests"""
    requests = await db.password_reset_requests.find({
        "status": "pending",
        "is_active": True
    }).to_list(1000)
    
    # Remove ObjectIds for JSON serialization
    for request in requests:
        if "_id" in request:
            del request["_id"]
    
    return requests

@api_router.get("/admin/deleted-users")
async def get_deleted_users(current_user: User = Depends(require_role(["admin"]))):
    """Get all deleted/inactive users"""
    deleted_users = await db.users.find({"is_active": False}).to_list(1000)
    
    # Remove password hashes and ObjectIds for security
    for user in deleted_users:
        if "_id" in user:
            del user["_id"]
        if "password_hash" in user:
            del user["password_hash"]
    
    return deleted_users

@api_router.post("/admin/restore-user/{user_id}")
async def restore_user(user_id: str, current_user: User = Depends(require_role(["admin"]))):
    """Restore a deleted user"""
    # Check if user exists and is deleted
    user = await db.users.find_one({"id": user_id, "is_active": False})
    if not user:
        raise HTTPException(status_code=404, detail="Deleted user not found")
    
    # Restore the user
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "is_active": True,
            "restored_at": datetime.utcnow(),
            "restored_by": current_user.id,
            "updated_at": datetime.utcnow(),
            "updated_by": current_user.id
        }}
    )
    
    return {
        "message": "User restored successfully",
        "user_id": user_id,
        "username": user.get("username"),
        "restored_by": current_user.username,
        "restored_at": datetime.utcnow().isoformat()
    }

@api_router.get("/users/{user_id}")
async def get_user(user_id: str, current_user: User = Depends(require_role(["admin"]))):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Remove ObjectId and password hash for security
    if "_id" in user:
        del user["_id"]
    if "password_hash" in user:
        del user["password_hash"]
    
    return user

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, user_data: dict, current_user: User = Depends(require_role(["admin"]))):
    # Check if user exists
    existing_user = await db.users.find_one({"id": user_id})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # If username is being changed, check if it's unique
    if "username" in user_data and user_data["username"] != existing_user["username"]:
        existing_username = await db.users.find_one({"username": user_data["username"]})
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already exists")
    
    # Hash password if provided
    if "password" in user_data:
        user_data["password_hash"] = hash_password(user_data["password"])
        del user_data["password"]
    
    # Add update metadata
    user_data["updated_at"] = datetime.utcnow()
    user_data["updated_by"] = current_user.id
    
    await db.users.update_one({"id": user_id}, {"$set": user_data})
    return {"message": "User updated successfully"}

@api_router.post("/users/{user_id}/reset-password")
async def reset_user_password(user_id: str, password_data: dict, current_user: User = Depends(require_role(["admin"]))):
    """Reset a user's password (Admin only)"""
    # Check if user exists
    existing_user = await db.users.find_one({"id": user_id})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate new password
    new_password = password_data.get("new_password")
    if not new_password:
        raise HTTPException(status_code=400, detail="New password is required")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
    
    # Hash and update password
    hashed_password = hash_password(new_password)
    
    update_data = {
        "password_hash": hashed_password,
        "updated_at": datetime.utcnow(),
        "updated_by": current_user.id,
        "password_reset_at": datetime.utcnow(),
        "password_reset_by": current_user.id
    }
    
    await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    return {
        "message": "Password reset successfully",
        "username": existing_user["username"],
        "reset_by": current_user.username,
        "reset_at": datetime.utcnow().isoformat()
    }

@api_router.post("/users/change-password")
async def change_own_password(password_data: dict, current_user: User = Depends(get_current_user)):
    """Allow users to change their own password"""
    current_password = password_data.get("current_password")
    new_password = password_data.get("new_password")
    
    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="Both current and new passwords are required")
    
    # Verify current password
    user = await db.users.find_one({"id": current_user.id})
    if not user or not verify_password(current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Validate new password
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
    
    if new_password == current_password:
        raise HTTPException(status_code=400, detail="New password must be different from current password")
    
    # Hash and update password
    hashed_password = hash_password(new_password)
    
    update_data = {
        "password_hash": hashed_password,
        "updated_at": datetime.utcnow(),
        "password_changed_at": datetime.utcnow()
    }
    
    await db.users.update_one({"id": current_user.id}, {"$set": update_data})
    
    return {
        "message": "Password changed successfully",
        "changed_at": datetime.utcnow().isoformat()
    }

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(require_role(["admin"]))):
    """Soft delete a user (mark as inactive)"""
    # Check if user exists
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting the admin user
    if user.get("username") == "admin":
        raise HTTPException(status_code=403, detail="Cannot delete admin user")
    
    # Mark user as inactive with audit trail
    await db.users.update_one(
        {"id": user_id}, 
        {"$set": {
            "is_active": False,
            "deleted_at": datetime.utcnow(),
            "deleted_by": current_user.id,
            "updated_at": datetime.utcnow(),
            "updated_by": current_user.id
        }}
    )
    
    return {
        "message": "User deleted successfully",
        "username": user.get("username"),
        "deleted_by": current_user.username,
        "deleted_at": datetime.utcnow().isoformat()
    }

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

@api_router.get("/templates/deleted", response_model=List[FormTemplate])
async def get_deleted_templates(current_user: User = Depends(require_role(["admin"]))):
    """Get all soft-deleted templates"""
    templates = await db.form_templates.find({"is_active": False}).to_list(1000)
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

@api_router.post("/templates/{template_id}/restore")
async def restore_template(template_id: str, current_user: User = Depends(require_role(["admin"]))):
    """Restore a soft-deleted template"""
    result = await db.form_templates.update_one(
        {"id": template_id, "is_active": False}, 
        {"$set": {"is_active": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Template not found or already active")
    return {"message": "Template restored successfully"}

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

@api_router.get("/submissions/{submission_id}")
async def get_submission(submission_id: str, current_user: User = Depends(get_current_user)):
    try:
        submission = await db.data_submissions.find_one({"id": submission_id})
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Check if user can view this submission
        if current_user.role in ["manager", "data_entry"] and submission["service_location"] != current_user.assigned_location:
            raise HTTPException(status_code=403, detail="Cannot view this submission")
        
        # Remove ObjectId for JSON serialization
        if "_id" in submission:
            del submission["_id"]
        
        return submission
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting submission {submission_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.put("/submissions/{submission_id}")
async def update_submission(submission_id: str, submission_data: dict, current_user: User = Depends(get_current_user)):
    # Check if user can edit this submission
    submission = await db.data_submissions.find_one({"id": submission_id})
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Only managers and admins can edit submissions
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions to edit submissions")
    
    # Managers can only edit submissions from their location
    if current_user.role == "manager" and submission["service_location"] != current_user.assigned_location:
        raise HTTPException(status_code=403, detail="Cannot edit submissions from other locations")
    
    # Add update metadata
    submission_data["updated_at"] = datetime.utcnow()
    submission_data["updated_by"] = current_user.id
    
    await db.data_submissions.update_one({"id": submission_id}, {"$set": submission_data})
    return {"message": "Submission updated successfully"}

@api_router.delete("/submissions/{submission_id}")
async def delete_submission(submission_id: str, current_user: User = Depends(require_role(["admin"]))):
    """Delete a submission (Admin only)"""
    # Check if submission exists
    submission = await db.data_submissions.find_one({"id": submission_id})
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Store submission info for response
    submission_info = {
        "id": submission["id"],
        "template_id": submission["template_id"],
        "service_location": submission["service_location"],
        "month_year": submission["month_year"],
        "submitted_by": submission["submitted_by"],
        "submitted_at": submission["submitted_at"]
    }
    
    # Delete the submission
    result = await db.data_submissions.delete_one({"id": submission_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Log the deletion
    logger.info(f"Submission {submission_id} deleted by admin {current_user.username}")
    
    return {
        "message": "Submission deleted successfully",
        "deleted_submission": submission_info,
        "deleted_by": current_user.username,
        "deleted_at": datetime.utcnow().isoformat()
    }

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

# User Role Management Routes (Admin only)
@api_router.post("/roles", response_model=UserRole)
async def create_role(role_data: UserRoleCreate, current_user: User = Depends(require_role(["admin"]))):
    # Check if role name already exists
    existing_role = await db.user_roles.find_one({"name": role_data.name})
    if existing_role:
        raise HTTPException(status_code=400, detail="Role name already exists")
    
    role = UserRole(**role_data.dict(), created_by=current_user.id)
    await db.user_roles.insert_one(role.dict())
    return role

@api_router.get("/roles")
async def get_roles(current_user: User = Depends(require_role(["admin"]))):
    roles = await db.user_roles.find({"is_active": True}).to_list(1000)
    
    # Remove ObjectIds for JSON serialization
    for role in roles:
        if "_id" in role:
            del role["_id"]
    
    return roles

@api_router.get("/roles/{role_id}")
async def get_role(role_id: str, current_user: User = Depends(require_role(["admin"]))):
    role = await db.user_roles.find_one({"id": role_id})
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Remove ObjectId for JSON serialization
    if "_id" in role:
        del role["_id"]
    
    return role

@api_router.put("/roles/{role_id}")
async def update_role(role_id: str, role_data: UserRoleCreate, current_user: User = Depends(require_role(["admin"]))):
    # Check if role exists
    existing_role = await db.user_roles.find_one({"id": role_id})
    if not existing_role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Check if new name conflicts with existing role (excluding current role)
    if role_data.name != existing_role["name"]:
        name_conflict = await db.user_roles.find_one({"name": role_data.name, "id": {"$ne": role_id}})
        if name_conflict:
            raise HTTPException(status_code=400, detail="Role name already exists")
    
    update_data = role_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    update_data["updated_by"] = current_user.id
    
    await db.user_roles.update_one({"id": role_id}, {"$set": update_data})
    return {"message": "Role updated successfully"}

@api_router.delete("/roles/{role_id}")
async def delete_role(role_id: str, current_user: User = Depends(require_role(["admin"]))):
    # Check if role exists
    role = await db.user_roles.find_one({"id": role_id})
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Check if it's a system role
    if role.get("is_system_role", False):
        raise HTTPException(status_code=403, detail="Cannot delete system roles")
    
    # Check if any users are using this role
    users_with_role = await db.users.find({"role": role["name"], "is_active": True}).to_list(1000)
    if users_with_role:
        raise HTTPException(status_code=400, detail=f"Cannot delete role: {len(users_with_role)} users are assigned to this role")
    
    await db.user_roles.update_one({"id": role_id}, {"$set": {"is_active": False}})
    return {"message": "Role deleted successfully"}

# Enhanced function to get available roles
async def get_available_roles():
    """Get all active roles for dropdown selection"""
    roles = await db.user_roles.find({"is_active": True}).to_list(1000)
    return [{"name": role["name"], "display_name": role["display_name"]} for role in roles]

# Admin Settings Routes
@api_router.post("/admin/settings")
async def create_or_update_setting(setting_data: AdminSettingCreate, current_user: User = Depends(require_role(["admin"]))):
    # Check if setting already exists
    existing_setting = await db.admin_settings.find_one({"setting_key": setting_data.setting_key})
    
    if existing_setting:
        # Update existing setting
        update_data = {
            "setting_value": setting_data.setting_value,
            "description": setting_data.description,
            "updated_by": current_user.id,
            "updated_at": datetime.utcnow()
        }
        await db.admin_settings.update_one({"setting_key": setting_data.setting_key}, {"$set": update_data})
        return {"message": "Setting updated successfully"}
    else:
        # Create new setting
        setting = AdminSetting(**setting_data.dict(), updated_by=current_user.id)
        await db.admin_settings.insert_one(setting.dict())
        return {"message": "Setting created successfully"}

@api_router.get("/admin/settings/{setting_key}")
async def get_setting(setting_key: str, current_user: User = Depends(get_current_user)):
    setting = await db.admin_settings.find_one({"setting_key": setting_key})
    if not setting:
        return {"setting_key": setting_key, "setting_value": None}
    
    # Remove ObjectId for JSON serialization
    if "_id" in setting:
        del setting["_id"]
    
    return setting

@api_router.get("/admin/settings")
async def get_all_settings(current_user: User = Depends(require_role(["admin"]))):
    settings = await db.admin_settings.find().to_list(1000)
    
    # Remove ObjectIds for JSON serialization
    for setting in settings:
        if "_id" in setting:
            del setting["_id"]
    
    return settings

# Dashboard Analytics Routes
@api_router.get("/dashboard/submissions-by-location")
async def get_submissions_by_location(
    month_year: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get submission statistics by location"""
    pipeline = []
    
    # Add month/year filter if provided
    match_conditions = {}
    if month_year:
        match_conditions["month_year"] = month_year
    
    # Role-based filtering
    if current_user.role in ["manager", "data_entry"]:
        match_conditions["service_location"] = current_user.assigned_location
    
    if match_conditions:
        pipeline.append({"$match": match_conditions})
    
    # Group by location and count submissions
    pipeline.extend([
        {
            "$group": {
                "_id": "$service_location",
                "submission_count": {"$sum": 1},
                "statuses": {
                    "$push": "$status"
                },
                "latest_submission": {"$max": "$submitted_at"}
            }
        },
        {
            "$project": {
                "location": "$_id",
                "submission_count": 1,
                "approved_count": {
                    "$size": {
                        "$filter": {
                            "input": "$statuses",
                            "cond": {"$eq": ["$$this", "approved"]}
                        }
                    }
                },
                "submitted_count": {
                    "$size": {
                        "$filter": {
                            "input": "$statuses",
                            "cond": {"$eq": ["$$this", "submitted"]}
                        }
                    }
                },
                "reviewed_count": {
                    "$size": {
                        "$filter": {
                            "input": "$statuses",
                            "cond": {"$eq": ["$$this", "reviewed"]}
                        }
                    }
                },
                "rejected_count": {
                    "$size": {
                        "$filter": {
                            "input": "$statuses",
                            "cond": {"$eq": ["$$this", "rejected"]}
                        }
                    }
                },
                "latest_submission": 1,
                "_id": 0
            }
        },
        {"$sort": {"submission_count": -1}}
    ])
    
    results = await db.data_submissions.aggregate(pipeline).to_list(1000)
    return results

@api_router.get("/dashboard/missing-reports")
async def get_missing_reports(current_user: User = Depends(get_current_user)):
    """Get locations that haven't submitted reports by the deadline"""
    
    # Get deadline setting
    deadline_setting = await db.admin_settings.find_one({"setting_key": "report_deadline"})
    if not deadline_setting:
        return {
            "deadline": None,
            "missing_locations": [],
            "message": "No deadline set by administrator"
        }
    
    deadline_date = deadline_setting["setting_value"]
    
    # Get all active locations
    all_locations = await db.service_locations.find({"is_active": True}).to_list(1000)
    
    # Get locations that have submitted reports after the deadline
    submitted_locations = await db.data_submissions.find({
        "submitted_at": {"$gte": datetime.fromisoformat(deadline_date.replace("Z", "+00:00"))}
    }).distinct("service_location")
    
    # Find missing locations
    missing_locations = []
    for location in all_locations:
        if location["name"] not in submitted_locations:
            # Role-based filtering - only show if user has access
            if current_user.role == "admin" or current_user.assigned_location == location["name"]:
                missing_locations.append({
                    "id": location["id"],
                    "name": location["name"],
                    "description": location.get("description", "")
                })
    
    return {
        "deadline": deadline_date,
        "missing_locations": missing_locations,
        "total_missing": len(missing_locations)
    }

# Statistics Routes
@api_router.post("/statistics/generate")
async def generate_statistics(query: StatisticsQuery, current_user: User = Depends(get_current_user)):
    """Generate custom statistics based on query parameters"""
    
    # Check if user has access to statistics
    if "statistics" not in current_user.page_permissions and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access to statistics page denied")
    
    # Build aggregation pipeline
    pipeline = []
    
    # Match conditions
    match_conditions = {}
    
    # Date filtering
    if query.date_from or query.date_to:
        date_filter = {}
        if query.date_from:
            date_filter["$gte"] = datetime.fromisoformat(query.date_from.replace("Z", "+00:00"))
        if query.date_to:
            date_filter["$lte"] = datetime.fromisoformat(query.date_to.replace("Z", "+00:00"))
        match_conditions["submitted_at"] = date_filter
    
    # Location filtering
    if query.locations:
        match_conditions["service_location"] = {"$in": query.locations}
    
    # Status filtering
    if query.status:
        match_conditions["status"] = {"$in": query.status}
    
    # Template filtering
    if query.templates:
        match_conditions["template_id"] = {"$in": query.templates}
    
    # Role-based access control
    if current_user.role in ["manager", "data_entry"]:
        match_conditions["service_location"] = current_user.assigned_location
    
    if match_conditions:
        pipeline.append({"$match": match_conditions})
    
    # Lookup user information for user role filtering
    pipeline.append({
        "$lookup": {
            "from": "users",
            "localField": "submitted_by",
            "foreignField": "id",
            "as": "user_info"
        }
    })
    
    pipeline.append({
        "$unwind": {
            "path": "$user_info",
            "preserveNullAndEmptyArrays": True
        }
    })
    
    # User role filtering
    if query.user_roles:
        pipeline.append({
            "$match": {
                "user_info.role": {"$in": query.user_roles}
            }
        })
    
    # Group by specified field
    group_id = "$service_location"  # default
    if query.group_by == "month":
        group_id = {"$dateToString": {"format": "%Y-%m", "date": "$submitted_at"}}
    elif query.group_by == "template":
        group_id = "$template_id"
    elif query.group_by == "status":
        group_id = "$status"
    elif query.group_by == "user_role":
        group_id = "$user_info.role"
    elif query.group_by == "custom_field" and query.custom_field_name:
        group_id = f"$form_data.{query.custom_field_name}"
        # Add condition to ensure custom field exists
        match_conditions[f"form_data.{query.custom_field_name}"] = {"$exists": True, "$ne": None}
    
    pipeline.append({
        "$group": {
            "_id": group_id,
            "total_submissions": {"$sum": 1},
            "approved_count": {
                "$sum": {"$cond": [{"$eq": ["$status", "approved"]}, 1, 0]}
            },
            "reviewed_count": {
                "$sum": {"$cond": [{"$eq": ["$status", "reviewed"]}, 1, 0]}
            },
            "submitted_count": {
                "$sum": {"$cond": [{"$eq": ["$status", "submitted"]}, 1, 0]}
            },
            "rejected_count": {
                "$sum": {"$cond": [{"$eq": ["$status", "rejected"]}, 1, 0]}
            },
            "unique_users": {"$addToSet": "$submitted_by"},
            "latest_submission": {"$max": "$submitted_at"},
            "earliest_submission": {"$min": "$submitted_at"}
        }
    })
    
    pipeline.append({
        "$project": {
            "category": "$_id",
            "total_submissions": 1,
            "approved_count": 1,
            "reviewed_count": 1,
            "submitted_count": 1,
            "rejected_count": 1,
            "unique_user_count": {"$size": "$unique_users"},
            "latest_submission": 1,
            "earliest_submission": 1,
            "_id": 0
        }
    })
    
    pipeline.append({"$sort": {"total_submissions": -1}})
    
    results = await db.data_submissions.aggregate(pipeline).to_list(1000)
    
    # Calculate summary statistics
    total_submissions = sum(item["total_submissions"] for item in results)
    total_approved = sum(item["approved_count"] for item in results)
    total_reviewed = sum(item["reviewed_count"] for item in results)
    total_submitted = sum(item["submitted_count"] for item in results)
    total_rejected = sum(item["rejected_count"] for item in results)
    
    return {
        "query_parameters": query.dict(),
        "summary": {
            "total_submissions": total_submissions,
            "total_approved": total_approved,
            "total_reviewed": total_reviewed,
            "total_submitted": total_submitted,
            "total_rejected": total_rejected,
            "approval_rate": round((total_approved / total_submissions * 100) if total_submissions > 0 else 0, 2)
        },
        "data": results,
        "group_by": query.group_by
    }

@api_router.get("/statistics/options")
async def get_statistics_options(current_user: User = Depends(get_current_user)):
    """Get available options for statistics filtering"""
    
    if "statistics" not in current_user.page_permissions and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access to statistics page denied")
    
    # Get all unique locations
    locations = await db.service_locations.find({"is_active": True}).to_list(1000)
    location_options = [{"id": loc["id"], "name": loc["name"]} for loc in locations]
    
    # Get all templates
    templates = await db.form_templates.find({"is_active": True}).to_list(1000)
    template_options = [{"id": template["id"], "name": template["name"]} for template in templates]
    
    # Get available user roles
    users = await db.users.find({"is_active": True}).to_list(1000)
    user_roles = list(set(user["role"] for user in users))
    
    # Status options
    status_options = ["submitted", "reviewed", "approved", "rejected"]
    
    return {
        "locations": location_options,
        "templates": template_options,
        "user_roles": user_roles,
        "status_options": status_options,
        "group_by_options": [
            {"id": "location", "name": "Location"},
            {"id": "month", "name": "Month"},
            {"id": "template", "name": "Template"},
            {"id": "status", "name": "Status"},
            {"id": "user_role", "name": "User Role"},
            {"id": "custom_field", "name": "Custom Field"}
        ]
    }

@api_router.get("/statistics/custom-fields")
async def get_custom_fields_for_statistics(current_user: User = Depends(get_current_user)):
    """Get available custom fields from templates for statistical analysis"""
    
    if "statistics" not in current_user.page_permissions and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access to statistics page denied")
    
    # Get all active templates
    templates = await db.form_templates.find({"is_active": True}).to_list(1000)
    
    custom_fields = []
    field_types = {}
    
    for template in templates:
        for field in template.get("fields", []):
            field_name = field.get("name", "")
            field_type = field.get("type", "text")
            field_label = field.get("label", field_name)
            
            if field_name and field_name not in field_types:
                field_types[field_name] = field_type
                custom_fields.append({
                    "name": field_name,
                    "label": field_label,
                    "type": field_type,
                    "template": template["name"]
                })
    
    return {"custom_fields": custom_fields}

@api_router.post("/statistics/generate-custom-field")
async def generate_custom_field_statistics(query: StatisticsQuery, current_user: User = Depends(get_current_user)):
    """Generate statistics for custom form fields"""
    
    if "statistics" not in current_user.page_permissions and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access to statistics page denied")
    
    if not query.custom_field_name:
        raise HTTPException(status_code=400, detail="Custom field name is required")
    
    # Build match conditions
    match_conditions = {}
    
    # Date filtering
    if query.date_from or query.date_to:
        date_filter = {}
        if query.date_from:
            date_filter["$gte"] = datetime.fromisoformat(query.date_from.replace("Z", "+00:00"))
        if query.date_to:
            date_filter["$lte"] = datetime.fromisoformat(query.date_to.replace("Z", "+00:00"))
        match_conditions["submitted_at"] = date_filter
    
    # Other filters
    if query.locations:
        match_conditions["service_location"] = {"$in": query.locations}
    if query.status:
        match_conditions["status"] = {"$in": query.status}
    if query.templates:
        match_conditions["template_id"] = {"$in": query.templates}
    
    # Role-based access control
    if current_user.role in ["manager", "data_entry"]:
        match_conditions["service_location"] = current_user.assigned_location
    
    # Ensure custom field exists in form_data
    match_conditions[f"form_data.{query.custom_field_name}"] = {"$exists": True, "$ne": None}
    
    pipeline = []
    if match_conditions:
        pipeline.append({"$match": match_conditions})
    
    # Get field values and analyze based on type
    if query.custom_field_analysis_type == "numerical":
        # Numerical analysis - convert to numbers and calculate stats
        pipeline.extend([
            {
                "$addFields": {
                    "field_value_num": {
                        "$toDouble": {
                            "$ifNull": [f"$form_data.{query.custom_field_name}", 0]
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_count": {"$sum": 1},
                    "average": {"$avg": "$field_value_num"},
                    "sum": {"$sum": "$field_value_num"},
                    "min": {"$min": "$field_value_num"},
                    "max": {"$max": "$field_value_num"},
                    "values": {"$push": "$field_value_num"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "total_count": 1,
                    "average": {"$round": ["$average", 2]},
                    "sum": {"$round": ["$sum", 2]},
                    "min": 1,
                    "max": 1,
                    "std_dev": {
                        "$round": [{"$stdDevSamp": "$values"}, 2]
                    }
                }
            }
        ])
        
    elif query.custom_field_analysis_type == "trend":
        # Trend analysis - group by month and show field values over time
        pipeline.extend([
            {
                "$group": {
                    "_id": {
                        "month": {"$dateToString": {"format": "%Y-%m", "date": "$submitted_at"}},
                        "field_value": f"$form_data.{query.custom_field_name}"
                    },
                    "count": {"$sum": 1}
                }
            },
            {
                "$group": {
                    "_id": "$_id.month",
                    "values": {
                        "$push": {
                            "value": "$_id.field_value",
                            "count": "$count"
                        }
                    },
                    "total_submissions": {"$sum": "$count"}
                }
            },
            {
                "$project": {
                    "month": "$_id",
                    "values": 1,
                    "total_submissions": 1,
                    "_id": 0
                }
            },
            {"$sort": {"month": 1}}
        ])
        
    else:
        # Frequency analysis - count occurrences of each value
        pipeline.extend([
            {
                "$group": {
                    "_id": f"$form_data.{query.custom_field_name}",
                    "count": {"$sum": 1},
                    "submissions": {"$push": {
                        "id": "$id",
                        "location": "$service_location",
                        "submitted_at": "$submitted_at"
                    }}
                }
            },
            {
                "$project": {
                    "value": "$_id",
                    "count": 1,
                    "percentage": {
                        "$multiply": [
                            {"$divide": ["$count", {"$sum": "$count"}]},
                            100
                        ]
                    },
                    "sample_submissions": {"$slice": ["$submissions", 5]},
                    "_id": 0
                }
            },
            {"$sort": {"count": -1}}
        ])
    
    results = await db.data_submissions.aggregate(pipeline).to_list(1000)
    
    return {
        "field_name": query.custom_field_name,
        "analysis_type": query.custom_field_analysis_type,
        "query_parameters": query.dict(),
        "results": results
    }

@api_router.get("/reports/pdf")
async def generate_pdf_report(
    report_type: str = "statistics",
    query_params: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Generate comprehensive PDF report"""
    
    if report_type == "statistics" and "statistics" not in current_user.page_permissions and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access to statistics reports denied")
    
    try:
        from io import BytesIO
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = Paragraph(f"CLIENT SERVICES Platform - {report_type.title()} Report", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Report metadata
        report_info = [
            ["Generated By:", current_user.username],
            ["Generated At:", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")],
            ["Report Type:", report_type.title()]
        ]
        
        if query_params:
            import json
            try:
                params = json.loads(query_params)
                for key, value in params.items():
                    if value:
                        report_info.append([key.replace("_", " ").title() + ":", str(value)])
            except:
                pass
        
        info_table = Table(report_info, colWidths=[2*72, 4*72])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Get recent statistics data for the report
        if report_type == "statistics":
            query = StatisticsQuery()
            stats_data = await generate_statistics(query, current_user)
            
            # Summary section
            summary_title = Paragraph("Summary Statistics", styles['Heading2'])
            story.append(summary_title)
            story.append(Spacer(1, 12))
            
            summary_data = [
                ["Metric", "Value"],
                ["Total Submissions", str(stats_data["summary"]["total_submissions"])],
                ["Approved", str(stats_data["summary"]["total_approved"])],
                ["Reviewed", str(stats_data["summary"]["total_reviewed"])],
                ["Pending", str(stats_data["summary"]["total_submitted"])],
                ["Rejected", str(stats_data["summary"]["total_rejected"])],
                ["Approval Rate", f"{stats_data['summary']['approval_rate']}%"]
            ]
            
            summary_table = Table(summary_data, colWidths=[3*72, 2*72])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Detailed breakdown
            details_title = Paragraph("Detailed Breakdown", styles['Heading2'])
            story.append(details_title)
            story.append(Spacer(1, 12))
            
            details_data = [["Category", "Total", "Approved", "Reviewed", "Pending", "Rejected", "Users"]]
            for item in stats_data["data"]:
                details_data.append([
                    str(item.get("category", "Unknown")),
                    str(item["total_submissions"]),
                    str(item["approved_count"]),
                    str(item["reviewed_count"]),
                    str(item["submitted_count"]),
                    str(item["rejected_count"]),
                    str(item["unique_user_count"])
                ])
            
            details_table = Table(details_data, colWidths=[1.5*72, 0.7*72, 0.7*72, 0.7*72, 0.7*72, 0.7*72, 0.7*72])
            details_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(details_table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return StreamingResponse(
            BytesIO(buffer.getvalue()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={report_type}_report.pdf"}
        )
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating PDF report: {str(e)}")

# Location and Template Restore Endpoints
@api_router.get("/locations/deleted", response_model=List[ServiceLocation])
async def get_deleted_locations(current_user: User = Depends(require_role(["admin"]))):
    """Get all soft-deleted locations"""
    locations = await db.service_locations.find({"is_active": False}).to_list(1000)
    return [ServiceLocation(**location) for location in locations]

@api_router.post("/locations/{location_id}/restore")
async def restore_location(location_id: str, current_user: User = Depends(require_role(["admin"]))):
    """Restore a soft-deleted location"""
    result = await db.service_locations.update_one(
        {"id": location_id, "is_active": False}, 
        {"$set": {"is_active": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Location not found or already active")
    return {"message": "Location restored successfully"}

# Enhanced submissions endpoint to include username
@api_router.get("/submissions-detailed")
async def get_detailed_submissions(
    location: Optional[str] = None,
    month_year: Optional[str] = None,
    template_id: Optional[str] = None,
    submitted_by: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get submissions with user details"""
    try:
        logger.info(f"Detailed submissions request - User: {current_user.username}, Role: {current_user.role}")
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
        if submitted_by:
            query["submitted_by"] = submitted_by
        if status:
            query["status"] = status
        
        logger.info(f"Query parameters: {query}")
        
        # Get submissions first
        submissions = await db.data_submissions.find(query).to_list(1000)
        logger.info(f"Found {len(submissions)} submissions")
        
        # Remove ObjectIds for JSON serialization
        for submission in submissions:
            if "_id" in submission:
                del submission["_id"]
        
        # Enrich with user information
        for submission in submissions:
            user = await db.users.find_one({"id": submission["submitted_by"]})
            submission["submitted_by_username"] = user["username"] if user else "Unknown User"
        
        # Sort by submission date
        submissions.sort(key=lambda x: x["submitted_at"], reverse=True)
        
        return submissions
    except Exception as e:
        logger.error(f"Error in detailed submissions: {str(e)}")
        # Return empty list instead of error
        return []

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
