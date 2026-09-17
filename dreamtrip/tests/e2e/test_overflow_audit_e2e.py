import pytest
from playwright.sync_api import Page, Browser

AUDIT_DOM_OVERFLOW_SCRIPT = """() => {
    const overflows = [];
    const viewportWidth = window.innerWidth;
    
    // 1. Check Global Root ScrollWidth
    if (document.documentElement.scrollWidth > viewportWidth + 2) {
        overflows.push({
            type: 'GLOBAL_PAGE_HORIZONTAL_OVERFLOW',
            tag: 'html',
            scrollWidth: document.documentElement.scrollWidth,
            viewportWidth: viewportWidth,
            diff: document.documentElement.scrollWidth - viewportWidth
        });
    }
    
    function hasScrollableOrClippingAncestor(element) {
        let curr = element.parentElement;
        while (curr && curr !== document.body && curr !== document.documentElement) {
            const pStyle = window.getComputedStyle(curr);
            if (pStyle.overflowX === 'auto' || pStyle.overflowX === 'scroll' || pStyle.overflowX === 'hidden' || pStyle.overflow === 'hidden') {
                return true;
            }
            curr = curr.parentElement;
        }
        return false;
    }
    
    const elements = document.querySelectorAll('body *');
    
    elements.forEach(el => {
        // Skip technical or SVG internal nodes
        if (el.tagName === 'SCRIPT' || el.tagName === 'STYLE' || el.tagName === 'SVG' || el.tagName === 'PATH' || el.tagName === 'CIRCLE') {
            return;
        }
        
        // Skip hidden or offscreen modal/drawer elements
        if (el.offsetParent === null) {
            return;
        }
        
        if (el.closest('.trip-cart-drawer') || el.closest('.modal-overlay:not(.active)') || el.closest('.b2b-modal-backdrop:not(.active)') || el.closest('[aria-hidden="true"]')) {
            return;
        }
        
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
            return;
        }
        
        // Skip fixed off-screen elements (e.g. parked slide-over bars)
        if (style.position === 'fixed' && (style.transform.includes('translateX') || style.right.startsWith('-') || style.left.startsWith('-'))) {
            return;
        }
        
        // Allowed scrollable containers
        const isScrollable = style.overflowX === 'auto' || style.overflowX === 'scroll';
        const isClipped = style.overflowX === 'hidden' || style.overflow === 'hidden';
        
        const rect = el.getBoundingClientRect();
        
        // 2. Element strictly exceeds right viewport boundary without being contained/clipped
        if (rect.right > viewportWidth + 2 && !isScrollable && !isClipped && !hasScrollableOrClippingAncestor(el)) {
            overflows.push({
                type: 'VIEWPORT_OVERFLOW',
                tag: el.tagName.toLowerCase(),
                id: el.id || '',
                className: el.className ? String(el.className) : '',
                rectRight: rect.right,
                viewportWidth: viewportWidth,
                text: (el.innerText || '').slice(0, 45).replace(/\\n/g, ' ')
            });
        }
        
        // 3. Check if element's internal content is bursting its own client bounds without scroll/wrap
        if (el.scrollWidth > el.clientWidth + 2 && !isScrollable && !isClipped && el.clientWidth > 0) {
            if (el !== document.body && el !== document.documentElement && el.tagName !== 'INPUT' && el.tagName !== 'TEXTAREA' && el.tagName !== 'SELECT') {
                overflows.push({
                    type: 'ELEMENT_CONTENT_BURST',
                    tag: el.tagName.toLowerCase(),
                    id: el.id || '',
                    className: el.className ? String(el.className) : '',
                    scrollWidth: el.scrollWidth,
                    clientWidth: el.clientWidth,
                    diff: el.scrollWidth - el.clientWidth,
                    text: (el.innerText || '').slice(0, 45).replace(/\\n/g, ' ')
                });
            }
        }
    });
    
    return overflows;
}"""

@pytest.mark.parametrize("viewport", [
    {"name": "Mobile_375px", "width": 375, "height": 667, "is_mobile": True},
    {"name": "Tablet_768px", "width": 768, "height": 1024, "is_mobile": False},
    {"name": "Desktop_1280px", "width": 1280, "height": 800, "is_mobile": False}
])
def test_b2b_landing_dom_pixel_audit(browser: Browser, live_server_url: str, viewport: dict):
    """Deep DOM pixel audit on /b2b across responsive viewports."""
    context = browser.new_context(
        viewport={"width": viewport["width"], "height": viewport["height"]},
        is_mobile=viewport.get("is_mobile", False)
    )
    page = context.new_page()
    page.goto(f"{live_server_url}/b2b", wait_until="networkidle")
    
    # Audit initial view
    overflows = page.evaluate(AUDIT_DOM_OVERFLOW_SCRIPT)
    
    # Also trigger the calculator preset buttons and re-audit
    boutique_preset = page.locator(".btn-preset", has_text="Boutique Iroda")
    if boutique_preset.count() > 0:
        boutique_preset.click()
        page.wait_for_timeout(200)
        calc_overflows = page.evaluate(AUDIT_DOM_OVERFLOW_SCRIPT)
        overflows.extend(calc_overflows)
        
    context.close()
    
    assert len(overflows) == 0, f"[{viewport['name']}] Found {len(overflows)} DOM element overflows on /b2b: {overflows[:5]}"

@pytest.mark.parametrize("viewport", [
    {"name": "Mobile_375px", "width": 375, "height": 667, "is_mobile": True},
    {"name": "Tablet_768px", "width": 768, "height": 1024, "is_mobile": False},
    {"name": "Desktop_1280px", "width": 1280, "height": 800, "is_mobile": False}
])
def test_planner_wizard_dom_pixel_audit(browser: Browser, live_server_url: str, viewport: dict):
    """Deep DOM pixel audit on /planner across exact/interval modes and stepper views."""
    context = browser.new_context(
        viewport={"width": viewport["width"], "height": viewport["height"]},
        is_mobile=viewport.get("is_mobile", False)
    )
    page = context.new_page()
    page.goto(f"{live_server_url}/planner", wait_until="networkidle")
    
    # Audit Step 0 Exact Mode
    overflows_exact = page.evaluate(AUDIT_DOM_OVERFLOW_SCRIPT)
    
    # Switch to Interval Mode & Audit
    tab_interval = page.locator("#tab_mode_interval")
    if tab_interval.count() > 0:
        tab_interval.click()
        page.wait_for_timeout(200)
        overflows_interval = page.evaluate(AUDIT_DOM_OVERFLOW_SCRIPT)
    else:
        overflows_interval = []
        
    context.close()
    
    all_overflows = overflows_exact + overflows_interval
    assert len(all_overflows) == 0, f"[{viewport['name']}] Found {len(all_overflows)} DOM element overflows on /planner: {all_overflows[:5]}"
