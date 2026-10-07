---
id: supabase
type: system
name: Supabase
status: active
description: Primary managed PostgreSQL relational database, authentication, and file storage backend.
source:
  type: database
  ref: https://ncsathcqpvlrygkphced.supabase.co
code:
  - landing_predikalo1/api/
  - landing_predikalo1/portal.html
  - landing_predikalo1/admin.html
related:
  - "[[customer]]"
  - "[[run]]"
  - "[[order]]"
  - "[[ADR-001-supabase-migration|ADR-001]]"
  - "[[ADR-005-strict-rls-security|ADR-005]]"
---

# System: Supabase (PostgreSQL & Storage)

Supabase serves as the persistent single source of truth for all VitaSteps operational, e-commerce, fulfillment, marketing, and analytics data.

## Entity-Relationship Architecture

```mermaid
erDiagram
    RUNNERS ||--o{ ORDERS : places
    RUNNERS ||--o{ RUNS : registers
    RUNNERS ||--o{ FEEDBACKS : submits
    ORDERS ||--|{ RUNS : contains
    RUNS ||--o| SHIPMENTS : fulfills
    RUNS ||--o| FEEDBACKS : receives
    LEADS }o..o| RUNNERS : converts_to
    
    VISITORS ||--o{ SESSIONS : initiates
    SESSIONS ||--o{ EVENTS : records
    SESSIONS ||--o| ORDERS : attributes
    
    RUNNERS {
        uuid id PK
        text email UK
        text name
        text phone
        text billing_name
        text billing_address
        timestamp created_at
    }

    ORDERS {
        bigint id PK
        uuid runner_id FK
        text stripe_session_id UK
        text stripe_payment_status
        integer amount_total
        text currency
        text campaign
        text billing_name
        text billing_email
        text billing_address
        text utm_campaign
        text utm_content
        integer referrals_redeemed
        boolean is_test
        timestamp created_at
    }

    RUNS {
        bigint id PK
        uuid runner_id FK
        bigint order_id FK
        text serial_number UK
        text name
        numeric distance_km
        text campaign
        boolean completed
        timestamp completion_date
        boolean proof_submitted
        text[] proof_urls
        timestamp proof_submitted_at
        boolean shipped
        text ship_together_with
        text referred_by
        boolean is_test
        timestamp created_at
    }

    SHIPMENTS {
        bigint id PK
        bigint run_id FK
        text method
        text phone
        text parcel_id
        text parcel_name
        text parcel_address
        text home_address
        boolean shipped
        timestamp shipped_at
        text tracking_code
        boolean received
        timestamp received_at
        timestamp created_at
    }

    FEEDBACKS {
        bigint id PK
        uuid runner_id FK
        bigint run_id FK
        text runner_email
        integer erem_minoseg
        integer szallitas_elegedett
        boolean reszvetel_ujra
        integer nps_score
        text kovetkezo_tajegyseg
        text tetszett_legjobban
        text jobba_tenne
        text photo_url
        timestamp created_at
    }

    LEADS {
        bigint id PK
        text email UK
        text name
        text campaign
        text source
        boolean converted
        timestamp converted_at
        boolean unsubscribed
        timestamp created_at
    }

    META_DAILY_METRICS {
        bigint id PK
        date date
        text campaign_id
        text campaign_name
        text adset_id
        text adset_name
        text ad_id
        text ad_name
        numeric spend
        integer impressions
        integer reach
        integer clicks
        integer link_clicks
        numeric ctr
        numeric cpc
        numeric cpm
        integer purchases
        numeric revenue
        numeric cpa
        numeric roas
        timestamp created_at
    }

    MARKETING_TARGETS {
        bigint id PK
        text campaign_name UK
        numeric target_cpa
        numeric warning_cpa
        numeric critical_cpa
        numeric target_roas
        numeric warning_roas
        numeric critical_roas
        numeric medal_cost
        numeric shipping_cost
    }

    ANALYTICS_VISITORS {
        text visitor_id PK
        timestamp first_seen_at
        timestamp last_seen_at
        integer total_sessions
        integer total_orders
        numeric total_revenue
        text first_touch_source
        text first_touch_campaign_name
        text first_touch_ad_name
        text last_touch_source
        text last_touch_campaign_name
        text last_touch_ad_name
        boolean is_test
    }

    ANALYTICS_SESSIONS {
        text session_id PK
        text visitor_id FK
        text utm_source
        text utm_medium
        text utm_campaign
        text utm_content
        text meta_campaign_name
        text meta_ad_name
        text landing_page
        text device_type
        text browser
        integer time_on_page
        integer max_scroll_depth
        boolean offer_viewed
        boolean cta_clicked
        boolean checkout_started
        boolean purchase_completed
        text order_id FK
        numeric revenue
        boolean is_test
        timestamp created_at
    }

    ANALYTICS_EVENTS {
        bigint id PK
        text session_id FK
        text visitor_id FK
        text event_name
        jsonb event_data
        boolean is_test
        timestamp created_at
    }
```

## Relational Tables Overview

### 1. Core E-Commerce & Fulfillment
* **`runners`:** User profiles and customer registry (`id`, `email`, `name`, `phone`, `billing_name`, `billing_address`).
* **`orders`:** Financial Stripe transactions (`id`, `runner_id`, `stripe_session_id`, `stripe_payment_status`, `amount_total`, `campaign`, `utm_campaign`, `utm_content`, `is_test`).
* **`runs`:** Challenge registrations and medal completions (`id`, `runner_id`, `order_id`, `campaign`, `serial_number`, `distance_km`, `completed`, `completion_date`, `proof_submitted`, `proof_urls`, `shipped`, `ship_together_with`).
* **`shipments`:** Logistics records for Foxpost / Home Delivery (`id`, `run_id`, `method`, `parcel_id`, `parcel_name`, `home_address`, `phone`, `shipped`, `shipped_at`, `tracking_code`, `received`).
* **`feedbacks`:** Post-completion ratings, reviews, and photo submissions (`runner_id`, `run_id`, `nps_score`, `erem_minoseg`, `szallitas_elegedett`).
* **`leads`:** Lead capture entries for Kalandfüzet & route downloads (`email`, `name`, `campaign`, `source`, `converted`, `converted_at`).

### 2. Marketing & Unit Economics
* **`meta_daily_metrics`:** Daily ad-level and campaign-level Meta Marketing performance (`date`, `spend`, `impressions`, `clicks`, `purchases`, `revenue`, `cpa`, `roas`, `ad_name`, `campaign_name`).
* **`marketing_targets`:** Target CAC, ROAS, and unit thresholds per campaign.

### 3. Analytics & Attribution Engine
* **`analytics_visitors`:** Multi-touch visitor tracking and lifetime value.
* **`analytics_sessions`:** Complete session journeys, engagement metrics, scroll depths, and conversion flags.
* **`analytics_events`:** Granular real-time event stream (`landing_session`, `cta_click`, `scroll_50/75/90`, `engaged_15s`, `foxpost_point_selected`, `checkout_submit_attempt`, `purchase`, `form_validation_failed`).

## Storage Buckets
* `proofs`: User GPX track uploads and summit selfie photos.
* `medals/finance`: Revolut bank statement CSVs.

## Security & Row-Level Security (RLS)
* Public anonymous access is locked down.
* Customer portal queries are scoped strictly to authenticated emails (`auth.jwt() ->> 'email' = email`).
* Admin operations use serverless Vercel endpoints authenticated via `ADMIN_SECRET` and the `service_role` key.
