from typing import List, Dict, Type
from app.models.indicator import IndicatorType
from app.services.enrichment.base import BaseEnricher

class EnrichmentEngineFactory:
    """
    Factory to manage and retrieve enrichers based on indicator types.
    """
    _enrichers: List[BaseEnricher] = []

    @classmethod
    def register_enricher(cls, enricher: BaseEnricher) -> None:
        """
        Register a new enricher instance.
        """
        cls._enrichers.append(enricher)

    @classmethod
    def get_enrichers_for_type(cls, indicator_type: IndicatorType) -> List[BaseEnricher]:
        """
        Returns all registered enrichers that support the given indicator type.
        """
        return [
            enricher for enricher in cls._enrichers
            if indicator_type in enricher.get_supported_types()
        ]

    @classmethod
    def get_enricher_by_name(cls, name: str) -> BaseEnricher:
        """
        Returns a registered enricher instance by its source name.
        """
        for enricher in cls._enrichers:
            if enricher.get_source_name() == name:
                return enricher
        return None

    @classmethod
    def clear_registry(cls) -> None:
        """
        Clear the registry (mainly for testing).
        """
        cls._enrichers = []

    @classmethod
    def setup_default_enrichers(cls) -> None:
        """
        Registers the default set of enricher instances.
        """
        from app.services.enrichment.whois import WHOISEnricher
        from app.services.enrichment.passive_dns import PassiveDNSEnricher
        from app.services.enrichment.asn import ASNEnricher
        from app.services.enrichment.ssl_cert import SSLEnricher
        from app.services.enrichment.behavioral import BehavioralAnalyser
        
        cls.clear_registry()
        cls.register_enricher(WHOISEnricher())
        cls.register_enricher(PassiveDNSEnricher())
        cls.register_enricher(ASNEnricher())
        cls.register_enricher(SSLEnricher())
        cls.register_enricher(BehavioralAnalyser())
