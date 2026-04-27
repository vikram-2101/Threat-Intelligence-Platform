# Indicator Scoring & Decay Logic

The TIP framework uses an advanced deterministic mathematical engine to dynamically calculate an indicator's inherent Threat Level `(Confidence)`.

## 1. Evidence Weight Mapping
Whenever external or internal pipelines push logs organically bounding an indicator, it drops an immutable `Evidence` payload natively inserting a deterministic `confidence_delta`.

### Standard Weightings:
- **Analyst Adjustment**: `-100.0` to `+100.0` (Absolute Override)
- **WHOIS Registration Anomaly**: `+10.0`
- **Passive DNS Flag**: `+25.0`
- **SSL Malicious Correlation**: `+30.0`
- **Revocation**: `-100.0` (Sets TTL boundary to instant-expire logically dumping bounds to 0)

The bounding strictly caps logic seamlessly verifying limits don't slip out mathematically below `0.0` natively avoiding negative thresholds, or pushing over `100.0`.

## 2. Logarithmic Time-Decay (λ)
An indicator’s confidence dynamically decays logically rendering explicit cooling mathematical algorithms.

**Equation**: `C(t) = C_initial * e^(-λ * t)`

### Specifications:
- `t`: Time bounds natively tracking days sequentially derived over the `last_seen` PostgreSQL structures.
- `λ (Lambda)`: The decay constant natively matching `.05` logically bound across `backend/app/core/config.py`.
- **Mechanism**: Every 24 hours, `tip-beat` explicitly fires the logic recalculating confidence bounds mapping against `e`. If logic hits below `AUTO_EXPIRE_THRESHOLD` (`10.0`), the system triggers an explicit `TTL` purge gracefully dropping status inherently to `EXPIRED`.
