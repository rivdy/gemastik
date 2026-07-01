#!/usr/bin/env python3
"""
03_generate_gridbox.py
Hitung grid box (center + size) LANGSUNG dari koordinat ligand kristal,
lalu tulis grid.txt otomatis.

Kenapa tidak pakai autogrid4 + prepare_gpf.py seperti di tutorial asli?
- prepare_gpf.py adalah script MGLTools lawas yang butuh interpreter
  Python 2 bawaan MGLTools (pythonsh) -> rapuh untuk pipeline otomatis
  di Colab/Linux modern.
- Vina sendiri TIDAK butuh grid map AutoDock4 (npts/gridcenter itu cuma
  dipakai untuk MENENTUKAN box) -> jadi box bisa dihitung langsung dari
  bounding box atom-atom ligand referensi + padding, tanpa autogrid4
  sama sekali. Ini pendekatan yang lebih umum dipakai di pipeline docking
  modern.

Jika target riset menggunakan protein TANPA ligand ko-kristal
(mis. model AlphaFold), box tidak bisa dihitung dari ligand -> center/size
harus diisi manual di config.sh berdasarkan hasil prediksi active site
(CASTp / PocketFinder / dll).
"""
import os
import numpy as np
from Bio.PDB import PDBParser

PDB_ID = os.environ.get("PDB_ID", "4ieh")
WORKDIR = os.environ.get("WORKDIR", os.path.expanduser(f"~/docking_{PDB_ID}"))
PADDING = float(os.environ.get("BOX_PADDING", "8.0"))  # Angstrom
os.chdir(WORKDIR)

ligand_raw = f"{PDB_ID}_ligand_raw.pdb"
parser = PDBParser(QUIET=True)
structure = parser.get_structure("ligand", ligand_raw)
coords = np.array([atom.coord for atom in structure.get_atoms()])

if len(coords) == 0:
    raise RuntimeError(f"Tidak ada atom terbaca dari {ligand_raw}")

center = coords.mean(axis=0)
extent = coords.max(axis=0) - coords.min(axis=0)
size = extent + PADDING

grid_txt = (
    f"center_x = {center[0]:.3f}\n"
    f"center_y = {center[1]:.3f}\n"
    f"center_z = {center[2]:.3f}\n"
    f"size_x = {size[0]:.3f}\n"
    f"size_y = {size[1]:.3f}\n"
    f"size_z = {size[2]:.3f}\n"
)
with open("grid.txt", "w") as f:
    f.write(grid_txt)

print("grid.txt berhasil dibuat dari posisi ligand kristal:")
print(grid_txt)
