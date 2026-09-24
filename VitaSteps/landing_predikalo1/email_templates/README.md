# VitaSteps – Email Sablonok (Email Templates)

Ez a mappa tartalmazza a VitaSteps rendszer összes tranzakciós és marketing e-mail sablonját szabványos HTML formátumban.

---

## 📁 Sablonok jegyzéke és használatuk

| Fájlnév | Típus | Hívó script / API végpont | Dinamikus Változók | Leírás |
| :--- | :--- | :--- | :--- | :--- |
| `welcome.html` | Tranzakciós | `api/process-payment.js`, `api/stripe-webhook.js` | `{{GREETING_NAMES}}`, `{{INTRO_TEXT}}`, `{{MEDALS_HTML}}`, `{{SHIPPING_HTML}}`, `{{LOCATION_NAME}}`, `{{CHALLENGE_PERIOD_TEXT}}`, `{{PROOF_METHOD_TEXT}}`, `{{DELIVERY_TEXT}}`, `{{PORTAL_LINK}}` | Sikeres nevezés & vásárlás utáni visszaigazoló levél portál belépési linkkel. |
| `proof_approved.html` | Tranzakciós | `api/admin-approve.js` | `{{RUNNER_NAME}}`, `{{CAMPAIGN_NAME}}`, `{{SHIPPING_TEXT}}`, `{{PORTAL_LINK}}`, `{{OKLEVEL_LINK}}` | Admin jóváhagyás utáni gratulációs levél letölthető digitális oklevéllel. |
| `lead_routes_kalandkonyv.html` | Lead mágnes | `api/capture-lead.js` | `{{NAME}}`, `{{UNLOCK_URL}}`, `{{KALANDKONYV_URL}}` | Ingyenes túraútvonalak és Kalandkönyv hozzáférést biztosító feloldó levél. |
| `lead_conversion_reminder.html` | Nurturing | `scripts/send_lead_conversion_email.js` | `{{NAME}}`, `{{LEAD_EMAIL}}`, `{{CHECKOUT_URL}}`, `{{KALANDKONYV_URL}}` | Meleg leadeknek küldött konverziós emlékeztető és motivációs levél. |
| `feedback_request.html` | Utókövetés | `scripts/daily_tracking.py`, `scripts/test_followup_send.py` | `{{FIRST_NAME}}`, `{{CAMPAIGN_NAME}}`, `{{TALLY_FEEDBACK_LINK}}` | Csomagátvétel után kiküldött élményértékelő és visszajelzés-kérő levél. |
| `referral_promoter.html` | Ajánlói | `api/submit-feedback.js`, `scripts/send_referral_emails.py` | `{{FIRST_NAME}}`, `{{REFERRAL_LINK}}`, `{{PORTAL_LINK}}` | NPS 9-10 értékelőknek kiküldött 10% kupon és progresszív ajánlói link. |
| `promo_referral.html` | Marketing | `scripts/send_promo_referral.js`, `scripts/send_promo_referral.py` | `{{NAME}}`, `{{REFERRAL_LINK}}`, `{{PORTAL_LINK}}` | Új kihívás (pl. Nagy-Kevély) indulásakor korábbi teljesítőknek küldött ajánlói levél. |
| `ping_reminder.html` | Emlékeztető | `scripts/send_emails.py` | `{{FIRST_NAME}}`, `{{COMPLETION_LINK}}`, `{{TALLY_LINK}}` | Emlékeztető levél igazolás és szállítási cím feltöltésére. |
| `completion_reminder.html` | Visszaigazolás | `scripts/send_emails.py` | `{{FIRST_NAME}}`, `{{KM_DISPLAY}}`, `{{TALLY_LINK}}` | Teljesítés jóváhagyási és szállítási adatkérő visszaigazolás. |
| `auth_confirm_signup.html` | Auth | Supabase Auth Custom SMTP | `{{ .ConfirmationURL }}` | Felhasználói fiók regisztráció megerősítése. |
| `auth_magic_link.html` | Auth | Supabase Auth Custom SMTP | `{{ .ConfirmationURL }}` | Jelszó nélküli egykattintásos bejelentkező Magic Link. |
| `leads_0927/email_1_3_days_before.html` | Lead Nurturing | `scripts/send_lead_conversion_email.js` | `{{NAME}}`, `{{CHECKOUT_URL}}`, `{{UNSUBSCRIBE_URL}}` | 3 nappal a határidő (szept. 27.) előtti emlékeztető többérmes és ajánlói akcióval, leiratkozó linkkel. |
| `leads_0927/email_2_1_day_before.html` | Lead Nurturing | `scripts/send_lead_conversion_email.js` | `{{NAME}}`, `{{CHECKOUT_URL}}`, `{{UNSUBSCRIBE_URL}}` | 1 nappal a határidő előtti sürgető levél 24 órás figyelmeztetéssel, leiratkozó linkkel. |
| `leads_0927/email_3_last_day.html` | Lead Nurturing | `scripts/send_lead_conversion_email.js` | `{{NAME}}`, `{{CHECKOUT_URL}}`, `{{UNSUBSCRIBE_URL}}` | Az utolsó napon (szept. 27.) éjféli zárás előtt kiküldött sürgősségi levél, leiratkozó linkkel. |

---

## 🎨 Arculati Szabályok
Minden sablon a VitaSteps sötét arculatát követi:
- **Háttér:** `#0b0f19` (outer wrapper), `#121824` (belső kártya)
- **Kiemelő szín:** `#c4ff00` (VitaSteps lime green), `#38bdf8` (sky blue)
- **Betűtípus:** `'Helvetica Neue', Arial, sans-serif`
- **Gombok:** Kerekített sarkú `#c4ff00` háttér fekete félkövér felirattal
