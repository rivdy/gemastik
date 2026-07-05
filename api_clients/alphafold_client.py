"""
AlphaFoldClient
================
Tidak butuh API key. Dipakai pada Fase 2 (AI Blind Spot Resolution):
mengambil model struktur 3D hasil prediksi AF2/AF3 untuk suatu UniProt
accession, sebagai fallback ketika protein target tidak tersedia di RCSB PDB.

Docs: https://alphafold.ebi.ac.uk/api-docs
"""

from typing import Optional

from .base_client import BaseAPIClient


class AlphaFoldClient(BaseAPIClient):
    BASE_URL = "https://alphafold.ebi.ac.uk/api"

    def get_prediction(self, qualifier: str) -> list:
        """
        Ambil semua model AF2/AF3 untuk suatu UniProt accession atau model ID.
        qualifier: mis. "Q5VSL9"
        """
        return self.get(f"/prediction/{qualifier}")

    def get_uniprot_summary(self, qualifier: str) -> dict:
        """Ringkasan struktur untuk rentang residu UniProt tertentu."""
        return self.get(f"/uniprot/summary/{qualifier}.json")

    def get_sequence_summary(self, sequence: str, rows: int = 500) -> dict:
        """
        Cari model AF2 berdasarkan urutan asam amino mentah (bukan accession).
        Berguna kalau protein target belum terpetakan ke UniProt ID manapun.
        """
        return self.get(
            "/sequence/summary",
            params={"id": sequence, "type": "sequence", "rows": rows},
        )

    def get_annotations(self, qualifier: str, annotation_type: Optional[str] = None) -> dict:
        params = {"type": annotation_type} if annotation_type else {}
        return self.get(f"/annotations/{qualifier}.json", params=params)

    def has_confident_model(self, qualifier: str, plddt_threshold: float = 70.0) -> bool:
        """
        Helper: cek apakah AF2 punya model dengan confidence memadai
        (ambang pLDDT >= 70 sesuai parameter kualitas di paper TropicDock).
        """
        predictions = self.get_prediction(qualifier)
        if not predictions:
            return False
        return any(
            p.get("globalMetricValue", 0) >= plddt_threshold for p in predictions
        )
