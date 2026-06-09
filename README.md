# Insurance Fraud Analysis: Identifying Predictors of Fraudulent Auto Claims

A claims-data analysis exploring which characteristics distinguish fraudulent auto insurance claims from legitimate ones, using a public dataset of 15,420 claims.

---

## About this project

This is a portfolio project built as part of my transition from insurance claims processor to data analytics. I spent several years as a claims processor in the insurance industry before stepping away to retrain in data analytics. This project leverages that domain knowledge to ask the kinds of questions a Special Investigations Unit (SIU) team actually faces: *given limited investigative capacity, which claims should we prioritize for fraud review?*

The analysis was completed entirely in Excel using COUNTIFS-based segmentation and lift calculations — the tools an analyst in a Microsoft-stack insurance environment would actually have on day one. I built the analysis tables by hand to genuinely understand the data, the methodology, and the limitations of what segmentation analysis can and can't conclude.

---

## The business question

Imagine an SIU Director walks into your office with a question:

> "We have limited investigator capacity. We can't review every claim flagged for potential fraud. Which claim characteristics should we prioritize so our team is spending time on the claims most likely to actually be fraudulent?"

This project answers that question by identifying which claim attributes have fraud rates meaningfully above (or below) the population base rate, and recommends a deprioritization strategy that could free up investigator capacity without meaningfully increasing fraud exposure.

---

## Data source

This analysis uses the publicly available **`fraud_oracle.csv`** dataset from Kaggle, a commonly-used dataset for auto insurance fraud detection research. The dataset contains 15,420 auto insurance claims, each labeled as fraudulent (`FraudFound_P = 1`) or non-fraudulent (`FraudFound_P = 0`).

Each claim includes 33 attributes covering:
- **Claim characteristics**: month, day of week, area (urban/rural), fault, deductible
- **Policy details**: policy type, base policy (Liability/Collision/All Perils), vehicle category, vehicle age
- **Policyholder profile**: age, marital status, past claims history, agent type
- **Verification signals**: police report filed, witness present, address change near claim date

**Base fraud rate across the full dataset: 923 fraudulent claims out of 15,420 total = 5.99%.** This base rate anchors the analysis — every attribute is evaluated against it to compute "lift" (how much more or less likely fraud is in each segment relative to the population average).

---

## Methodology

**Tools:** Microsoft Excel (Microsoft 365), using COUNTIF and COUNTIFS formulas for segmentation, with lift ratios calculated by dividing each segment's fraud rate by the overall base rate.

**Approach:**

1. **Establish the base rate.** Computed overall fraud rate (5.99%) as the benchmark against which all segments are compared.

2. **Exploratory cut — weekday vs. weekend claims.** A first-pass test of whether claim timing carries a fraud signal.

3. **Identify candidate predictive attributes.** Examined claim attributes that my domain knowledge as a claims processor suggested might carry fraud signal: vehicle age, claims history, and policy type.

4. **Segment-level fraud-rate calculation.** For each candidate attribute, counted total claims and fraudulent claims per category, then computed each category's fraud rate and its lift vs. the base rate.

5. **Reconciliation check.** Verified that segment totals sum back to the 15,420 / 923 population totals at every cut, catching any classification errors before drawing conclusions.

---

## Key findings

### 1. BasePolicy is the strongest signal in the dataset

Fraud rates vary dramatically by policy type:

| BasePolicy | Total Claims | Fraud Claims | Fraud Rate | Lift vs. Base |
|------------|--------------|--------------|------------|---------------|
| Liability  | 5,009        | 36           | **0.72%**  | **0.12x**     |
| Collision  | 5,962        | 435          | 7.30%      | 1.22x         |
| All Perils | 4,449        | 452          | **10.16%** | **1.70x**     |
| **Total**  | **15,420**   | **923**      | **5.99%**  | 1.00x         |

The spread is striking: All Perils claims are fraudulent at roughly **14 times the rate of Liability claims**. This is the single most actionable finding in the analysis.

### 2. PastNumberOfClaims shows an inverse relationship — and contradicts industry intuition

| PastNumberOfClaims | Claims | Fraud Rate | Lift |
|---------------------|--------|------------|------|
| none                | 4,352  | 7.79%      | 1.30x |
| 1                   | 3,573  | 6.21%      | 1.04x |
| 2 to 4              | 5,485  | 5.36%      | 0.90x |
| more than 4         | 2,010  | 3.38%      | 0.57x |

**Customers with NO past claims are more than 2x as likely to file a fraudulent claim as customers with more than 4 past claims.** This was the most surprising finding in the analysis. In claims work, claim frequency is conventionally treated as a fraud risk indicator — ISO and standard industry guidance often flag high claim frequency as a red flag warranting closer review. This dataset shows the opposite pattern: frequency is *inversely* correlated with fraud rate, with the lowest-frequency segment (none) showing the highest fraud rate and the highest-frequency segment (more than 4) showing the lowest.

Whether this generalizes beyond this dataset is an open question — but it illustrates the value of testing industry assumptions against actual data rather than relying on conventional framing.

### 3. AgeOfVehicle: signal exists, but smaller categories warrant caution

Newer vehicles show elevated fraud rates, declining for older vehicles:

| AgeOfVehicle | Claims | Fraud Rate | Lift |
|--------------|--------|------------|------|
| new          | 373    | 8.58%      | 1.43x |
| 2 years      | 73     | 4.11%      | 0.69x |
| 3 years      | 152    | 8.55%      | 1.43x |
| 4 years      | 229    | 9.17%      | 1.53x |
| 5 years      | 1,357  | 7.00%      | 1.17x |
| 6 years      | 3,448  | 6.61%      | 1.10x |
| 7 years      | 5,807  | 5.60%      | 0.94x |
| more than 7  | 3,981  | 5.17%      | 0.86x |

The general pattern (newer vehicles → higher fraud rate) is consistent, but the small-sample categories (2 years, 3 years, 4 years) have such small claim counts that their rates aren't statistically reliable. The "2 years" category in particular, with only 73 total claims, would need a much larger sample before any conclusion could be drawn.

### 4. Weekday vs. weekend: minimal signal

| Day | Claims | Fraud Rate |
|-----|--------|------------|
| Weekday | 11,693 | 5.72% |
| Weekend | 3,727  | 6.82% |

Weekend claims fraud rate is ~19% higher than weekday, but in absolute terms the gap is small (1.1 percentage points) and likely not actionable in isolation.

---

## Recommendation

Based on the BasePolicy findings, an SIU team operating with limited investigator capacity could consider **deprioritizing Liability-only claims from routine fraud review.**

The reasoning:
- Liability claims show a fraud rate of **0.72%** — roughly 1 in 140 claims.
- All Perils claims show a fraud rate of **10.16%** — roughly 1 in 10.
- A reviewer hour spent on All Perils is approximately **14 times more likely to surface actual fraud** than the same hour spent on Liability.

For an SIU team with finite capacity, reallocating investigator time away from Liability and toward All Perils (and to a lesser extent Collision) could meaningfully increase the fraud-detection yield per reviewer-hour, without materially reducing total fraud caught — because the Liability segment contributes such a small share of fraud in the first place (36 of 923 total fraud claims, ≈ 3.9%).

This is a recommendation about *prioritization*, not *elimination*. Some review of Liability claims should remain in place to catch the outliers and to preserve auditability. But for routine triage, this dataset suggests the bulk of investigative attention should sit on All Perils.

---

## Limitations

A few important caveats about what this analysis can and cannot conclude:

**Sample size on small segments.** Some of the AgeOfVehicle categories — particularly "2 years" with only 73 claims — have too few observations to draw reliable conclusions from. A fraud rate computed on 73 records is highly sensitive to a few individual cases. Any operational decision based on these small segments would need a larger sample first.

**Interaction effects not measured.** This analysis treats each attribute independently. In reality, attributes may interact — for example, fraud rate for "new vehicles" might differ significantly between Liability and All Perils policies. A more rigorous analysis would examine combinations of attributes rather than each attribute in isolation.

**Observational data, not causal.** This dataset shows correlations between attributes and fraud labels. It does not establish that any attribute *causes* fraud, or that changing the attribute would change fraud risk. The findings identify *patterns worth investigating* — not mechanisms.

**Dataset provenance.** The dataset is from Kaggle and lacks detailed documentation of its origin, time period, or geographic scope. Findings may or may not generalize to other insurance portfolios, time periods, or jurisdictions.

**Single-coder analysis.** All categorization and reconciliation was done by one person (me). A production analysis would benefit from a second reviewer to catch classification errors.

---

## What I'd do next

If I were extending this analysis, the next steps would be:

1. **Verify the findings against a larger or more recent dataset.** The PastNumberOfClaims result especially deserves a second look — does the inverse relationship hold in other claims data, or is it specific to this dataset?

2. **Investigate combinations of attributes.** Right now this analysis looks at each attribute on its own. Looking at combinations (e.g., does BasePolicy matter differently for new vehicles vs. older ones?) could surface stronger or more specific signals.
