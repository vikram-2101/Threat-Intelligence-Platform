# Software Requirements Plan

## Threat Intelligence Platform (TIP) – MVP

---

## 1. Purpose of This Document

This document defines the **functional, non-functional, and acceptance requirements** for the **Minimum Viable Product (MVP)** of a Threat Intelligence Platform focused on **enrichment-driven intelligence creation**.

It is intended to be used as:

- a build specification
- a scope control mechanism
- a basis for milestone acceptance

---

## 2. MVP Objective

The MVP must demonstrably prove that the platform can:

1. Ingest raw indicators from untrusted external sources
2. Enrich those indicators with independent evidence
3. Correlate indicators across sources
4. Dynamically score and decay confidence
5. Provide human-explainable justification for risk decisions

Any functionality that does not materially support the above objectives is out of scope.

---

## 3. MVP Scope Definition

### 3.1 Included in MVP

- Raw indicator ingestion
- Normalization and storage
- Context and light behavioral enrichment
- Cross-source correlation
- Confidence scoring and decay
- Analyst review interface
- Controlled export and API access

### 3.2 Explicitly Excluded from MVP

- Threat actor attribution
- Campaign modeling
- Automated blocking or enforcement
- Full STIX internal data model
- TAXII client/server
- Machine learning or AI-based classification
- Internal customer telemetry ingestion
- Executive dashboards

---

## 4. System Architecture Overview

### 4.1 High-Level Components

- Ingestion Service
- Indicator Store
- Enrichment Engine
- Correlation Engine
- Confidence Engine
- Analyst Interface (Web UI)
- Export & API Layer
- Audit & Logging Service

### 4.2 Architectural Principles

- Asynchronous enrichment
- Event-driven processing
- Strong data immutability for evidence
- Horizontal scalability
- Full explainability and traceability

---

## 5. Functional Requirements

---

## 5.1 Indicator Ingestion

### 5.1.1 Supported Indicator Types

- IPv4 / IPv6 addresses
- Domains
- URLs
- File hashes (MD5, SHA1, SHA256)

### 5.1.2 Supported Input Methods

- Manual upload (CSV, TXT, JSON)
- Scheduled HTTP pull (CSV or JSON)
- REST API submission

### 5.1.3 Ingestion Rules

- Indicators must be syntactically validated
- Duplicate indicators must be merged, not re-created
- Each indicator must retain all source references
- No indicator may be auto-classified at ingestion

### 5.1.4 Source Metadata

Each source must include:

- Source name
- Source category (community, research, commercial, internal)
- Trust tier (Low, Medium, High)
- Default confidence weight
- Description of feed intent

---

## 5.2 Indicator Normalization and Storage

### 5.2.1 Canonical Indicator Schema

Each indicator record must include:

- Internal unique ID
- Indicator value
- Indicator type
- Source list
- First seen timestamp
- Last seen timestamp
- Current confidence score
- Confidence history
- TTL / expiration date
- Indicator status (active, expired, revoked)

### 5.2.2 Time and State Management

- Indicators must expire automatically unless reaffirmed
- Expired indicators must remain queryable for historical analysis
- Reappearance of expired indicators must re-trigger enrichment

---

## 5.3 Enrichment Engine

### 5.3.1 Context Enrichment (Mandatory)

For IPs, domains, and URLs:

- WHOIS data (registrar, creation date, update date)
- ASN and hosting provider
- Passive DNS resolution history
- Domain age calculation
- SSL certificate metadata (where applicable)

For file hashes:

- File type
- Known sightings count (if available)

### 5.3.2 Behavioral Light Enrichment

- URL path pattern analysis
- Detection of infrastructure reuse (same IP/domain previously observed)
- Identification of short-lived or throwaway domains

### 5.3.3 Enrichment Rules

- Each enrichment must be stored as independent evidence
- Each enrichment must include:
  - source
  - timestamp
  - confidence contribution

- Enrichment must not overwrite raw data

---

## 5.4 Correlation Engine

### 5.4.1 Cross-Indicator Correlation

The system must identify:

- Multiple indicators resolving to the same infrastructure
- Indicators sharing SSL certificates
- Indicators appearing across multiple independent sources

### 5.4.2 Correlation Impact

- Each correlation event must:
  - be recorded as evidence
  - increase confidence according to defined rules
  - be reversible if evidence is withdrawn

---

## 5.5 Confidence Scoring and Decay

### 5.5.1 Scoring Model

- Confidence must be numeric (0–100)
- Initial confidence must be low by default
- Confidence must increase based on:
  - source trust
  - enrichment depth
  - correlation count

- Confidence must decrease over time via decay

### 5.5.2 Explainability

For each indicator, the system must display:

- current confidence
- contributing factors
- score changes over time
- rationale for each adjustment

---

## 5.6 Analyst Interface (Web UI)

### 5.6.1 Required Views

- Indicator detail page
- Enrichment and evidence breakdown
- Confidence evolution timeline
- Correlation summary

### 5.6.2 Analyst Actions

- Add analyst notes
- Promote or demote confidence manually
- Mark indicators as reviewed
- Revoke indicators
- Adjust TTL within policy limits

---

## 5.7 Export and API Access

### 5.7.1 REST API

- Query indicators by type, confidence, status, source
- Retrieve enrichment and evidence
- Role-based access control

### 5.7.2 Export Formats

- CSV
- JSON

### 5.7.3 Distribution Controls

- Export based on confidence thresholds
- Explicit approval required for high-confidence exports

---

## 6. Non-Functional Requirements

---

## 6.1 Security

- Role-based access control
- Secure API authentication
- Full audit logging
- Tamper-evident evidence storage

---

## 6.2 Performance

- Ingestion latency under 5 minutes
- Enrichment processing asynchronous
- UI response time under 2 seconds for standard queries

---

## 6.3 Scalability

- Support millions of indicators
- Horizontal scaling of ingestion and enrichment
- Stateless API services

---

## 6.4 Reliability

- Graceful handling of enrichment source failures
- Retry and backoff mechanisms
- No data loss on partial failures

---

## 7. Auditability and Compliance

- Every confidence change must be logged
- Every enrichment must be traceable to a source
- Analyst actions must be fully auditable
- Historical state reconstruction must be possible

---

## 8. Acceptance Criteria (MVP Gate)

The MVP will be accepted only if:

1. Confidence scores change meaningfully over time
2. Indicators expire automatically without reaffirmation
3. Analysts can explain why an indicator is high or low risk
4. Raw feeds become more actionable after enrichment
5. No automated blocking occurs without human approval

Failure to meet any of the above constitutes MVP failure.

---

## 9. Delivery Expectations

The development agency must deliver:

- System architecture documentation
- Data models and schemas
- Scoring and decay logic documentation
- Deployed MVP environment
- Security review summary
- Operational runbook

---

## 10. Final Constraint

The MVP must **prioritize correctness, explainability, and analyst trust over feature breadth**.
Any implementation that trades these for speed or visual appeal is unacceptable.
