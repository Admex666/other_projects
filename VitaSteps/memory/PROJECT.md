# 🏔️ VitaSteps - Project Overview & Goals

## 📖 Project Description
VitaSteps is a premium virtual hiking and running challenge platform. Participants select a challenge route, register by paying a entry fee, complete the hike using any GPS tracking app (e.g., Strava, Garmin), and upload their proof to a personal portal. Upon verification, they receive a high-quality, custom-designed physical finisher medal shipped directly to their selected Foxpost parcel locker or home address.

---

## 🏔️ Campaigns

1.  **Prédikálószék Vertical (Completed - June 2026)**
    *   *Finishers:* 67 paid participants.
    *   *Medal:* 75mm custom-designed, hand-painted Antique Nickel medal.
    *   *Outcome:* 10/10 NPS customer satisfaction, profitable first batch.
2.  **A Nagy-Kevély csillagjai (Active/Upcoming - August-September 2026)**
    *   *Price:* 7 990 Ft (AAM invoice, free Foxpost delivery).
    *   *Finishers Limit:* 100 participants.
    *   *Medal:* 70mm custom 3D Antique Silver medal with green soft enamel coloring and custom printed ribbon.
    *   *Unique Elements:* Egri Vár movie copy ruins & Teve-szikla rock formations, virtual downloadable PDF Guidebook (Kalandkönyv), 4 optional route lengths (from family-friendly 6km to 25km ultra).

---

## 🎯 Objectives
*   **Customer Delight:** Maintain 10/10 NPS on medal quality and delivery speed.
*   **Operational Automation:** Eliminate manual work by automating invoicing (Számlázz.hu), email sequences (Resend/SMTP), data backups (Google Sheets), and participant indexing (Supabase).
*   **Financial Growth:** Keep Facebook Ads CPA below 3,000 Ft to maintain a stable >2x ROAS.

---

## 🛠️ Core Technology Stack
*   **Frontend:** HTML5, CSS3, Vanilla Javascript, Leaflet.js (for map route visualizations).
*   **Backend:** Node.js (Vercel Serverless Functions).
*   **Database:** Supabase (PostgreSQL & Supabase Storage for GPX/Photo uploads).
*   **Invoicing:** Számlázz.hu (XML API for Alanyi Adómentes - AAM e-invoices).
*   **Data Sheets:** Google Sheets API (for raw logs, shipping spreadsheets, and real-time dashboards).
*   **Email Services:** NodeMailer (Google SMTP) / Resend.
*   **Payments:** Stripe Checkout (with dynamic quantity and home delivery surcharge).
*   **Automations/Crons:** GitHub Actions workflows (for daily Foxpost package status sync and email follow-ups).
