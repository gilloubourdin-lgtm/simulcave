# app/routers/auth.py

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.services.auth import (
    hash_password,
    verify_password,
    create_session_token,
    decode_session_token,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    token = request.cookies.get("session")

    if not token:
        return None

    user_id = decode_session_token(token)

    if not user_id:
        return None

    return db.query(User).filter(User.id == user_id).first()


def require_user(
    request: Request,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)

    if not user:
        raise HTTPException(status_code=401, detail="Connexion requise.")

    return user


@router.get("/register")
def register_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={},
    )


@router.post("/register")
def register_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: Session = Depends(get_db),
):
    email = email.lower().strip()

    if password != password_confirm:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Les mots de passe ne correspondent pas."},
        )

    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Un compte existe déjà avec cet email."},
        )

    user = User(
        email=email,
        hashed_password=hash_password(password),
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_session_token(user.id)

    response = RedirectResponse(url="/caves", status_code=303)
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )

    return response


@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={},
    )


@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    email = email.lower().strip()

    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Email ou mot de passe incorrect."},
        )

    token = create_session_token(user.id)

    response = RedirectResponse(url="/caves", status_code=303)
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )

    return response


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session")
    return response