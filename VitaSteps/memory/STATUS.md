# 📊 Current Project Status & Focus

## 🟢 What is Working
*   **Unified Campaign Configuration:** The frontend checkout and success pages are unified and configuration-driven (`config/campaigns.json`). Bugfixes deploy globally, and launching new campaigns requires editing a single JSON block.
*   **Stripe Checkout Pipeline:** Supports dynamic quantity selection (multi-medal orders), participant details entry per medal, and optional home delivery surcharge (+1 200 Ft).
*   **Automated Webhook Sync:** The Vercel Node.js webhook (`api/stripe-webhook.js`) handles payment checkout completion, logs rows in Google Sheets, registers profiles in Supabase with custom serial numbering, generates Számlázz.hu AAM e-invoices, and sends welcome emails.
*   **Database & Sheets Integrity:** Serial number extraction regex (`/#(\d+)\//`) is fixed, stopping exponential rank calculations in Supabase.
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
    *   **Mobil Sticky CTA és Kicsúszás Fixek (FIXED):** Globális CSS szabályokkal (`html, body { overflow-x: hidden; }` és `max-width` megkötések) megszüntettük a vízszintes kicsúszást (különös tekintettel az iPhone 12 Pro 390px szélességű kijelzőjére). A navigációs sávot és a sticky gombsávot reszponzívvá tettük.
    *   **Érem kép pozicionálása mobilon (FIXED):** Telefonos nézetben az érem képe az akciós árazás és a CTA gombok elé került beágyazásra a jobb vizuális elrendezés érdekében.
    *   **Nagy-Kevély Kalandkönyv Generátor (COMPLETED 2026-07-13):** Elkészült a `nagykevely/kalandkonyv.html` személyre szabható és nyomtatható A5/A4 túranapló és kalandkönyv generátor (dinamikus útvonal ellenőrzőpontok, GPX QR-kód API-k, erdei bingók, kvízek, kitölthető túranaplók).
    *   **Személyes Portál Kalandkönyv Tab (COMPLETED 2026-07-13):** A `portal.html` oldalon létrehoztunk egy új "Kalandkönyv" fület, ami kizárólag a Nagy-Kevély kihívás nevezőinek (`PK` sorszám előtag) jelenik meg, lehetővé téve a névvel és távval előre kitöltött könyv színes vagy tintakímélő B&W exportálását.
*   **Prédikálószék Ping Email System (COMPLETED 2026-07-13):**
    *   `scripts/send_emails.py` updated with `ping` mode as default.
    *   `email_ping_template.html` rewritten with dual CTA: ✅ igazolás (NpRz5W) + 📦 szállítás (predikalo/szallitas.html).
    *   15 emails sent to non-finisher Prédikálószék participants; `ping0713` column auto-updated in Sheets.

---

## 🎯 Current Focus
*   **Nagy-Kevély csillagai Campaign Pre-launch:**
    *   Verify Stripe live environment for the `VSBARAT10` coupon code.
    *   Verify standard pixel events (PageView, InitiateCheckout, Purchase) using Meta Pixel Helper.

---

## 🛑 Known Blockers / Issues
*   `DRY_RUN = True` is currently set in `scripts/send_emails.py` — must be manually changed to `False` before any live email send.
*   Stripe `VSBARAT10` referral coupon code: live environment testing still pending.
