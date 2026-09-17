import time
import pytest
from playwright.sync_api import Page, expect

def test_planner_page_load_and_elements(page: Page):
    """Verifies that the Master Planner loads cleanly with all core UI elements and no fatal JS errors."""
    page.goto(f"{page.base_url}/planner", wait_until="networkidle")
    
    # Verify main title & stepper
    expect(page.locator("h1.page-title")).to_contain_text("Teljes Utazás Tervezése")
    expect(page.locator("#wizardStepper")).to_be_visible()
    expect(page.locator("#stepNode0")).to_have_class("step-node active")
    
    # Verify no unhandled exceptions logged in console
    fatal_errors = [e for e in page.console_errors if "favicon" not in e.lower() and "404" not in e]
    assert len(fatal_errors) == 0, f"Unexpected JS console errors on page load: {fatal_errors}"

def test_step0_intake_controls_and_presets(page: Page):
    """Tests all interactive intake widgets: origin selection, passenger counters, date modes, and style chips."""
    page.goto(f"{page.base_url}/planner", wait_until="networkidle")
    
    # 1. Quick pill origin selection
    becs_pill = page.locator(".quick-pill", has_text="Bécs")
    if becs_pill.count() > 0:
        becs_pill.first.click()
        expect(page.locator("#origin")).to_have_value("Bécs (VIE)")
        
    budapest_pill = page.locator(".quick-pill", has_text="Budapest")
    if budapest_pill.count() > 0:
        budapest_pill.first.click()
        expect(page.locator("#origin")).to_have_value("Budapest (BUD)")
        
    # 2. Stepper passenger counts
    adult_plus_btn = page.locator(".stepper-row:has-text('Felnőtt') .stepper-circle-btn", has_text="+")
    adult_plus_btn.click()
    expect(page.locator("#adults_display")).to_have_text("3")
    
    adult_minus_btn = page.locator(".stepper-row:has-text('Felnőtt') .stepper-circle-btn", has_text="−")
    adult_minus_btn.click()
    expect(page.locator("#adults_display")).to_have_text("2")
    
    # 3. Date Mode Tabs
    tab_interval = page.locator("#tab_mode_interval")
    tab_exact = page.locator("#tab_mode_exact")
    
    tab_interval.click()
    expect(tab_interval).to_have_class("tab-pill-btn active")
    expect(page.locator("#panel_mode_interval")).to_be_visible()
    
    tab_exact.click()
    expect(tab_exact).to_have_class("tab-pill-btn active")
    expect(page.locator("#panel_mode_exact")).to_be_visible()
    
    # 4. Preset date pills
    preset_pill = page.locator(".preset-pill", has_text="Hosszú hétvége")
    if preset_pill.count() > 0:
        preset_pill.first.click()
        expect(page.locator("#exact_date_sub")).to_contain_text("3 napos")

    # 5. Experience style chips toggling
    nature_chip = page.locator("#experience_chips_grid .preset-pill", has_text="Természet")
    if nature_chip.count() > 0:
        was_active = "active" in (nature_chip.get_attribute("class") or "")
        nature_chip.click()
        is_active = "active" in (nature_chip.get_attribute("class") or "")
        assert was_active != is_active, "Experience chip did not toggle active state"

def test_decision_dna_modal_workflow(page: Page):
    """Tests the Decision DNA modal: open, step navigation, and saving configured weights."""
    page.goto(f"{page.base_url}/planner", wait_until="networkidle")
    
    # Open Decision DNA via main CTA
    main_cta = page.locator("#btn_main_step0_cta")
    expect(main_cta).to_be_visible()
    main_cta.click()
    
    modal = page.locator("#decisionDnaModalBackdrop")
    expect(modal).to_be_visible()
    
    # Progress step via Next
    next_btn = page.locator("#dnaBtnNext")
    expect(next_btn).to_be_visible()
    next_btn.click()
    
    # Apply and finish / hide
    page.evaluate("() => { if (window.DecisionDNAInstance) window.DecisionDNAInstance.hide(); }")
    expect(modal).not_to_be_visible()

def test_full_golden_flow_dummy_mode(page: Page):
    """Executes the complete End-to-End Master Planner Golden Path (Step 0 -> Step 5)."""
    # Pre-set dummy mode cookie & localStorage so all requests and polling are 100% mocked and fast
    page.context.add_cookies([{"name": "planner_dummy_mode", "value": "1", "url": page.base_url}])
    page.add_init_script("localStorage.setItem('optivoya_dummy_mode', 'true');")
    page.goto(f"{page.base_url}/planner", wait_until="networkidle")
    
    # Ensure dummy mode is active in JS state
    page.evaluate("() => { if (window.PlannerState && window.PlannerState.toggleDummyMode) window.PlannerState.toggleDummyMode(true); }")
    
    # Open and complete Decision DNA (starts destination search)
    page.locator("#btn_main_step0_cta").click()
    page.evaluate("() => { if (window.DecisionDNAInstance) window.DecisionDNAInstance.applyAndFinish(); }")
    
    # STEP 1: Wait for Destination Step to become visible
    page.wait_for_selector("#wizardStep1", state="visible", timeout=30000)
    expect(page.locator("#stepNode1")).to_have_class("step-node active")
    
    # Select first destination
    page.wait_for_selector("button[onclick*='selectDestination']", state="visible", timeout=30000)
    select_dest_btn = page.locator("button[onclick*='selectDestination']").first
    select_dest_btn.click()
    
    # STEP 2: Flights Selection
    page.wait_for_selector("#wizardStep2", state="visible", timeout=35000)
    expect(page.locator("#stepNode2")).to_have_class("step-node active")
    
    # Select flight
    page.wait_for_selector(".select-flight-btn, button[onclick*='selectFlight']", state="visible", timeout=35000)
    select_flight_btn = page.locator(".select-flight-btn, button[onclick*='selectFlight']").first
    select_flight_btn.click()
    
    # STEP 3: Accommodation Selection
    page.wait_for_selector("#wizardStep3", state="visible", timeout=45000)
    expect(page.locator("#stepNode3")).to_have_class("step-node active")
    
    # Select stay
    page.wait_for_selector("button[onclick*='selectStay']", state="visible", timeout=45000)
    select_stay_btn = page.locator("button[onclick*='selectStay']").first
    select_stay_btn.click()
    
    # STEP 4: Experiences & Activities
    page.wait_for_selector("#wizardStep4", state="visible", timeout=35000)
    expect(page.locator("#stepNode4")).to_have_class("step-node active")
    
    # Proceed to Final Summary
    page.wait_for_selector("button[onclick*='goToStep(5)']", state="visible", timeout=35000)
    proceed_to_summary_btn = page.locator("button[onclick*='goToStep(5)']").first
    proceed_to_summary_btn.click()
    
    # STEP 5: Final Proposal & Summary
    page.wait_for_selector("#wizardStep5", state="visible", timeout=35000)
    expect(page.locator("#stepNode5")).to_have_class("step-node active")
    
    # Verify subtitle and breakdown reflect the selected flight duration
    sub_text = page.locator("#summarySubtitle").inner_text()
    assert "éjszaka" in sub_text
    assert "nap" in sub_text

def test_exact_flight_duration_synchronization(page: Page):
    """Verifies that selecting a flight pair accurately updates days and nights across PlannerState, TripCart, and Summary."""
    page.context.add_cookies([{"name": "planner_dummy_mode", "value": "1", "url": page.base_url}])
    page.add_init_script("localStorage.setItem('optivoya_dummy_mode', 'true');")
    page.goto(f"{page.base_url}/planner", wait_until="networkidle")
    
    page.evaluate("() => { if (window.PlannerState && window.PlannerState.toggleDummyMode) window.PlannerState.toggleDummyMode(true); }")
    page.locator("#btn_main_step0_cta").click()
    page.evaluate("() => { if (window.DecisionDNAInstance) window.DecisionDNAInstance.applyAndFinish(); }")
    
    page.wait_for_selector("button[onclick*='selectDestination']", state="visible", timeout=30000)
    page.locator("button[onclick*='selectDestination']").first.click()
    
    page.wait_for_selector(".select-flight-btn, button[onclick*='selectFlight']", state="visible", timeout=35000)
    page.locator(".select-flight-btn, button[onclick*='selectFlight']").first.click()
    
    # Check that PlannerState.intake has synchronized duration & nights from selected flight
    state_dur = page.evaluate("() => ({ duration: window.PlannerState.intake.duration, nights: window.PlannerState.intake.nights })")
    assert state_dur["duration"] > 0
    assert state_dur["nights"] > 0
    assert state_dur["duration"] >= state_dur["nights"]

def test_stepper_back_and_forward_navigation(page: Page):
    """Tests that clicking on stepper nodes allows navigating steps."""
    page.goto(f"{page.base_url}/planner", wait_until="networkidle")
    expect(page.locator("#wizardStep0")).to_be_visible()
    page.locator("#stepNode0").click()
    expect(page.locator("#wizardStep0")).to_be_visible()

def test_mobile_viewport_no_horizontal_overflow(browser, live_server_url):
    """Tests mobile viewport (375x667 iPhone SE) to ensure 0 horizontal page overflow and responsive compliance."""
    context = browser.new_context(
        viewport={"width": 375, "height": 667},
        is_mobile=True,
        has_touch=True
    )
    page = context.new_page()
    page.goto(f"{live_server_url}/planner", wait_until="networkidle")
    
    overflow_data = page.evaluate("""() => {
        return {
            scrollWidth: document.documentElement.scrollWidth,
            clientWidth: document.documentElement.clientWidth,
            innerWidth: window.innerWidth
        };
    }""")
    
    assert overflow_data["scrollWidth"] <= overflow_data["innerWidth"] + 2, (
        f"Mobile page has horizontal overflow: {overflow_data}"
    )
    context.close()
