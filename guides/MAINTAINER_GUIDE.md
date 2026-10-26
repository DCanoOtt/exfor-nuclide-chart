# Maintainer guide — building, updating and publishing

## 1. Requirements
Python ≥ 3.8 (standard library only), git. ~2 GB disk for the master files, a few minutes of CPU.

## 2. First-time set-up
```bash
git clone https://github.com/<you>/<repo>.git && cd <repo>
python tests/test_build.py                       # should print OK
python build_nuclide_chart.py --download         # clone IAEA exfor_master (shallow) and build docs/index.html
```
`exfor_master/` is in `.gitignore`; never commit it.

Command-line options of `build_nuclide_chart.py`:

| Option | Meaning |
|---|---|
| `--master DIR` | master-file folder (default `./exfor_master`; must contain `exforall/`) |
| `--download` | clone or update `--master` before building |
| `--out FILE` | output page (default `docs/index.html`); `data-version.json` is written next to it |
| `--template FILE` | page template (default `template.html`) |
| `--workers N` | parallel processes |
| `--project-url URL` | address shown in the footer (also `DEFAULT_PROJECT_URL` in the script) |
| `--check-remote` | no build; exit 0 = up to date, 10 = newer IAEA data exist, 2 = error |

## 3. Updating when a new EXFOR release appears
**By hand:** `python build_nuclide_chart.py --check-remote`; if it says NEW DATA AVAILABLE run
`python build_nuclide_chart.py --download`, check the counts printed (they normally grow slowly), then
`git add docs && git commit && git push`.

**Automatic:** `.github/workflows/update-data.yml` does exactly this every Monday. Settings required: Workflow
permissions = *Read and write*. The workflow is skipped quickly when nothing changed. After committing it starts
**Deploy page** itself (a push made with the default token does not trigger other workflows).

## 4. Publishing
Settings → Pages → Source = **GitHub Actions**; run **Deploy page** once. See README for the alternative branch/docs route.

## 5. Changing the page
Edit `template.html` (plain HTML/CSS/JS; the placeholders `__DATA__`, `__QLIST__`, `__ENTS__`, `__MDATE__`,
`__BUILDINFO__`, `__PROJECT_URL__` are replaced by the builder), rebuild with the existing master files, open
`docs/index.html`, run the tests. The page must stay free of external resources (fonts, scripts, images), so that it
works offline; the test checks this.

## 6. Counting rules (as implemented in the builder)
* Only `*.x4` files in `exforall/`; projectile neutron; single-term REACTION `(Z-SYM-A(n,X)Y,…)`; target A ≠ 0.
* A data set needs a `DATA` table; points = rows of the table.
* Flags: 1 TOF (METHOD keyword in the subentry, or in subentry 1 for the whole entry), 2 SIG (quantity `SIG`),
  4 RP (see README). Flags add up (3 = TOF + SIG).
* Energy: first available column among `EN`, `EN-MIN/MAX/MEAN/CM/APRX`, `EN-RES(-MIN/MAX)`, `COMMON` energies, or the
  `EN` column next to the quantity column in resonance-parameter tables; EXFOR numbers such as `1.5-3` or
  `1.003  -01` are interpreted; units converted to MeV with `exfor_retrieve.convert_energy`; values outside
  1e-14…1e5 MeV are ignored. Stored as `round(log10(E/MeV)*1000)`.
* Year: from the main REFERENCE (patterns YYYY, YYMM, YYYYMM, YYYYMMDD, two digits), range 1930…current year + 1.
* Output rows: `[Z, A, process, [[points, flags, entryIdx, quantityIdx, logEmin, logEmax, subentry], …]]`.

## 7. Known assumptions to re-check from time to time
* Layout of the IAEA repository (`exforall/NNN/NNNNN.x4`) and its URL.
* The list of stable nuclides in the template (fixed, from the nuclear-physics literature).
* The citation text in the footer (checked on 2026-10-26 against https://nds.iaea.org/nrdc/about/citation-exfor.html: N. Otuka et al., Nucl. Data Sheets 120 (2014) 272).

## 8. Releases
Tag releases (`git tag v1.1`); the data version is always in `docs/data-version.json`.
