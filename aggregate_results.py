#!/usr/bin/env python3
"""
aggregate_results.py (revisi 2)
=================================
Direvisi total setelah melihat isi asli 04_run_docking.sh dan
05_calculate_rmsd.sh. Pipeline kalian itu SINGLE-LIGAND RE-DOCKING
VALIDATION (1 protein + 1 ligand kristal, banyak pose), bukan skrining
multi-senyawa. Jadi skrip ini merangkum SEMUA POSE dari satu ligand,
bukan banyak ligand berbeda.

Sumber data (semuanya ada di $WORKDIR, lihat config.sh):
  - results.txt        <- tabel Vina: mode | affinity (kcal/mol) | rmsd l.b. | rmsd u.b.
  - rmsd_results.txt   <- output obrms: RMSD tiap pose vs ligand kristal asli

Pemakaian:
    python aggregate_results.py --workdir "$WORKDIR" --pdb-id 4ieh
"""

import argparse
import json
import logging
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Baris tabel Vina, contoh: "   1       -7.8      0.000      0.000"
VINA_MODE_RE = re.compile(r"^\s*(\d+)\s+(-?\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)")

# Baris obrms, contoh umum: "<file>.pdbqt: 0.452" atau "RMSD ... : 0.452"
OBRMS_LINE_RE = re.compile(r"(-?\d+\.\d+)\s*$")


def parse_vina_results(results_file: Path) -> dict:
    """Ekstrak semua pose (mode, affinity, rmsd l.b./u.b. relatif ke pose#1) dari results.txt."""
    poses = {}
    if not results_file.exists():
        logger.warning("File %s tidak ditemukan.", results_file)
        return poses

    for line in results_file.read_text(errors="ignore").splitlines():
        match = VINA_MODE_RE.match(line)
        if match:
            mode, affinity, rmsd_lb, rmsd_ub = match.groups()
            poses[int(mode)] = {
                "mode": int(mode),
                "binding_affinity_kcal_mol": float(affinity),
                "rmsd_lb": float(rmsd_lb),
                "rmsd_ub": float(rmsd_ub),
            }
    if not poses:
        logger.warning(
            "Tidak ada baris tabel Vina yang cocok di %s — cek apakah format "
            "output Vina di sistem kamu beda (mis. versi Vina berbeda).",
            results_file,
        )
    return poses


def parse_obrms_results(rmsd_file: Path) -> dict:
    """
    Ekstrak RMSD tiap pose vs ligand kristal referensi dari rmsd_results.txt.
    Nomor pose diasumsikan mengikuti urutan baris (baris ke-1 = pose 1, dst) —
    ini sesuai urutan default output vina_split (_1, _2, _3, ...).
    """
    rmsd_by_pose = {}
    if not rmsd_file.exists():
        logger.warning("File %s tidak ditemukan (mungkin belum jalan 05_calculate_rmsd.sh).", rmsd_file)
        return rmsd_by_pose

    lines = [l for l in rmsd_file.read_text(errors="ignore").splitlines() if l.strip()]
    for idx, line in enumerate(lines, start=1):
        match = OBRMS_LINE_RE.search(line)
        if match:
            rmsd_by_pose[idx] = float(match.group(1))
        else:
            logger.warning("Baris obrms tidak dikenali (dilewati): %r", line)
    return rmsd_by_pose


def build_report(workdir: Path, pdb_id: str) -> dict:
    results_file = workdir / "results.txt"
    rmsd_file = workdir / "rmsd_results.txt"

    vina_poses = parse_vina_results(results_file)
    obrms_rmsd = parse_obrms_results(rmsd_file)

    report = {"pdb_id": pdb_id, "poses": []}
    all_mode_numbers = sorted(set(vina_poses) | set(obrms_rmsd))

    for mode in all_mode_numbers:
        entry = {"mode": mode}
        entry.update(vina_poses.get(mode, {}))
        entry["rmsd_vs_crystal_ligand"] = obrms_rmsd.get(mode)
        entry["redocking_valid"] = (
            entry["rmsd_vs_crystal_ligand"] < 2.0
            if entry.get("rmsd_vs_crystal_ligand") is not None
            else None
        )
        report["poses"].append(entry)

    if report["poses"]:
        best = min(
            (p for p in report["poses"] if p.get("binding_affinity_kcal_mol") is not None),
            key=lambda p: p["binding_affinity_kcal_mol"],
            default=None,
        )
        report["best_pose"] = best
    else:
        report["best_pose"] = None

    return report


def main():
    parser = argparse.ArgumentParser(description="Agregasi hasil re-docking (Vina + obrms) jadi satu laporan JSON")
    parser.add_argument("--workdir", required=True, type=Path, help="Sama dengan $WORKDIR di config.sh")
    parser.add_argument("--pdb-id", required=True, help="Sama dengan $PDB_ID di config.sh, mis. 4ieh")
    parser.add_argument("--out", default=None, type=Path, help="Default: <workdir>/final_report.json")
    args = parser.parse_args()

    out_path = args.out or (args.workdir / "final_report.json")
    report = build_report(args.workdir, args.pdb_id)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    logger.info(
        "Laporan tersimpan di %s (%d pose ditemukan)", out_path, len(report["poses"])
    )
    if report["best_pose"]:
        logger.info(
            "Pose terbaik: mode %s, afinitas %.2f kcal/mol",
            report["best_pose"]["mode"],
            report["best_pose"]["binding_affinity_kcal_mol"],
        )


if __name__ == "__main__":
    main()