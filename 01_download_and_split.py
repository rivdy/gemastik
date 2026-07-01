#!/usr/bin/env python3
"""
01_download_and_split.py
Download struktur dari RCSB PDB, lalu pisahkan protein & ligand secara
otomatis (pengganti langkah manual "Separation of ligand and protein"
yang di tutorial asli pakai Biovia Discovery Studio).

Ligand utama dideteksi otomatis sebagai residu HETATM (non-air, non-ion
umum) dengan jumlah atom terbanyak. Kalau protein punya banyak
ligand/kofaktor dan mau pilih spesifik, isi LIGAND_RESNAME di config.sh
(pakai kode 3-huruf ligand, misal "STI").
"""
import os
from Bio.PDB import PDBList, PDBParser, PDBIO, Select

PDB_ID = os.environ.get("PDB_ID", "4ieh").lower()
WORKDIR = os.environ.get("WORKDIR", os.path.expanduser(f"~/docking_{PDB_ID}"))
LIGAND_RESNAME = os.environ.get("LIGAND_RESNAME", "").strip().upper()

os.makedirs(WORKDIR, exist_ok=True)
os.chdir(WORKDIR)

WATER_NAMES = {"HOH", "WAT", "H2O"}
COMMON_IONS_OR_ADDITIVES = {
    "NA", "CL", "MG", "ZN", "CA", "K", "MN", "FE", "SO4", "PO4", "GOL", "EDO", "DMS"
}


def download_structure():
    print(f"[1/3] Download {PDB_ID.upper()} dari RCSB PDB...")
    pdbl = PDBList()
    fetched = pdbl.retrieve_pdb_file(PDB_ID, pdir=WORKDIR, file_format="pdb")
    raw_pdb = os.path.join(WORKDIR, f"{PDB_ID}.pdb")
    os.replace(fetched, raw_pdb)
    print(f"    -> {raw_pdb}")
    return raw_pdb


def detect_ligand(structure):
    candidates = {}
    for model in structure:
        for chain in model:
            for residue in chain:
                hetflag = residue.id[0]
                resname = residue.resname.strip()
                is_hetero = hetflag != " "
                if not is_hetero:
                    continue
                if resname in WATER_NAMES or resname in COMMON_IONS_OR_ADDITIVES:
                    continue
                key = (chain.id, residue.id, resname)
                candidates[key] = len(list(residue.get_atoms()))
        break  # hanya model pertama (cukup untuk kristal struktur biasa)

    if not candidates:
        raise RuntimeError(
            "Tidak ada kandidat ligand (HETATM non-air/ion) yang ditemukan.\n"
            "Set LIGAND_RESNAME manual di config.sh kalau ligand termasuk\n"
            "residu yang ter-filter di atas (mis. ligand berbasis ion logam)."
        )
    best = max(candidates, key=candidates.get)
    print(f"    -> Ligand terdeteksi otomatis: {best[2]} "
          f"(chain {best[0]}, residu {best[1]}, {candidates[best]} atom)")
    return best


def strip_alt_locations(pdb_path):
    """
    Bersihkan alternate location (altLoc A/B/dst) dari file PDB.
    Struktur kristal sering punya beberapa conformer untuk residu yang sama
    (mis. rantai samping fleksibel) -> kalau dibiarkan, ADFR prepare_receptor
    bisa salah parsing kolom fixed-width PDB dan menghasilkan PDBQT korup.
    Strategi: untuk tiap atom, pilih satu altLoc (utamakan 'A', kalau tidak
    ada pakai altLoc pertama yang muncul), lalu kosongkan kolom altLoc-nya.
    """
    with open(pdb_path) as f:
        lines = f.readlines()

    preferred = {}
    for line in lines:
        if line.startswith(("ATOM", "HETATM")) and len(line) > 26:
            altloc = line[16]
            if altloc == " ":
                continue
            key = (line[21], line[22:26], line[26], line[12:16])  # chain, resseq, icode, atom name
            if key not in preferred or altloc == "A":
                preferred[key] = "A" if altloc == "A" else preferred.get(key, altloc)

    cleaned = []
    removed = 0
    for line in lines:
        if line.startswith(("ATOM", "HETATM")) and len(line) > 26:
            altloc = line[16]
            if altloc != " ":
                key = (line[21], line[22:26], line[26], line[12:16])
                if altloc != preferred.get(key, "A"):
                    removed += 1
                    continue  # buang conformer yang tidak dipilih
                line = line[:16] + " " + line[17:]  # kosongkan kolom altLoc
        cleaned.append(line)

    with open(pdb_path, "w") as f:
        f.writelines(cleaned)

    if removed:
        print(f"    -> Dibersihkan {removed} baris alternate-location dari {os.path.basename(pdb_path)}")



class ProteinSelect(Select):
    """Simpan hanya rantai polimer standar (buang semua HETATM: air, ligand, ion)."""
    def accept_residue(self, residue):
        return residue.id[0] == " "


class LigandSelect(Select):
    def __init__(self, chain_id, res_id):
        self.chain_id = chain_id
        self.res_id = res_id

    def accept_residue(self, residue):
        return residue.get_parent().id == self.chain_id and residue.id == self.res_id


def split_structure(raw_pdb):
    print("[2/3] Parsing & memisahkan protein vs ligand...")
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure(PDB_ID, raw_pdb)

    io = PDBIO()
    io.set_structure(structure)

    protein_out = os.path.join(WORKDIR, f"{PDB_ID}_protein_raw.pdb")
    io.save(protein_out, ProteinSelect())
    strip_alt_locations(protein_out)
    print(f"    -> Protein: {protein_out}")

    if LIGAND_RESNAME:
        chain_id = res_id = None
        for model in structure:
            for chain in model:
                for residue in chain:
                    if residue.resname.strip() == LIGAND_RESNAME:
                        chain_id, res_id = chain.id, residue.id
            break
        if chain_id is None:
            raise RuntimeError(f"LIGAND_RESNAME={LIGAND_RESNAME} tidak ditemukan di struktur.")
    else:
        chain_id, res_id, _ = detect_ligand(structure)

    ligand_out = os.path.join(WORKDIR, f"{PDB_ID}_ligand_raw.pdb")
    io.save(ligand_out, LigandSelect(chain_id, res_id))
    strip_alt_locations(ligand_out)
    print(f"    -> Ligand: {ligand_out}")
    return protein_out, ligand_out


if __name__ == "__main__":
    raw_pdb = download_structure()
    protein_out, ligand_out = split_structure(raw_pdb)
    print("[3/3] Selesai. Lanjut ke 02_prepare_receptor_ligand.sh")
