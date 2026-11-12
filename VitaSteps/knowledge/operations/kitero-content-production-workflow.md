---
id: kitero-content-production-workflow
type: operation
name: VitaSteps Kitérő Ingyenes Sétagyártási Workflow
status: active
date: 2026-11-12
source:
  - "[[kitero-master-system-plan]]"
  - "E:/Data/hosszulepes/setatervezo_workflow.md"
prompts:
  - landing_predikalo1/prompts/kitero_workflow/01_discovery_prompt.txt
  - landing_predikalo1/prompts/kitero_workflow/02_deep_research_prompt.txt
  - landing_predikalo1/prompts/kitero_workflow/03.2_webapp_prompt.txt
  - landing_predikalo1/prompts/kitero_workflow/03_setakonyv_prompt.txt
---

# 🎙️ VitaSteps Kitérő: Ingyenes Sétagyártási Master Workflow

Ez az útmutató bemutatja, hogyan lehet **100%-ban ingyenes vagy minimális költségű AI eszközökkel** (Deep Research, Prompt láncok, geokódolás, TSP optimalizálás, böngészős/ingyenes TTS hanggenerálás) profi, magával ragadó városi élménysétákat készíteni a VitaSteps Kitérőhöz.

---

## 🗺️ 1. A Sétagyártás 5 Lépéses AI-Ember Folyamata

```mermaid
flowchart TD
    subgraph F1 ["1. Fázis: Ötletelés & Szögek (10 perc)"]
        A([Téma / Városrész kijelölése]) --> B["Prompt #1 (01_discovery_prompt.txt)<br>Gemini / Claude ingyenes Deep Search"]
        B --> C[30 POI lista + 3-4 Izgalmas Narratív Szög]
    end

    subgraph F2 ["2. Fázis: Kurálás & Útvonalterv (10 perc)"]
        C --> D["Emberi szelekció: 8-10 megálló kiválasztása<br>Start & Cél pont rögzítése"]
        D --> E["Geokódolás & TSP Útvonal-optimalizálás<br>(optimizer.py: Nearest Neighbor / 2-Opt)"]
        E --> F[Térképes Útvonalterv: terkep.html + Koordináták]
    end

    subgraph F3 ["3. Fázis: Mélykutatás (15 perc)"]
        F --> G["Prompt #2 (02_deep_research_prompt.txt)<br>Konkrét 8-10 POI mélyfúrása"]
        G --> H[Rejtett történetek, botrányok, anekdoták, ellenőrzött források]
    end

    subgraph F4 ["4. Fázis: Hangoskönyv Szövegezés (10 perc)"]
        H --> I["Prompt #3.2 (03.2_webapp_prompt.txt)<br>TTS-optimalizált JSON generálás"]
        I --> J["JSON kimenet:<br>• audio_hook (15-20 mp)<br>• audio_story (300-400 szó folyó szöveg)"]
    end

    subgraph F5 ["5. Fázis: Ingyenes Hangosítás & Élesítés (15 perc)"]
        J --> K["Ingyenes TTS Audio generálás<br>(Edge TTS Python / Web Speech / ElevenLabs Free)"]
        K --> L[Végleges tour_config.json + MP3 fájlok]
        L --> M([Importálás a Supabase-be & Tesztelés Terepen])
    end
```

---

## 🛠️ 2. Hogyan oldjuk meg 0 Ft-ból a gyártást?

1. **Kutatás & Szöveg:**
   * **Gemini 2.5 Pro / Flash** (Google AI Studio vagy ingyenes webes felület) $\rightarrow$ korlátlan mélykeresés és forráskutatás magyar nyelven.
   * A `01_discovery_prompt.txt` és `02_deep_research_prompt.txt` promptok azonnal beilleszthetők.
2. **Útvonaltervezés & Sorrendezés:**
   * Ingyenes Nominatim / OpenStreetMap geokódolás és Python TSP optimalizálás (`optimizer.py`), ami garantálja a legkevesebb felesleges gyaloglást.
3. **Hangalámondás (TTS) 0 Ft költséggel:**
   * **Microsoft Edge TTS (`edge-tts` python csomag):** Teljesen ingyenes, nincs token-korlát. A Microsoft természetes neurális magyar hangjai (`hu-HU-TamasNeural`, `hu-HU-NoemiNeural`) kimagaslóan jó minőségűek, felveszik a versenyt a fizetős rendszerekkel.
   * Alternatíva: ElevenLabs ingyenes tier (havi 10 000 karakter = kb. 1 komplett pilot séta hanganyaga).

---

## 📁 3. Elérhető Promptok a Projektben

A prompt sablonok közvetlenül elérhetők a projektben:
* [landing_predikalo1/prompts/kitero_workflow/01_discovery_prompt.txt](file:///E:/Data/other_projects/VitaSteps/landing_predikalo1/prompts/kitero_workflow/01_discovery_prompt.txt) — 30 POI ötletelés és tematika
* [landing_predikalo1/prompts/kitero_workflow/02_deep_research_prompt.txt](file:///E:/Data/other_projects/VitaSteps/landing_predikalo1/prompts/kitero_workflow/02_deep_research_prompt.txt) — Tényfeltáró mélykutatás és anekdoták
* [landing_predikalo1/prompts/kitero_workflow/03.2_webapp_prompt.txt](file:///E:/Data/other_projects/VitaSteps/landing_predikalo1/prompts/kitero_workflow/03.2_webapp_prompt.txt) — Felolvasásra optimalizált Hook és Story JSON generálás
* [landing_predikalo1/prompts/kitero_workflow/03_setakonyv_prompt.txt](file:///E:/Data/other_projects/VitaSteps/landing_predikalo1/prompts/kitero_workflow/03_setakonyv_prompt.txt) — Részletes sétakönyv/kalandfüzet generáló prompt
