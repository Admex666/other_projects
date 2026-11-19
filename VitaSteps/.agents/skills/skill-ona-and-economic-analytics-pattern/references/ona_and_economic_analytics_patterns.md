# 📐 ONA and Economic Analytics Patterns for Trading Game Debrief

**Domain:** Data Analytics & Organisational Network Analysis (ONA)  
**Related Specs:** `MVP_PLAN_v2.md`, `backend_contracts_and_state_machine.md`  
**Date:** 2026-11-15  

---

## 1. Network Centrality & ONA Metrics

In the PeerPlay Trading Game, interaction data is captured at two layers:
1. **P2P Trade Transactions (`TradeTransaction`):** Behavioral, objective interaction network with asset and money flow.
2. **Post-Game Peer Recognition (`SurveyResponse`):** Perceptual, relational endorsement network.

### Formulas & Benchmarks:
- **Directed Trade Density ($D_d$):**
  $$D_d = \frac{E_{\text{accepted}}}{N(N-1)}$$
  Where $N=4$ teams, maximum possible directed pairs is 12. A density of $>40\%$ indicates healthy cross-silo engagement.
- **Undirected Connectivity ($C_u$):**
  $$C_u = \frac{P_{\text{connected}}}{\frac{N(N-1)}{2}}$$
  With $N=4$, max pairs is 6. If any pair has 0 accepted trades, it signifies a functional silo (e.g. Béta-Gamma divergence).
- **Betweenness Centrality ($C_B$):**
  $$C_B(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$$
  Identifies key broker teams bridging isolated resource profiles (e.g. Capital or Emerging acting as bridges between Resource and Tech).

---

## 2. Economic & Financial Efficiency Ratios

### Total Net Wealth Calculation:
$$\text{Total Net Wealth} = \text{Cash Balance} + \sum (\text{Asset Count} \times \text{Standard Asset Valuation})$$
Standard asset liquidation values:
- Paper sheet: \$30
- Scissors: \$150
- Ruler: \$100
- Template: \$200

### Bank Dependency Rate (BDR):
$$\text{BDR} = \frac{\text{Bank Revenue}}{\text{Bank Revenue} + \text{Trade Cash Inflow}} \times 100\%$$
- **High BDR (>90%):** Indicates strong reliance on the central authority for liquidity, standard in short rounds where P2P barter or token payments dominate over large P2P cash settlements.
- **Low BDR (<70%):** Indicates a mature internal peer market where teams generate revenue through service fees and rental models.

### Market Shock Elasticity:
$$\text{Shock Elasticity} = \frac{\text{Premium Event Sales Payout}}{\text{Total Bank Payout}} \times 100\%$$
Teams with high shock elasticity (e.g. Gamma at 100%) hoard or produce high-margin goods (Circles, Premium Packs) until multiplier events trigger, maximizing capital return.

---

## 3. Psychometric Delta & Behavioral Safety

- **Energy Shift ($\Delta \text{Energy}$):**
  $$\Delta \text{Energy} = \text{finalEnergyLevel} - \text{initialEnergyLevel}$$
  Positive shifts across $>80\%$ of participants indicate an energizing, gameful learning climate with low psychological friction.
- **Informal Champions (Consensus Nominations):**
  Players receiving $>75\%$ nomination consensus represent the operational backbone and trusted dealmakers within the organizational informal network.

---

## 4. Multi-Layer Interpersonal ONA & Cross-Functional Silo Analysis

### Dual-Layer Representation:
1. **Macro Layer (Enterprise & Central Authority):**
   - 4 simulated companies (Alfa, Béta, Gamma, Delta) arranged radially around the Central Bank.
   - Bank sales lines (emerald) reflect liquidity extraction and production output.
   - P2P inter-company lines (blue) reflect barter volume and resource dependency.
2. **Micro Layer (Interpersonal Individual ONA):**
   - Individual participants as discrete nodes (arranged in radial clusters by simulated company).
   - Dual-coloring mode:
     - **By Simulation Company:** Shows within-team cohesion vs. inter-team dealmaking.
     - **By Real Organizational Department (Pénzügy, Gyártás, Logisztika, K+F, QA, Sales, Termék):** Directly exposes cross-functional corporate silos and reveals whether real-life colleagues stick together or establish bridges across disparate departments.
   - Multi-relational edges:
     - **Solid Blue Arrows:** Concrete closed trades (`createdBy` $\rightarrow$ `acceptedBy`).
     - **Dashed Purple Lines:** Mutual and directed trust/enabler nominations (`brokerNominations`, `internalEnablerNominations`, `networkRecognitions`).
   - Facilitator Confidentiality Gate: Marked `"🔒 BIZALMAS - CSAK FACILITÁTORI NÉZET"` to prevent psychological safety breaches on public auditorium screens while empowering the facilitator with deep diagnostic intelligence.
