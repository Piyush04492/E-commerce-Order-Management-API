from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.user import UserRegister, UserResponse, Token, UserLogin
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Registers a new customer.
    Creates a new user record and initializes an empty cart.
    """
    return AuthService.register_user(db, user_data)

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Standard OAuth2/JWT login.
    Expects form-data fields: 'username' (which is the email) and 'password'.
    Returns a signed JWT bearer token on success.
    """
    credentials = UserLogin(email=form_data.username, password=form_data.password)
    return AuthService.authenticate_user(db, credentials)
