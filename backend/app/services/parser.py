import csv
import io
import re
from typing import List, Tuple
from app.models.indicator import IndicatorType

class IndicatorParser:
    @staticmethod
    def parse_csv(content: str) -> List[Tuple[IndicatorType, str]]:
        """
        Parses CSV data. Expected formats:
        1. type,value (e.g. "IPV4,1.1.1.1")
        2. value only (defaults to smart detection)
        """
        indicators = []
        f = io.StringIO(content.strip())
        reader = csv.reader(f)
        
        for row in reader:
            if not row or not row[0]:
                continue
            
            # Skip header if present
            if row[0].strip().lower() in ("type", "indicator_type", "category"):
                continue

            # Case 1: Type and Value present
            if len(row) >= 2:
                itype_str = row[0].strip().upper()
                ivalue = row[1].strip()
                
                # Try to map string to enum
                itype = None
                try:
                    itype = IndicatorType(itype_str)
                except ValueError:
                    # Check member names
                    for member in IndicatorType:
                        if member.name == itype_str:
                            itype = member
                            break
                
                if itype:
                    indicators.append((itype, ivalue))
                else:
                    # Fallback to smart detection on the original row or skip
                    indicators.append(IndicatorParser.smart_detect(row[0] if len(row) == 1 else row[1]))
            
            # Case 2: One column only
            elif len(row) == 1:
                indicators.append(IndicatorParser.smart_detect(row[0]))
                
        return indicators

    @staticmethod
    def parse_txt(content: str) -> List[Tuple[IndicatorType, str]]:
        """
        Parses raw text. Expected format: one indicator value per line.
        """
        lines = content.strip().splitlines()
        indicators = []
        for line in lines:
            val = line.strip()
            if val and not val.startswith("#"):
                indicators.append(IndicatorParser.smart_detect(val))
        return indicators


    @staticmethod
    def smart_detect(value: str) -> Tuple[IndicatorType, str]:
        """
        Heuristic to guess the indicator type from a raw string.
        """
        val = value.strip()
        
        # IPV4
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", val):
            return IndicatorType.IPV4, val
        
        # Hashes (Length based)
        length = len(val)
        if re.match(r"^[a-fA-F0-9]+$", val):
            if length == 32: return IndicatorType.MD5, val
            if length == 40: return IndicatorType.SHA1, val
            if length == 64: return IndicatorType.SHA256, val
            
        # URL (starts with common schemes)
        if re.match(r"^h[tx]{2}ps?://", val, re.IGNORECASE):
            return IndicatorType.URL, val
            
        # Default to DOMAIN if it contains a dot, or URL if it contains a slash
        if "/" in val:
            return IndicatorType.URL, val
        
        return IndicatorType.DOMAIN, val
