---
id: how-to-manual-approve
type: operation
name: How to Manually Approve a Run
status: active
description: Procedure for verifying and approving runners who submitted proof via email or social media.
code:
  - landing_predikalo1/admin.html
  - landing_predikalo1/api/admin-approve.js
related:
  - "[[proof-verification|Proof Verification]]"
  - "[[run]]"
---

# Operation: How to Manually Approve a Run

If a runner sends proof (screenshot, GPX, summit photo) outside the runner portal:

## Procedure
1. Open `admin.html` and go to the **`⏳ Várakozó`** (Pending) tab.
2. Search for the runner by name, email, or serial number.
3. Click the sub-filter **`🏃 Még nem igazolt`** (Unsubmitted) if necessary.
4. On the runner's card, click the green **`✅ Manuális Jóváhagyás`** button.
5. Confirm the browser confirmation dialog.
6. **Result:** The system marks the run as `completed = true`, saves the current date as `completion_date`, generates their official diploma link, and automatically dispatches the congratulatory email. The run immediately moves into the **Logisztika** queue for medal shipping.
