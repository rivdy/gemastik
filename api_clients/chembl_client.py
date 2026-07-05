"""
ChEMBLClient
============
Tidak butuh API key. Pelengkap PubChem untuk data bioaktivitas
(IC50/Ki/Kd) senyawa terhadap target tertentu — berguna untuk
cross-validation skor docking (Bagian V paper: validitas prediktif
docking vs data eksperimental).

Docs: https://www.ebi.ac.uk/chembl/api/data/docs
"""

from .base_client import BaseAPIClient


class ChEMBLClient(BaseAPIClient):
    BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"

    def search_molecule(self, name: str) -> dict:
        return self.get("/molecule/search", params={"q": name, "format": "json"})

    def get_activities_for_target(self, target_chembl_id: str, limit: int = 50) -> dict:
        """Ambil data bioaktivitas eksperimental (IC50/Ki/Kd) untuk suatu target ChEMBL."""
        return self.get(
            "/activity",
            params={"target_chembl_id": target_chembl_id, "limit": limit, "format": "json"},
        )

    def get_target_by_uniprot(self, uniprot_accession: str) -> dict:
        return self.get(
            "/target",
            params={"target_components__accession": uniprot_accession, "format": "json"},
        )
