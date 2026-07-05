# Tambahan untuk `otomasi-gemastik`

File-file ini mengisi bagian yang belum ada di struktur repo kalian
(`00_setup_environment.sh` s.d. `run_all.sh`). Cara pasang: copy folder
`api_clients/` dan file-file ini ke root repo `otomasi-gemastik`.

## Yang ditambahkan & kenapa

| File | Mengisi bagian apa |
|---|---|
| `api_clients/base_client.py` | Implementasi konkret dari `BaseAPIClient` di UML kalian — session, retry, rate limit, auth pluggable |
| `api_clients/alphafold_client.py` | Fase 2 (AI Blind Spot Resolution) — query model AF2/AF3 by UniProt |
| `api_clients/rcsb_client.py` | Cek struktur eksperimental dulu sebelum fallback ke AlphaFold |
| `api_clients/pubchem_client.py` | Fase 1 (Ligand Preparation) — ambil SMILES/SDF senyawa fitokimia |
| `api_clients/chembl_client.py` | Cross-validation skor docking vs data bioaktivitas eksperimental |
| `api_clients/disgenet_client.py` | Resolusi gen-penyakit (butuh API key, lihat `.env.example`) |
| `api_clients/opentargets_client.py` | Alternatif/silang-cek DisGeNET, tidak butuh API key |
| `03b_resolve_structure.py` | Otomatisasi keputusan "pakai PDB atau fallback AF2?" — sisipkan antara `02_prepare_receptor_ligand.sh` dan `03_generate_gridbox.py` |
| `06_analyze_interactions.py` | Fase 4 (Post-Docking Analysis) via PLIP — sisipkan setelah `05_calculate_rmsd.sh` |
| `aggregate_results.py` | Gabungkan skor afinitas + RMSD + interaksi jadi satu JSON siap-pakai buat dashboard/frontend |
| `.env.example` | Template penyimpanan API key (DisGeNET, ClinPGx, OMIM) — **jangan commit `.env` asli** |
| `requirements.txt` | Dependency baru: `requests`, `plip`, `pytest`, dst |
| `tests/` | Smoke test ber-mock (tidak butuh koneksi internet) untuk `api_clients/` |
| `.gitignore_additions.txt` | Baris yang perlu ditambahkan ke `.gitignore` kalian |

## Cara pakai singkat

```bash
pip install -r requirements.txt
cp .env.example .env   # lalu isi API key kalau mau pakai DisGeNET/ClinPGx/OMIM

# Fase 2: resolusi struktur (baru)
python 03b_resolve_structure.py --uniprot Q5VSL9 --outdir ./structures

# ... (03_generate_gridbox.py, 04_run_docking.sh, 05_calculate_rmsd.sh seperti biasa) ...

# Fase 4: analisis interaksi (baru)
python 06_analyze_interactions.py --complex-dir ./docking_output --outdir ./interaction_reports

# Agregasi akhir buat dashboard (baru)
python aggregate_results.py \
    --docking-dir ./docking_output \
    --interactions-file ./interaction_reports/interaction_summary.json \
    --out ./results/final_report.json
```

## Jalankan test

```bash
python -m pytest tests/ -v
```

## Yang masih perlu keputusan manual dari kalian

- **Sekuens tanpa entri UniProt/AF2 precomputed**: `03b_resolve_structure.py`
  tidak bisa otomatis menjalankan ColabFold (butuh GPU + notebook Colab).
  Skrip hanya akan memberi instruksi kapan ini terjadi.
- **API key DisGeNET/ClinPGx/OMIM**: masing-masing butuh pendaftaran manual
  di situs resminya — tidak bisa didapat lewat kode.
- **Format ID penyakit**: `DisgenetClient` & `OpenTargetsClient` pakai skema
  ID berbeda (mis. `C0011849` vs `EFO_0000676` untuk penyakit yang sama) —
  perlu mapping manual atau tabel referensi kecil kalau mau dipakai bersamaan.
