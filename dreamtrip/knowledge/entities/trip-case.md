---
id: trip-case
type: entity
name: Trip Case
status: active

description: A B2B Advisor Workspace elsődleges üzleti és tervezési entitása. Összefogja az ügynökségi klienst, a briefet, a feloldott preferenciákat, a kutatási folyamatot, a generált 3 alternatív utazási opciót, az összehasonlítást és az ügyfélajánlat-verziókat.

source:
  type: code
  ref: app.models.advisor_models.TripCase

code:
  - app/models/advisor_models.py
  - app/services/advisor_orchestration_service.py
  - static/js/advisor/advisor_state.js

related:
  - "[[advisor-workspace-blueprint]]"
  - "[[trip]]"
  - "[[proposal-generation]]"
  - "[[unified-trip-model]]"

used_by:
  - "[[fastapi-backend]]"
  - "[[supabase-database]]"
---

# Entity: Trip Case

A `Trip Case` az **Optivoya Advisor Workspace** központi aggregátuma, amely felváltja az egyszeri szekvenciális munkameneteket egy tartós, perzisztens, verziózható és több-opciós döntéstámogató munkafolyamattal.

## Hierarchia & Adatkapcsolatok

```text
Agency
 └── Advisor
      └── Client
           └── Trip Case
                ├── Brief (Client requirements, dates, travelers, budgets)
                ├── Preferences (Resolved: Advisor defaults + Client profile + Case overrides)
                ├── Constraints (Hard constraints, relaxation alternatives)
                ├── Research (Candidate destinations, flights, stays, activities)
                ├── Options (3 complete archetype options: Best Overall, Best Value, Best Experience)
                ├── Comparisons (Side-by-side relative matrix, trade-offs)
                ├── Proposals (Multi-option proposal documents, versions v1/v2/v3)
                └── Timeline & Revisions (Audit log of advisor & client actions)
```

## Főbb attribútumok
- `id`: Egyedi azonosító (UUID / case ID).
- `agency_id`, `advisor_id`, `client_id`: Szervezeti és ügyféli hovatartozás.
- `title`, `status`: `Brief`, `Research`, `Shortlist`, `Proposal`, `Waiting for Client`, `Revision`, `Closed`.
- `origin`, `destination_focus`: Indulási repülőtér és célállomás fókusz.
- `adults`, `children`: Utasok száma.
- `date_mode`, `out_date`, `in_date`, `date_window`, `min_stay`, `max_stay`: Időbeli keretek.
- `budget_mode`, `total_budget`, `component_budgets`, `search_scope`: Költségvetési és keresési hatókör.
- `created_at`, `updated_at`: Időbélyegek.
