
# UPDATED PRODUCT REQUIREMENTS DOCUMENT (PRD)

## 1. Product Name (working)

**Domain Email Intelligence Engine**

---

## 2. Product Goal

Build an autonomous system that continuously:

* discovers domains (websites)
* extracts publicly available emails
* validates email deliverability
* infers email patterns ONLY from verified emails
* expands email coverage using pattern intelligence
* enriches company metadata
* stores structured, queryable results

System runs fully in the background with no user-driven ingestion.

---

## 3. Core Principle

> “Truth-first system: real emails come first, patterns come after proof.”

Pipeline rule:

```text id="p1"
Discovery → Extraction → Validation → Pattern Inference → Expansion → Enrichment → Storage → Serving
```

---

# 4. HIGH-LEVEL ARCHITECTURE

## Modules

1. Domain Discovery Engine
2. Domain Queue System
3. Crawler Engine
4. Email Extraction Engine
5. Validation Engine
6. Pattern Inference & Expansion Engine (NEW)
7. Enrichment Engine
8. Data Store
9. API Layer

---

# 5. SYSTEM FLOW (UPDATED)

---

## 5.1 Domain Discovery Layer

Same as before:

* Common Crawl
* Open company databases
* Directory pages
* Link expansion crawling

Output:

```json id="d1"
{
  "domain": "example.com",
  "source": "commoncrawl",
  "priority": 0.7,
  "status": "queued"
}
```

---

## 5.2 Domain Queue System

Same rules:

* no duplicates
* priority-based processing
* rate-controlled execution

---

## 5.3 Crawler Engine

Same behavior:

* homepage
* /contact
* /about
* limited depth crawling

Stop early if emails found.

---

## 5.4 Email Extraction Engine

Extract raw emails from HTML.

Rules:

* must match domain OR be legitimate public business email
* remove disposable emails
* remove irrelevant personal emails unless verified business usage

Output:

```json id="e1"
{
  "email": "info@company.com",
  "domain": "company.com",
  "source_page": "/contact",
  "confidence": "high"
}
```

---

## 5.5 Validation Engine

### Layers:

1. Syntax validation
2. MX record validation
3. External verification API (optional)

Statuses:

```text id="v1"
valid
invalid
risky
unknown
```

---

# 5.6 PATTERN INFERENCE & EXPANSION ENGINE (NEW CORE MODULE)

## Purpose

Generate additional emails ONLY when a verified email pattern exists.

---

## Trigger condition (STRICT RULE)

```text id="p2"
Pattern inference is allowed ONLY IF:
≥ 1 VALID email exists for the domain
```

---

## Step 1: Pattern Detection

From verified email:

Example:

```text id="p3"
john.doe@company.com
```

Infer:

```text id="p4"
first.last@domain
```

Other possible patterns:

* first@domain
* firstlast@domain
* f.last@domain
* first.l@domain

---

## Step 2: Controlled Expansion

Generate limited candidates:

```text id="p5"
max 3–10 emails per domain
```

Example output:

```text id="p6"
jane.smith@company.com
mike.ali@company.com
sarah.john@company.com
```

---

## Step 3: Validation Gate

Every generated email MUST pass:

* MX check (domain-level)
* optional API verification
* pattern consistency check

---

## Step 4: Confidence Scoring

```text id="p7"
High → found on website OR verified API
Medium → pattern derived from real email
Low → fallback pattern guess (rare)
```

---

## Key Constraint

> Pattern emails NEVER outrank real scraped emails.

Real emails always dominate system output.

---

## 5.7 Enrichment Engine

Same as before:

* company info
* industry
* location
* public executives (if available)

---

## 5.8 Data Storage System

### Domains Table

```json id="t1"
{
  "domain": "example.com",
  "status": "processed",
  "priority": 0.8
}
```

### Emails Table

```json id="t2"
{
  "email": "info@company.com",
  "domain": "company.com",
  "status": "valid",
  "confidence": 0.95,
  "source": "scraper"
}
```

### Pattern Table (NEW)

```json id="t3"
{
  "domain": "company.com",
  "inferred_pattern": "first.last",
  "source_email": "john.doe@company.com"
}
```

---

# 6. ANTI-BLOCKING STRATEGY

Same system:

* rate limiting (1–3 req/sec max)
* randomized delays
* user-agent rotation
* optional proxy rotation
* crawl depth limits
* fail-fast behavior

---

# 7. DATA QUALITY SYSTEM (UPDATED)

## Confidence hierarchy:

### Tier 1 — Truth

* scraped + validated emails

### Tier 2 — Derived truth

* pattern-generated emails (from verified anchor)

### Tier 3 — Unsafe guesses

* fallback patterns (minimized usage)

---

# 8. BACKGROUND JOB SYSTEM

Updated loop:

```text id="b1"
while true:
  domain = get_next_domain()

  crawl(domain)
  emails = extract_emails(domain)

  validated = validate(emails)

  store(validated)

  if exists(validated):
      pattern = infer_pattern(validated)
      expanded_emails = generate(pattern)
      validate(expanded_emails)
      store(expanded_emails)
```

---

# 9. API LAYER

Same endpoints:

### GET /emails

* filter by confidence, status

### GET /domains

* processing status

### GET /stats

* valid vs invalid ratio
* pattern expansion rate

---

# 10. SYSTEM BEHAVIOR SUMMARY

## What it does:

* discovers domains continuously
* extracts real emails first
* validates aggressively
* learns patterns from real data
* expands coverage carefully
* improves accuracy over time

---

## What it does NOT do:

* no blind email generation
* no user-driven input
* no uncontrolled pattern explosion

---

# 11. SUCCESS METRICS (UPDATED)

* valid email ratio > 60–80%
* pattern-derived emails < 40% of dataset
* duplicate rate < 5%
* crawl efficiency (emails per domain)
* pattern accuracy rate (derived vs invalid)

---

# 12. KEY DESIGN INSIGHT (IMPORTANT)

This system is now:

> a **truth-first email intelligence engine with controlled learning expansion**

Not:

* scraper
* generator
* or lookup tool

---

# FINAL REALITY CHECK

This version is strong because:

* real emails anchor the system
* patterns only amplify truth
* validation protects quality
* expansion is controlled, not chaotic

