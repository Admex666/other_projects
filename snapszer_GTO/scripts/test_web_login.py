import os
import json
from pathlib import Path
from dotenv import dotenv_values
from playwright.sync_api import sync_playwright

def test_login():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    env_vars = dotenv_values(env_path) if env_path.exists() else {}
    email = env_vars.get("EMAIL", "").strip()
    password = env_vars.get("PASSWORD", "").strip()

    print(f"Loaded credentials: Email={email}, Password length={len(password)}")
    if not email or not password:
        print("Missing credentials in .env")
        return

    output_dir = Path(__file__).resolve().parent.parent / "browser_state"
    output_dir.mkdir(exist_ok=True)
    state_file = output_dir / "storage_state.json"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Capture network responses for login API calls
        auth_responses = []
        def on_response(response):
            if any(k in response.url for k in ["api", "auth", "login", "token", "firebase", "user"]):
                try:
                    auth_responses.append({
                        "url": response.url,
                        "status": response.status,
                        "method": response.request.method,
                        "response_text": response.text()[:500] if response.status < 400 or response.status == 401 else f"HTTP {response.status}"
                    })
                except Exception:
                    pass

        page.on("response", on_response)

        print("Navigating to https://schnopsn.com/login...")
        page.goto("https://schnopsn.com/login", wait_until="networkidle", timeout=30000)
        print(f"Loaded {page.url} - Title: {page.title()}")

        # Check for cookie banner / consent popup
        consent_buttons = page.query_selector_all("button:has-text('Akzeptieren'), button:has-text('Accept'), button:has-text('Alle akzeptieren'), button:has-text('Elfogadom'), button:has-text('Zustimmen')")
        if consent_buttons:
            for cb in consent_buttons:
                if cb.is_visible():
                    print(f"Clicking cookie consent button: '{cb.inner_text()}'")
                    cb.click()
                    page.wait_for_timeout(1000)
                    break

        page.screenshot(path=str(output_dir / "01_login_page.png"))

        # Find email and password inputs
        email_input = page.query_selector("input[type='email'], input[formcontrolname='email'], input[name='email']")
        pass_input = page.query_selector("input[type='password'], input[formcontrolname='password'], input[name='password']")

        if not email_input or not pass_input:
            print("Could not find email/password with standard selectors. Searching all inputs:")
            for inp in page.query_selector_all("input"):
                print(f"  Input type={inp.get_attribute('type')}, placeholder={inp.get_attribute('placeholder')}, id={inp.get_attribute('id')}")
            return

        print("Filling email and password...")
        email_input.fill(email)
        pass_input.fill(password)
        page.screenshot(path=str(output_dir / "02_filled.png"))

        # Submit button
        submit_btn = page.query_selector("button[type='submit'], button:has-text('Anmelden'), button:has-text('Login')")
        if submit_btn:
            print(f"Clicking submit button: '{submit_btn.inner_text()}'...")
            submit_btn.click()
        else:
            print("Pressing Enter on password input...")
            pass_input.press("Enter")

        # Wait for navigation or API response
        print("Waiting for response...")
        page.wait_for_timeout(5000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        print(f"Post-login URL: {page.url}")
        print(f"Post-login Title: {page.title()}")
        page.screenshot(path=str(output_dir / "03_post_login.png"))

        # Save cookies & storage state
        cookies = context.cookies()
        print(f"Cookies ({len(cookies)}):")
        for c in cookies:
            print(f"  {c['name']} = {c['value'][:30]}... ({c['domain']})")

        local_storage = page.evaluate("() => ({...localStorage})")
        print(f"localStorage keys ({len(local_storage)}): {list(local_storage.keys())}")

        context.storage_state(path=str(state_file))
        print(f"Storage state saved to {state_file}")

        print("\nAuth network logs:")
        for log in auth_responses:
            print(f"  [{log['method']}] {log['status']} -> {log['url']}")
            if "response_text" in log:
                print(f"     Body: {log['response_text'][:200]}")

        # Now test going to https://schnopsn.com/game/schnopsn.htm with this authenticated session!
        print("\nNow navigating to https://schnopsn.com/game/schnopsn.htm with authenticated session...")
        page.goto("https://schnopsn.com/game/schnopsn.htm", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(8000)
        page.screenshot(path=str(output_dir / "04_game_page_auth.png"))
        print(f"Game page URL: {page.url}, Title: {page.title()}")
        print(f"Game page screenshot saved to {output_dir / '04_game_page_auth.png'}")

        # Save updated storage state including game page
        context.storage_state(path=str(state_file))
        print(f"Updated storage state saved to {state_file}")

        browser.close()

if __name__ == "__main__":
    test_login()
