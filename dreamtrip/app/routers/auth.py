from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.config import templates
from app.core.auth import (
    verify_credentials, create_session, sessions,
    get_current_user, is_advisor_user, is_admin_user, get_user_role
)

router = APIRouter(tags=["Auth"])

@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    user = get_current_user(request)
    if user:
        if is_advisor_user(user):
            return RedirectResponse(url="/hub", status_code=303)
        return RedirectResponse(url="/planner", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if verify_credentials(username, password):
        token = create_session(username)
        # Advisor / Admin fiókok a Hub-ra kerülnek választási lehetőséggel,
        # míg a standard / planner-only fiókok azonnal a Master Plannerre
        target_url = "/hub" if is_advisor_user(username) else "/planner"
        response = RedirectResponse(url=target_url, status_code=303)
        response.set_cookie(key="session_token", value=token, httponly=True)
        return response
    return RedirectResponse(url="/?error=invalid", status_code=303)

@router.get("/hub", response_class=HTMLResponse)
async def app_hub_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    # Ha a bejelentkezett felhasználó nem advisor, irányítsuk közvetlenül a plannerre
    if not is_advisor_user(user):
        return RedirectResponse(url="/planner", status_code=303)
        
    role = get_user_role(user)
    is_admin = is_admin_user(user)
    return templates.TemplateResponse("hub.html", {
        "request": request,
        "user": user,
        "role": role,
        "is_advisor": True,
        "is_admin": is_admin
    })


@router.get("/logout")
async def logout(request: Request):
    token = request.cookies.get("session_token")
    if token in sessions:
        del sessions[token]
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session_token")
    return response

