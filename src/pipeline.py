import os
import json
import logging
import asyncio
import re
from typing import Any, Dict, List, Optional, AsyncGenerator

# Load .env from any parent directory (works regardless of CWD or how this module is imported)
def _load_env():
    try:
        from dotenv import load_dotenv
        search = os.path.dirname(os.path.abspath(__file__))
        for _ in range(7):
            candidate = os.path.join(search, '.env')
            if os.path.isfile(candidate):
                load_dotenv(candidate, override=False)
                return
            search = os.path.dirname(search)
    except Exception:
        pass

_load_env()

try:
    from .jina_reader import JinaReader
    from .extractor import CompanyDataExtractor
    from .page_selector import PageSelector
    from .url_discovery import URLDiscovery, normalize_domain_url
    from .wikipedia_fallback import get_wikipedia_company_data
    from .models import CompanyData, FieldEvidence
    from .uk import CompaniesHouseClient, UKCompanyResolver, CompaniesHouseMapper
    from .telemetry import TelemetryLogger
except ImportError:
    from jina_reader import JinaReader
    from extractor import CompanyDataExtractor
    from page_selector import PageSelector
    from url_discovery import URLDiscovery, normalize_domain_url
    from wikipedia_fallback import get_wikipedia_company_data
    from models import CompanyData, FieldEvidence
    from uk import CompaniesHouseClient, UKCompanyResolver, CompaniesHouseMapper
    from telemetry import TelemetryLogger

logger = logging.getLogger(__name__)



def is_uk_company(data: CompanyData, start_url: str) -> bool:
    """Determine if company/domain is UK based."""
    domain_lower = (data.domain or start_url or "").lower()
    if domain_lower.endswith(".uk") or ".co.uk" in domain_lower or ".org.uk" in domain_lower:
        return True

    country_lower = (data.country or "").lower()
    if country_lower in ("united kingdom", "uk", "great britain", "gb", "scotland", "england", "wales", "northern ireland"):
        return True

    reg = (data.registration_number or "").upper().strip()
    if reg:
        if reg.startswith(("SC", "NI", "OC", "LP", "SO", "IP", "SL", "NC", "NL", "NZ")):
            return True
        if reg.isdigit() and len(reg) in (7, 8):
            return True

    if data.postal_code:
        from validator import validate_uk_postcode
        if validate_uk_postcode(data.postal_code):
            return True

    return False


class CompanyIntelligencePipeline:
    """Centralized pipeline for company research, extraction, UK registry resolution and enrichment."""

    def __init__(self, max_pages: int = 10, enable_ch: bool = True):
        self.max_pages = max_pages
        self.enable_ch = enable_ch
        self.telemetry = TelemetryLogger()

    @property
    def ch_api_key(self) -> Optional[str]:
        """Always read from env at call time so _load_env() has time to run first."""
        return os.getenv("COMPANIES_HOUSE_API_KEY")

    async def run_generator(self, domain_or_url: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run the full research pipeline as an async generator.
        Yields structured status logs, intermediate states, and final normalized entity profile.

        Flow:
            URL Discovery → Page Selection → Jina Reader API → Extraction
            → Companies House (UK) → Wikipedia → Final JSON
        """
        start_url = normalize_domain_url(domain_or_url)
        yield {"type": "log", "level": "PHASE", "msg": f"🚀 Starting entity intelligence research for: {start_url}"}

        # 1. URL Discovery
        yield {"type": "log", "level": "INFO", "msg": "🔍 Phase 1: Discovering URLs (robots.txt, sitemaps, BFS internal links)..."}
        discovery = URLDiscovery(start_url)
        all_urls = await discovery.discover_all()
        if not all_urls:
            all_urls = [start_url]
        yield {"type": "log", "level": "SUCCESS", "msg": f"✅ Discovered {len(all_urls)} unique URLs."}
        self.telemetry.log_discovery(
            domain=start_url,
            sitemaps_found=1 if discovery.sitemap_urls_count > 0 else 0,
            sitemap_urls=discovery.sitemap_urls_count,
            bfs_urls=discovery.bfs_discovered_count,
            total_unique=len(all_urls)
        )

        # 2. Page Selection & Scoring
        yield {"type": "log", "level": "INFO", "msg": "🎯 Phase 2: Scoring and selecting high-priority pages..."}
        selector = PageSelector(start_url, max_pages=self.max_pages)
        selected_items = selector.select_relevant_pages(all_urls)
        target_urls = [item[0] for item in selected_items]
        yield {"type": "log", "level": "SUCCESS", "msg": f"✅ Selected {len(target_urls)} pages for extraction."}
        self.telemetry.log_selection(selected_items)

        # 3. Jina Reader API — read each selected page
        yield {"type": "log", "level": "INFO", "msg": f"📖 Phase 3: Reading {len(target_urls)} pages via Jina Reader API..."}
        for idx, url in enumerate(target_urls, 1):
            yield {"type": "log", "level": "INFO", "msg": f"   Reading page {idx}/{len(target_urls)}: {url}"}
        reader = JinaReader()
        crawled_pages = await reader.read_pages(target_urls)
        yield {"type": "log", "level": "SUCCESS", "msg": f"✅ Successfully read {len(crawled_pages)}/{len(target_urls)} pages via Jina."}
        self.telemetry.log_crawling(crawled_pages)

        # 4. Core Data Extraction
        yield {"type": "log", "level": "PHASE", "msg": "🏗️ Phase 4: Core Company Identity Extraction & Validation..."}
        extractor = CompanyDataExtractor(start_url)
        company_data = extractor.extract_all(crawled_pages)
        yield {"type": "json", "content": company_data.model_dump()}
        yield {"type": "log", "level": "SUCCESS", "msg": "✅ Core extraction complete."}
        self.telemetry.log_extraction(company_data)

        # 5. Country Detection & UK Companies House Resolution
        uk_detected = is_uk_company(company_data, start_url)
        if uk_detected and self.ch_api_key and self.enable_ch:
            yield {"type": "log", "level": "PHASE", "msg": "🇬🇧 Phase 5: Querying Official UK Companies House Registry..."}
            try:
                ch_client = CompaniesHouseClient(self.ch_api_key)
                resolver = UKCompanyResolver(ch_client)
                resolution = await resolver.resolve(company_data)

                company_data.companies_house_resolution = resolution.to_dict()
                company_data.companies_house_status = resolution.status
                company_data.identity_match = resolution.matched
                company_data.identity_match_method = resolution.match_method
                company_data.identity_confidence = resolution.confidence

                if resolution.matched and resolution.company_number:
                    comp_no = resolution.company_number
                    yield {"type": "log", "level": "SUCCESS", "msg": f"✅ Verified Official Registry Match: {comp_no} (Confidence: {int(resolution.confidence * 100)}%)"}

                    profile, officers, psc, history, charges, insolvency = await asyncio.gather(
                        ch_client.get_company_profile(comp_no),
                        ch_client.get_officers(comp_no),
                        ch_client.get_psc(comp_no),
                        ch_client.get_filing_history(comp_no),
                        ch_client.get_charges(comp_no),
                        ch_client.get_insolvency(comp_no)
                    )

                    if profile:
                        self._merge_ch_data(company_data, profile, officers, psc, history, charges, insolvency, comp_no)
                        yield {"type": "json", "content": company_data.model_dump()}
                else:
                    yield {"type": "log", "level": "INFO", "msg": f"ℹ️ Companies House resolution: {resolution.status}"}
            except Exception as e:
                logger.error(f"Companies House Error: {e}", exc_info=True)
                yield {"type": "log", "level": "ERROR", "msg": f"⚠️ Companies House Error: {str(e)}"}
                company_data.companies_house_status = "error"
        elif not uk_detected:
            yield {"type": "log", "level": "INFO", "msg": "ℹ️ Phase 5: Non-UK company detected. Skipping UK Companies House registry lookup."}

        # 6. Optional Wikipedia Enrichment
        yield {"type": "log", "level": "INFO", "msg": "📚 Phase 6: Supplementary Wikipedia Enrichment..."}
        # Prefer legal_name (most accurate after CH enrichment) over raw page title
        brand = (
            company_data.legal_name
            or company_data.brand_name
            or company_data.company_name
            or start_url
        )
        wiki_data = await get_wikipedia_company_data(brand, start_url)
        if wiki_data:
            yield {"type": "wiki_json", "content": wiki_data}
            if wiki_data.get("_domain_match"):
                yield {"type": "log", "level": "SUCCESS", "msg": "✅ Wikipedia supplementary data verified."}
                self._merge_wiki_data(company_data, wiki_data)
                yield {"type": "json", "content": company_data.model_dump()}
            else:
                yield {"type": "log", "level": "INFO", "msg": "ℹ️ Wikipedia page found (unverified domain - supplementary context only)."}
        else:
            yield {"type": "log", "level": "INFO", "msg": "ℹ️ No Wikipedia article found for supplementary context."}

        # Recalculate completeness score
        important_fields = ["company_name", "legal_name", "registration_number", "vat_tax_number", "full_address", "postal_code", "email", "phone"]
        filled = sum(1 for f in important_fields if getattr(company_data, f, None))
        company_data.data_completeness = round(filled / len(important_fields), 2)

        yield {"type": "log", "level": "SUCCESS", "msg": "✨ Pipeline Execution Complete!"}
        yield {"type": "done", "content": company_data.model_dump()}

    def _merge_ch_data(self, data: CompanyData, profile, officers, psc, history, charges, insolvency, comp_no: str):
        """Map official Companies House registry data preserving website address separately."""
        mapper = CompaniesHouseMapper()
        ch_fields = mapper.map_profile(profile)
        ch_officers = mapper.map_officers(officers)
        source_url = f"https://find-and-update.company-information.service.gov.uk/company/{comp_no}"

        # Assign official registered office address distinctly
        data.official_registered_address = ch_fields.get("registered_office_address", {})

        # Build clean normalized official profile object
        data.official_registry_profile = mapper.build_normalized_profile(
            profile=profile,
            officers=officers,
            psc=psc,
            filing_history=history,
            charges=charges,
            insolvency=insolvency
        )

        # Official corporate identity fields (Registry is authoritative for these)
        if ch_fields.get("legal_name"):
            data.legal_name = ch_fields["legal_name"]
            data.field_evidence["legal_name"] = FieldEvidence(
                value=data.legal_name,
                source_url=source_url,
                category="legal",
                method="companies_house_registry",
                confidence=1.0
            )

        if ch_fields.get("registration_number"):
            data.registration_number = ch_fields["registration_number"]
            data.field_evidence["registration_number"] = FieldEvidence(
                value=data.registration_number,
                source_url=source_url,
                category="legal",
                method="companies_house_registry",
                confidence=1.0
            )

        data.company_status = ch_fields.get("company_status")
        data.company_type = ch_fields.get("company_type")
        data.jurisdiction = ch_fields.get("jurisdiction")

        if ch_fields.get("founded") and not data.founded:
            data.founded = ch_fields["founded"]

        if ch_fields.get("sic_codes"):
            data.sic_codes = ch_fields["sic_codes"]

        if ch_officers["directors"]:
            data.directors = ch_officers["directors"]
        if ch_officers["management"]:
            data.management = ch_officers["management"]

        data.persons_with_significant_control = mapper.map_psc(psc)
        data.filing_history = mapper.map_filing_history(history)
        data.charges = charges or []
        data.insolvency = insolvency

    def _merge_wiki_data(self, data: CompanyData, wiki: Dict[str, Any]):
        """Merge supplementary non-authoritative Wikipedia fields."""
        for field in ["industry", "business_description", "parent_company"]:
            val = wiki.get(field)
            if val and not getattr(data, field, None):
                setattr(data, field, val)
                data.field_evidence[field] = FieldEvidence(
                    value=val,
                    source_url=wiki.get("_source", "Wikipedia"),
                    category="enrichment",
                    method="wikipedia_infobox",
                    confidence=0.80
                )

        if wiki.get("subsidiaries") and not data.subsidiaries:
            data.subsidiaries = wiki["subsidiaries"]
