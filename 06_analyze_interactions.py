#!/usr/bin/env python3
"""
06_analyze_interactions.py (revisi 3)
========================================
Bangun kompleks reseptor-ligand dari protein_raw.pdb + ligand_pose1.pdb,
lalu analisis interaksi molekuler pakai PLIP (Fase 4).

PLIP menyimpan hasilnya sebagai "<nama_file>_report.xml" langsung di
folder output (bukan report.xml di subfolder terpisah).
"""

import argparse
import json
import logging
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

LIGAND_RESNAME = "LIG"
LIGAND_CHAIN = "X"


def build_complex_pdb(protein_raw, ligand_pose, out_path):
    if not protein_raw.exists():
        raise FileNotFoundError(f"Tidak ditemukan: {protein_raw}")
    if not ligand_pose.exists():
        raise FileNotFoundError(f"Tidak ditemukan: {ligand_pose}")

    protein_lines = []
    for line in protein_raw.read_text(errors="ignore").splitlines(keepends=True):
        if line.startswith(("ATOM", "HETATM")):
            protein_lines.append(line)
        elif line.startswith("TER"):
            protein_lines.append(line)

    ligand_lines = []
    atom_serial = 1
    for line in ligand_pose.read_text(errors="ignore").splitlines():
        if not line.startswith(("ATOM", "HETATM")):
            continue
        new_line = (
            "HETATM"
            + f"{atom_serial:>5}"
            + line[11:17]
            + f"{LIGAND_RESNAME:<3}"
            + " "
            + f"{LIGAND_CHAIN}"
            + line[22:]
        )
        ligand_lines.append(new_line.rstrip("\n") + "\n")
        atom_serial += 1

    if not ligand_lines:
        raise ValueError(f"Tidak ada baris ATOM/HETATM valid ditemukan di {ligand_pose}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        f.writelines(protein_lines)
        if not protein_lines or not protein_lines[-1].startswith("TER"):
            f.write("TER\n")
        f.writelines(ligand_lines)
        f.write("END\n")

    logger.info(
        "Kompleks dibuat: %s (%d atom protein, %d atom ligand)",
        out_path, len(protein_lines), len(ligand_lines),
    )
    return out_path


def run_plip(complex_pdb, outdir):
    outdir.mkdir(parents=True, exist_ok=True)

    cmd = ["plip", "-f", str(complex_pdb), "-x", "-o", str(outdir)]
    logger.info("Menjalankan: %s", " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode != 0:
        raise RuntimeError(f"PLIP gagal untuk {complex_pdb}:\n{proc.stderr}")

    report_xml = outdir / f"{complex_pdb.stem}_report.xml"
    if not report_xml.exists():
        raise FileNotFoundError(f"PLIP tidak menghasilkan {report_xml.name} untuk {complex_pdb}")
    return report_xml


def parse_plip_report(report_xml):
    tree = ET.parse(report_xml)
    root = tree.getroot()

    summary = {
        "hydrogen_bonds": [],
        "hydrophobic_interactions": [],
        "pi_stacking": [],
        "salt_bridges": [],
    }

    for site in root.findall(".//bindingsite"):
        interactions = site.find("interactions")
        if interactions is None:
            continue

        for hb in interactions.findall("hydrogen_bonds/hydrogen_bond"):
            summary["hydrogen_bonds"].append({
                "residue": hb.findtext("restype", "") + hb.findtext("resnr", ""),
                "distance_h_a": hb.findtext("dist_h-a"),
                "distance_d_a": hb.findtext("dist_d-a"),
                "donor_is_protein": hb.findtext("protisdon"),
            })

        for hc in interactions.findall("hydrophobic_interactions/hydrophobic_interaction"):
            summary["hydrophobic_interactions"].append({
                "residue": hc.findtext("restype", "") + hc.findtext("resnr", ""),
                "distance": hc.findtext("dist"),
            })

        for pi in interactions.findall("pi_stacks/pi_stack"):
            summary["pi_stacking"].append({
                "residue": pi.findtext("restype", "") + pi.findtext("resnr", ""),
                "distance": pi.findtext("centdist"),
                "type": pi.findtext("type"),
            })

        for sb in interactions.findall("salt_bridges/salt_bridge"):
            summary["salt_bridges"].append({
                "residue": sb.findtext("restype", "") + sb.findtext("resnr", ""),
                "distance": sb.findtext("dist"),
            })

    summary["n_hydrogen_bonds"] = len(summary["hydrogen_bonds"])
    summary["n_hydrophobic"] = len(summary["hydrophobic_interactions"])
    summary["n_pi_stacking"] = len(summary["pi_stacking"])
    return summary


def main():
    parser = argparse.ArgumentParser(description="Bangun kompleks reseptor-ligand lalu analisis interaksi via PLIP (Fase 4)")
    parser.add_argument("--workdir", required=True, type=Path)
    parser.add_argument("--pdb-id", required=True)
    parser.add_argument("--outdir", default=None, type=Path)
    args = parser.parse_args()

    outdir = args.outdir or (args.workdir / "interaction_reports")
    protein_raw = args.workdir / f"{args.pdb_id}_protein_raw.pdb"
    ligand_pose = args.workdir / f"{args.pdb_id}_ligand_pose1.pdb"
    complex_pdb = args.workdir / f"{args.pdb_id}_complex_pose1.pdb"

    build_complex_pdb(protein_raw, ligand_pose, complex_pdb)

    try:
        report_xml = run_plip(complex_pdb, outdir)
        summary = parse_plip_report(report_xml)
    except (RuntimeError, FileNotFoundError) as exc:
        logger.error("Analisis PLIP gagal: %s", exc)
        summary = {"error": str(exc)}

    out_json = outdir / "interaction_summary.json"
    outdir.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2))
    logger.info("Ringkasan interaksi tersimpan di %s", out_json)


if __name__ == "__main__":
    main()
