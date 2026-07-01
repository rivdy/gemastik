#!/bin/bash
# ============================================================
# 00_setup_environment.sh
# Install semua dependency untuk pipeline docking.
# Ditujukan untuk Google Colab / Ubuntu Linux.
#
# CATATAN PENTING:
# - UNTESTED. Script baru dicoba dengan setup dependency manual dan dijalankan secara LOKAL.
# ============================================================
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"
mkdir -p "$WORKDIR" && cd "$WORKDIR"

echo "[1/6] Install dependency dasar (openbabel, wget)..."
if [ "$(id -u)" -eq 0 ]; then
  APT="apt-get"
else
  APT="sudo apt-get"
fi
$APT update -qq && $APT install -y -qq wget openbabel > /dev/null

echo "[2/6] Install BioPython & numpy..."
pip install -q biopython numpy

echo "[3/6] Cek/pasang AutoDock Vina 1.2.3..."
if command -v vina >/dev/null 2>&1 && command -v vina_split >/dev/null 2>&1; then
  echo "  -> vina & vina_split sudah ada di PATH ($(command -v vina)), skip download."
elif [ -f "$WORKDIR/vina" ] && [ -f "$WORKDIR/vina_split" ]; then
  echo "  -> vina & vina_split sudah ada di $WORKDIR, skip download."
  chmod +x "$WORKDIR/vina" "$WORKDIR/vina_split"
else
  wget -q https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v1.2.3/vina_1.2.3_linux_x86_64 -O vina
  wget -q https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v1.2.3/vina_split_1.2.3_linux_x86_64 -O vina_split
  chmod +x vina vina_split
fi

echo "[4/6] Download & pasang ADFRsuite (untuk prepare_receptor / prepare_ligand)..."
if [ -x "$ADFR_HOME/bin/prepare_receptor" ]; then
  echo "  -> ADFRsuite sudah terpasang di $ADFR_HOME, skip instalasi."
else
  wget -q https://ccsb.scripps.edu/adfr/download/1038/ADFRsuite_Linux-x86_64_1.0_install -O ADFRsuite_install.sh || \
    echo "  !! wget gagal - download manual installer ADFRsuite Linux dari https://ccsb.scripps.edu/adfr/downloads/ lalu taruh di $WORKDIR sebagai ADFRsuite_install.sh"
  if [ -f ADFRsuite_install.sh ]; then
    chmod +x ADFRsuite_install.sh
    echo "Y" | ./ADFRsuite_install.sh -d "$ADFR_HOME" -c 0
  fi
fi

echo "[5/6] Tambahkan tool ke PATH sesi ini..."
export PATH="$WORKDIR:$ADFR_HOME/bin:$PATH"

echo "[6/6] Cek instalasi..."
./vina --version || echo "  !! vina belum terpasang dengan benar"
"$ADFR_HOME/bin/prepare_receptor" -h > /dev/null 2>&1 && echo "  OK: prepare_receptor siap" || echo "  !! prepare_receptor belum terpasang dengan benar"
obabel -V || echo "  !! openbabel belum terpasang dengan benar"

echo ""
echo "Setup selesai. Untuk sesi terminal baru, jalankan dulu:"
echo "  export PATH=\"$WORKDIR:$ADFR_HOME/bin:\$PATH\""
