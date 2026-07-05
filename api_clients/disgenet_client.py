"""
DisgenetClient
==============
BUTUH API KEY. Sejak 2020 DisGeNET pindah ke model lisensi: akademisi bisa
mengajukan lisensi berlangganan gratis, organisasi profit harus berlangganan
berbayar (lihat https://disgenet.com/api/). Simpan key di environment variable
DISGENET_API_KEY, jangan hardcode.

Dipakai untuk resolusi target penyakit -> gen: mis. cari gen apa saja yang
berasosiasi dengan Dengue atau Diabetes Tipe-2 sebelum melangkah ke
prediksi struktur protein.

Docs: https://disgenet.com/interactive-console
"""

from .base_client import BaseAPIClient


class DisgenetClient(BaseAPIClient):
    BASE_URL = "https://api.disgenet.com/api/v1"

    def _auth_headers(self) -> dict:
        if not self.api_key:
            raise ValueError(
                "DisgenetClient butuh api_key. Daftar lisensi akademik gratis di "
                "https://www.disgenet.com/ lalu set env var DISGENET_API_KEY."
            )
        return {"Authorization": self.api_key}

    def get_gene_disease_associations(self, disease_id: str, source: str = "ALL") -> dict:
        return self.get("/gda/summary", params={"disease": disease_id, "source": source})

    def get_disease_properties(self, disease_query: str) -> dict:
        return self.get("/entity/disease", params={"disease": disease_query})

    def get_gene_enrichment(self, gene_ids: list) -> dict:
        return self.post("/enrichment/gene", json_body={"genes": gene_ids})
