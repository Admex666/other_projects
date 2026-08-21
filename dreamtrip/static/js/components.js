/**
 * OPTIVOYA CENTRAL UI COMPONENTS CONTROLLER
 * Unified Flatpickr Date Picker, Steppers (+-1), and Location Autocomplete
 */

// 1. DISCRETE STEPPERS (+-1)
window.stepUp = function(elementId, maxLimit = 99) {
    const input = document.getElementById(elementId);
    if (!input) return;
    let current = parseInt(input.value, 10);
    if (isNaN(current)) current = 1;
    if (current < maxLimit) {
        input.value = current + 1;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
    }
};

window.stepDown = function(elementId, minLimit = 0) {
    const input = document.getElementById(elementId);
    if (!input) return;
    let current = parseInt(input.value, 10);
    if (isNaN(current)) current = 1;
    if (current > minLimit) {
        input.value = current - 1;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
    }
};

// 2. CENTRAL DATE RANGE PICKER (FLATPICKR WRAPPER)
window.initAdvisorDatePicker = function(config) {
    const {
        triggerElementId,
        datePrimaryLabelId,
        dateSubLabelId,
        hiddenStartInputId,
        hiddenEndInputId,
        defaultStartDays = 7,
        defaultDurationDays = 7,
        onDateChange
    } = config;

    const triggerEl = document.getElementById(triggerElementId);
    const primaryLabel = document.getElementById(datePrimaryLabelId);
    const subLabel = document.getElementById(dateSubLabelId);
    const startInput = document.getElementById(hiddenStartInputId);
    const endInput = document.getElementById(hiddenEndInputId);

    if (!triggerEl) return null;

    function formatHuDate(d) {
        if (!d) return '';
        const months = ['jan.', 'febr.', 'márc.', 'ápr.', 'máj.', 'jún.', 'júl.', 'aug.', 'szept.', 'okt.', 'nov.', 'dec.'];
        return `${months[d.getMonth()]} ${d.getDate()}.`;
    }

    function formatIsoDate(d) {
        if (!d) return '';
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    function updateDisplay(startDate, endDate) {
        if (startDate && endDate) {
            const nights = Math.max(1, Math.round((endDate - startDate) / (1000 * 60 * 60 * 24)));
            if (primaryLabel) primaryLabel.innerText = `${formatHuDate(startDate)} — ${formatHuDate(endDate)}`;
            if (subLabel) subLabel.innerText = `${nights} éjszaka • ${startDate.getFullYear()}`;
            if (startInput) startInput.value = formatIsoDate(startDate);
            if (endInput) endInput.value = formatIsoDate(endDate);
            if (onDateChange) onDateChange(formatIsoDate(startDate), formatIsoDate(endDate), nights);
        } else if (startDate) {
            if (primaryLabel) primaryLabel.innerText = `${formatHuDate(startDate)} — Válassz visszaútat`;
            if (subLabel) subLabel.innerText = "Kattints a visszaút dátumára";
            if (startInput) startInput.value = formatIsoDate(startDate);
        }
    }

    // Determine initial dates from inputs or defaults
    const today = new Date();
    let initialStart = new Date(today);
    initialStart.setDate(today.getDate() + defaultStartDays);
    
    let initialEnd = new Date(initialStart);
    initialEnd.setDate(initialStart.getDate() + defaultDurationDays);

    if (startInput && startInput.value) {
        const parsed = new Date(startInput.value);
        if (!isNaN(parsed)) initialStart = parsed;
    }
    if (endInput && endInput.value) {
        const parsed = new Date(endInput.value);
        if (!isNaN(parsed)) initialEnd = parsed;
    }

    const fp = flatpickr(triggerEl, {
        mode: "range",
        minDate: "today",
        dateFormat: "Y-m-d",
        locale: (typeof flatpickr !== 'undefined' && flatpickr.l10ns && flatpickr.l10ns.hu) ? flatpickr.l10ns.hu : 'default',
        defaultDate: [initialStart, initialEnd],
        showMonths: window.innerWidth > 768 ? 2 : 1,
        onChange: function(selectedDates) {
            if (selectedDates.length === 2) {
                updateDisplay(selectedDates[0], selectedDates[1]);
            } else if (selectedDates.length === 1) {
                updateDisplay(selectedDates[0], null);
            }
        }
    });

    // Run initial display update
    updateDisplay(initialStart, initialEnd);

    // Expose preset helper on fp instance
    fp.applyPreset = function(daysFromNow, durationDays) {
        const s = new Date();
        s.setDate(s.getDate() + daysFromNow);
        const e = new Date(s);
        e.setDate(s.getDate() + durationDays);
        fp.setDate([s, e], true);
        updateDisplay(s, e);
    };

    return fp;
};

// 3. CENTRAL LOCATION AUTOCOMPLETE
window.initLocationAutocomplete = function(config) {
    const {
        inputId,
        dropdownId,
        mode = 'destination', // 'destination' or 'origin'
        onSelect
    } = config;

    const input = document.getElementById(inputId);
    const dropdown = document.getElementById(dropdownId);
    if (!input || !dropdown) return;

    let debounceTimer = null;
    let activeIndex = -1;
    let currentItems = [];

    async function fetchSuggestions(term) {
        try {
            const res = await fetch(`/api/locations/autocomplete?term=${encodeURIComponent(term)}&mode=${mode}`);
            if (!res.ok) return [];
            return await res.json();
        } catch (e) {
            console.error("Autocomplete fetch error:", e);
            return [];
        }
    }

    function renderDropdown(items) {
        currentItems = items;
        activeIndex = -1;
        if (!items || items.length === 0) {
            dropdown.style.display = 'none';
            dropdown.innerHTML = '';
            return;
        }

        dropdown.innerHTML = items.map((item, idx) => `
            <div class="autocomplete-row-item" data-index="${idx}">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                    <circle cx="12" cy="10" r="3"></circle>
                </svg>
                <div style="display: flex; flex-direction: column; text-align: left;">
                    <span style="font-weight: 600; font-size: 14px;">${item.display}</span>
                    <span style="font-size: 11.5px; color: var(--text-muted);">${item.city}, ${item.country}${item.code ? ' (' + item.code + ')' : ''}</span>
                </div>
            </div>
        `).join('');

        dropdown.style.display = 'block';

        dropdown.querySelectorAll('.autocomplete-row-item').forEach(el => {
            el.addEventListener('mousedown', (e) => {
                e.preventDefault();
                const idx = parseInt(el.dataset.index, 10);
                selectItem(currentItems[idx]);
            });
        });
    }

    function selectItem(item) {
        if (!item) return;
        input.value = item.display || `${item.city}, ${item.country}`;
        dropdown.style.display = 'none';
        if (onSelect) onSelect(item);
    }

    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        const val = input.value.trim();
        if (val.length < 1) {
            dropdown.style.display = 'none';
            return;
        }
        debounceTimer = setTimeout(async () => {
            const results = await fetchSuggestions(val);
            renderDropdown(results);
        }, 220);
    });

    input.addEventListener('keydown', (e) => {
        const rows = dropdown.querySelectorAll('.autocomplete-row-item');
        if (!rows.length || dropdown.style.display === 'none') return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            activeIndex = (activeIndex + 1) % rows.length;
            highlightRow(rows);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            activeIndex = (activeIndex - 1 + rows.length) % rows.length;
            highlightRow(rows);
        } else if (e.key === 'Enter') {
            if (activeIndex >= 0 && activeIndex < currentItems.length) {
                e.preventDefault();
                selectItem(currentItems[activeIndex]);
            }
        } else if (e.key === 'Escape') {
            dropdown.style.display = 'none';
        }
    });

    function highlightRow(rows) {
        rows.forEach((r, idx) => {
            if (idx === activeIndex) {
                r.classList.add('active');
                r.scrollIntoView({ block: 'nearest' });
            } else {
                r.classList.remove('active');
            }
        });
    }

    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.style.display = 'none';
        }
    });
};
