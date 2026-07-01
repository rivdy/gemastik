#!/bin/bash
# ============================================================
# 04_run_docking.sh
# Jalankan AutoDock Vina + pisahkan hasil per-pose (vina_split).
# Ini sudah CLI dari awal di tutorial asli, jadi tinggal di-wrap.
# ============================================================
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
cd "$WORKDIR"

# Pakai vina dari PATH kalau sudah terpasang global, kalau tidak pakai binary lokal di WORKDIR
if command -v vina >/dev/null 2>&1; then
  VINA_BIN="vina"
elif [ -f "$WORKDIR/vina" ]; then
  VINA_BIN="$WORKDIR/vina"
  chmod +x "$VINA_BIN"
else
  echo "  vina tidak ditemukan, download ke $WORKDIR..."
  wget -q https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v1.2.3/vina_1.2.3_linux_x86_64 -O "$WORKDIR/vina"
  chmod +x "$WORKDIR/vina"
  VINA_BIN="$WORKDIR/vina"
fi

if command -v vina_split >/dev/null 2>&1; then
  VINA_SPLIT_BIN="vina_split"
elif [ -f "$WORKDIR/vina_split" ]; then
  VINA_SPLIT_BIN="$WORKDIR/vina_split"
  chmod +x "$VINA_SPLIT_BIN"
else
  echo "  vina_split tidak ditemukan, download ke $WORKDIR..."
  wget -q https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v1.2.3/vina_split_1.2.3_linux_x86_64 -O "$WORKDIR/vina_split"
  chmod +x "$WORKDIR/vina_split"
  VINA_SPLIT_BIN="$WORKDIR/vina_split"
fi

echo "[1/2] Menjalankan AutoDock Vina (exhaustiveness=${EXHAUSTIVENESS})..."
"$VINA_BIN" --receptor "${PDB_ID}_protein.pdbqt" \
       --ligand "${PDB_ID}_ligand.pdbqt" \
       --config grid.txt \
       --exhaustiveness="$EXHAUSTIVENESS" \
       --out "${PDB_ID}_ligand_vina_out.pdbqt" > results.txt

echo "[2/2] Split hasil docking per pose..."
"$VINA_SPLIT_BIN" --input "${PDB_ID}_ligand_vina_out.pdbqt"

echo ""
echo "Docking selesai. Ringkasan energi binding:"
grep -A 20 "mode |" results.txt || cat results.txt
echo ""
echo "File pose individual: ${PDB_ID}_ligand_vina_out_ligand_1.pdbqt, _2.pdbqt, dst."
