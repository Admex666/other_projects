---
id: proof-verification
type: process
name: Proof Verification
status: active
description: User proof submission, admin approval, diploma generation, and congratulatory email workflow.
code:
  - landing_predikalo1/portal.html
  - landing_predikalo1/admin.html
  - landing_predikalo1/api/admin-approve.js
related:
  - "[[verified-challenge|Verified Challenge]]"
  - "[[run]]"
  - "[[supabase]]"
  - "[[order-fulfillment|Order Fulfillment]]"
---

# Process: Proof Verification

```text
Runner on portal.html
       │ (Uploads GPX track file or summit photos)
       ▼
api/submit-proof.js
       │ (Stores files in Supabase Storage 'proofs', sets proof_submitted=true)
       ▼
Admin on admin.html (⏳ Várakozó tab)
       │ (Inspects GPS track / images / participant data)
       ▼
api/admin-approve.js
       ├─► 1. Sets runs.completed = true & records completion_date
       ├─► 2. Generates diploma_url
       ├─► 3. Sends HTML Congratulatory Email with diploma link
       └─► 4. Moves run to 'Logisztika / Szállításra vár' state
```

## Manual Verification Fallback
* If a runner sends proof via email or social media, admins can trigger `✅ Manuális Jóváhagyás` directly from the `admin.html` pending list without requiring portal upload.
