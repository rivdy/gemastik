#!/bin/bash
# ============================================================
# Konfigurasi Pipeline Docking Otomatis - AutoDock Vina
# Target contoh: Protein 4IEH
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export PDB_ID="4ieh"
export WORKDIR="$SCRIPT_DIR/data_${PDB_ID}"   # folder kerja di dalam folder project ini, bukan $HOME
export LIGAND_RESNAME=""          # kosongkan = auto-detect ligand HETATM terbesar (non-air/ion)
export EXHAUSTIVENESS=8
export BOX_PADDING=8.0            # angstrom, ruang ekstra di sekitar ligand kristal untuk grid box
export ADFR_HOME="$HOME/ADFRsuite-1.1dev"   # sesuaikan dengan lokasi instalasi manual kamu
