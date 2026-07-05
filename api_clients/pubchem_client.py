"""
PubChemClient
=============
Tidak butuh API key, tapi PubChem PUG-REST punya soft rate limit resmi
(maks. ~5 request/detik) — makanya diberi min_request_interval default.

Dipakai pada Fase 1 (Ligand Preparation) untuk mengambil data senyawa
fitokimia (mis. Karpain, Karantin, Andrographolide) sebelum dikonversi
OpenBabel jadi PDBQT.

Docs: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest
"""

from .base_client import BaseAPIClient


class PubChemClient(BaseAPIClient):
    BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

    def __init__(self, **kwargs):
        kwargs.setdefault("min_request_interval", 0.25)  # ~4 req/detik, aman di bawah limit
        super().__init__(**kwargs)

    def get_cid_by_name(self, compound_name: str) -> list:
        """Cari PubChem CID dari nama senyawa, mis. 'Carpaine'."""
        data = self.get(f"/compound/name/{compound_name}/cids/JSON")
        return data.get("IdentifierList", {}).get("CID", []) if data else []

    def get_smiles(self, cid: int) -> str:
        data = self.get(f"/compound/cid/{cid}/property/IsomericSMILES/JSON")
        props = data["PropertyTable"]["Properties"][0]
        return props.get("IsomericSMILES") or props.get("SMILES")

    def get_properties(self, cid: int, properties: str = "MolecularFormula,MolecularWeight,CanonicalSMILES,IUPACName") -> dict:
        data = self.get(f"/compound/cid/{cid}/property/{properties}/JSON")
        return data["PropertyTable"]["Properties"][0]

    def download_sdf(self, cid: int) -> bytes:
        """Ambil struktur 3D mentah dalam format SDF (utk dikonversi OpenBabel)."""
        return self.get(f"/compound/cid/{cid}/record/SDF/", expect_json=False)
