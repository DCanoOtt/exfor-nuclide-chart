#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_nuclide_chart.py  -  build the EXFOR nuclide chart (one self-contained HTML page)

The page (template.html) shows, for every target nuclide, how many EXFOR data sets exist for neutron-induced
reactions, with filters for reaction, quantity, method, energy, publication year and so on.  All numbers are
computed HERE, once, from the EXFOR master files, and embedded in the page: the finished page needs no server and
no connection to EXFOR.

Usage
-----
    python build_nuclide_chart.py                      # uses ./exfor_master, writes docs/index.html
    python build_nuclide_chart.py --download           # first clone the EXFOR master files (needs git)
    python build_nuclide_chart.py --master /path/to/exfor_master --out docs/index.html
    python build_nuclide_chart.py --check-remote       # is a newer exfor_master available? (exit code 10 = yes)

The EXFOR master files are the IAEA-NDS repository https://github.com/IAEA-NDS/exfor_master (licence CC BY 4.0).
Only the Python standard library is needed, plus git for --download / --check-remote.
exfor_retrieve.py (next to this file) supplies the EXFOR parsing helpers.

What is counted
---------------
One data set = one REACTION record with a DATA table, in a subentry of an EXFOR entry, for a neutron projectile
and a simple (single-term) reaction on a nuclide target (natural targets, A = 0, are skipped; sums, ratios and
other complex reactions are skipped).  For every data set the page keeps: number of points, flags (1 = time of
flight, 2 = cross section SIG, 4 = resonance parameters RP), entry, quantity code, lowest and highest incident
energy (log10 MeV x 1000, null if EXFOR gives none) and subentry number.  Per entry it keeps the first author,
year, citation and title of the main reference.  See guides/MAINTAINER_GUIDE.md for the rules in detail.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import exfor_retrieve as X          # noqa: E402  (parsing helpers: RX, parse_table, convert_energy, ...)

__version__ = "1.0"
REPO_URL = "https://github.com/IAEA-NDS/exfor_master.git"
DEFAULT_PROJECT_URL = "https://github.com/OWNER/exfor-nuclide-chart"   # replace, or use --project-url

# --------------------------------------------------------------------------
# classification rules (change here, then rebuild)
# --------------------------------------------------------------------------
# Resonance parameters (RP): widths, spins, orbital momenta ... and resonance energies filed under (n,0).
RP_CODES = re.compile(r"^(WID|GAM|GN|GG|GF|GNG|J|L|JL|KRM|RES)(/|$)")
TOF = re.compile(r"\bTOF\b")
# columns holding the incident neutron energy
ENERGY_COLUMNS = ("EN", "EN-MIN", "EN-MAX", "EN-MEAN", "EN-CM", "EN-APRX", "EN-RES", "EN-RES-MIN", "EN-RES-MAX")
E_MIN_MEV, E_MAX_MEV = 1e-14, 1e5          # energies outside are treated as errors of the source
YEAR_MIN, YEAR_MAX = 1930, date.today().year + 1


def is_rp(process, quantity):
    return bool(RP_CODES.match(quantity)) or (quantity == "EN" and process == "0")


_NUM = re.compile(r"^([+-]?\d*\.?\d+)([+-]\d+)$")


def exfor_number(text):
    """EXFOR numbers: '1.5-3' means 1.5e-3, and blanks inside the number are allowed ('1.003  -01')."""
    text = re.sub(r"\s+", "", text)
    if not text:
        return None
    m = _NUM.match(text)
    try:
        return float(m.group(1) + "e" + m.group(2)) if m else float(text)
    except ValueError:
        return None


def energies_mev(cols, units, rows, quantity, k=0):
    """All incident-neutron energies of a table, in MeV."""
    idx = [i for i, (name, _) in enumerate(cols) if name in ENERGY_COLUMNS]
    if not idx and quantity == "EN":
        # resonance energies: the DATA column itself; k = position of this reaction among the DATA columns
        data_cols = [i for i, (name, _) in enumerate(cols) if name == "DATA"]
        idx = data_cols[k:k + 1] if len(data_cols) > k else []
    out = []
    for i in idx:
        unit = units[i] if i < len(units) else ""
        for row in rows:
            v = exfor_number(row[i]) if i < len(row) else None
            if v is None or v <= 0:
                continue
            e, _, status = X.convert_energy(v, unit, 1, True)
            if e and status == "ok" and E_MIN_MEV < e < E_MAX_MEV:
                out.append(e)
    return out


def log_e(e_mev):
    return int(round(math.log10(e_mev) * 1000))


def keyword_block(lines, i):
    """Text of a BIB keyword with its continuation lines, and the index of the first line after it."""
    j = i + 1
    while j < len(lines) and lines[j].startswith("           "):
        j += 1
    return " ".join(l[10:66] for l in lines[i:j]), j


# --------------------------------------------------------------------------
# scan one master file (one EXFOR entry)
# --------------------------------------------------------------------------
def scan_file(path):
    try:
        raw = open(path, "rb").read()
    except OSError:
        return None
    if b"(N," not in raw:
        return None
    L = raw.decode("latin-1").splitlines()
    out = {}
    entry = None
    sub_idx = 0
    cur_sub = 0
    tof_entry = tof_sub = False          # METHOD with TOF in the first subentry (whole entry) or in this subentry
    matches = []
    common_entry, common_sub = [], []
    i = 0
    while i < len(L):
        l = L[i]
        if l.startswith("ENTRY"):
            entry = l.split()[1]
        elif l.startswith("SUBENT"):
            sub_idx += 1
            tof_sub = False
            matches = []
            common_sub = []
            tail = l.split()[1][-3:]
            cur_sub = int(tail) if tail.isdigit() else 0
        elif l.startswith("METHOD"):
            text, j = keyword_block(L, i)
            if TOF.search(text):
                if sub_idx == 1:
                    tof_entry = True
                else:
                    tof_sub = True
            i = j
            continue
        elif l.startswith("REACTION"):
            text, j = keyword_block(L, i)
            text = " ".join(x.strip() for x in text.split("\n"))
            n_terms = max(len(X.RX.findall(text)), len(X.RX_TERM.findall(text)))
            if n_terms == 1:                                    # a simple, single-term reaction
                for tgt, proj, proc, _prod, rest in X.RX.findall(text):
                    if X.canon_code(proj) != "N":
                        continue
                    parts = (rest.split(",")[1:] if rest else []) + ["", ""]
                    matches.append((tgt, proc.upper(), parts[1]))
            i = j
            continue
        elif l.startswith("COMMON") and len(l.split()) >= 3 and l.split()[1].isdigit():
            j = i + 1
            while j < len(L) and not L[j].startswith("ENDCOMMON"):
                j += 1
            try:
                c, u, r = X.parse_table(L[i + 1:j], int(l.split()[1]))
                ev = energies_mev(c, u, r, "")
            except Exception:
                ev = []
            if sub_idx == 1:
                common_entry = ev
            else:
                common_sub = ev
            i = j
        elif l.startswith("DATA ") and matches and sub_idx > 1:
            tok = l.split()
            n_points = int(tok[2]) if len(tok) > 2 and tok[2].isdigit() else 0
            n_cols = int(tok[1]) if tok[1].isdigit() else 0
            j = i + 1
            while j < len(L) and not L[j].startswith("ENDDATA"):
                j += 1
            try:
                cols, units, rows = X.parse_table(L[i + 1:j], n_cols)
            except Exception:
                cols, units, rows = [], [], []
            is_tof = tof_sub or tof_entry
            # resonance widths etc. take the energy of the sibling EN item of the same table
            sibling = None
            for k, (_t, _p, q) in enumerate(matches):
                if q == "EN":
                    sibling = energies_mev(cols, units, rows, "EN", k) or None
                    break
            for k, (tgt, proc, q) in enumerate(matches):
                ev = (energies_mev(cols, units, rows, q, k) or (sibling if q != "EN" else None)
                      or common_sub or common_entry)
                flags = (1 if is_tof else 0) | (2 if q == "SIG" else 0) | (4 if is_rp(proc, q) else 0)
                out.setdefault((tgt, proc), []).append(
                    [n_points, flags, entry, q, log_e(min(ev)) if ev else None, log_e(max(ev)) if ev else None, cur_sub])
            matches = []
            i = j
        i += 1
    return out or None


# --------------------------------------------------------------------------
# entry information: first author, year, citation, title
# --------------------------------------------------------------------------
def year_from_token(tok):
    """EXFOR dates: YYYY, YYMM, YYYYMM, YYYYMMDD."""
    n = int(tok)
    if len(tok) >= 8:
        y = int(tok[:4])
    elif len(tok) == 6:
        y = int(tok[:4])
        if not YEAR_MIN <= y <= YEAR_MAX:
            yy = int(tok[:2])
            y = 1900 + yy if yy >= 30 else 2000 + yy
    elif len(tok) == 4:
        y = n
        if not YEAR_MIN <= y <= YEAR_MAX:
            yy, mm = int(tok[:2]), int(tok[2:])
            if not 1 <= mm <= 12:
                return None
            y = 1900 + yy if yy >= 30 else 2000 + yy
    elif len(tok) == 2:                                      # two-digit year at the end of a reference code
        y = 1900 + n if n >= 30 else 2000 + n
    else:
        return None
    return y if YEAR_MIN <= y <= YEAR_MAX else None


def year_of(reference_text):
    for pat in (r",\s*(\d{4,8})\s*\)", r"[,\s](\d{4,8})\s*$", r"\b((?:19|20)\d{2})\b", r",\s*(\d{2})\s*\)"):
        for m in re.finditer(pat, reference_text):
            y = year_from_token(m.group(1))
            if y:
                return y
    return None


def entry_info(master, eid):
    path = master / "exforall" / eid[:3] / (eid + ".x4")
    try:
        _, subs = X.parse_entry(path)
        bib = subs[0]["bib"]
    except Exception:
        return [eid, "", "", "", ""]

    def first(key):
        v = bib.get(key)
        return v[0]["text"] if v else ""

    authors = [x.strip() for x in re.split(r"\s*,\s*", first("AUTHOR").strip("() ")) if x.strip()]
    first_author = (X.pretty_name(authors[0]) if authors else "") + (" et al." if len(authors) > 1 else "")
    ref = first("REFERENCE")
    citation = X.parse_reference(ref)["text"] if ref else ""
    y = year_of(ref) or year_of(citation)
    year = str(y) if y else ""
    m = re.search(r"\((\d{4})\)", citation)                 # repair a wrong year inside the citation text
    if m and year and m.group(1) != year and not YEAR_MIN <= int(m.group(1)) <= YEAR_MAX:
        citation = citation[:m.start()] + "(" + year + ")" + citation[m.end():]
    return [eid, first_author, year, citation, first("TITLE")]


# --------------------------------------------------------------------------
# master-file metadata and remote check
# --------------------------------------------------------------------------
def git(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=600)


def master_info(master):
    """Commit and date of the local copy of the master files (from git; else the newest date in entry_updatedate.dat)."""
    info = {"commit": "", "date": ""}
    if (master / ".git").exists():
        r = git("log", "-1", "--format=%H|%cI", cwd=master)
        if r.returncode == 0 and "|" in r.stdout:
            info["commit"], d = r.stdout.strip().split("|", 1)
            info["date"] = d[:10]
    if not info["date"]:
        f = master / "entry_updatedate.dat"
        if f.exists():
            ds = re.findall(r"\b(\d{4}-\d{2}-\d{2})", f.read_text(errors="replace"))
            info["date"] = max(ds) if ds else ""
    info["date"] = info["date"] or date.today().isoformat()
    return info


def remote_head():
    r = git("ls-remote", REPO_URL, "HEAD")
    if r.returncode != 0 or not r.stdout.split():
        raise RuntimeError("git ls-remote failed: " + (r.stderr.strip() or "no output"))
    return r.stdout.split()[0]


def download(master):
    """Shallow clone (or update) of the EXFOR master files."""
    if (master / ".git").exists():
        print("Updating", master, "...", file=sys.stderr)
        for cmd in (["fetch", "--depth", "1", "origin", "HEAD"], ["reset", "--hard", "FETCH_HEAD"]):
            r = git(*cmd, cwd=master)
            if r.returncode != 0:
                raise RuntimeError("git %s failed: %s" % (cmd[0], r.stderr.strip()))
    else:
        print("Cloning the EXFOR master files into", master, "(about 1 GB) ...", file=sys.stderr)
        r = git("clone", "--depth", "1", REPO_URL, str(master))
        if r.returncode != 0:
            raise RuntimeError("git clone failed: " + r.stderr.strip())


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Build the EXFOR nuclide chart (one self-contained HTML page).")
    ap.add_argument("--master", default="exfor_master", help="folder of the EXFOR master files (default ./exfor_master)")
    ap.add_argument("--download", action="store_true", help="clone the master files (or update them) before building")
    ap.add_argument("--template", default=str(HERE / "template.html"), help="HTML template (default template.html)")
    ap.add_argument("--out", default=str(HERE / "docs" / "index.html"), help="output page (default docs/index.html)")
    ap.add_argument("--version-file", default=None,
                    help="JSON file describing the data used (default: data-version.json next to --out)")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2, help="parallel processes (default: all cores)")
    ap.add_argument("--project-url", default=DEFAULT_PROJECT_URL, help="project web address shown in the page")
    ap.add_argument("--check-remote", action="store_true",
                    help="only compare the commit in the version file with the remote exfor_master; exit 10 if new data "
                         "are available, 0 if up to date, 2 on error")
    args = ap.parse_args()

    out = Path(args.out)
    vfile = Path(args.version_file) if args.version_file else out.parent / "data-version.json"

    if args.check_remote:
        try:
            remote = remote_head()
        except Exception as e:
            print("ERROR:", e, file=sys.stderr)
            return 2
        have = json.loads(vfile.read_text()).get("commit", "") if vfile.exists() else ""
        print("remote", remote, "| built from", have or "(none)")
        if remote != have:
            print("NEW DATA AVAILABLE")
            return 10
        print("up to date")
        return 0

    master = Path(args.master)
    if args.download:
        download(master)
    if not (master / "exforall").is_dir():
        print("ERROR: %s/exforall not found. Use --download or --master FOLDER (see README.md)." % master, file=sys.stderr)
        return 2

    t0 = time.time()
    files = sorted(str(p) for p in (master / "exforall").rglob("*.x4"))
    print("Scanning %d master files with %d processes ..." % (len(files), args.workers), file=sys.stderr)
    agg = {}
    with ProcessPoolExecutor(args.workers) as ex:
        for res in ex.map(scan_file, files, chunksize=100):
            for key, lst in (res or {}).items():
                agg.setdefault(key, []).extend(lst)

    entries, quantities, rows = {}, {}, []
    for (tgt, proc), lst in sorted(agg.items()):
        z, _sym, a = tgt.split("-")[:3]
        if not a.isdigit() or int(a) == 0:                       # natural targets cannot be put on a chart of nuclides
            continue
        rows.append([int(z), int(a), proc,
                     [[p, f, entries.setdefault(e, len(entries)), quantities.setdefault(q, len(quantities)), lo, hi, sb]
                      for p, f, e, q, lo, hi, sb in lst]])
    names = sorted(quantities, key=quantities.get)
    counts = [0] * len(names)
    for r in rows:
        for d in r[3]:
            counts[d[3]] += 1
    ents = [None] * len(entries)
    for eid, i in entries.items():
        ents[i] = entry_info(master, eid)

    info = master_info(master)
    n_sets = sum(len(r[3]) for r in rows)
    nuclides = len({(r[0], r[1]) for r in rows})
    version = {"source": "https://github.com/IAEA-NDS/exfor_master", "commit": info["commit"], "data_date": info["date"],
               "built": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "builder": "build_nuclide_chart.py " + __version__,
               "nuclides": nuclides, "data_sets": n_sets, "entries": len(ents)}

    def js(obj):
        return json.dumps(obj, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")

    html = Path(args.template).read_text(encoding="utf-8")
    build_info = "EXFOR master files of %s (exfor_master commit %s), page built %s with build_nuclide_chart.py %s." % (
        info["date"], (info["commit"] or "unknown")[:10], version["built"], __version__)
    for key, val in (("__DATA__", js(rows)), ("__QLIST__", js({"names": names, "counts": counts})), ("__ENTS__", js(ents)),
                     ("__MDATE__", info["date"]), ("__BUILDINFO__", build_info), ("__PROJECT_URL__", args.project_url)):
        if key not in html:
            print("WARNING: placeholder %s not found in the template" % key, file=sys.stderr)
        html = html.replace(key, val)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    vfile.write_text(json.dumps(version, indent=2) + "\n")
    print("Wrote %s (%.1f MB): %d nuclides, %d data sets, %d entries, %d quantity codes; %.0f s" % (
        out, out.stat().st_size / 1e6, nuclides, n_sets, len(ents), len(names), time.time() - t0))
    print("Data: EXFOR master files of", info["date"], "commit", info["commit"][:10] or "unknown")
    return 0


if __name__ == "__main__":
    sys.exit(main())
