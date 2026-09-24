---
id: advisor-security-and-multitenancy
type: system
name: Advisor Multi-Tenancy & Proposal Security
status: active

description: Az Optivoya B2B Advisor Workspace többügynökséges (Multi-Tenant) izolációja, szerveroldali jogosultságkezelése, Supabase Row Level Security (RLS) szabályai és az ügyfél-ajánlatok kriptográfiai megosztásának védelme.

source:
  type: code
  ref: app.core.auth

code:
  - app/core/auth.py
  - app/services/user_service.py
  - app/services/proposal_service.py
  - scripts/migrations/003_advisor_workspace.sql

related:
  - "[[advisor-workspace-blueprint]]"
  - "[[supabase-database]]"
  - "[[fastapi-backend]]"
  - "[[QUALITY_GATES]]"

used_by:
  - "[[advisor-workspace-blueprint]]"
---

# 🛡️ Advisor Multi-Tenancy & Proposal Security

Ez a dokumentum rögzíti az **Optivoya B2B Advisor Workspace** többügynökséges (Multi-Tenant) biztonsági architektúráját és az ügyfél-ajánlatok megosztásának védelmi garanciáit.

---

## 1. Multi-Tenant Szervezeti Hierarchia & Izoláció

```text
[Agency / Utazási Iroda] (agency_id)
        │
        ├── [Advisors / Tanácsadók] (advisor_id)
        │         │
        │         ├── [Clients / Ügyfelek] (client_id)
        │         │         │
        │         │         └── [TripCases / Ügyek] (case_id)
        │         │                   │
        │         │                   └── [Proposals & Versions] (prop_id, v1, v2)
```

### Szigorú Hozzáférési Szabályok:
1. **Ügynökségi Izoláció**: Egy adott ügynökség tanácsadói kizárólag a saját ügynökségükhöz (`agency_id`) tartozó ügyfelekhez és ügyekhez férhetnek hozzá.
2. **Szerveroldali Hitelesítés**: A frontendről érkező kérésekben lévő `agency_id` vagy `user_id` nem fogadható el vakon; a backend minden kérést az aktív munkamenet (`session_token`) alapján szerveroldalon ellenőriz.
3. **Supabase Row Level Security (RLS)**: Az adatbázis szintjén minden tábla (`trip_cases`, `clients`, `proposals`, `research_runs`) RLS házirenddel védett.

---

## 2. Kriptográfiai Ajánlat-Megosztás (`ProposalShare`)

Az ügyfeleknek kiküldött nyilvános ajánlat linkek nem tartalmaznak kitalálható ID-kat vagy auto-increment sorszámokat:

```yaml
ProposalShare:
  id: "share_uuid"
  proposal_id: "prop_uuid"
  proposal_version_number: 1
  token: "cryptographically_random_urlsafe_32_bytes_token"
  token_hash: "sha256_hash"
  created_at: "2026-09-24T14:00:00Z"
  expires_at: "2026-10-24T14:00:00Z" # 30 napos lejárati idő
  revoked_at: null
  is_revoked: false
  access_count: 3
  last_accessed_at: "2026-09-24T14:20:00Z"
```

### Biztonsági Garanciák:
- **Nem Kitalálható Token**: 256 bites véletlenszerű string (`secrets.token_urlsafe(32)`).
- **Azonnali Visszavonhatóság (Revocable)**: Az Advisor 1 kattintással visszavonhatja a megosztást; a token ezt követően azonnal 404-et ad.
- **Lejárati Idő (Expiry)**: Alapértelmezetten 30 nap után automatikusan inaktiválódik.
- **Szigorú Scoping**: A megosztott linken keresztül az ügyfél **kizárólag az adott Proposal pillanatfelvételét (Snapshot)** látja.
  - **Soha nem férhet hozzá**: A teljes ügyhöz, a CRM adatokhoz, a belső tanácsadói jegyzetekhez (`advisor_notes`) vagy a nyers pontszámokhoz.
