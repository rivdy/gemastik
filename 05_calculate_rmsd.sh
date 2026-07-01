#!/bin/bash
# ============================================================
# 05_calculate_rmsd.sh
# Pengganti langkah manual RMSD di Discovery Studio -> versi Linux
# + OpenBabel yang sudah disebut di README asli (obrms), tinggal di-wrap.
# ============================================================
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
cd "$WORKDIR"
export PATH="$PATH:$ADFR_HOME/bin"   # utamakan tool sistem (apt); ADFRsuite cuma fallback

if ! command -v obrms >/dev/null 2>&1; then
  echo "!! 'obrms' tidak ditemukan di PATH."
  echo "   obrms tidak dibundle di ADFRsuite, harus dari paket openbabel sistem:"
  echo "     sudo apt-get update && sudo apt-get install -y openbabel"
  exit 1
fi
if ! command -v obabel >/dev/null 2>&1; then
  echo "!! 'obabel' tidak ditemukan di PATH (sistem maupun ADFRsuite)."
  exit 1
fi
echo "  (pakai obabel: $(command -v obabel), obrms: $(command -v obrms))"

echo "[1/2] Hitung RMSD tiap pose vs ligand referensi (kristal)..."
obrms "${PDB_ID}_ligand_raw.pdb" "${PDB_ID}_ligand_vina_out.pdbqt" | tee rmsd_results.txt

echo ""
echo "[2/2] Konversi pose terbaik (pose 1) ke .pdb untuk visualisasi..."
obabel "${PDB_ID}_ligand_vina_out_ligand_1.pdbqt" -O "${PDB_ID}_ligand_pose1.pdb"

echo ""
echo "Catatan: RMSD < 2 Angstrom umumnya dianggap re-docking valid/reliable."
echo "Hasil lengkap tersimpan di: ${WORKDIR}/rmsd_results.txt"
