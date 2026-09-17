import os
import time
import socket
import threading
import pytest
import uvicorn
from playwright.sync_api import sync_playwright

def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

@pytest.fixture(scope="session")
def live_server_url():
    """Starts the FastAPI app in a background thread on an ephemeral port."""
    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    
    # Configure uvicorn server in a daemon thread
    config = uvicorn.Config("app.main:app", host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    
    # Wait for server to become responsive
    import urllib.request
    max_retries = 30
    ready = False
    for _ in range(max_retries):
        try:
            with urllib.request.urlopen(f"{base_url}/b2b", timeout=1) as resp:
                if resp.status in (200, 302, 307):
                    ready = True
                    break
        except Exception:
            time.sleep(0.15)
            
    if not ready:
        raise RuntimeError(f"FastAPI server failed to start on {base_url}")
        
    yield base_url
    
    # Teardown
    server.should_exit = True

@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p

@pytest.fixture(scope="session")
def browser(playwright_instance):
    browser = playwright_instance.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-gpu"]
    )
    yield browser
    browser.close()

@pytest.fixture
def page(browser, live_server_url):
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Optivoya-E2E-Automated-Tester/2.0"
    )
    page = context.new_page()
    
    # Capture console error logs
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda err: console_errors.append(str(err)))
    
    # Attach helper attributes
    page.base_url = live_server_url
    page.console_errors = console_errors
    
    yield page
    
    context.close()
