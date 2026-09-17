import pytest
from playwright.sync_api import Page, expect

def test_b2b_landing_page_load_and_elements(page: Page):
    """Verifies that the B2B landing page loads with zero fatal console errors, proper emerald styling, and key value prop."""
    page.goto(f"{page.base_url}/b2b", wait_until="networkidle")
    
    # Title and Hero
    expect(page.locator("h1.b2b-hero-title")).to_contain_text("Könnyítsd meg és gyorsítsd fel a munkád")
    expect(page.locator(".b2b-engine-trust-box")).to_be_visible()
    
    # Brand logo and badge
    expect(page.locator(".b2b-brand-name").first).to_contain_text("Optivoya")
    expect(page.locator(".b2b-brand-badge").first).to_contain_text("FOR ADVISORS")
    
    # Check 0 fatal console errors
    fatal_errors = [e for e in page.console_errors if "favicon" not in e.lower() and "404" not in e]
    assert len(fatal_errors) == 0, f"Unexpected JS console errors on /b2b: {fatal_errors}"

def test_b2b_roi_calculator_interactivity_and_presets(page: Page):
    """Tests the interactive ROI calculator sliders and 1-click role presets."""
    page.goto(f"{page.base_url}/b2b#calculator", wait_until="networkidle")
    
    # Verify Initial numbers
    expect(page.locator("#outHoursSaved")).to_contain_text("óra / hó")
    expect(page.locator("#outMoneySaved")).to_contain_text("Ft")
    
    # Click Boutique preset (25 clients/mo, 4h, 15000 rate)
    boutique_preset = page.locator(".btn-preset", has_text="Boutique Iroda")
    boutique_preset.click()
    
    expect(boutique_preset).to_have_class("btn-preset active")
    expect(page.locator("#calcClientsVal")).to_have_text("25 ügyfél / hó")
    
    # Click Concierge preset (40 clients/mo, 5h, 20000 rate)
    concierge_preset = page.locator(".btn-preset", has_text="Prémium Concierge")
    concierge_preset.click()
    
    expect(concierge_preset).to_have_class("btn-preset active")
    expect(page.locator("#calcClientsVal")).to_have_text("40 ügyfél / hó")

def test_b2b_access_gate_modal_and_form(page: Page):
    """Tests that demo and beta CTA buttons bring up the access-gate lead collection modal."""
    page.goto(f"{page.base_url}/b2b", wait_until="networkidle")
    
    modal = page.locator("#b2bBetaModal")
    expect(modal).not_to_be_visible()
    
    # Click primary hero CTA
    hero_cta = page.locator(".trigger-beta-modal").first
    hero_cta.click()
    
    expect(modal).to_be_visible()
    
    # Close modal
    close_btn = page.locator("#b2bModalClose")
    close_btn.click()
    expect(modal).not_to_be_visible()

def test_b2b_mobile_layout_no_overflow(browser, live_server_url):
    """Tests mobile viewport (375x667) for /b2b to ensure 0 horizontal overflow."""
    context = browser.new_context(
        viewport={"width": 375, "height": 667},
        is_mobile=True,
        has_touch=True
    )
    page = context.new_page()
    page.goto(f"{live_server_url}/b2b", wait_until="networkidle")
    
    overflow_data = page.evaluate("""() => {
        return {
            scrollWidth: document.documentElement.scrollWidth,
            clientWidth: document.documentElement.clientWidth,
            innerWidth: window.innerWidth
        };
    }""")
    
    assert overflow_data["scrollWidth"] <= overflow_data["innerWidth"] + 2, (
        f"Mobile B2B page has horizontal overflow: {overflow_data}"
    )
    context.close()
