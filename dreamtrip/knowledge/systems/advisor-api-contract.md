---
id: advisor-api-contract
type: system
name: Advisor REST API Contract & Endpoint Specification
status: active

description: Az Optivoya B2B Advisor Workspace RESTful API szerződése, kérés/válasz sémái, hibakezelése, aszinkron kutatási végpontjai és idempotenciája.

source:
  type: code
  ref: app.routers.advisor_api

code:
  - app/routers/advisor_api.py
  - app/models/advisor_models.py

related:
  - "[[advisor-workspace-blueprint]]"
  - "[[fastapi-backend]]"
  - "[[QUALITY_GATES]]"

used_by:
  - "[[advisor-workspace-blueprint]]"
---

# 📡 Advisor REST API Contract & Endpoint Specification

Ez a dokumentum rögzíti az **Optivoya Advisor Workspace** REST API szerződéseit és végpontjait.

---

## 1. Végpontjegyzék (Endpoint Catalog)

### 1. Dashboard & CRM
- `GET /api/advisor/me`: Bejelentkezett tanácsadó és ügynökség profilja.
- `GET /api/advisor/dashboard/kpis`: Valós idejű működési KPI-k (aktív ügyek, generált ajánlatok, megtakarított órák).
- `GET /api/advisor/clients`: Ügyféllista keresési és szűrési paraméterekkel.
- `POST /api/advisor/clients`: Új ügyfél létrehozása tartós preferenciaprofillal.
- `GET /api/advisor/clients/{client_id}`: Ügyfél részletei és kapcsolódó korábbi ügyei.
- `PUT /api/advisor/clients/{client_id}`: Ügyfélprofil módosítása.

### 2. Trip Case Menedzsment
- `GET /api/advisor/cases`: Ügylista státusz szerinti szűréssel.
- `POST /api/advisor/cases`: Új utazási ügy indítása.
- `GET /api/advisor/cases/{case_id}`: Ügy teljes aggregátuma (kliens, megkötések, opciók).
- `PUT /api/advisor/cases/{case_id}/brief`: Mély brief, költségkeret (`BudgetConstraint`) és preferenciák frissítése.
- `GET /api/advisor/cases/{case_id}/resolved-preferences`: 4 rétegű feloldott preferencia-hierarchia.
- `POST /api/advisor/cases/{case_id}/duplicate`: Ügy klónozása alternatív variációkhoz.
- `POST /api/advisor/cases/{case_id}/override`: Tanácsadói manuális felülbírálás auditált naplózása.

### 3. Aszinkron Kutatás (Research Lifecycle)
- `POST /api/advisor/cases/{case_id}/research`: Kutatási futás indítása a 9 stratégia egyikével $\to$ visszaadja a `job_id`-t.
- `GET /api/advisor/cases/{case_id}/research/{run_id}`: Adott kutatási futás állapotának, lépéseinek és szolgáltatói bontásának lekérdezése.
- `POST /api/advisor/cases/{case_id}/research/{run_id}/cancel`: Futó kutatás leállítása.
- `GET /api/advisor/cases/{case_id}/candidates`: Legenerált nyers és köztes kandidátusok listája.
- `POST /api/advisor/cases/{case_id}/candidates/pin`: Kandidátus komponens (város, járat, hotel) rögzítése.

### 4. Döntéstámogatás, Diagnosztika & Összehasonlítás
- `POST /api/advisor/cases/{case_id}/diagnose-constraints`: 0 találat esetén feltétel-ütközések diagnosztikája és 1-kattintásos enyhítési javaslatok.
- `POST /api/advisor/cases/{case_id}/apply-relaxation`: Jóváhagyott enyhítési patch alkalmazása és 3 opció újraszintézise.
- `GET /api/advisor/cases/{case_id}/verification-status`: Opciók adat-eredetének, TTL-jének és mélylinkjeinek ellenőrzése.
- `GET /api/advisor/cases/{case_id}/risks`: Működési kockázatok (átszállási idő, éjszakai érkezés) kiértékelése.

### 5. Ajánlatok, Verziózás & Biztonságos Megosztás
- `GET /api/advisor/cases/{case_id}/proposals`: Ügyhöz tartozó ajánlatverziók listája.
- `POST /api/advisor/cases/{case_id}/proposals`: Új ajánlat (v1) pillanatfelvétel generálása.
- `GET /api/advisor/proposals/{proposal_id}`: Ajánlat lekérése ID alapján.
- `PUT /api/advisor/proposals/{proposal_id}`: Ajánlatszöveg vagy kijelölt opciók módosítása.
- `POST /api/advisor/proposals/{proposal_id}/new-version`: Új ajánlatverzió (v2, v3...) elágaztatása.
- `POST /api/advisor/proposals/{proposal_id}/share`: Kriptográfiai, lejáró, visszavonható publikus megosztási token generálása.
- `GET /api/advisor/public/proposals/{token}`: Ügyfél-biztonságos ajánlat lekérése publikus token alapján (belső jegyzetek nélkül).
- `POST /api/advisor/proposals/{proposal_id}/revoke-share`: Megosztási link azonnali visszavonása.
- `GET /api/advisor/proposals/{proposal_id}/preview`: Nyomtatásbarát A4 HTML előnézet.

### 6. Idővonal & Visszacsatolás
- `GET /api/advisor/cases/{case_id}/timeline`: Ügy kronologikus audit naplója.
- `POST /api/advisor/cases/{case_id}/timeline`: Manuális esemény vagy jegyzet rögzítése.
- `POST /api/advisor/cases/{case_id}/feedback`: Ügyfél visszajelzés rögzítése.
- `POST /api/advisor/cases/{case_id}/reoptimize`: 1-kattintásos újrahangolás új ajánlatverzióval.
