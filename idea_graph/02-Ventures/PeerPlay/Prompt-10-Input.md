# PROMPT 10 — EXECUTIVE VENTURE DECISION (PEERPLAY)
## Definitive Strategic Verdict, Risk-Adjusted Scoring and Action Mandate

### ROLE

Act as the Investment Board / Managing Director evaluating the comprehensive due diligence package of PeerPlay.

Your task is to cut through nuance, balance optimism against adversarial skepticism, and issue a definitive, binding one-page executive decision.

---

### INPUT CONTEXT (COMPLETE VENTURE DOSSIER)

- Opportunity Definition: `[[02-Ventures/PeerPlay/00-Opportunity]]`
- Question Graph: `[[02-Ventures/PeerPlay/01-Question-Graph]]`
- Full Research Dossier: `[[Research/Market]]`, `[[Research/Customer]]`, `[[Research/Competition]]`, `[[Research/Business-Model]]`, `[[Research/Financial]]`, `[[Research/Execution]]`
- Cross-Analysis & Synthesis: `[[02-Ventures/PeerPlay/03-Cross-Analysis]]`
- Adversarial Due Diligence Review: `[[02-Ventures/PeerPlay/04-Adversarial-Review]]` (or Prompt 09 output)

---

### CENTRAL QUESTION

Should this venture be stopped immediately, investigated further, validated through live customer experiments, launched as a pilot, funded for full development, or prepared for scale?

---

### DECISION OPTIONS (MUTUALLY EXCLUSIVE)

1. **STOP:** Fatal flaws make the opportunity unviable; close the project.
2. **RESEARCH:** Critical information voids remain; return to targeted investigation.
3. **VALIDATE:** Attractive thesis, but 1–3 critical assumptions must be tested via behavioral customer experiments before committing capital.
4. **PILOT:** Sufficient confidence to build a minimal prototype and deploy with 1–3 paying commercial clients.
5. **BUILD:** Strong evidence of product-market fit and commercial viability; proceed to full-scale development.
6. **SCALE:** Validated economics and execution capabilities; invest aggressively in customer acquisition.

---

### REQUIRED ONE-PAGE EXECUTIVE DECISION BRIEF STRUCTURE

Format the output strictly as a one-page **Executive Decision Brief**:

```markdown
# EXECUTIVE DECISION BRIEF: PEERPLAY

## 1. Executive Verdict
[A concise 3-sentence summary of the opportunity, its primary strength, and its central vulnerability.]

## 2. Opportunity Attractiveness & Evidence Confidence Scores
- **Opportunity Attractiveness:** [Rating: Low / Moderate / High / Very High] + rationale
- **Evidence Confidence Level:** [Rating: Low / Moderate / High / Very High] + rationale

## 3. Top 3 Strategic Strengths (Why this could win)
1. ...
2. ...
3. ...

## 4. Top 3 Fatal Risks (What could destroy it)
1. ...
2. ...
3. ...

## 5. The Critical Unknown (The make-or-break question)
[The single unverified assumption that determines venture success.]

## 6. Binding Strategic Decision
**STATUS:** [STOP / RESEARCH / VALIDATE / PILOT / BUILD / SCALE]

## 7. Decision Rationale
[Why this specific status is mandated based on the synthesis of research and adversarial critique.]

## 8. Next-Best Validation Experiment (Sprint 0)
[The immediate, low-cost real-world experiment to run within the next 14–30 days.]
- **Hypothesis to Test:**
- **Experiment Format:**
- **Target Audience:**
- **Execution Cost & Timeline:**

## 9. Definitive Success & Kill Criteria
- **Green Light (Proceed to Paid Commercial Deployment):** [Specific metric, e.g., 2 BSC HR heads agree to run a pilot and pay 300k+ HUF]
- **Red Light (Kill / Pivot Immediately):** [Specific falsification signal, e.g., >80% of HR managers state they refuse to facilitate the game themselves]
```
