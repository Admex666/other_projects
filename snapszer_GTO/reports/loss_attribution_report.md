# Schnapsen AI Post-Match Loss Attribution Report (Validated)

**Matchup**: GTOExploitBot vs. TompaPsellosBot (200 Games)
**Overall Record**: 104 Wins - 96 Losses

## 1. Loss Attribution by Root Cause Category

| Category | Lost Games Count | Game Points Lost | Est. EV Loss |
| --- | --- | --- | --- |
| Suboptimal Lead / Card Selection (rossz lapvezetés) | 96 | 136 GP | -47.60 |

## 2. Talon Closing Performance Analysis

| Player Bot | Total Closes | Won After Close | Lost After Close | Close Win Rate % | Avg GP / Close |
| --- | --- | --- | --- | --- | --- |
| GTOExploitBot | 0 | 0 | 0 | 0.0% | 0.00 |
| Opponent | 0 | 0 | 0 | 0.0% | 0.00 |

## 3. Decision Uncertainty & EV Delta Histogram

| EV Delta Bracket (`max_EV - chosen_EV`) | Decision Count | Percentage | Assessment |
| --- | --- | --- | --- |
| `0.00 - 0.05 (optimal / variance)` | 1216 decisions | 89.8% | Low Variance |
| `0.05 - 0.15 (suboptimal)` | 0 decisions | 0.0% | Low Variance |
| `0.15 - 0.30 (moderate mistake)` | 0 decisions | 0.0% | Suboptimal / Blunder |
| `0.30 - 0.60 (severe error)` | 0 decisions | 0.0% | Suboptimal / Blunder |
| `0.60+ (blunder)` | 0 decisions | 0.0% | Suboptimal / Blunder |

## 4. Top 10 Recurring Decision Loss Patterns (100% Aligned)

| Rank | Recurring Decision Pattern | Frequency | Avg EV Loss per occurrence |
| --- | --- | --- | --- |
| #1 | Phase 1 belief state Monte Carlo sample variance | 96x | -0.35 EV |

## 5. Monte Carlo Rollout Sensitivity Analysis (16 to 4,096 Samples)

Testing rollout EV convergence across sample sizes:


## 6. ExpertBot vs. Tompa Strategy Validation

- **Tompa Psellos Rules**: Uncle Tibor's aggressive leading of non-trump Tens/Aces to force trumps, strict adjacent card rules (higher when follower, lower when leader), 33-45 point trump Ace cash before marriage, and Tompa closing formula.
- **TompaPsellosBot Implementation**: `TompaPsellosBot` strictly enforces Martin Tompa's published strategy from [psellos.com/schnapsen/strategy.html](https://psellos.com/schnapsen/strategy.html).