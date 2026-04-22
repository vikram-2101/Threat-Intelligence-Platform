# Threat Intelligence Platform — Presentation Roadmap

---

## How to Open & Navigate

> Open `http://localhost:5173` in your browser.
> The app lands directly on the **Indicators** page.
> Sidebar on the left has three links: **Indicators · Ingest · Sources**

---

---

# PAGE 1 — Indicators (The Main Dashboard)

## What This Page Is

This is the **command centre** for every threat your platform is tracking.
Every IP address, domain, URL, or file hash that has been ingested and analysed appears here as a row in the table — sorted from highest to lowest threat confidence by default.

Think of it like a **live threat leaderboard**: the most dangerous, most confirmed threats are at the top.

---

## The Filter Bar (Top Card)

Before looking at the table, show the filter bar — it demonstrates that the platform is built for analysts working with large datasets.

| Filter | What it does |
|---|---|
| **Value** search box | Type part of an IP or domain — e.g. `185.` — table filters live as you type |
| **Source** filter | Show only indicators from one specific feed, e.g. "AlienVault OTX" |
| **Type** dropdown | Filter by `IPV4`, `DOMAIN`, `URL`, `MD5`, `SHA1`, `SHA256` |
| **Status** dropdown | `ACTIVE` (live threats), `EXPIRED` (aged out), `REVOKED` (analyst-dismissed) |
| **Confidence slider** | Pull left end to 70 — now you only see high-confidence threats |
| **Reset Filters** | One click brings everything back |

**Talking point:** *"Instead of dumping thousands of raw IPs on an analyst, the platform lets them zoom in — e.g. show me only high-confidence active domains."*

---

## The Indicators Table

Each row is one threat indicator. Walk through each column:

| Column | What it means |
|---|---|
| **Value** | The actual threat — an IP like `185.220.101.45` or a domain like `malware-command-host.xyz` |
| **Type** | What kind of indicator it is — colour badge: `IPV4` (blue), `DOMAIN` (purple), `URL` (brand), `MD5/SHA` (grey) |
| **Score** | Confidence score from **0 to 100** — colour coded: red (high threat, 70+), orange (medium, 40-69), grey (low, below 40) |
| **Status** | `ACTIVE` = live threat being tracked · `EXPIRED` = aged out automatically · `REVOKED` = analyst manually dismissed it |
| **Sources** | Which intelligence feeds reported this indicator. Multiple source tags mean more credibility. |
| **Last Seen** | When this indicator was last observed or updated |
| **TTL** | Time To Live — the expiry date after which the platform auto-expires this indicator if confidence is too low |

**Talking point:** *"Notice expired and revoked indicators appear greyed out — they're not deleted, they stay in the system for historical audit. If the same IP reappears from a new source, it will re-trigger the full enrichment pipeline automatically."*

---

## How Confidence Scores Are Calculated (Key Explanation)

> This is the most important technical point to explain. The score is **not a random number** — it is a deterministic formula.

The score is built from **5 components**:

### 1. Evidence Weight (Base Score)
Every piece of collected evidence contributes points. But the points are **multiplied by the Trust Tier** of the source that reported it:
- `HIGH` trust source → multiplier **1.0** (full credit)
- `MEDIUM` trust source → multiplier **0.6** (partial credit)
- `LOW` trust source → multiplier **0.3** (low credit)

So the same WHOIS evidence from a HIGH-trust commercial feed contributes **3× more** than from a LOW-trust community feed.

### 2. Enrichment Depth Bonus (+2 per distinct evidence type)
If the platform collected WHOIS **and** ASN **and** Passive DNS — that's 3 different evidence types. Bonus = 3 × 2 = **+6 points**. More evidence types = deeper understanding = higher confidence.

### 3. Correlation Bonus
- Shared infrastructure with another known threat: **+5**
- Shared SSL certificate fingerprint: **+8**
- Seen across multiple independent sources: **+3 × number of sources**

### 4. Analyst Manual Adjustment
Analysts can add or subtract points with a reason (shown in the Analyst Controls panel).

### 5. Time Decay (Exponential Decay)
Old threat intelligence goes stale. The platform applies: `score × e^(−0.05 × days_since_last_seen)`. After 14 days, a score of 100 decays to ~50. After 30 days, to ~22. **Threats that aren't reaffirmed automatically become less credible.**

**Final formula:**
```
Final Score = CLAMP(
  (Evidence × Trust Weight + Enrichment Bonus + Correlation Bonus + Analyst Adjustment)
  × e^(−0.05 × days_elapsed),
  0, 100
)
```

---

---

# PAGE 1B — Indicator Detail Page

> Click on any row in the Indicators table. This opens the full analysis view.

This page has **5 panels**. Walk through each one.

---

## Panel 1 — Metadata & Score Breakdown (Top Left)

Shows everything about this specific indicator at a glance.

**Top section:**
- The indicator value (e.g. `185.220.101.45`) with its type badge
- Current Status badge (ACTIVE / EXPIRED / REVOKED)
- TTL expiry date — *"after this date, if the score drops below 10, the platform auto-expires it"*
- First Seen / Last Seen timestamps — *"first seen tells us when this threat was first reported to our system"*
- Source list — which intelligence feeds reported it

**Score Breakdown section (the "why" panel):**

This is the explainability feature — the most important part of the platform.

It shows every single factor that contributed to the current score:

| Field shown | Meaning |
|---|---|
| **Current Score** | The final clamped 0-100 score |
| **Base Score** | Raw sum of all evidence × trust weights before bonuses |
| **Enrichment Depth Bonus** | Points added for having multiple evidence types |
| **Correlation Bonus** | Points from shared infrastructure or SSL matches |
| **Analyst Adjustment** | Manual points added or removed by analysts |
| **Decay Factor** | e.g. `0.9512` — how much of the score remains after time decay (1.0 = no decay, 0.0 = fully decayed) |
| **Days Elapsed** | Days since last_seen — drives the decay |
| **Individual Factors list** | Each evidence piece: what type, what source, what weight, what contribution |

**Talking point:** *"An analyst can look at this panel and explain exactly why this indicator is scored 67 — not because an algorithm said so, but because WHOIS evidence from a HIGH-trust source contributed 10 points, ASN contributed 5, there was a correlation with another known threat adding 8 more, and it's 1 day old so decay is minimal. Every decision is traceable."*

---

## Panel 2 — Confidence Timeline (Top Right)

A **line chart** showing how the indicator's confidence score changed over time.

- Each point on the line is a **confidence snapshot** — recorded every time the score changed
- Hover over any point to see the exact score and what triggered it
- **Triggers shown:** `evidence.created` (new enrichment), `correlation.created` (new correlation found), `decay.job` (scheduled decay run)

**Talking point:** *"This timeline tells a story. You can see the score jump when enrichment completed, jump again when a correlation was found, and slowly decay if the threat goes quiet. If an analyst manually adjusts the score, that spike appears on the timeline too."*

---

## Panel 3 — Evidence & Enrichments (Bottom Left, large panel)

This is the **raw intelligence** collected about this indicator. Each row is one piece of evidence.

Evidence types and what they mean:

| Evidence Type | What the platform collected |
|---|---|
| `WHOIS` | Domain registrar, creation date, registrant — a 1-day-old domain registered in Russia is suspicious |
| `PASSIVE_DNS` | Historical DNS resolution — who else did this domain point to? What IPs did it use over time? |
| `ASN` | Autonomous System Number — which hosting provider / country owns this IP block |
| `SSL_CERT` | SSL certificate fingerprint, issuer, subject, expiry — who signed this certificate? |
| `CORRELATION_INFRA` | This indicator shares the same ASN/IP block as another known threat |
| `CORRELATION_SSL` | This indicator shares an SSL certificate fingerprint with another known threat |
| `MULTI_SOURCE_SIGHTING` | Seen across N independent intelligence sources |
| `ANALYST_NOTE` | A human analyst's observation (score unchanged) |
| `ANALYST_ADJUSTMENT` | A human analyst manually changed the score with a reason |
| `REVOCATION` | Analyst formally revoked this indicator (−50 to score) |

Each evidence row shows:
- **Type badge** — colour coded by category
- **Timestamp** — when this evidence was collected
- **Confidence Delta** — how many points this evidence contributed (e.g. `+10`, `+5`, `−50` for revocation)
- **Expand button** — click to see the full raw payload (the actual JSON from WHOIS, ASN lookup, etc.)

**Talking point:** *"Evidence is append-only — we never delete or modify it. This is a tamper-evident audit trail. Even if an analyst reverses a decision, the original evidence is still there, just marked as reversed."*

---

## Panel 4 — Analyst Controls (Bottom Right, top section)

This is where human intelligence meets automated scoring. Three actions:

### Add Observation Note
- A text area to write a hypothesis or context observation
- Example: *"Seen in IR report 2026-04-15. Associated with Emotet campaign."*
- Click **Append Note** → creates an `ANALYST_NOTE` evidence row
- **Score does NOT change** — notes are context, not scoring inputs
- **Use case during demo:** Type a short note and hit submit. Show that it appears instantly in the Evidence panel above.

### Confidence Override (Promote / Demote)
- Toggle between **Promote** (green) and **Demote** (orange)
- Drag the **Delta slider** to choose how many points to add or subtract (0–50, in steps of 5)
- Type a **mandatory reason** in the text field (e.g. *"IR team confirmed this IP in active C2 traffic"*)
- Click **Commit Adjustment**

**What happens:**
1. Backend inserts an `ANALYST_ADJUSTMENT` evidence row with the delta
2. Scoring engine re-runs immediately with the new adjustment applied
3. The score on the page updates
4. The timeline chart gets a new data point showing the score jump
5. A toast notification confirms success

**Talking point:** *"The slider goes from 0 to 50 in steps of 5. A +50 from an analyst saying 'IR confirmed malicious' is a very strong signal. The reason field is mandatory — this goes into the audit log for compliance."*

### Set Expiry (TTL Override)
- A date-time picker pre-filled with the current TTL
- Change it to any future date → click **Save**
- **Use case:** An analyst knows from IR context that this threat will be active for another 30 days — they extend the TTL to prevent auto-expiry

### Revoke Indicator
- The red **Revoke Indicator...** button at the bottom
- Opens a confirmation modal
- Requires a **mandatory justification** (e.g. *"False positive — this is a legitimate CDN IP"*)
- Confirmation → inserts a `REVOCATION` evidence with **−50 confidence delta**
- Status changes to `REVOKED`
- The entire Actions panel gets overlaid with a lock screen — *"no further analyst interactions on a revoked indicator"*
- In the indicators list, this row turns grey

**Talking point:** *"Revocation is not deletion. The indicator stays in the database, stays queryable, stays in the audit trail. But it's formally de-listed. If this IP reappears in a new feed, the platform will create a fresh ingestion event."*

---

## Panel 5 — Indicator Correlations (Bottom Right, below controls)

Shows threat relationships — other indicators that share infrastructure with this one.

Three correlation types:

| Correlation Type | What it means | Confidence Delta |
|---|---|---|
| `CORRELATION_INFRA` | Shares the same ASN/IP block as another known threat | +5 |
| `CORRELATION_SSL` | Shares SSL certificate fingerprint | +8 |
| `MULTI_SOURCE_SIGHTING` | Reported by multiple independent feeds | +3 × N sources |

Each correlation entry is **clickable** — clicking it navigates to that related indicator's detail page.

**Talking point:** *"This is where the platform becomes genuinely useful. A single IP might only have a score of 30. But if it shares infrastructure with 3 other known malicious domains, that pattern is meaningful. The correlation engine detected this automatically, no analyst had to manually link them."*

---

---

# PAGE 2 — Ingest

## What This Page Is

This is the **data entry point** — where raw threat data comes into the platform. The platform accepts indicators from two input methods.

---

## Step 1 — Select an Intelligence Source (mandatory)

Before submitting any indicators, you must pick a **Source** from the dropdown.

**What is an Intelligence Source?**
A Source is a named, registered threat intelligence feed. Every indicator ingested must be attributed to a source because:
- The source's **Trust Tier** determines how much weight its indicators carry in confidence scoring
- The audit trail shows who reported what
- Duplicate indicators from multiple sources are merged (not duplicated)

If no sources are listed, you need to create one first in the **Sources page**.

For the demo: select **AlienVault OTX** (or whatever source you created).

---

## Tab 1 — Manual Entry

**The text box:**
- Type or paste indicators, **one per line**
- The platform **auto-detects the type** — you don't need to specify it manually
- Or you can prefix with `TYPE:` for explicit control

**Auto-detection rules:**
```
185.220.101.45          → auto → IPV4
2001:db8::1             → auto → IPV6
malware-domain.xyz      → auto → DOMAIN
https://phish.site/x    → auto → URL
d41d8cd98f00b204...     → auto → MD5  (32 hex chars)
aabbccdd1122...         → auto → SHA1 (40 hex chars)
e3b0c44298fc1c14...     → auto → SHA256 (64 hex chars)
IPV4:192.168.1.1        → explicit → IPV4
```

Lines starting with `#` are ignored (comments).

**Live Preview panel:**
As you type, a preview appears below the text box showing each indicator with its detected type. You can verify before submitting.

**Submit:**
Click **Ingest N Indicators** → the platform processes them

**Result Summary:**
| Field | Meaning |
|---|---|
| **Ingested** | New indicators added to the database |
| **Duplicates** | Already existed — `last_seen` timestamp updated, source reference merged |
| **Errors** | Failed validation (e.g. invalid IP format) — error details shown below |

**After ingestion:**
- The platform dispatches a `indicator.created` event internally
- Enrichment workers (Celery) begin processing in the background: WHOIS lookups, ASN queries, Passive DNS, SSL cert checks
- Confidence scoring runs after enrichment
- Click **"View Indicators"** link in the result card to go see the ingested data

---

## Tab 2 — File Upload

**Drag and drop** a `.csv` or `.txt` file into the drop zone, or click to browse.

**TXT format** (use `sample_indicators.txt`):
```
# One per line, type auto-detected
185.220.101.45
malware-command-host.xyz
https://phish.site/login
```

**CSV format** (use `sample_indicators.csv`):
```csv
type,value
IPV4,185.220.101.45
DOMAIN,malware-command-host.xyz
URL,https://phish.site/login
```

Click **Upload File** → same result summary appears.

**Demo talking point:** *"In production, this file upload endpoint can be scheduled. The platform pulls from a feed URL on a cron schedule automatically — every 6 hours from AlienVault OTX, for example."*

---

---

# PAGE 3 — Sources

## What This Page Is

Sources are the **registered intelligence feeds** that this platform trusts to report threat indicators. Think of them as verified data suppliers with different levels of trustworthiness.

Every indicator ingested must come from a registered source. The source's Trust Tier directly affects how much every piece of its evidence contributes to confidence scoring.

---

## The Sources Table

| Column | Meaning |
|---|---|
| **Name** | The feed's display name (with intent description below) |
| **Category** | What kind of feed it is |
| **Trust Tier** | LOW / MEDIUM / HIGH — the most important field for scoring |
| **Weight** | Numeric multiplier automatically set from Trust Tier (0.3 / 0.6 / 1.0) |
| **Status** | Active (can receive indicators) or Inactive (blocked from ingestion) |
| **Created** | When this source was registered |
| **Actions** | ✏️ Edit · 🗑️ Delete |

### Source Categories Explained

| Category | Meaning | Example |
|---|---|---|
| `community` | Free, open, crowd-sourced feeds | AlienVault OTX, Abuse.ch |
| `research` | Academic or independent security researchers | University CTI feeds |
| `commercial` | Paid threat intelligence subscriptions | Recorded Future, Mandiant |
| `internal` | Your own internal telemetry | SIEM logs, firewall alerts |

---

## Adding a New Source — Field by Field

Click **Add Source** → a modal opens.

### Demo Input Example:

| Field | Example Value | Why |
|---|---|---|
| **Source Name** | `AlienVault OTX` | Any recognisable name |
| **Category** | `community` | It's a free open-source feed |
| **Trust Tier** | `HIGH` | You've vetted it and trust it |
| **Default Weight** | `1.0` *(auto-filled)* | Auto-calculated from Trust Tier |
| **Intent Description** | `Open Threat Exchange - community IP and domain blacklist` | Documents what this feed provides |
| **Pull URL** | `https://otx.alienvault.com/api/v1/indicators/...` | Optional - for scheduled auto-pull |
| **Active toggle** | ON | Must be ON to receive indicators |

### Trust Tier → Weight auto-fill rule (hardcoded per spec):
- Select `LOW` → Weight auto-fills to `0.3`
- Select `MEDIUM` → Weight auto-fills to `0.6`
- Select `HIGH` → Weight auto-fills to `1.0`

**You cannot manually type the weight** — it's derived from the tier to prevent mismatches.

### What happens when you click "Register Source":
1. Source is saved to the database
2. It immediately appears in the Sources table
3. It is now selectable in the **Ingest** page source dropdown
4. All indicators ingested from this source will use its trust weight in confidence calculations

---

## Editing a Source

Click the **pencil icon** on any row → same modal opens pre-filled with current values.

Use case: Downgrade a source from `HIGH` → `MEDIUM` if it starts producing false positives. Every existing indicator from that source will reflect the new weight the next time scoring runs.

## Deleting a Source

Click the **trash icon** → confirmation dialog appears.

**Important:** Deleting a source does NOT delete the indicators that came from it. The historical ingestion records remain. The source reference is removed.

---

---

# Presentation Flow (Recommended Order)

## Open with Sources (30 seconds)
*"Before ingesting any data, we need to tell the platform where that data comes from and how much to trust it."*
- Show the Sources page → existing sources table
- Add a new source: `AlienVault OTX`, category `community`, trust tier `HIGH`

## Ingest Data (1 minute)
*"Now we bring in the actual threat indicators."*
- Go to Ingest → select AlienVault OTX → File Upload tab
- Upload `sample_indicators.csv`
- Show the result card: **23 ingested, 0 duplicates, 0 errors**
- Click "View Indicators"

## Indicators Dashboard (2 minutes)
*"The platform has immediately scored and organized all 23 indicators."*
- Show the table — highest confidence at top
- Use filters: type = `IPV4` → show only IPs
- Use confidence slider: 70–100 → high confidence threats only
- Reset filters

## Indicator Detail — The Core Demo (3–4 minutes)
*"Let me click on the highest-scored indicator and show you exactly WHY the platform thinks this is dangerous."*
- Click the top row
- Walk through Score Breakdown: *"67.4 — base score 45, enrichment depth added 6, correlation added 13, decay factor 0.95 — it was seen 1 day ago"*
- Show Timeline: *"you can see the score jumped when enrichment finished, then again when a correlation was detected"*
- Show Evidence: expand one WHOIS row, one ASN row — *"this is the raw data from the enrichment"*
- Show Correlations: *"this IP shares infrastructure with 3 other indicators — that's the correlation engine working"*

## Analyst Actions (1 minute)
*"Now let me show the human-in-the-loop control."*
- Add a note: `"Confirmed in R&D network logs — active scanning observed"`
- Promote confidence: +20, reason `"IR team confirmed active malicious activity"`
- Show the score update in real time on the timeline
- Click Revoke on a low-score indicator: reason `"False positive — shared CDN infrastructure"` → show it turn grey

## Close with the Big Idea (30 seconds)
*"Every decision in this platform is explainable, every analyst action is audited, and no indicator is ever blocked or actioned automatically without a human approving it. The score tells you what, the rationale tells you why, and the audit trail tells you who decided and when."*
