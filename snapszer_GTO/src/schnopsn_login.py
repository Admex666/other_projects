import os
import json
from pathlib import Path
from dotenv import dotenv_values
from playwright.sync_api import sync_playwright

def inspect_and_login():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    env_vars = dotenv_values(env_path) if env_path.exists() else {}
    email = env_vars.get("EMAIL", "")
    password = env_vars.get("PASSWORD", "")
    
    print(f"Loaded credentials from .env: Email: {email}, Password length: {len(password)}")
    if not email or not password:
        print("ERROR: Email or Password missing in .env")
        return

    output_dir = Path(__file__).resolve().parent.parent / "browser_state"
    output_dir.mkdir(exist_ok=True)
    state_file = output_dir / "storage_state.json"
    screenshot_file = output_dir / "login_screen.png"
    dom_dump_file = output_dir / "page_dom.html"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Track network requests
        network_logs = []
        def on_response(response):
            if "api" in response.url or "login" in response.url or "auth" in response.url or "game" in response.url:
                try:
                    network_logs.append({
                        "url": response.url,
                        "status": response.status,
                        "method": response.request.method,
                        "post_data": response.request.post_data,
                    })
                except Exception:
                    pass

        page.on("response", on_response)

        print("Navigating to https://schnopsn.com/game/schnopsn.htm...")
        page.goto("https://schnopsn.com/game/schnopsn.htm", wait_until="networkidle", timeout=30000)
        print(f"Loaded! Current URL: {page.url}, Title: {page.title()}")

        # Save initial DOM
        html_content = page.content()
        dom_dump_file.write_text(html_content, encoding="utf-8")
        print(f"Initial DOM saved to {dom_dump_file}")

        # Check input elements
        inputs = page.query_selector_all("input")
        print(f"Found {len(inputs)} input elements:")
        for idx, inp in enumerate(inputs):
            inp_type = inp.get_attribute("type") or "text"
            inp_id = inp.get_attribute("id") or ""
            inp_name = inp.get_attribute("name") or ""
            inp_placeholder = inp.get_attribute("placeholder") or ""
            is_visible = inp.is_visible()
            print(f"  [{idx}] Type: {inp_type}, ID: {inp_id}, Name: {inp_name}, Placeholder: '{inp_placeholder}', Visible: {is_visible}")

        # Check buttons and links
        buttons = page.query_selector_all("button, a, input[type='button'], input[type='submit']")
        print(f"Found {len(buttons)} button/clickable elements:")
        for idx, btn in enumerate(buttons):
            text = (btn.inner_text() or "").strip()
            btn_id = btn.get_attribute("id") or ""
            btn_class = btn.get_attribute("class") or ""
            is_visible = btn.is_visible()
            if text or is_visible:
                print(f"  [{idx}] Tag: {btn.evaluate('el => el.tagName')}, ID: {btn_id}, Class: {btn_class}, Text: '{text}', Visible: {is_visible}")

        # Check iframes
        frames = page.frames
        print(f"Total frames: {len(frames)}")
        for f_idx, f in enumerate(frames):
            print(f"  Frame {f_idx}: {f.url}")

        # Attempt to find login fields
        # Try common selectors
        email_field = page.query_selector("input[type='email'], input[name*='email'], input[name*='user'], input[id*='email'], input[id*='user'], input[placeholder*='Email'], input[placeholder*='Benutzer']")
        pass_field = page.query_selector("input[type='password'], input[name*='pass'], input[id*='pass']")

        if email_field and pass_field:
            print("Found email and password inputs! Filling them...")
            email_field.fill(email)
            pass_field.fill(password)
            page.screenshot(path=str(output_dir / "filled_login.png"))

            # Find submit button
            submit_btn = page.query_selector("button[type='submit'], input[type='submit'], button:has-text('Login'), button:has-text('Anmelden'), button:has-text('Bejelentkezés'), a:has-text('Login'), a:has-text('Anmelden')")
            if submit_btn:
                print(f"Clicking submit button: '{submit_btn.inner_text()}'...")
                submit_btn.click()
            else:
                print("Submit button not found directly, pressing Enter in password field...")
                pass_field.press("Enter")

            page.wait_for_timeout(5000)
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            print(f"Post-login URL: {page.url}, Title: {page.title()}")
        else:
            print("Could not find standard email/password fields on root page.")
            # Check if there's a login modal trigger button
            login_trigger = page.query_selector("button:has-text('Login'), a:has-text('Login'), button:has-text('Anmelden'), a:has-text('Anmelden')")
            if login_trigger and login_trigger.is_visible():
                print(f"Found login trigger button: '{login_trigger.inner_text()}'. Clicking it...")
                login_trigger.click()
                page.wait_for_timeout(2000)
                # re-check inputs
                inputs2 = page.query_selector_all("input")
                print(f"Inputs after clicking login trigger ({len(inputs2)}):")
                for idx, inp in enumerate(inputs2):
                    print(f"  [{idx}] Type: {inp.get_attribute('type')}, ID: {inp.get_attribute('id')}, Name: {inp.get_attribute('name')}, Placeholder: '{inp.get_attribute('placeholder')}', Visible: {inp.is_visible()}")

        # Take screenshot of final state
        page.screenshot(path=str(screenshot_file))
        print(f"Screenshot saved to {screenshot_file}")

        # Check cookies and localStorage
        cookies = context.cookies()
        print(f"Collected {len(cookies)} cookies:")
        for c in cookies:
            print(f"  Cookie: {c['name']} = {c['value'][:20]}... Domain: {c['domain']}, Expires: {c.get('expires')}")

        local_storage = page.evaluate("() => ({...localStorage})")
        print(f"Collected {len(local_storage)} localStorage items: {list(local_storage.keys())}")

        session_storage = page.evaluate("() => ({...sessionStorage})")
        print(f"Collected {len(session_storage)} sessionStorage items: {list(session_storage.keys())}")

        # Save storage state
        context.storage_state(path=str(state_file))
        print(f"Full storage state saved to {state_file}")

        # Save network logs summary
        with open(output_dir / "network_logs.json", "w", encoding="utf-8") as nf:
            json.dump(network_logs, nf, indent=2)
        print(f"Network logs saved to {output_dir / 'network_logs.json'}")

        browser.close()

if __name__ == "__main__":
    inspect_and_login()
