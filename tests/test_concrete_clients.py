import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from api_clients.alphafold_client import AlphaFoldClient
from api_clients.pubchem_client import PubChemClient


def test_alphafold_has_confident_model(requests_mock):
    requests_mock.get(
        "https://alphafold.ebi.ac.uk/api/prediction/Q5VSL9",
        json=[{"globalMetricValue": 92.4}, {"globalMetricValue": 55.0}],
    )
    client = AlphaFoldClient()
    assert client.has_confident_model("Q5VSL9", plddt_threshold=70.0) is True


def test_alphafold_no_confident_model(requests_mock):
    requests_mock.get(
        "https://alphafold.ebi.ac.uk/api/prediction/XXXXX",
        json=[{"globalMetricValue": 40.0}],
    )
    client = AlphaFoldClient()
    assert client.has_confident_model("XXXXX", plddt_threshold=70.0) is False


def test_pubchem_get_cid_by_name(requests_mock):
    requests_mock.get(
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Carpaine/cids/JSON",
        json={"IdentifierList": {"CID": [442758]}},
    )
    client = PubChemClient(min_request_interval=0)  # matikan rate limit biar test cepat
    cids = client.get_cid_by_name("Carpaine")
    assert cids == [442758]
