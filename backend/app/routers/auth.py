
import jwt
from app.database import settings
from app.models import RevokedToken
from app.dependencies import get_current_user
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas import UserRegister, UserResponse, EmailVerificationRequest
from app.email_service import (
    send_verification_email,
    send_password_reset_email
)

from app.database import get_db
from app.models import User, EmailVerificationCode, PasswordResetCode
from app.schemas import (
    UserRegister,
    UserResponse,
    EmailVerificationRequest,
    UserLogin,
    PasswordResetRequest,
    PasswordResetVerify,
    PasswordResetConfirm
)


from app.security import (
    hash_password,
    generate_verification_code,
    hash_verification_code,
    verify_password,
    create_access_token
)





from app.email_service import send_verification_email


router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer_scheme = HTTPBearer()

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):

    existing_username = db.query(User).filter(
        User.username == user_data.username
    ).first()

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )

    existing_email = db.query(User).filter(
        User.email == str(user_data.email)
    ).first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists"
        )

    # Create new user
    new_user = User(
        username=user_data.username,
        email=str(user_data.email),
        password_hash=hash_password(user_data.password)
    )

    db.add(new_user)
    db.flush()

    # Generate verification code
    code = generate_verification_code()

    # Store hashed code with expiration time
    verification_record = EmailVerificationCode(
        user_id=new_user.id,
        code_hash=hash_verification_code(code),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
    )

    db.add(verification_record)
    db.commit()
    db.refresh(new_user)

    # Send verification email
    send_verification_email(new_user.email, code)

    return new_user



@router.post("/verify-email")
def verify_email(
    verification_data: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    # Find user
    user = db.query(User).filter(
    User.email == str(verification_data.email)
    ).first()


    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.is_verified:
        raise HTTPException(
            status_code=400,
            detail="Email is already verified"
        )

    # Get latest verification code
    verification_record = (
        db.query(EmailVerificationCode)
        .filter(
            EmailVerificationCode.user_id == user.id,
            EmailVerificationCode.used_at.is_(None)
        )
        .order_by(EmailVerificationCode.id.desc())
        .first()
    )

    if not verification_record:
        raise HTTPException(
            status_code=400,
            detail="No active verification code found"
        )

    # Check expiration
    if verification_record.expires_at <= datetime.now(timezone.utc):
        verification_record.used_at = datetime.now(timezone.utc)
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Verification code has expired"
        )

    # Limit attempts to 5
    if verification_record.attempts >= 5:
        raise HTTPException(
            status_code=429,
            detail="Too many attempts. Request a new code."
        )

    # Check code
    submitted_hash = hash_verification_code(
        verification_data.code
    )

    verification_record.attempts += 1

    if submitted_hash != verification_record.code_hash:
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Invalid verification code"
        )

    # Activate account
    user.is_verified = True
    verification_record.used_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "message": "Email verified successfully",
        "is_verified": True
    }




@router.post("/resend-code")
def resend_verification_code(
    email: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    # Find user
    user = db.query(User).filter(
        User.email == str(email.email)
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.is_verified:
        raise HTTPException(
            status_code=400,
            detail="Email is already verified"
        )

    now = datetime.now(timezone.utc)

    # Get the latest verification record
    latest_record = (
        db.query(EmailVerificationCode)
        .filter(EmailVerificationCode.user_id == user.id)
        .order_by(EmailVerificationCode.id.desc())
        .first()
    )

    # Allow only one resend per 60 seconds
    if latest_record:
        sent_at = latest_record.expires_at - timedelta(minutes=10)

        if now < sent_at + timedelta(seconds=60):
            raise HTTPException(
                status_code=429,
                detail="Please wait 60 seconds before requesting another code"
            )

    # Invalidate previous unused codes
    old_codes = (
        db.query(EmailVerificationCode)
        .filter(
            EmailVerificationCode.user_id == user.id,
            EmailVerificationCode.used_at.is_(None)
        )
        .all()
    )

    for old_code in old_codes:
        old_code.used_at = now

    # Generate a new code
    code = generate_verification_code()

    new_record = EmailVerificationCode(
        user_id=user.id,
        code_hash=hash_verification_code(code),
        expires_at=now + timedelta(minutes=10)
    )

    db.add(new_record)
    db.commit()

    # Send the new code
    send_verification_email(user.email, code)

    return {
        "message": "A new verification code has been sent",
        "email": user.email
    }


@router.post("/login")
def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        (User.email == login_data.identifier) |
        (User.username == login_data.identifier)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password"
        )

    if not verify_password(
        login_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password"
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in"
        )

    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user



@router.post("/forgot-password")
def forgot_password(
    data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == data.email
    ).first()

    # لا نكشف إذا كان الإيميل مسجلاً أم لا
    if user is None:
        return {
            "message": "If the email exists, a reset code will be sent."
        }

    # إلغاء الأكواد القديمة غير المستخدمة
    old_codes = db.query(PasswordResetCode).filter(
        PasswordResetCode.user_id == user.id,
        PasswordResetCode.used_at.is_(None)
    ).all()

    for old_code in old_codes:
        old_code.used_at = datetime.now(timezone.utc)

    # إنشاء كود جديد
    code = generate_verification_code()

    reset_code = PasswordResetCode(
        user_id=user.id,
        code_hash=hash_verification_code(code),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
    )

    db.add(reset_code)
    db.commit()

    # إرسال الكود على إيميل المستخدم
    send_password_reset_email(user.email, code)

    return {
        "message": "If the email exists, a reset code will be sent."
    }


@router.post("/reset-password")
def reset_password(
    data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if user is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid email or verification code"
        )

    reset_code = db.query(PasswordResetCode).filter(
        PasswordResetCode.user_id == user.id,
        PasswordResetCode.used_at.is_(None)
    ).order_by(
        PasswordResetCode.id.desc()
    ).first()

    if reset_code is None:
        raise HTTPException(
            status_code=400,
            detail="No valid reset code found"
        )

    now = datetime.now(timezone.utc)

    if reset_code.expires_at <= now:
        raise HTTPException(
            status_code=400,
            detail="Verification code has expired"
        )

    if reset_code.attempts >= 5:
        raise HTTPException(
            status_code=400,
            detail="Too many attempts"
        )

    if hash_verification_code(data.code) != reset_code.code_hash:
        reset_code.attempts += 1
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Invalid verification code"
        )

    # تغيير كلمة المرور
    user.password_hash = hash_password(data.new_password)

    # استخدام الكود حتى لا يمكن استخدامه مرة أخرى
    reset_code.used_at = now

    db.commit()

    return {
        "message": "Password reset successfully"
    }

@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )

    expires_at = datetime.fromtimestamp(
        payload["exp"],
        tz=timezone.utc
    )

    revoked_token = RevokedToken(
        token=token,
        expires_at=expires_at
    )

    db.add(revoked_token)
    db.commit()

    return {"message": "Logged out successfully"}