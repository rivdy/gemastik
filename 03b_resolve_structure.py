#!/usr/bin/env python3
"""
03b_resolve_structure.py
=========================
Otomatisasi Fase 2 (Resolusi AI Blind Spot via AlphaFold) dari paper TropicDock.

Alur:
  1. Cek RCSB PDB dulu -> kalau ada struktur eksperimental, pakai itu (lebih
     akurat & tidak perlu prediksi AI).
  2. Kalau TIDAK ada (crystallographic blind spot) -> tarik model AF2/AF3
     dari AlphaFold EBI API berdasarkan UniProt accession.
  3. Kalau protein bahkan tidak punya entri UniProt (sekuens benar-benar baru)
     -> tidak bisa diotomasi murni via API; skrip ini akan mencetak instruksi
     manual untuk menjalankan ColabFold (perlu GPU, di luar cakupan REST API).

Pemakaian:
    python 03b_resolve_structure.py --uniprot Q5VSL9 --outdir ./structures --plddt-threshold 70
"""

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from api_clients import AlphaFoldClient, RCSBSearchClient, RCSBDataClient, APIClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def resolve_structure(uniprot_accession: str, outdir: Path, plddt_threshold: float = 70.0) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    result = {"uniprot_accession": uniprot_accession, "source": None, "detail": None}

    # 1. Cek RCSB PDB dulu
    with RCSBSearchClient() as search_client:
        try:
            has_experimental = search_client.has_experimental_structure(uniprot_accession)
        except APIClientError as exc:
            logger.warning("Pencarian RCSB gagal (%s), lanjut ke AlphaFold fallback.", exc)
            has_experimental = False

    if has_experimental:
        logger.info("Struktur eksperimental ditemukan di RCSB PDB untuk %s.", uniprot_accession)
        result["source"] = "RCSB_PDB"
        result["detail"] = "Struktur eksperimental tersedia — gunakan entri PDB, AF2 tidak diperlukan."
        return result

    # 2. Fallback ke AlphaFold
    logger.info("Tidak ada struktur eksperimental (blind spot). Mencoba AlphaFold EBI API...")
    with AlphaFoldClient() as af_client:
        try:
            predictions = af_client.get_prediction(uniprot_accession)
        except APIClientError as exc:
            logger.error("AlphaFold API juga gagal: %s", exc)
            predictions = None

        if predictions:
            best = max(predictions, key=lambda p: p.get("globalMetricValue", 0))
            if best.get("globalMetricValue", 0) >= plddt_threshold:
                cif_url = best.get("cifUrl")
                pdb_url = best.get("pdbUrl")
                out_file = outdir / f"{uniprot_accession}_AF2.json"
                out_file.write_text(json.dumps(best, indent=2))
                logger.info(
                    "Model AF2 ditemukan (pLDDT global %.1f >= ambang %.1f). Metadata disimpan di %s",
                    best["globalMetricValue"], plddt_threshold, out_file,
                )
                result["source"] = "AlphaFold_EBI"
                result["detail"] = {
                    "global_plddt": best.get("globalMetricValue"),
                    "cif_url": cif_url,
                    "pdb_url": pdb_url,
                    "metadata_file": str(out_file),
                }
                return result
            else:
                logger.warning(
                    "Model AF2 ada tapi pLDDT (%.1f) di bawah ambang (%.1f) — kualitas kurang meyakinkan.",
                    best.get("globalMetricValue", 0), plddt_threshold,
                )

    # 3. Tidak ada di RCSB maupun AlphaFold precomputed -> perlu ColabFold manual
    logger.warning(
        "Protein %s tidak ditemukan di RCSB maupun database AF2 precomputed.",
        uniprot_accession,
    )
    result["source"] = "MANUAL_COLABFOLD_REQUIRED"
    result["detail"] = (
        "Sekuens ini tidak punya entri UniProt/model AF2 precomputed. "
        "Prediksi de novo perlu dijalankan manual via ColabFold "
        "(https://github.com/sokrypton/ColabFold) di Google Colab dengan GPU, "
        "lalu terapkan ambang pLDDT >= {:.0f} dan proses hasilnya dengan PyMOL/AutoDockTools "
        "seperti Fase 2 pada metodologi paper.".format(plddt_threshold)
    )
    return result


def main():
    parser = argparse.ArgumentParser(description="Resolusi struktur protein: RCSB PDB -> AlphaFold fallback")
    parser.add_argument("--uniprot", required=True, help="UniProt accession protein target, mis. Q5VSL9")
    parser.add_argument("--outdir", default="./structures", type=Path)
    parser.add_argument("--plddt-threshold", default=70.0, type=float)
    args = parser.parse_args()

    result = resolve_structure(args.uniprot, args.outdir, args.plddt_threshold)
    print(json.dumps(result, indent=2))

    summary_file = args.outdir / f"{args.uniprot}_resolution_summary.json"
    args.outdir.mkdir(parents=True, exist_ok=True)
    summary_file.write_text(json.dumps(result, indent=2))
    logger.info("Ringkasan resolusi disimpan di %s", summary_file)


if __name__ == "__main__":
    main()
