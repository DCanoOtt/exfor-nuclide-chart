# EXFOR nuclide chart

An interactive chart of the nuclides (Z–N plane) that shows, for every target nuclide, **how much neutron-induced
data exist in the EXFOR library**: number of data sets, data points, resonance-parameter data sets (RP), time-of-flight
(TOF) measurements, with filters for reaction, quantity, energy range, number of points, publication year and more.
Click a nuclide to see its data sets and the list of references.

**Live page:** `https://<your-user>.github.io/<your-repo>/` (after you deploy it, see [Deployment](#deployment))

The page is **one self-contained HTML file** (`docs/index.html`). All numbers are computed once from the EXFOR master
files when the page is built and embedded in it, so the page needs **no server, no database and no internet
connection**: you can also download it and open it from disk.

## Contents

1. [Quick start](#quick-start)
2. [What the chart shows and how it is counted](#what-the-chart-shows-and-how-it-is-counted)
3. [Rebuilding the page with new EXFOR data](#rebuilding-the-page-with-new-exfor-data)
4. [Deployment (GitHub Pages)](#deployment)
5. [Automatic update when a new EXFOR release appears](#automatic-update)
6. [Repository layout](#repository-layout)
7. [Tests](#tests)
8. [Limitations](#limitations)
9. [Troubleshooting](#troubleshooting)
10. [Licence, data licence and how to cite](#licence-data-licence-and-how-to-cite)

More detail: [guides/USER_GUIDE.md](guides/USER_GUIDE.md) (using the page) and
[guides/MAINTAINER_GUIDE.md](guides/MAINTAINER_GUIDE.md) (building, updating, publishing, rules in detail).

## Quick start

**Just use it.** Open the live page, or download `docs/index.html` and open it in any recent browser
(Chrome, Firefox, Edge, Safari). The "Instructions" button inside the page explains every control.

**Build it yourself** (needs Python ≥ 3.8 and git; no other packages):

```bash
git clone https://github.com/<your-user>/<your-repo>.git
cd <your-repo>
python build_nuclide_chart.py --download      # clones the EXFOR master files (~1 GB) and builds docs/index.html
```

Open `docs/index.html`. A build takes a few minutes (it scans ~27,000 master files, using all CPU cores).
Later builds with new data: run the same command again; it updates the local copy of the master files.

If you already have the EXFOR master files:

```bash
python build_nuclide_chart.py --master /path/to/exfor_master
```

Is there newer data? `python build_nuclide_chart.py --check-remote` (exit code 10 = yes, 0 = up to date).

## What the chart shows and how it is counted

* **Data set** = one `REACTION` record with a `DATA` table in an EXFOR subentry, for a **neutron** projectile and a
  **simple (single-term) reaction** on a **nuclide** target. Natural targets (A = 0), sums, ratios and other complex
  reactions are not counted.
* **SIG** = cross section; **RP** = resonance parameters (energies, widths, J, l, ...). RP is *not* a single EXFOR
  code: a data set is RP if its quantity is one of `WID, GAM, GN, GG, GF, GNG, J, L, JL, KRM, RES` (also `/`
  variants such as `WID/RED`), or an `EN` column of a resonance-parameter reaction. D, STF, RI and SIF are *not* RP.
  The page can select SIG, RP, SIG+RP, other combinations, or any EXFOR quantity code.
* **TOF** = the subentry (or entry) declares a time-of-flight method (`METHOD` keyword).
* **Energy** is converted to MeV (log scale in the filters). Data sets without an incident-energy column have no
  energy range and are excluded when an energy range is selected.
* **Year** is the publication year read from the main `REFERENCE` (a few entries have none).
* **Dashed squares** mark radioactive nuclides, using a list of the 252 stable nuclides built into the page
  (Bi-209, Th-232, U-235 and U-238 are treated as radioactive).

The exact rules are in [guides/MAINTAINER_GUIDE.md](guides/MAINTAINER_GUIDE.md).

## Rebuilding the page with new EXFOR data

The IAEA-NDS publishes the master files in the repository
[IAEA-NDS/exfor_master](https://github.com/IAEA-NDS/exfor_master); it changes several times a year. To rebuild:

```bash
python build_nuclide_chart.py --download    # updates exfor_master/ (shallow clone, fast after the first time)
git add docs && git commit -m "Rebuild with new EXFOR data" && git push
```

The build also writes `docs/data-version.json` (EXFOR commit, date, counts). The page footer shows the EXFOR
version it was built from, so users always know which data they are looking at.

## Deployment

One-time set-up on GitHub (about 5 minutes):

1. Create a repository and push this folder to it (`git init`, `git add .`, `git commit`, `git remote add origin ...`, `git push -u origin main`).
2. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
3. Open the **Actions** tab, run **Deploy page** once (or push any change under `docs/`).
4. The address appears in the run summary: `https://<your-user>.github.io/<your-repo>/`.
5. Optional: edit the project address shown in the page footer (`DEFAULT_PROJECT_URL` in `build_nuclide_chart.py`,
   or `--project-url`), rebuild, push.

Alternative without Actions: **Settings → Pages → Source: Deploy from a branch → `main` / `docs`**
(and delete `.github/workflows/pages.yml`). `docs/.nojekyll` is already there.

## Automatic update

`.github/workflows/update-data.yml` runs every Monday (and on demand). It compares the commit in
`docs/data-version.json` with the current IAEA `exfor_master`; **only if they differ** does it download the data
(~1 GB, a few minutes), run the tests, rebuild `docs/`, commit, and start the **Deploy page** workflow.

One-time set-up: **Settings → Actions → General → Workflow permissions → Read and write permissions.**
To force a rebuild: **Actions → Update EXFOR data → Run workflow → force = true.**
If you do not want this, delete the file; the manual route above always works.

## Repository layout

```
build_nuclide_chart.py   builds the page from the EXFOR master files (also --check-remote)
exfor_retrieve.py        EXFOR parsing helpers used by the builder
template.html            the page itself (HTML/CSS/JS) with placeholders for the data
docs/index.html          the finished page (what GitHub Pages serves)
docs/data-version.json   which EXFOR release it was built from, and counts
guides/                  USER_GUIDE.md, MAINTAINER_GUIDE.md
tests/                   test_build.py and one small real EXFOR entry
.github/workflows/       pages.yml (deploy), update-data.yml (rebuild on new EXFOR data)
LICENSE                  code licence (MIT); the data have their own, see below
```

## Tests

```bash
python tests/test_build.py
```

Checks the parsing rules, a full build on one real entry (Pu-239), and that the published page makes no external
requests and contains no private paths.

## Limitations

* Counts are of **data sets in EXFOR**, not of independent measurements: one paper can give several data sets.
* The page reflects the master files, which lag behind new EXFOR entries by weeks.
* Complex reactions, natural targets and non-neutron projectiles are left out on purpose.
* The stable-nuclide list used for the dashed pattern is fixed in the page (not read from a half-life database).
* Quantity names are EXFOR codes as written in the entries; some are used inconsistently by compilers.
* Always check important results in the original EXFOR entry; the page lists entry numbers and subentries.

## Troubleshooting

| Problem | Cause / solution |
|---|---|
| `ERROR: exfor_master/exforall not found` | Use `--download` or `--master FOLDER` pointing to the folder that contains `exforall/`. |
| `git: command not found` | Install git, or download the master files manually (Code → Download ZIP on the IAEA repository) and use `--master`. |
| Build is slow | The first scan of ~27,000 files takes minutes; `--workers N` changes the number of processes. |
| "Save image" does nothing / asks for permission | Allow downloads for the page in your browser; the image is a normal file download. |
| Page opens but is empty | Open the browser console (F12); a very old browser lacking modern JavaScript is the usual cause. |
| Workflow cannot push | Set **Workflow permissions** to *Read and write* (see above). |
| Pages not published | Check **Settings → Pages → Source = GitHub Actions** and that **Deploy page** ran successfully. |
| Numbers differ from my own count | See [What the chart shows](#what-the-chart-shows-and-how-it-is-counted); the rules are explicit and strict. |

## Licence, data licence and how to cite

* **Code** (this repository): MIT, see [LICENSE](LICENSE). *(Copyright holder to be filled in.)*
* **EXFOR data** embedded in `docs/index.html`: IAEA Nuclear Data Section,
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). You may use and redistribute them with attribution.
  The page footer already carries the attribution and the version.

When you use the chart or its numbers, please cite EXFOR — N. Otuka et al., "Towards a More Complete and Accurate Experimental Nuclear Reaction Data Library (EXFOR): International Collaboration Between Nuclear Reaction Data Centres (NRDC)", *Nuclear Data Sheets* **120** (2014) 272 (the form recommended by the [IAEA Nuclear Reaction Data Centres](https://nds.iaea.org/nrdc/about/citation-exfor.html); note the spelling *Otuka*) —
and state the EXFOR version shown in the page footer (for example "EXFOR master files of 2026-09-28"), plus this
repository.
