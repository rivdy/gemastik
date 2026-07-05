#!/bin/bash
# ============================================================
# run_all.sh - Jalankan seluruh pipeline docking 4IEH end-to-end
# ============================================================
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
chmod +x *.sh
source "$SCRIPT_DIR/config.sh"   # penting: supaya WORKDIR/PDB_ID ikut ke-export ke python3 juga

if [ "$1" == "--with-setup" ]; then
  echo "=================================================="
  echo " STEP 0: Setup environment & install tools"
  echo "=================================================="
  ./00_setup_environment.sh
else
  echo "(Lewati setup environment. Jalankan dengan '--with-setup' kalau ini run pertama kali"
  echo " atau kalau tool belum terpasang: ./run_all.sh --with-setup)"
fi

echo "=================================================="
echo " STEP 1: Download & pisahkan protein/ligand"
echo "=================================================="
python3 01_download_and_split.py

echo "=================================================="
echo " STEP 2: Preparasi receptor & ligand (-> .pdbqt)"
echo "=================================================="
./02_prepare_receptor_ligand.sh

echo "=================================================="
echo " STEP 3: Hitung grid box"
echo "=================================================="
python3 03_generate_gridbox.py

echo "=================================================="
echo " STEP 4: Jalankan docking (Vina)"
echo "=================================================="
./04_run_docking.sh

echo "=================================================="
echo " STEP 5: Hitung RMSD"
echo "=================================================="
./05_calculate_rmsd.sh

echo ""
echo "=================================================="
echo " STEP 6: Agregasi hasil (afinitas + RMSD -> JSON)"
echo "=================================================="
python3 aggregate_results.py --workdir "$WORKDIR" --pdb-id "$PDB_ID"

echo "=================================================="
echo " STEP 7: Analisis interaksi pose terbaik (PLIP)"
echo "=================================================="
python3 06_analyze_interactions.py --workdir "$WORKDIR" --pdb-id "$PDB_ID"
echo "=== PIPELINE SELESAI ==="
echo "Semua file ada di: \$WORKDIR (lihat config.sh)"
echo "Ringkasan akhir (JSON): ${WORKDIR}/final_report.json"
