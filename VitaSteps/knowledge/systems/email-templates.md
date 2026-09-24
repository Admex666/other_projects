---
id: email-templates
type: system
name: Email Templates System
status: active
description: Centralized, brand-aligned HTML email template system stored under landing_predikalo1/email_templates/.
code:
  - landing_predikalo1/email_templates/
  - landing_predikalo1/email_templates/welcome.html
  - landing_predikalo1/email_templates/proof_approved.html
  - landing_predikalo1/email_templates/lead_routes_kalandkonyv.html
  - landing_predikalo1/email_templates/lead_conversion_reminder.html
  - landing_predikalo1/email_templates/feedback_request.html
  - landing_predikalo1/email_templates/referral_promoter.html
  - landing_predikalo1/email_templates/promo_referral.html
  - landing_predikalo1/email_templates/ping_reminder.html
  - landing_predikalo1/email_templates/completion_reminder.html
  - landing_predikalo1/email_templates/auth_confirm_signup.html
  - landing_predikalo1/email_templates/auth_magic_link.html
related:
  - "[[checkout-pipeline]]"
  - "[[proof-verification]]"
  - "[[customer-funnel]]"
  - "[[referral-program]]"
---

# System: Email Templates (`landing_predikalo1/email_templates/`)

## 1. Overview
All transactional, nurturing, referral, and authentication email communications in the VitaSteps platform are strictly separated from backend logic and structured as external HTML files in `landing_predikalo1/email_templates/`.

## 2. Design Guidelines
* **Dark theme:** Background `#0b0f19` (outer), `#121824` (inner card).
* **Brand Accents:** `#c4ff00` (VitaSteps lime green), `#38bdf8` (sky blue).
* **Typography:** `Helvetica Neue, Arial, sans-serif` with high readability.
* **Layout:** Centered table structure (max width 600px) compatible with Gmail, Outlook, Apple Mail, and mobile clients.

## 3. Template Registry

| Template File | Purpose | Invoking Component | Key Placeholders |
| :--- | :--- | :--- | :--- |
| `welcome.html` | Post-checkout confirmation & onboarding | `api/process-payment.js`, `api/stripe-webhook.js` | `{{GREETING_NAMES}}`, `{{MEDALS_HTML}}`, `{{PORTAL_LINK}}` |
| `proof_approved.html` | Verification approval & diploma delivery | `api/admin-approve.js` | `{{RUNNER_NAME}}`, `{{CAMPAIGN_NAME}}`, `{{OKLEVEL_LINK}}` |
| `lead_routes_kalandkonyv.html` | Free route pack & Kalandkönyv lead magnet | `api/capture-lead.js` | `{{NAME}}`, `{{UNLOCK_URL}}`, `{{KALANDKONYV_URL}}` |
| `lead_conversion_reminder.html` | Lead nurturing & discount incentive | `scripts/send_lead_conversion_email.js` | `{{NAME}}`, `{{CHECKOUT_URL}}` |
| `feedback_request.html` | Delivered medal follow-up & NPS review | `scripts/daily_tracking.py` | `{{FIRST_NAME}}`, `{{CAMPAIGN_NAME}}`, `{{TALLY_FEEDBACK_LINK}}` |
| `referral_promoter.html` | NPS 9-10 promoter reward & friend referral link | `api/submit-feedback.js`, `scripts/send_referral_emails.py` | `{{FIRST_NAME}}`, `{{REFERRAL_LINK}}`, `{{PORTAL_LINK}}` |
| `promo_referral.html` | New challenge launch campaign | `scripts/send_promo_referral.js` | `{{NAME}}`, `{{REFERRAL_LINK}}` |
| `ping_reminder.html` | Missing proof/shipping reminder | `scripts/send_emails.py` | `{{FIRST_NAME}}`, `{{COMPLETION_LINK}}` |
| `completion_reminder.html` | Finish acknowledgement & shipping prompt | `scripts/send_emails.py` | `{{FIRST_NAME}}`, `{{KM_DISPLAY}}` |
| `auth_confirm_signup.html` | Supabase signup verification | Supabase Auth SMTP | `{{ .ConfirmationURL }}` |
| `auth_magic_link.html` | Supabase passwordless sign-in | Supabase Auth SMTP | `{{ .ConfirmationURL }}` |
| `leads_0927/email_1_3_days_before.html` | Lead nurturing (3 nappal a szept. 27. zárás előtt) | `scripts/send_lead_conversion_email.js` | `{{NAME}}`, `{{CHECKOUT_URL}}` |
| `leads_0927/email_2_1_day_before.html` | Lead nurturing (1 nappal a határidő előtt) | `scripts/send_lead_conversion_email.js` | `{{NAME}}`, `{{CHECKOUT_URL}}` |
| `leads_0927/email_3_last_day.html` | Lead nurturing (Utolsó napi éjféli zárás) | `scripts/send_lead_conversion_email.js` | `{{NAME}}`, `{{CHECKOUT_URL}}` |
