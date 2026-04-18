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
            if not row:
                continue
            
            # Case 1: Type and Value present
            if len(row) >= 2:
                try:
                    # Normalize type string to enum
                    itype_str = row[0].strip().upper()
                    itype = IndicatorType(itype_str)
                    ivalue = row[1].strip()
                    indicators.append((itype, ivalue))
                except ValueError:
                    # If first col isn't a valid type, treat whole row as data or skip
                    indicators.append(IndicatorParser.smart_detect(row[0]))
            
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
            if val := line.strip():
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
