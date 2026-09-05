---
id: proof-verification
type: process
name: Proof Verification
status: active
description: User proof submission, admin approval, diploma generation, and congratulatory email workflow.
code:
  - landing_predikalo1/portal.html
  - landing_predikalo1/api/submit-proof.js
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
       │ (Uploads GPX track file or summit photos to Supabase Storage 'proofs')
       ▼
api/submit-proof.js
       │ (Persists proof_urls, sets proof_submitted=true, proof_submitted_at via service role)
       ▼
Admin on admin.html (⏳ Várakozó tab – prioritised at the top with image thumbnails)
       │ (Inspects GPS track / images / participant data)
       ▼
api/admin-approve.js
       ├─► 1. Sets runs.completed = true & records completion_date
       ├─► 2. Generates oklevel diploma URL
       ├─► 3. Sends HTML Congratulatory Email with diploma link to runner
       ├─► 4. Sends instant Pushbullet notification to admin (PUSHBULLET_ACCESS_TOKEN)
       └─► 5. Moves run to 'Logisztika / Szállításra vár' state
```

## Manual Verification Fallback
* If a runner sends proof via email or social media, admins can trigger `✅ Manuális Jóváhagyás` directly from the `admin.html` pending list without requiring portal upload.
