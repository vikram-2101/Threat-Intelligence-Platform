import pytest
from pydantic import ValidationError
from app.schemas.indicator import IndicatorBase, IndicatorType

def test_valid_md5():
    indicator = IndicatorBase(type=IndicatorType.MD5, value="d41d8cd98f00b204e9800998ecf8427e")
    assert indicator.value == "d41d8cd98f00b204e9800998ecf8427e"

def test_invalid_md5_length():
    with pytest.raises(ValidationError):
        IndicatorBase(type=IndicatorType.MD5, value="d41d8cd98f00b204e9800998ecf8427")

def test_invalid_md5_chars():
    with pytest.raises(ValidationError):
        IndicatorBase(type=IndicatorType.MD5, value="g41d8cd98f00b204e9800998ecf8427e")

def test_sha256_normalization():
    upper_sha = "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"
    indicator = IndicatorBase(type=IndicatorType.SHA256, value=upper_sha)
    assert indicator.value == upper_sha.lower()

def test_domain_normalization():
    indicator = IndicatorBase(type=IndicatorType.DOMAIN, value="EXAMPLE.COM")
    assert indicator.value == "example.com"

def test_ipv4_no_normalization():
    indicator = IndicatorBase(type=IndicatorType.IPV4, value="1.2.3.4")
    assert indicator.value == "1.2.3.4"
