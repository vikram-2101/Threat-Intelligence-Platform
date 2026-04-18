import re
import ipaddress
from urllib.parse import urlparse, urlunparse
from typing import List, Tuple, Optional
from pydantic import BaseModel
from app.models.indicator import IndicatorType

class ValidationItem(BaseModel):
    raw: str
    type: IndicatorType
    normalized: Optional[str] = None
    is_valid: bool = False
    error: Optional[str] = None

class ValidationBatchResult(BaseModel):
    valid: List[ValidationItem]
    invalid: List[ValidationItem]

class IndicatorValidator:
    @staticmethod
    def normalize_url(raw: str) -> str:
        # 1. Strip leading/trailing whitespace
        url = raw.strip()

        # 2. Refang — restore defanged schemas and brackets
        # Handle hxxp/hxxps
        url = re.sub(r'hxxps?', lambda m: m.group().replace('xx', 'tt'), url, flags=re.IGNORECASE)
        # Handle brackets and defanged dots
        url = url.replace('[:]', ':').replace('[://]', '://').replace('[. ]', '.').replace('[.]', '.')

        # 3. Ensure parseable — add schema if missing so urlparse works correctly
        if not re.match(r'^https?://', url, re.IGNORECASE):
            url = 'http://' + url

        # 4. Parse
        parsed = urlparse(url)

        # 5. Normalize host to lowercase (host is case-insensitive per RFC)
        # parsed.netloc includes port if present (e.g., evil.com:8080)
        host = parsed.netloc.lower()

        # 6. Keep path exactly as-is (case-sensitive)
        # but strip trailing slash only if path is bare root
        path = parsed.path if parsed.path != '/' else ''

        # 7. Reconstruct into canonical form
        # Drop fragment (#anchor), Keep query string (?param=val)
        # Always store as http for canonicalization
        normalized = urlunparse((
            'http',
            host,
            path,
            parsed.params,
            parsed.query,
            '',  # drop fragment
        ))

        return normalized

    @staticmethod
    def validate_ipv4(value: str) -> Tuple[bool, Optional[str]]:
        try:
            ip = ipaddress.IPv4Address(value.strip())
            return True, str(ip)
        except ValueError:
            return False, "Invalid IPv4 address format"

    @staticmethod
    def validate_ipv6(value: str) -> Tuple[bool, Optional[str]]:
        try:
            ip = ipaddress.IPv6Address(value.strip())
            return True, ip.compressed # Standardize to compressed form
        except ValueError:
            return False, "Invalid IPv6 address format"

    @staticmethod
    def validate_domain(value: str) -> Tuple[bool, Optional[str]]:
        # Defang dots if present e.g. evil[.]com
        val = value.strip().replace('[.]', '.').lower()
        # Basic RFC 1035 regex for domains
        pattern = r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$"
        if re.match(pattern, val):
            return True, val
        return False, "Invalid domain format"

    @staticmethod
    def validate_hash(value: str, htype: IndicatorType) -> Tuple[bool, Optional[str]]:
        val = value.strip().lower()
        hash_rules = {
            IndicatorType.MD5: (32, r"^[a-f0-9]{32}$"),
            IndicatorType.SHA1: (40, r"^[a-f0-9]{40}$"),
            IndicatorType.SHA256: (64, r"^[a-f0-9]{64}$"),
        }
        
        if htype not in hash_rules:
            return False, f"Unsupported hash type: {htype}"
            
        length, pattern = hash_rules[htype]
        if re.match(pattern, val):
            return True, val
        return False, f"Invalid {htype} format (expected {length} hex chars)"

    @classmethod
    def validate_indicator(cls, itype: IndicatorType, value: str) -> ValidationItem:
        item = ValidationItem(raw=value, type=itype)
        is_valid = False
        normalized = None
        error = None

        try:
            if itype == IndicatorType.IPV4:
                is_valid, normalized = cls.validate_ipv4(value)
            elif itype == IndicatorType.IPV6:
                is_valid, normalized = cls.validate_ipv6(value)
            elif itype == IndicatorType.DOMAIN:
                is_valid, normalized = cls.validate_domain(value)
            elif itype == IndicatorType.URL:
                normalized = cls.normalize_url(value)
                is_valid = True # normalize_url is robust, but we could add more checks
            elif itype in [IndicatorType.MD5, IndicatorType.SHA1, IndicatorType.SHA256]:
                is_valid, normalized = cls.validate_hash(value, itype)
            else:
                error = f"Unsupported indicator type for validation: {itype}"
                
            if not is_valid and not error:
                error = f"Failed validation for {itype}"
        except Exception as e:
            is_valid = False
            error = str(e)

        item.is_valid = is_valid
        item.normalized = normalized
        item.error = error
        return item

    @classmethod
    def validate_batch(cls, indicators: List[Tuple[IndicatorType, str]]) -> ValidationBatchResult:
        valid = []
        invalid = []
        for itype, val in indicators:
            res = cls.validate_indicator(itype, val)
            if res.is_valid:
                valid.append(res)
            else:
                invalid.append(res)
        return ValidationBatchResult(valid=valid, invalid=invalid)
