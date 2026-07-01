#!/bin/bash
# ============================================================
# 02_prepare_receptor_ligand.sh
# Pengganti langkah manual di AutoDockTools GUI:
#   Add Hydrogen -> Add Gasteiger Charge -> Merge Non Polar -> Save PDBQT
# `prepare_receptor` dan `prepare_ligand` (ADFRsuite) melakukan
# semua langkah itu otomatis dalam satu perintah.
# ============================================================
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
cd "$WORKDIR"
export PATH="$PATH:$ADFR_HOME/bin"   # utamakan tool sistem (apt); ADFRsuite cuma fallback untuk prepare_receptor/prepare_ligand

PROTEIN_RAW="${PDB_ID}_protein_raw.pdb"
LIGAND_RAW="${PDB_ID}_ligand_raw.pdb"

echo "[1/2] Preparasi protein -> ${PDB_ID}_protein.pdbqt"
prepare_receptor -r "$PROTEIN_RAW" -o "${PDB_ID}_protein.pdbqt" -A checkhydrogens

echo "[2/2] Preparasi ligand -> ${PDB_ID}_ligand.pdbqt"
# Catatan: kalau muncul warning "libxml2.so.2: cannot open shared object file",
# itu cuma plugin XML/CML OpenBabel yang tidak dipakai di sini (tidak fatal).
# Untuk hilangkan warning-nya (opsional): sudo apt-get install -y libxml2
# Struktur kristal biasanya tidak punya H eksplisit -> tambahkan dulu via OpenBabel
obabel "$LIGAND_RAW" -O "${PDB_ID}_ligand_h.pdb" -h
# -U nphs_lps = hapus H nonpolar & lone pair, setara langkah GUI "Merge Non Polar"
prepare_ligand -l "${PDB_ID}_ligand_h.pdb" -o "${PDB_ID}_ligand.pdbqt" -U nphs_lps

echo ""
echo "Selesai. Output:"
echo "  - ${WORKDIR}/${PDB_ID}_protein.pdbqt"
echo "  - ${WORKDIR}/${PDB_ID}_ligand.pdbqt"
