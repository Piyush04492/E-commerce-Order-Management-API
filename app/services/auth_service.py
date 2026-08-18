from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.cart import Cart
from app.schemas.user import UserRegister, UserLogin
from app.utils.security import get_password_hash, verify_password, create_access_token

class AuthService:
    """
    Handles user account lifecycle and token authentication.
    Good interview points:
    1. Check for email uniqueness before inserting.
    2. Automatically initialize an empty Cart for newly registered Customers.
    3. Issue JWT with role claim for role-based access control (RBAC).
    """

    @staticmethod
    def register_user(db: Session, user_data: UserRegister) -> User:
        # Check if email is already taken
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists."
            )
        
        # Hash the password
        hashed_password = get_password_hash(user_data.password)
        
        # If registering admin, we can check email or make first user admin,
        # but let's default to customer. Admin can be configured manually in DB or via seed.
        new_user = User(
            name=user_data.name,
            email=user_data.email,
            password_hash=hashed_password,
            role="customer"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Automatically create cart for the customer
        cart = Cart(user_id=new_user.id)
        db.add(cart)
        db.commit()
        
        return new_user

    @staticmethod
    def authenticate_user(db: Session, credentials: UserLogin) -> dict:
        user = db.query(User).filter(User.email == credentials.email).first()
        if not user or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token, embedding the sub (email), user_id, and role
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "role": user.role}
        )
        return {"access_token": access_token, "token_type": "bearer"}
