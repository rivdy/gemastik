#!/usr/bin/env python3
"""
smiles_to_pdbqt.py
Utility untuk tahap "Foods -> cari senyawa -> SMILES -> bentuk 3D ligand"
Pengganti otomatis untuk:
  - Avogadro (gen 3D + optimasi geometri MMFF94)
  - AutoDockTools ligand prep (-> .pdbqt siap docking)

Pakai untuk satu senyawa:
    python3 smiles_to_pdbqt.py "CCO" ethanol

Pakai untuk banyak senyawa sekaligus (file .csv 2 kolom: name,smiles):
    python3 smiles_to_pdbqt.py --batch compounds.csv
"""
import csv
import os
import subprocess
import sys

ADFR_BIN = os.environ.get("ADFR_HOME", os.path.expanduser("~/ADFRsuite-1.0")) + "/bin"


def smiles_to_pdbqt(smiles: str, name: str, outdir: str = "."):
    mol2_file = os.path.join(outdir, f"{name}.mol2")
    pdbqt_file = os.path.join(outdir, f"{name}.pdbqt")

    # 1. SMILES -> 3D + optimasi geometri (MMFF94), pengganti langkah Avogadro
    subprocess.run(
        ["obabel", f"-:{smiles}", "-O", mol2_file, "--gen3d", "--minimize", "--ff", "MMFF94"],
        check=True,
    )

    # 2. Convert ke .pdbqt siap docking (samakan dengan preparasi ligand di pipeline utama)
    subprocess.run(
        [os.path.join(ADFR_BIN, "prepare_ligand"), "-l", mol2_file, "-o", pdbqt_file, "-U", "nphs_lps"],
        check=True,
    )
    print(f"  OK: {name} -> {pdbqt_file}")
    return pdbqt_file


def batch(csv_path: str, outdir: str = "compounds_pdbqt"):
    os.makedirs(outdir, exist_ok=True)
    with open(csv_path) as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 2:
                continue
            name, smiles = row[0].strip(), row[1].strip()
            try:
                smiles_to_pdbqt(smiles, name, outdir)
            except subprocess.CalledProcessError:
                print(f"  GAGAL: {name} ({smiles}) - skip, cek validitas SMILES")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] != "--batch":
        smiles_to_pdbqt(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 3 and sys.argv[1] == "--batch":
        batch(sys.argv[2])
    else:
        sys.exit(__doc__)
