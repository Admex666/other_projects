"""
Tests for Dual Auth & Role-Based Access Control (Master Planner vs. Advisor Workspace)
Validates login redirection, /hub launcher, /advisor route protection, and admin role management.
"""
import os
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.auth import create_session, is_advisor_user, get_user_role, sessions
from app.services.user_service import create_beta_user, get_user_by_username, update_user_role

@pytest.fixture
def client():
    return TestClient(app, follow_redirects=False)

def test_auth_helper_roles():
    """Verify role determination and is_advisor checks."""
    assert is_advisor_user("admin") is True
    assert is_advisor_user("bean") is True
    assert get_user_role("admin") == "admin"
    assert get_user_role("bean") == "advisor"
    assert is_advisor_user(None) is False
    assert get_user_role(None) == "guest"

def test_advisor_login_redirects_to_hub(client):
    """Advisor credentials (e.g. bean or admin) should redirect to /hub."""
    res = client.post("/login", data={"username": "bean", "password": "bean"})
    assert res.status_code == 303
    assert res.headers["location"] == "/hub"
    assert "session_token" in res.cookies

def test_planner_user_lifecycle_and_login_routing(client):
    """A planner-only user should be routed directly to /planner upon login."""
    test_uname = f"planner_{uuid.uuid4().hex[:8]}"
    test_pass = "pass1234"
    
    # Create user with role='planner'
    create_res = create_beta_user(
        username=test_uname,
        password=test_pass,
        full_name="Planner Tester",
        role="planner"
    )
    assert create_res.get("status") == "ok"
    
    # Verify role
    assert get_user_role(test_uname) == "planner"
    assert is_advisor_user(test_uname) is False

    # Perform login
    login_res = client.post("/login", data={"username": test_uname, "password": test_pass})
    assert login_res.status_code == 303
    assert login_res.headers["location"] == "/planner"

def test_hub_access_control(client):
    """Unauthenticated users or planner-only users cannot stay on /hub."""
    # 1. Unauthenticated -> redirect to /
    res_anon = client.get("/hub")
    assert res_anon.status_code == 303
    assert res_anon.headers["location"] == "/"

    # 2. Planner user -> redirect to /planner
    planner_user = f"planner_g_{uuid.uuid4().hex[:8]}"
    create_beta_user(username=planner_user, password="pwd", role="planner")
    planner_token = create_session(planner_user)
    
    res_planner = client.get("/hub", cookies={"session_token": planner_token})
    assert res_planner.status_code == 303
    assert res_planner.headers["location"] == "/planner"

    # 3. Advisor user -> 200 OK HTML
    advisor_token = create_session("bean")
    res_advisor = client.get("/hub", cookies={"session_token": advisor_token})
    assert res_advisor.status_code == 200
    assert "Alkalmazásválasztó" in res_advisor.text
    assert "Master Travel Planner" in res_advisor.text
    assert "Advisor Workspace" in res_advisor.text

def test_advisor_workspace_route_guard(client):
    """Non-advisors cannot access /advisor."""
    # 1. Unauthenticated -> redirect to /
    res_anon = client.get("/advisor")
    assert res_anon.status_code == 303
    assert res_anon.headers["location"] == "/"

    # 2. Planner-only user -> redirect to /planner
    planner_user = f"planner_adv_{uuid.uuid4().hex[:8]}"
    create_beta_user(username=planner_user, password="pwd", role="planner")
    planner_token = create_session(planner_user)
    
    res_planner = client.get("/advisor", cookies={"session_token": planner_token})
    assert res_planner.status_code == 303
    assert "/planner" in res_planner.headers["location"]

    # 3. Advisor user -> 200 OK
    advisor_token = create_session("bean")
    res_advisor = client.get("/advisor", cookies={"session_token": advisor_token})
    assert res_advisor.status_code == 200
    assert "Advisor Workspace" in res_advisor.text

def test_admin_update_user_role():
    """Test updating user role between planner and advisor."""
    user_name = f"role_toggle_{uuid.uuid4().hex[:8]}"
    res = create_beta_user(username=user_name, password="pwd", role="planner")
    user_id = res.get("user_id")
    if not user_id:
        user_record = get_user_by_username(user_name)
        user_id = user_record.get("id") if user_record else None
    
    assert user_id is not None
    assert get_user_role(user_name) == "planner"
    assert is_advisor_user(user_name) is False

    # Promote to advisor
    update_user_role(user_id, "advisor")
    assert get_user_role(user_name) == "advisor"
    assert is_advisor_user(user_name) is True

    # Demote back to planner
    update_user_role(user_id, "planner")
    assert get_user_role(user_name) == "planner"
    assert is_advisor_user(user_name) is False

def test_adam_admin_account_and_hub_visibility(client):
    """Verify adam login, admin role, and admin card visibility exclusively for admin users."""
    from app.core.auth import FALLBACK_USERS
    adam_password = FALLBACK_USERS.get("adam", os.getenv("ADMIN_PASSWORD", "admin_fallback"))
    # 1. Login with adam credentials
    login_res = client.post("/login", data={"username": "adam", "password": adam_password})
    assert login_res.status_code == 303
    assert login_res.headers["location"] == "/hub"

    # 2. Hub view as adam -> MUST show Adminisztrátori Pult card and link
    adam_token = create_session("adam")
    hub_adam = client.get("/hub", cookies={"session_token": adam_token})
    assert hub_adam.status_code == 200
    assert "Adminisztrátori Pult" in hub_adam.text
    assert "/admin/dashboard" in hub_adam.text

    # 3. Direct access to admin dashboard with adam session -> MUST work
    admin_dash = client.get("/admin/dashboard", cookies={"session_token": adam_token})
    assert admin_dash.status_code == 200

    # 4. Hub view as non-admin advisor (bean) -> MUST NOT show Adminisztrátori Pult
    bean_token = create_session("bean")
    hub_bean = client.get("/hub", cookies={"session_token": bean_token})
    assert hub_bean.status_code == 200
    assert "Adminisztrátori Pult" not in hub_bean.text

