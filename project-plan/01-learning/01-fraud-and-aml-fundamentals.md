# 1. Fraud & AML Fundamentals

## Why this matters for the project

Every technical decision downstream — what fields go in your knowledge graph,
what features your risk model uses, what a SAR needs to contain — depends on
understanding what fraud and money laundering actually *look like* in data.
If you don't know what "structuring" or "layering" looks like in a
transaction table, you can't design a system to detect it, and you can't
explain your project convincingly in a review.

You already have working definitions in `banking_fraud_ai_platform.md`
(section 2) and on the Key Concepts slides you cut from the deck. This file
tells you how to go from "I can define it" to "I understand it operationally."

## Core concepts to learn

- **Types of fraud**: card fraud, account takeover, identity fraud, synthetic
  identity fraud, insider fraud — know what data signal each one leaves
  behind (e.g. account takeover often shows a device/location change right
  before unusual transactions).
- **Money laundering stages**: placement → layering → integration. Be able to
  describe a concrete example of each stage, not just name them.
- **Structuring / smurfing**: why criminals split transactions into amounts
  just under reporting thresholds, and what that looks like across multiple
  accounts over time.
- **KYC (Know Your Customer)**: what data a bank actually collects at
  onboarding, and why weak KYC is a root cause of synthetic identity fraud.
- **Regulatory reporting**: what a SAR (Suspicious Activity Report) and CTR
  (Currency Transaction Report) actually require as fields/content — you'll
  need this to design your compliance-assistant output in Stage 4.
- **Why rule-based systems fail**: understand concretely why a static
  threshold rule ("flag if > ₹50,000") generates so many false positives —
  this is the argument your entire project rests on, so you should be able
  to defend it with a real example, not just cite the "95% false positive"
  statistic.

## Recommended resources (free)

- **FATF (Financial Action Task Force) — "What is Money Laundering"**:
  https://www.fatf-gafi.org/en/pages/frequently-asked-questions.html —
  the actual international standard-setting body's own explainer. Short,
  authoritative, free.
- **ACAMS (Association of Certified Anti-Money Laundering Specialists) —
  free resources/blog**: https://www.acams.org/en/resources — industry
  perspective on real typologies (structuring, trade-based laundering, etc.)
- **Kaggle — IEEE-CIS Fraud Detection competition + discussion**:
  https://www.kaggle.com/c/ieee-fraud-detection — read the competition
  overview and top discussion threads even if you don't enter; they explain
  which real-world features matter and why.
- **RBI (Reserve Bank of India) Master Directions on KYC**:
  https://www.rbi.org.in — since your project references FIU-IND, skim the
  actual KYC master direction to see what compliance teams work with. You
  don't need to read all of it — just enough to recognize the structure of a
  real regulatory document (this also previews what your RAG pipeline in
  Stage 4 will be retrieving from).

## Checkpoint

Before moving to the next file, you should be able to answer, unaided:

> "Walk me through a realistic smurfing scenario: what does the criminal do,
> what does the transaction data look like across accounts, and why would a
> simple rule ('flag transactions over ₹50,000') miss it?"

If you can answer that with a concrete example (not textbook language), move
on to graphs.
