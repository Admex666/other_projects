# 📊 Current Project Status & Focus

## 🟢 What is Working
*   **Unified Campaign Configuration:** The frontend checkout and success pages are unified and configuration-driven (`config/campaigns.json`). Bugfixes deploy globally, and launching new campaigns requires editing a single JSON block.
*   **Stripe Checkout Pipeline:** Supports dynamic quantity selection (multi-medal orders), participant details entry per medal, and optional home delivery surcharge (+1 200 Ft).
*   **Automated Webhook Sync:** The Vercel Node.js webhook (`api/stripe-webhook.js`) still exists as fallback, but the **primary post-payment pipeline is now `api/process-payment.js`** (webhook-free, triggered from `siker.html` via `session_id` URL param). This was necessary because Stripe's free plan does not support webhook endpoint registration. The pipeline covers: Google Sheets (`tally_raw` + `stripe_raw2`), Supabase runner registration, Számlázz.hu e-invoice, and welcome email. Test/live mode is auto-detected from `cs_test_` session_id prefix. Idempotency is enforced via `stripe_session_id` column in Supabase.
*   **Database & Sheets Integrity:** Serial number extraction regex (`/#(\d+)\//`) is fixed. `is_test` column in `runners` table excludes test buys from serial rank calculations. `tally_szallitas` writes removed — shipping data (incl. `parcelId`) is in `stripe_raw2` column I.
*   **Daily Foxpost Cron:** GitHub Actions run `scripts/daily_tracking.py` daily to fetch package updates and email follow-ups. Path mapping is correct.
*   **Meta Ads Campaign Configuration:**
    *   Prospecting Ad Set (LAL 1% exclusion of buyers) is active/ready.
    *   Retargeting Ad Set (VitaSteps Webhelylátogatók 30 nap + FB/IG Engagers 90 nap, buyer exclusions) configured.
    *   Ads setup configured at a starting budget of **1 600 HUF / day**.
    *   High-converting, sales-oriented ad copywriting variations for V4 (product) and V5 (hiker) saved and prepared.
*   **Nagy-Kevély Landing Page Megújítás (UPDATED 2026-07-13):**
    *   Beillesztettük a közösségi kilométer-statisztikát (1 230 km completed) és a Kalandkönyv (PDF) promóciós szekciót.
    *   A visszaszámlálót a kihívás végére (**szeptember 13. 23:59**) állítottuk be.
    *   A gombok felett kiemeltük az akciós árat (**13.990 Ft helyett 7.990 Ft**).
    *   A hívó gombok feliratát átírtuk a konverziós szempontból erősebb **„Megszerzem az érmemet! 🏅”** (és mobilon/nav sávban **„Kérem az érmet 🏅”**) szövegre.
    *   A gombok alá elhelyeztük az `✓ Ingyenes szállítás` és `✓ Ajándék kalandkönyv` meggyőző előny-címkéket.
    *   A térképes útvonal-szűrőket kiterjesztettük a 4 új távra (6km, 10km, 15km, 25km).
    *   **Hero kép cseréje (FIXED):** A korábbi nem betöltődő éremképet lecseréltük az éles termék kreatívra (`nagy_kevely_creative_v4.png`), 12px border-radius-szal.
    *   **Mobil Sticky CTA és Kicsúszás Fixek (FIXED):** Globális CSS szabályokkal megszüntettük a vízszintes kicsúszást.
    *   **Nagy-Kevély Kalandkönyv Generátor (COMPLETED 2026-07-15):** Elkészült a `nagykevely/kalandkonyv.html` 6 oldalas túranapló és kalandkönyv füzet generátor. Leaflet térkép (340px), HTML5 Canvas szintmetszet, max 5 POI/oldal, A5 nyomtatás.
    *   **Személyes Portál Kalandkönyv Tab (COMPLETED 2026-07-13):** A `portal.html` oldalon létrehoztunk egy új „Kalandkönyv” fület PK sorszámú nevezőknek.
*   **Prédikálószék Ping Email System (COMPLETED 2026-07-13):**
    *   `scripts/send_emails.py` updated with `ping` mode as default.
    *   15 emails sent to non-finisher Prédikálószék participants; `ping0713` column auto-updated in Sheets.

---

## 🎯 Current Focus
*   **Payment Pipeline Tesztelése:**
    *   Számlázz.hu és welcome email működésének end-to-end ellenőrzése `?test=true` módban.
    *   Vercel deploy (`vercel --prod`) az összes mai változással.
*   **Nagy-Kevély csillagai Campaign Pre-launch:**
    *   Secure checkout: `?test=true` teszt mód működik, live védelem aktív.
    *   Verify Stripe live environment for the `VSBARAT10` coupon code.
    *   Verify standard pixel events (PageView, InitiateCheckout, Purchase) using Meta Pixel Helper.

---

## 🛑 Known Blockers / Issues
*   `DRY_RUN = True` is currently set in `scripts/send_emails.py` — must be manually changed to `False` before any live email send.
*   Nagy-Kevély campaign pre-launch: Checkout is blocked globally on live Vercel domains to avoid premature signups. Must be removed when launching.
*   Stripe `VSBARAT10` referral coupon code: live environment testing still pending.
*   **Supabase migration pending:** `ALTER TABLE runners ADD COLUMN IF NOT EXISTS stripe_session_id text;` — szükséges a process-payment idempotencia-ellenőrzéshez.
*   **Vercel deploy pending:** Összes mai változás (`process-payment.js`, `siker.html`, `checkout.js`, `stripe-webhook.js`) még nincs élesítve.
