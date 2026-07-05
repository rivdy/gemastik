"""
OpenTargetsClient
=================
Tidak butuh API key. Open Targets pakai GraphQL, bukan REST biasa —
jadi override method-nya beda dari client lain (semua lewat POST /graphql
dengan query string).

Berguna sebagai pelengkap/silang-cek DisGeNET untuk asosiasi gen-penyakit
plus skor evidence yang sudah dikurasi.

Docs: https://platform.opentargets.org/api
"""

from .base_client import BaseAPIClient


class OpenTargetsClient(BaseAPIClient):
    BASE_URL = "https://api.platform.opentargets.org/api/v4/graphql"

    _TARGET_DISEASE_QUERY = """
    query targetDiseaseAssociations($diseaseId: String!) {
      disease(efoId: $diseaseId) {
        id
        name
        associatedTargets(page: {index: 0, size: 25}) {
          rows {
            target { id approvedSymbol }
            score
          }
        }
      }
    }
    """

    def get_associated_targets(self, disease_efo_id: str) -> dict:
        """
        disease_efo_id: EFO id penyakit, mis. "EFO_0000676" (Dengue) atau
        cari ID-nya lewat pencarian di https://platform.opentargets.org
        """
        body = {"query": self._TARGET_DISEASE_QUERY, "variables": {"diseaseId": disease_efo_id}}
        return self.post("", json_body=body)
