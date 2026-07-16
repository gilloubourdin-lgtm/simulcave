# app/routers/auth.py password reset routes added

import os
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.services.auth import (
    hash_password,
    verify_password,
    create_session_token,
    decode_session_token,
)

from app.services.email import send_email
from app.services.auth import (
    create_password_reset_token,
    verify_password_reset_token,
    get_password_hash,
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

@router.get("/forgot-password")
def forgot_password_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="forgot_password.html",
        context={},
    )


@router.post("/forgot-password")
def forgot_password_submit(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()

    if user:
        token = create_password_reset_token(user.email)
        base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
        reset_url = f"{base_url}/reset-password/{token}"

        body = f"""
Bonjour,

Vous avez demandé la réinitialisation de votre mot de passe SimulCave.

Cliquez sur ce lien pour choisir un nouveau mot de passe :

{reset_url}

Ce lien est valable pendant 1 heure.

Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet email.

SimulCave
"""

        email_sent = send_email(
        to_email=user.email,
        subject="Réinitialisation de votre mot de passe SimulCave",
        body=body,
    )

    if not email_sent:
        print("Lien de réinitialisation:", reset_url)

    return templates.TemplateResponse(
        request=request,
        name="forgot_password.html",
        context={
            "message": "Si un compte existe avec cette adresse, un email a été envoyé.",
        },
    )


@router.get("/reset-password/{token}")
def reset_password_form(request: Request, token: str):
    email = verify_password_reset_token(token)

    if not email:
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "error": "Lien invalide ou expiré.",
                "token": token,
            },
        )

    return templates.TemplateResponse(
        request=request,
        name="reset_password.html",
        context={
            "token": token,
        },
    )


@router.post("/reset-password/{token}")
def reset_password_submit(
    request: Request,
    token: str,
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: Session = Depends(get_db),
):
    email = verify_password_reset_token(token)

    if not email:
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "error": "Lien invalide ou expiré.",
                "token": token,
            },
        )

    if password != password_confirm:
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "error": "Les mots de passe ne correspondent pas.",
                "token": token,
            },
        )

    if len(password) < 8:
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "error": "Le mot de passe doit contenir au moins 8 caractères.",
                "token": token,
            },
        )

    user = db.query(User).filter(User.email == email).first()

    if not user:
        return templates.TemplateResponse(
            request=request,
            name="reset_password.html",
            context={
                "error": "Utilisateur introuvable.",
                "token": token,
            },
        )

    user.hashed_password = get_password_hash(password)
    db.commit()

    return RedirectResponse(
        url="/login?password_reset=1",
        status_code=303,
    )