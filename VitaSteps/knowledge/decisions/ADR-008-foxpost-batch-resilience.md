---
id: ADR-008-foxpost-batch-resilience
type: decision
name: ADR-008 Foxpost Batch Validation and Phone Number Sanitization
status: active
description: Pre-validating recipient phone numbers and parcel destinations to prevent all-or-nothing batch creation failures in Foxpost API.
date: 2026-08-31
deciders:
  - Adam
  - Antigravity AI
related:
  - "[[foxpost]]"
  - "[[order-fulfillment|Order Fulfillment]]"
  - "[[admin-panel|Admin Panel]]"
---

# ADR-008: Foxpost Batch Validation and Phone Number Sanitization

## Context
When dispatching locker parcels in bulk via Foxpost WebAPI (`POST /api/parcel`):
1. **All-or-Nothing Batch Rejection:** Foxpost evaluates the entire array payload atomically. If even a single parcel in the array contains an invalid or malformed field (e.g. `recipientPhone: "+"` caused by text entered in the phone field during checkout), Foxpost responds with `valid: false` and generates zero barcodes for all valid parcels in that batch.
2. **Checkout Data Entry Variance:** Participants occasionally input their name in the phone field and their phone number in the billing address field, producing non-numeric strings that fail standard regex.

## Decisions

1. **Pre-Validation and Batch Error Isolation (`api/create-foxpost-parcels.js`):**
   * Before sending parcels to Foxpost API, each item is pre-validated for mandatory fields:
     * Valid mobile phone number format (`+36...` with standard Hungarian length).
     * Non-empty destination locker ID (e.g. `hu351`).
     * Valid recipient email.
   * Any parcel failing pre-validation is isolated into a `failed` collection and excluded from the outbound API payload, ensuring valid parcels are dispatched without interruption.

2. **Intelligent Phone Number Sanitization:**
   * `formatPhone` extracts mobile numbers matching `(?:(?:\+|00)?36|06)[\s\-]?[1-9]\d...` from both the primary phone field and billing address fallbacks.
   * Returns standard E.164-compatible `+36XXXXXXXXX` or `null` if insufficient digits exist.

3. **Inline Admin Parcel Editor (`admin.html`):**
   * The logistics dashboard flags parcels with missing or invalid phone numbers with a visual warning (`⚠️`) and provides an inline editor (`✏️`) to update phone numbers and locker IDs directly in Supabase (`/api/admin-approve` with `action: 'update_shipment'`).

## Consequences
* High dispatch reliability: one invalid order can no longer block warehouse batch fulfillment.
* Immediate administrative feedback with human-readable error reasons.
* Zero data corruption from malformed contact information.
