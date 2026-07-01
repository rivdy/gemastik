# Pipeline Docking Otomatis - AutoDock Vina (Target: 4IEH)
## NOTE: Dibuat dengan bantuan Claude, sama sekali tidak final, dan masih SANGAT Kasar :D

Percobaan otomasi dari tutorial https://github.com/purnawanpp/Docking-4ieh. Semua langkah manual GUI
(Discovery Studio, AutoDockTools, Avogadro) diganti tool command-line
setara: **ADFRsuite** (`prepare_receptor`/`prepare_ligand`), **OpenBabel**,
dan **BioPython**.

## Cara pakai (Google Colab / Ubuntu Linux)

```bash
git clone <link-repo>  # atau upload folder ini
cd 4ieh_docking_pipeline
chmod +x run_all.sh
./run_all.sh
```

Atau jalankan tahap per tahap (lebih aman untuk debugging pertama kali):

```bash
./00_setup_environment.sh
python3 01_download_and_split.py
./02_prepare_receptor_ligand.sh
python3 03_generate_gridbox.py
./04_run_docking.sh
./05_calculate_rmsd.sh
```

Ganti target protein cukup edit `PDB_ID` di `config.sh`.

## Pemetaan langkah manual -> otomatis

| Langkah di tutorial asli | Tool GUI asli | Pengganti otomatis |
|---|---|---|
| Cari active site | Baca literatur/UniProt/CASTp | **Tetap manual** untuk protein baru; untuk 4IEH box dihitung dari posisi ligand ko-kristal |
| Pisah ligand & protein | Discovery Studio | `01_download_and_split.py` (BioPython) |
| Preparasi protein (H, gasteiger, merge nonpolar) | AutoDockTools GUI | `prepare_receptor` (ADFRsuite) di `02_prepare_receptor_ligand.sh` |
| Preparasi ligand | AutoDockTools GUI | `obabel` + `prepare_ligand` (ADFRsuite) |
| Tentukan grid box | AutoGrid4 + edit `.gpf` manual di Notepad | `03_generate_gridbox.py` - dihitung langsung dari bounding box ligand kristal + padding |
| Docking | Vina CLI (sudah CLI) | `04_run_docking.sh` |
| Split hasil docking | vina_split (sudah CLI) | termasuk di `04_run_docking.sh` |
| RMSD | Discovery Studio / `obrms` | `05_calculate_rmsd.sh` (`obrms`) |
| Optimasi geometri ligand (screening senyawa makanan) | Avogadro GUI | `utils/smiles_to_pdbqt.py` (OpenBabel `--gen3d --minimize`) |

## Kenapa grid box dihitung dari ligand, bukan autogrid4?

Tutorial asli pakai `prepare_gpf.py` + `autogrid4` untuk dapat nilai
`npts`/`gridcenter`. Masalahnya, `prepare_gpf.py` adalah script MGLTools
lawas yang butuh interpreter Python 2 bawaan MGLTools (`pythonsh`) -
rapuh untuk pipeline otomatis di Linux/Colab modern. Karena Vina sendiri
tidak butuh grid map AutoDock4 (cukup center + size box), grid box di
pipeline ini dihitung langsung dari koordinat atom ligand ko-kristal
(centroid + bounding box + padding). Lebih robust dan tidak butuh
dependency legacy.

**Batasan:** pendekatan ini hanya berlaku kalau protein target punya
ligand ko-kristal (seperti 4IEH). Untuk protein hasil prediksi AlphaFold
(tanpa ligand referensi) atau protein `apo` tanpa ligand terikat, box
harus ditentukan manual dari hasil prediksi active site (CASTp/PocketFinder/
UniProt) dan diisi langsung ke `grid.txt`, atau modifikasi
`03_generate_gridbox.py` untuk baca koordinat manual dari `config.sh`.

## Struktur file

```
config.sh                       # semua parameter (PDB ID, path, dll)
00_setup_environment.sh         # install vina, ADFRsuite, openbabel, biopython
01_download_and_split.py        # download RCSB + pisah protein/ligand
02_prepare_receptor_ligand.sh   # -> protein.pdbqt, ligand.pdbqt
03_generate_gridbox.py          # -> grid.txt
04_run_docking.sh               # jalankan vina + vina_split
05_calculate_rmsd.sh            # hitung RMSD vs ligand referensi
run_all.sh                      # jalankan semua tahap berurutan
utils/smiles_to_pdbqt.py        # bonus: SMILES -> pdbqt untuk screening senyawa makanan
```
