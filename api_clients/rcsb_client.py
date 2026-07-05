"""
RCSBClient
==========
Tidak butuh API key. Dipakai untuk mengecek apakah protein target sudah
punya struktur eksperimental (crystallography/cryo-EM/NMR) di RCSB PDB
SEBELUM fallback ke AlphaFold — ini logika inti "crystallographic blind
spot detection" pada Fase 2.

Docs: https://www.rcsb.org/docs/programmatic-access/web-apis-overview
"""

from .base_client import BaseAPIClient


class RCSBSearchClient(BaseAPIClient):
    BASE_URL = "https://search.rcsb.org/rcsbsearch/v2"

    def search_by_uniprot(self, uniprot_accession: str) -> dict:
        """Cari entri PDB eksperimental yang terasosiasi dengan UniProt accession tertentu."""
        query = {
            "query": {
                "type": "terminal",
                "service": "full_text",
                "parameters": {"value": uniprot_accession},
            },
            "return_type": "entry",
        }
        return self.post("/query", json_body=query)

    def has_experimental_structure(self, uniprot_accession: str) -> bool:
        result = self.search_by_uniprot(uniprot_accession)
        if not result:
            return False
        return len(result.get("result_set", [])) > 0


class RCSBDataClient(BaseAPIClient):
    BASE_URL = "https://data.rcsb.org/rest/v1/core"

    def get_entry(self, pdb_id: str) -> dict:
        """Metadata lengkap suatu entri PDB (metode eksperimental, resolusi, dst)."""
        return self.get(f"/entry/{pdb_id.upper()}")

    def get_polymer_entity(self, pdb_id: str, entity_id: str = "1") -> dict:
        return self.get(f"/polymer_entity/{pdb_id.upper()}/{entity_id}")
