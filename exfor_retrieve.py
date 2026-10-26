#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exfor_retrieve.py  (version 2.2)
================================
Retrieve EXFOR data for reactions induced by a selectable set of projectiles on
a given target isotope: neutrons, protons, deuterons, tritons, 3He, alphas,
photons, electrons, pions, kaons, antiprotons, heavy ions, or all of them.

How it works
------------
The script works on the IAEA-NDS "exfor_master" repository
(https://github.com/IAEA-NDS/exfor_master), which holds the complete EXFOR
library as one text file per entry (exforall/<xxx>/<entry>.x4) and is updated
daily from the NRDC transmissions.  The repository is cloned once (about 1.4 GB
including git data) and then scanned locally, so queries are fast, reproducible
and do not load the IAEA web servers.

For every entry that contains the requested target with one of the selected
projectiles, the script parses the bibliographic information and the data
tables (COMMON blocks, multi-reaction subentries with pointers, multi-line
records) and writes:

  Files go to <out>/<target name>/ (default ./data/Nb-93/ for niobium-93, data/Ti-nat/ for natural
  titanium), so the data of every target are kept in their own folder:

  * <prefix>_data.csv      one row per data point (long format), written as the
                           entries are parsed, in EXFOR entry order
  * <prefix>_datasets.csv  one row per dataset (entry/subentry/reaction) = catalogue
  * with --json:  <prefix>_datasets.json and <prefix>_data.jsonl (one JSON object per line)

Only the Python standard library and git are needed.

Selecting projectiles (--projectiles)
-------------------------------------
A comma-separated string (spaces or semicolons also work) of items:

  all                    every projectile in EXFOR (including "no projectile")
  n p d t he3 a g e      neutron, proton, deuteron, triton, 3He, alpha, photon, electron
  pi+ pi- k+ k- ap       pions, kaons, antiproton
  0                      no incident particle (spontaneous processes, e.g. spontaneous fission)
  12C  C-12  6-C-12      a heavy ion (any of these spellings); 18F-L selects a level/isomer code
  C-*   Ne*              every isotope of that element used as a projectile (heavy-ion codes only)
  light                  p, d, t, he3, a
  neutral                n, g
  mesons                 pi+, pi-, k+, k-
  exotic                 pi+, pi-, k+, k-, ap, e
  heavy-ions (or hi)     every heavy ion (any projectile coded as Z-SYMBOL-A)
  -n  !n                 exclude (applied after the inclusions)

Examples:  d,p,he3,a   |   all   |   all,-n   |   --projectiles=all,-n,-g
           n,g   |   12C,16O,Ne-*   |   light,heavy-ions   |   d p 3He
Use --projectiles=all,-n (with "=") if the string starts with "-".
List everything that is understood with:  python exfor_retrieve.py --list-projectiles

The EXFOR master files
----------------------
  python exfor_retrieve.py --master-info       date of the latest data update, git commit, newer snapshot on GitHub?
  python exfor_retrieve.py --update --master-info    update the local copy (git pull), then show its date

Checking what EXFOR has (no data retrieved)
--------------------------------------------
  python exfor_retrieve.py --target Nb-93 --available            projectile / quantity / product table
  python exfor_retrieve.py --target Nb-93 --projectiles d --available entries      the EXFOR entries
  python exfor_retrieve.py --find --projectiles d --product Nb-92m                 which targets have such data
  python exfor_retrieve.py --find --target "Nb-*" --projectiles p                  all niobium isotopes

References of the datasets (--references)
-----------------------------------------
--references writes <prefix>_references.txt (numbered citations with title, DOI, EXFOR entry and the data used),
.bib (BibTeX) and .csv for the datasets retrieved (--ref-format txt,bib,csv; --ref-authors N).

Selecting the final product (--product)
---------------------------------------
Restrict the output to reactions that lead to a given final nucleus or particle.
A comma-separated string of items (default: all):

  all                       every product (including reactions without a product, e.g. fission)
  Nb-92m  92mNb  41-NB-92-M  a metastable state only;  Nb-92g / -G: ground state only;  m1, m2: higher isomers
  Nb-92  92Nb  41-NB-92     the nuclide in every state (ground, isomers, unspecified, ratios and sums of states)
  Zr-89                     a nuclide;  Zr-*  or Zr*: every isotope of the element;  natZr: natural element
  n p d t he3 a g           neutron, proton, deuteron, triton, 3He, alpha, gamma as products
  none                      reactions with no product given (fission, for example)
  heavy  heavy-ions  hi     every nuclide with Z >= 3: all products except n, p, d, t, 3He, alpha and gamma
                            (He-6 and the other helium or hydrogen isotopes are not included)
  residual                  the same, but without the target nucleus itself (elastic scattering): the
                            residual nuclei, which are what activation cross sections are about
  -n  !n                    exclude (applied after the inclusions)

Fission-fragment and mass-yield tables that give the product in the data table (ELEMENT, MASS) are
filtered point by point.  Add --product-exact to match the EXFOR product code exactly as written
(41-NB-92 then selects only data with no state given).

Examples:  --product Nb-92m   |   --product 92mNb,89Zr   |   --product "Zr-*"   |   --product=all,-n

Other examples
--------------
  python exfor_retrieve.py --target Nb-93                       (writes ./data/Nb-93/EXFOR_NB-93_data.csv ...)
  python exfor_retrieve.py --target Nb-93 --projectiles all --summary-only
  python exfor_retrieve.py --target Mn-55 --projectiles d,p --quantity SIG --emax 60
  python exfor_retrieve.py --target Fe-56 --projectiles "n,g" --quantity SIG --out results
  python exfor_retrieve.py --target Ti-nat --projectiles light --update --json
  python exfor_retrieve.py --target Nb-93 --projectiles d --quantity SIG --product Nb-92m,Zr-89

Target notation: Nb-93, 93Nb, NB93, 41-NB-93; natural composition: Ti-nat, natTi, Ti-0.

Notes and caveats
-----------------
* Values are converted to mb (cross sections), mb/sr (angular distributions) and
  mb/MeV (energy distributions) when the EXFOR units allow it; other quantities
  keep their original units (column value_unit).  The original unit is always
  kept in raw_unit.  Percent uncertainties are converted to absolute ones.
* E_MeV is the incident (laboratory) energy of the projectile in MeV (total
  kinetic energy).  For energies given per nucleon (MEV/A, GEV/A) it is
  converted with the projectile mass number; E_per_u_MeV is the energy per
  nucleon.  E_unit is the original unit and E_source tells which column the
  energy came from (EN, EN-MIN/MAX mid-point, or EN-MEAN).  Neutron wavelengths
  (ANGSTROM) are converted with E = 81.804 meV A^2 / lambda^2.  Energies in
  units that cannot be converted are left empty (E_MeV empty) and a warning
  with the number of affected points is printed; they are never assumed to be MeV.
* For spectra (DA/DE, DE, NU/DE, PN/DE, ...) the outgoing energy is in E_out_MeV (the mid-point when
  EXFOR gives the energy bin as E-MIN and E-MAX).  If the
  incident energy is not a column of the table, E_MeV stays empty and the entry
  (or incident_energy_note in the datasets file) must be consulted.
* "reaction_type" is "simple" for a single reaction and "complex" for ratios,
  sums or other combinations that involve the requested target.
* "status" reproduces the EXFOR STATUS code(s) (e.g. APRVD, TABLE, CURVE,
  SPSDD = superseded, DEP = dependent).  Datasets marked SPSDD or DEP are
  usually duplicates of other entries.
* The script retrieves what is in EXFOR.  It does not judge data quality and does
  not merge duplicates.  With --projectiles all, popular targets give very large
  tables (neutron data dominate): use --summary-only first, then restrict the
  projectiles and quantities.
"""
import argparse
import collections
import csv
import sqlite3
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import urllib.request
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

__version__ = "2.3"
__build__ = "2026-10-09"       # date of the last change
API_LEVEL = 2                     # what exfor_plot.py needs from this file; exfor_plot.py checks it

# Folder of the EXFOR master files, used when --master is not given and the folder exists. Otherwise the default is
# the folder exfor_master in the folder where the command is run (it is downloaded there if it does not exist).
MASTER_DEFAULT = ""   # optional: a fixed folder of the EXFOR master files; empty = ./exfor_master
REPO_URL = "https://github.com/IAEA-NDS/exfor_master.git"
ZIP_URL = "https://codeload.github.com/IAEA-NDS/exfor_master/zip/refs/heads/main"

ELEMENTS = ("H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr "
            "Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm "
            "Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No "
            "Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og").split()
Z_OF = {s.upper(): i + 1 for i, s in enumerate(ELEMENTS)}

# --------------------------------------------------------------------------
# projectile catalogue
# --------------------------------------------------------------------------
# EXFOR code, label, Z, A, accepted spellings (lower case), description
PARTICLES = [
    ("N", "n", 0, 1, ["n", "neutron", "neutrons"], "neutron"),
    ("P", "p", 1, 1, ["p", "proton", "protons", "h1", "1h", "h-1"], "proton"),
    ("D", "d", 1, 2, ["d", "deuteron", "deuterons", "h2", "2h", "h-2"], "deuteron"),
    ("T", "t", 1, 3, ["t", "triton", "tritons", "h3", "3h", "h-3"], "triton"),
    ("HE3", "3He", 2, 3, ["he3", "3he", "he-3", "helion", "helions"], "helion (3He)"),
    ("A", "alpha", 2, 4, ["a", "alpha", "alphas", "he4", "4he", "he-4"], "alpha particle (4He)"),
    ("G", "gamma", None, None, ["g", "gamma", "gammas", "photon", "photons"], "photon"),
    ("E", "e", None, None, ["e", "electron", "electrons", "e-"], "electron"),
    ("PIP", "pi+", None, None, ["pi+", "pip"], "positive pion"),
    ("PIN", "pi-", None, None, ["pi-", "pin"], "negative pion"),
    ("KP", "K+", None, None, ["k+", "kp"], "positive kaon"),
    ("KN", "K-", None, None, ["k-", "kn"], "negative kaon"),
    ("AP", "pbar", None, None, ["ap", "pbar", "antiproton", "antiprotons"], "antiproton"),
    ("0", "none", None, None, ["0", "none", "spontaneous", "sf"],
     "no incident particle (spontaneous processes, e.g. spontaneous fission)"),
]
BY_CODE = {p[0]: p for p in PARTICLES}
ALIASES = {}
for _p in PARTICLES:
    for _a in _p[4]:
        ALIASES[_a] = _p[0]
GROUPS = {
    "light": {"P", "D", "T", "HE3", "A"},
    "neutral": {"N", "G"},
    "mesons": {"PIP", "PIN", "KP", "KN"},
    "exotic": {"PIP", "PIN", "KP", "KN", "AP", "E"},
}
HEAVY_ION_GROUP = ("heavy-ions", "heavyions", "heavy_ions", "hi", "ions")
CODE_FIX = {"GAMMA": "G"}          # spellings found in a few EXFOR entries
NUCL_CODE = re.compile(r"^(\d{1,3})-([A-Z]{1,2})-(\d{1,3})(?:-([A-Z]\d?))?$")


def canon_code(raw):
    """Canonical EXFOR projectile code (upper case, known spelling variants fixed)."""
    c = raw.strip().upper()
    return CODE_FIX.get(c, c)


def proj_info(code):
    """Label, Z and A of an EXFOR projectile code."""
    if code in BY_CODE:
        p = BY_CODE[code]
        return {"code": code, "label": p[1], "Z": p[2], "A": p[3]}
    m = NUCL_CODE.match(code)
    if m:
        z, sym, a, suf = int(m.group(1)), m.group(2), int(m.group(3)), m.group(4)
        label = ("nat" + sym.capitalize()) if a == 0 else f"{a}{sym.capitalize()}"
        if suf:
            label += "-" + suf
        return {"code": code, "label": label, "Z": z, "A": a or None}
    return {"code": code, "label": code, "Z": None, "A": None}


def parse_target(text):
    """Return the EXFOR target code 'Z-SYM-A' (A = 0 for natural composition)."""
    s = text.strip().upper().replace(" ", "")
    m = re.fullmatch(r"(\d{1,3})-([A-Z]{1,2})-(\d{1,3})", s)
    if m:
        z, sym, a = int(m.group(1)), m.group(2), int(m.group(3))
        if Z_OF.get(sym) != z:
            raise ValueError(f"Z={z} does not match element {sym}")
        return f"{z}-{sym}-{a}"
    patterns = [
        (r"NAT-?([A-Z]{1,2})", lambda m: (m.group(1), 0)),
        (r"([A-Z]{1,2})-?NAT", lambda m: (m.group(1), 0)),
        (r"(\d{1,3})-?([A-Z]{1,2})", lambda m: (m.group(2), int(m.group(1)))),
        (r"([A-Z]{1,2})-?(\d{1,3})", lambda m: (m.group(1), int(m.group(2)))),
    ]
    for pat, fn in patterns:
        m = re.fullmatch(pat, s)
        if m:
            sym, a = fn(m)
            if sym in Z_OF:
                return f"{Z_OF[sym]}-{sym}-{a}"
    raise ValueError(f"Cannot interpret target '{text}' (try e.g. Nb-93, 93Nb, 41-NB-93, Ti-nat)")


def target_dirname(code):
    """Folder name of a target: 41-NB-93 -> Nb-93, 22-TI-0 -> Ti-nat."""
    m = re.fullmatch(r"(\d+)-([A-Z]{1,2})-(\d+)", code or "")
    if not m:
        return re.sub(r"[^A-Za-z0-9+.-]+", "_", code or "").strip("_") or "data"
    sym, a = m.group(2).capitalize(), int(m.group(3))
    return f"{sym}-nat" if a == 0 else f"{sym}-{a}"


def _token_matcher(tok):
    """Return a predicate on canonical EXFOR codes for one projectile token, or raise ValueError."""
    t = tok.lower().replace(" ", "")
    if t in ("all", "any", "*"):
        return lambda c: True
    if t in GROUPS:
        codes = GROUPS[t]
        return lambda c: c in codes
    if t in HEAVY_ION_GROUP:
        return lambda c: bool(NUCL_CODE.match(c))
    if t in ALIASES:
        code = ALIASES[t]
        return lambda c: c == code
    T = t.upper()
    # element wildcard: C-*  C*  6-C-*
    m = re.fullmatch(r"(?:(\d{1,3})-)?([A-Z]{1,2})-?\*", T)
    if m and m.group(2) in Z_OF:
        sym = m.group(2)
        return lambda c, sym=sym: bool(NUCL_CODE.match(c)) and c.split("-")[1] == sym
    # single nuclide: 6-C-12, C-12, C12, 12C, 18F-L
    m = re.fullmatch(r"(?:(\d{1,3})-)?([A-Z]{1,2})-?(\d{1,3})(?:-([A-Z]\d?))?", T)
    z = sym = a = suf = None
    if m and m.group(2) in Z_OF:
        z, sym, a, suf = m.group(1), m.group(2), m.group(3), m.group(4)
    else:
        m = re.fullmatch(r"(\d{1,3})([A-Z]{1,2})(?:-([A-Z]\d?))?", T)
        if m and m.group(2) in Z_OF:
            a, sym, suf = m.group(1), m.group(2), m.group(3)
    if sym:
        if z is not None and int(z) != Z_OF[sym]:
            raise ValueError(f"Z={z} does not match element {sym} in '{tok}'")
        base = f"{Z_OF[sym]}-{sym}-{int(a)}"
        if suf:
            full = f"{base}-{suf}"
            return lambda c, full=full: c == full
        return lambda c, base=base: c == base or c.startswith(base + "-")
    raise ValueError(f"unknown projectile '{tok}'")


class Selection:
    """Set of projectiles defined by a string such as 'd,p,he3,a', 'all,-n' or '12C,16O,Ne-*'."""

    def __init__(self, spec):
        self.spec = spec
        self.inc, self.exc = [], []
        for tok in re.split(r"[,;\s]+", spec.strip()):
            if not tok:
                continue
            neg = len(tok) > 1 and tok[0] in "-!"
            body = tok[1:] if neg else tok
            try:
                (self.exc if neg else self.inc).append(_token_matcher(body))
            except ValueError as exc:
                raise ValueError(f"{exc}. Use --list-projectiles to see the accepted names.") from None
        if not self.inc and not self.exc:
            raise ValueError("empty projectile selection")
        self.all_included = not self.inc

    def accepts(self, code):
        ok = True if not self.inc else any(f(code) for f in self.inc)
        return ok and not any(f(code) for f in self.exc)


# --------------------------------------------------------------------------
# product (final nucleus or particle) parsing and selection
# --------------------------------------------------------------------------
PRODUCT_CODE = re.compile(r"^(\d{1,3})-([A-Z]{1,2})-(\d{1,3})(?:-([A-Z0-9+/]+))?$")
PRODUCT_ELEMENT = re.compile(r"^(\d{1,3})-([A-Z]{1,2})$")
PRODUCT_MASS = re.compile(r"^MASS-(\d{1,3})$")
PRODUCT_PARTICLES = {"0-NN-1": "n", "1-H-1": "p", "1-H-2": "d", "1-H-3": "t",
                     "2-HE-3": "3He", "2-HE-4": "alpha", "0-G-0": "gamma"}
PRODUCT_ALIASES = {"n": "0-NN-1", "neutron": "0-NN-1", "neutrons": "0-NN-1",
                   "p": "1-H-1", "proton": "1-H-1", "protons": "1-H-1",
                   "d": "1-H-2", "deuteron": "1-H-2", "deuterons": "1-H-2",
                   "t": "1-H-3", "triton": "1-H-3", "tritons": "1-H-3",
                   "he3": "2-HE-3", "3he": "2-HE-3", "helion": "2-HE-3", "helions": "2-HE-3",
                   "a": "2-HE-4", "alpha": "2-HE-4", "alphas": "2-HE-4", "he4": "2-HE-4", "4he": "2-HE-4",
                   "g": "0-G-0", "gamma": "0-G-0", "photon": "0-G-0", "photons": "0-G-0"}
TABLE_PRODUCTS = ("ELEM/MASS", "ELEM", "MASS")   # product given in the data table, row by row


def parse_product(code):
    """Describe an EXFOR product field: kind, Z, A, element symbol, state and a readable label."""
    c = code.strip().upper()
    base = {"code": c, "kind": "other", "Z": None, "A": None, "sym": "", "state": "", "label": c or "none"}
    if not c:
        base["kind"] = "none"
        return base
    m = PRODUCT_CODE.match(c)
    if m:
        z, sym, a, st = int(m.group(1)), m.group(2), int(m.group(3)), m.group(4) or ""
        if c in PRODUCT_PARTICLES:
            label = PRODUCT_PARTICLES[c]
        elif sym not in Z_OF:
            label = c
        else:
            s = sym.capitalize()
            if a == 0:
                label = "nat" + s
            elif st in ("M", "G") or re.fullmatch(r"[MG]\d", st):
                label = f"{a}{st.lower()}{s}"
            elif st:
                label = f"{a}{s}-{st}"
            else:
                label = f"{a}{s}"
        base.update(kind="nuclide", Z=z, A=a, sym=sym, state=st, label=label)
        return base
    m = PRODUCT_ELEMENT.match(c)
    if m and m.group(2) in Z_OF:
        base.update(kind="element", Z=int(m.group(1)), sym=m.group(2), label=m.group(2).capitalize())
        return base
    m = PRODUCT_MASS.match(c)
    if m:
        base.update(kind="mass", A=int(m.group(1)), label=f"A={m.group(1)}")
        return base
    if c in TABLE_PRODUCTS:
        base["kind"] = "table"
    return base


def _parse_product_token(tok):
    """Return (Z, sym, A, state) for a nuclide token; state is None when not given. Raises ValueError."""
    t = tok.replace(" ", "")
    T = t.upper()
    m = re.fullmatch(r"(\d{1,3})-([A-Z]{1,2})-(\d{1,3})(?:-([A-Z0-9+/]+))?", T)      # EXFOR code
    if m:
        return int(m.group(1)), m.group(2), int(m.group(3)), m.group(4)
    m = re.fullmatch(r"NAT-?([A-Z]{1,2})|([A-Z]{1,2})-?NAT", T)                          # natural element
    if m:
        sym = m.group(1) or m.group(2)
        if sym in Z_OF:
            return Z_OF[sym], sym, 0, None
    m = re.fullmatch(r"([A-Za-z]{1,2})-?(\d{1,3})(?:-?([MGLmgl])(\d?))?", t)           # Nb-92, Nb-92m, Nb92m1
    if m and m.group(1).upper() in Z_OF:
        st = (m.group(3).upper() + m.group(4)) if m.group(3) else None
        return Z_OF[m.group(1).upper()], m.group(1).upper(), int(m.group(2)), st
    m = re.fullmatch(r"(\d{1,3})([A-Za-z]{1,2})", t)                                    # 89Zr (no state)
    if m and m.group(2).upper() in Z_OF:
        return Z_OF[m.group(2).upper()], m.group(2).upper(), int(m.group(1)), None
    m = re.fullmatch(r"(\d{1,3})([mgl])(\d?)([A-Za-z]{1,2})", t)                       # 92mNb, 92m1Nb
    if m and m.group(4).upper() in Z_OF:
        return Z_OF[m.group(4).upper()], m.group(4).upper(), int(m.group(1)), m.group(2).upper() + m.group(3)
    raise ValueError(f"unknown product '{tok}'")


def _product_matcher(tok, exact=False):
    t = tok.lower().replace(" ", "")
    if t in ("all", "any", "*"):
        return lambda p: True
    if t in ("none", "nothing"):
        return lambda p: p["kind"] == "none"
    if t in PRODUCT_ALIASES:
        code = PRODUCT_ALIASES[t]
        return lambda p, code=code: p["code"] == code
    m = re.fullmatch(r"([a-z]{1,2})-?\*", t)                                            # Zr-*  Zr*
    if m and m.group(1).upper() in Z_OF:
        sym = m.group(1).upper()
        return lambda p, sym=sym: p["kind"] in ("nuclide", "element") and p["sym"] == sym
    z, sym, a, st = _parse_product_token(tok)

    def match(p, z=z, a=a, st=st, sym=sym):
        if p["kind"] != "nuclide" or p["Z"] != z or p["A"] != a or p["sym"] != sym:
            return False
        if st is None:
            return (p["state"] == "") if exact else True
        return p["state"] == st
    return match


HEAVY_WORDS = {"heavy", "heavy-ion", "heavy-ions", "heavyions", "hi", "ion", "ions"}
RESIDUAL_WORDS = {"residual", "residuals", "residue", "residues"}


def is_heavy_product(p):
    """A nuclide (or element) with Z >= 3: everything except n, p, d, t, 3He, alpha and gamma."""
    return p["kind"] in ("nuclide", "element") and p["Z"] is not None and p["Z"] >= 3


class ProductSelection:
    """Set of final products defined by a string such as 'Nb-92m,Zr-89', 'Zr-*', 'n', 'all,-n', 'heavy' or
    'residual' (heavy products other than the target nucleus itself)."""

    def __init__(self, spec="all", exact=False):
        self.spec, self.exact = spec, exact
        self.inc, self.exc = [], []
        self.target_za = None
        for tok in re.split(r"[,;\s]+", spec.strip()):
            if not tok:
                continue
            neg = len(tok) > 1 and tok[0] in "-!"
            body = tok[1:] if neg else tok
            try:
                low = body.lower().replace(" ", "")
                if low in HEAVY_WORDS:
                    matcher = is_heavy_product
                elif low in RESIDUAL_WORDS:
                    matcher = lambda p, self=self: is_heavy_product(p) and not self._is_target(p)
                else:
                    matcher = _product_matcher(body, exact)
                (self.exc if neg else self.inc).append(matcher)
            except ValueError as exc:
                raise ValueError(f"{exc}. Products are written like Nb-92m, 92mNb, 41-NB-92-M, Zr-89, Zr-*, "
                                 f"n, alpha, gamma, none, heavy or residual.") from None
        if not self.inc and not self.exc:
            raise ValueError("empty product selection")
        self.is_all = (len(self.exc) == 0 and len(self.inc) == 1 and spec.strip().lower() in ("all", "any", "*"))

    def set_target(self, code):
        """Tell the selection which target the data belong to (needed by 'residual')."""
        info = parse_product(code or "")
        self.target_za = (info["Z"], info["A"]) if info["kind"] == "nuclide" else None

    def _is_target(self, p):
        """The product is the target nucleus itself without a state (elastic scattering)."""
        return (self.target_za is not None and p["kind"] == "nuclide" and p["state"] == ""
                and (p["Z"], p["A"]) == self.target_za)

    def accepts(self, info):
        ok = True if not self.inc else any(f(info) for f in self.inc)
        return ok and not any(f(info) for f in self.exc)


def print_projectile_table():
    print("Accepted projectile names for --projectiles (case insensitive):\n")
    print(f"{'EXFOR code':10} {'label':6} {'accepted spellings':44} particle")
    for code, label, z, a, al, desc in PARTICLES:
        print(f"{code:10} {label:6} {', '.join(al):44} {desc}")
    print("\nHeavy ions (EXFOR code Z-SYMBOL-A, e.g. 6-C-12): write 12C, C-12, C12 or 6-C-12.")
    print("  18F-L (with a level/isomer suffix) selects exactly that code; 18F also matches its -M/-L codes.")
    print("  C-* or Ne* selects every isotope of the element used as a projectile (heavy-ion codes only).")
    print("\nGroups:")
    for g, codes in GROUPS.items():
        print(f"  {g:12} {', '.join(BY_CODE[c][1] for c in sorted(codes, key=lambda x: [p[0] for p in PARTICLES].index(x)))}")
    print(f"  {'heavy-ions':12} every projectile coded as Z-SYMBOL-A (aliases: hi, ions)")
    print(f"  {'all':12} every projectile (aliases: any, *), including 'none'")
    print("\nExclusion: put - or ! in front of an item, e.g.  all,-n,-g  (use --projectiles=all,-n).")


# --------------------------------------------------------------------------
# repository handling
# --------------------------------------------------------------------------
def master_date(master):
    """Date (YYYY-MM-DD) of the latest data update in the master files, from entry_updatedate.dat, or ''."""
    best, n = "", 0
    try:
        with open(Path(master) / "entry_updatedate.dat", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                t = line.split()
                if len(t) > 1:
                    n += 1
                    if t[1] > best:
                        best = t[1]
    except OSError:
        return ""
    return best


def _git(args, timeout=60):
    try:
        r = subprocess.run(["git"] + list(args), capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def master_info(master):
    """Print the date of the master files, their git commit and whether GitHub has something newer."""
    master = Path(master)
    print(f"EXFOR master files: {master.resolve()}")
    if not (master / "exforall").is_dir():
        print("  not downloaded yet: they are downloaded at the first retrieval, or with\n"
              f"    git clone --depth 1 {REPO_URL}")
        return
    files = {p.stem for p in (master / "exforall").rglob("*.x4")}
    listed = set()
    try:
        with open(master / "entry_updatedate.dat", encoding="utf-8", errors="replace") as fh:
            listed = {line.split()[0] for line in fh if line.strip()}
    except OSError:
        pass
    print(f"  entries                : {len(listed) or len(files)}")
    if listed:
        absent = len(listed - files)
        if absent == 0:
            print(f"  entry files in exforall: {len(files)} (every listed entry is present)")
        else:
            print(f"  entry files in exforall: {len(files)}: WARNING, {absent} listed entries have no file, so the "
                  f"copy is incomplete. Update it (--update) or download it again.")
    print(f"  latest data update     : {master_date(master) or 'unknown'} (latest date in entry_updatedate.dat)")
    if not (master / ".git").exists() or not shutil.which("git"):
        print("  git information        : not available (the files were not obtained with git clone)")
        return
    local = _git(["-C", str(master), "rev-parse", "HEAD"])
    when = _git(["-C", str(master), "log", "-1", "--format=%cd", "--date=iso"])
    print(f"  local git commit       : {local[:10]}  {when}")
    remote = _git(["-C", str(master), "ls-remote", "origin", "refs/heads/main"], timeout=30).split()
    if not remote:
        print("  GitHub                 : could not be reached (offline?), so the comparison was skipped")
    elif remote[0] == local:
        print("  GitHub latest commit   : the same: your copy is up to date")
    else:
        print(f"  GitHub latest commit   : {remote[0][:10]}: a newer snapshot exists. Update with\n"
              f"    python exfor_retrieve.py --master {master} --update --master-info")
    tags = _git(["-C", str(master), "ls-remote", "--tags", "origin", "Backup-*"], timeout=30)
    names = sorted({t.split("refs/tags/")[1].replace("^{}", "") for t in tags.splitlines() if "refs/tags/" in t})
    if names:
        print(f"  latest backup releases : {', '.join(names[-3:][::-1])}")


def update_problem(path):
    """Explain why --update cannot be done and how to fix it."""
    have = master_date(path) or "unknown date"
    if not shutil.which("git"):
        return (f"--update skipped: git was not found on this computer, and --update needs it. Your copy of the "
                f"master files is from the data update of {have}.\n"
                f"  Install git (macOS: type 'git --version' in a terminal and accept the offer to install the "
                f"command line tools, or 'brew install git'; Windows: https://git-scm.com; Linux: your package "
                f"manager), then rename or delete the folder '{path}' and run again: the files are then cloned with "
                f"git and can be updated later.")
    return (f"--update skipped: the folder '{path}' is not a git clone (it has no .git folder), so it cannot be "
            f"updated with git pull. It was probably downloaded as a ZIP file, or copied without the hidden .git "
            f"folder. Your copy is from the data update of {have}.\n"
            f"  To be able to update it, rename or delete the folder and run again (the files are then cloned with "
            f"git), or clone it yourself:\n"
            f"    git clone --depth 1 {REPO_URL} {path}\n"
            f"  Or download a fresh ZIP file and unzip it over the folder.")


def default_master():
    """The folder of the master files when --master is not given."""
    return MASTER_DEFAULT if MASTER_DEFAULT and Path(MASTER_DEFAULT).is_dir() else "exfor_master"


def ensure_master(path, update=False):
    path = Path(path)
    if (path / "exforall").is_dir():
        if update:
            if (path / ".git").exists() and shutil.which("git"):
                print("Updating exfor_master (git pull) ...", file=sys.stderr)
                subprocess.run(["git", "-C", str(path), "pull", "--ff-only", "origin", "main"], check=False)
                print(f"Master files now from the data update of {master_date(path) or 'unknown date'}.",
                      file=sys.stderr)
            else:
                print(update_problem(path), file=sys.stderr)
        return path
    if shutil.which("git"):
        print(f"Cloning {REPO_URL} into {path} (about 1.4 GB, one-off) ...", file=sys.stderr)
        r = subprocess.run(["git", "clone", "--depth", "1", REPO_URL, str(path)])
        if r.returncode == 0 and (path / "exforall").is_dir():
            return path
        print("git clone failed, falling back to the zip archive.", file=sys.stderr)
    if not shutil.which("git"):
        print("git was not found, so the EXFOR master files are downloaded as a ZIP file. Such a copy cannot be "
              "updated with --update: install git and download the files again to enable updates.", file=sys.stderr)
    print(f"Downloading {ZIP_URL} ...", file=sys.stderr)
    path.mkdir(parents=True, exist_ok=True)
    zpath = path / "exfor_master.zip"
    urllib.request.urlretrieve(ZIP_URL, zpath)
    with zipfile.ZipFile(zpath) as z:
        for member in z.namelist():
            parts = member.split("/", 1)
            if len(parts) == 2 and parts[1]:
                dest = path / parts[1]
                if member.endswith("/"):
                    dest.mkdir(parents=True, exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(member) as src, open(dest, "wb") as out:
                        shutil.copyfileobj(src, out)
    zpath.unlink()
    if not (path / "exforall").is_dir():
        raise SystemExit("Could not obtain the EXFOR master files.")
    return path


def build_prefilter(target_code):
    """Fast pre-filter: the target followed by '(projectile,' anywhere in the file."""
    return re.compile(rb"(?<![0-9A-Za-z])" + re.escape(target_code).encode() + rb"\([^,()]+,")


_PREFILTER = None


def _init_worker(pattern, flags):
    global _PREFILTER
    _PREFILTER = re.compile(pattern, flags)


def _scan_file(path):
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError:
        return None
    return path if _PREFILTER.search(data) else None


# --------------------------------------------------------------------------
# facility filter (--facility)
# --------------------------------------------------------------------------
# Named facilities: the entry is accepted if the FACILITY / INSTITUTE / TITLE / REFERENCE text matches.
# n_TOF: criterion 1: FACILITY field with the CERN institute code 2ZZZCER and the text nTOF / n-TOF / n_TOF;
#        criterion 2: n_TOF named in the TITLE, INSTITUTE or REFERENCE of an entry whose FACILITY text is missing
#        or does not say it (CERN or 2ZZZCER must also appear). GELINA, IUCF ... "neutron TOF" facilities do not match.
_NTOF_TXT = re.compile(r"n[-_ ]?TOF", re.I)
FACILITY_ALIASES = {
    "NTOF": "n_TOF at CERN",
    "N_TOF": "n_TOF at CERN",
    "N-TOF": "n_TOF at CERN",
    "GELINA": "GELINA (JRC Geel)",
}


def _bib_block(text, key):
    """Text of one BIB keyword of an entry (all subentries), continuation lines included."""
    out = []
    for m in re.finditer(r"(?ms)^%s\s+(.*?)(?=^\S)" % key, text):
        out.append(m.group(1))
    return "\n".join(out)


def facility_matcher(spec):
    """Predicate on the text of an entry file for --facility. spec: ntof, gelina, or a regular expression
    (case-insensitive) searched in the FACILITY and INSTITUTE fields, for example 'LANSCE|WNR' or 'ORELA'."""
    sp = (spec or "").strip()
    key = sp.upper().replace(" ", "")
    if key in ("NTOF", "N_TOF", "N-TOF"):
        def pred(text):
            fac = _bib_block(text, "FACILITY")
            if "2ZZZCER" in fac and _NTOF_TXT.search(fac):
                return True
            if re.search(r"GELINA|2ZZZGEL", fac) and not _NTOF_TXT.search(fac):
                return False
            head = _bib_block(text, "TITLE") + "\n" + _bib_block(text, "INSTITUTE") + "\n" + _bib_block(text, "REFERENCE") + "\n" + fac
            return bool(_NTOF_TXT.search(head)) and ("CERN" in head.upper() or "2ZZZCER" in text)
        return pred
    if key == "GELINA":
        return lambda text: bool(re.search(r"GELINA|2ZZZGEL", _bib_block(text, "FACILITY") + _bib_block(text, "INSTITUTE")))
    rx = re.compile(sp, re.I)
    return lambda text: bool(rx.search(_bib_block(text, "FACILITY") + "\n" + _bib_block(text, "INSTITUTE")))


_FACILITY_CACHE = {}


def facility_files(master, spec):
    """All entry files of the master folder that pass --facility (cached: a run over many targets scans once)."""
    key = (str(master), spec)
    if key not in _FACILITY_CACHE:
        pred = facility_matcher(spec)
        keep = []
        for p in sorted((master / "exforall").rglob("*.x4")):
            try:
                txt = p.read_text(encoding="latin-1")
            except OSError:
                continue
            if pred(txt):
                keep.append(str(p))
        _FACILITY_CACHE[key] = keep
    return _FACILITY_CACHE[key]


def find_candidate_files(master, prefilter, jobs, facility=None):
    files = sorted(str(p) for p in (master / "exforall").rglob("*.x4"))
    n_all = len(files)
    if facility:
        files = facility_files(master, facility)
    hits = []
    if jobs > 1:
        with ProcessPoolExecutor(max_workers=jobs, initializer=_init_worker,
                                 initargs=(prefilter.pattern, prefilter.flags)) as ex:
            for r in ex.map(_scan_file, files, chunksize=200):
                if r:
                    hits.append(r)
    else:
        _init_worker(prefilter.pattern, prefilter.flags)
        for f in files:
            r = _scan_file(f)
            if r:
                hits.append(r)
    return n_all, hits


# --------------------------------------------------------------------------
# EXFOR (X4) parsing
# --------------------------------------------------------------------------
_NUM = re.compile(r"^([+-]?(?:\d+\.?\d*|\.\d+))([+-]\d+)?$")


def exfor_float(s):
    s = s.strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        pass
    m = _NUM.match(s)
    if m:
        try:
            return float(m.group(1) + ("E" + m.group(2) if m.group(2) else ""))
        except ValueError:
            return None
    return None


def parse_bib(lines):
    """Return {keyword: [ {'ptr': '1', 'text': '...'} ]}."""
    bib, items, cur = {}, None, None
    for l in lines:
        l = l.ljust(66)
        key, ptr, txt = l[:10].strip(), l[10:11].strip(), l[11:66].rstrip()
        if key:
            items = bib.setdefault(key, [])
            cur = {"ptr": ptr, "lines": [txt]}
            items.append(cur)
        elif items is not None:
            if ptr:
                cur = {"ptr": ptr, "lines": [txt]}
                items.append(cur)
            elif cur is not None:
                cur["lines"].append(txt)
    out = {}
    for k, its in bib.items():
        sep = "" if k == "REACTION" else " "
        out[k] = [{"ptr": it["ptr"], "text": sep.join(x.strip() for x in it["lines"]).strip()} for it in its]
    return out


def parse_table(lines, nc):
    """Parse a DATA/COMMON block body (heading lines, unit lines, data lines)."""
    hl = max(1, math.ceil(nc / 6))
    heads_raw = lines[:hl]
    units_raw = lines[hl:2 * hl]
    data_raw = [l for l in lines[2 * hl:] if l.strip()]

    def fields(block, n):
        flat = []
        for l in block:
            l = l.ljust(66)
            flat += [l[i:i + 11] for i in range(0, 66, 11)]
        return flat[:n]

    heads = fields(heads_raw, nc)
    cols = [(f[:10].strip(), f[10:11].strip()) for f in heads]
    units = [f.strip() for f in fields(units_raw, nc)]
    rows = []
    for i in range(0, len(data_raw) - hl + 1, hl):
        rows.append(fields(data_raw[i:i + hl], nc))
    return cols, units, rows


def parse_entry(path):
    """Return (entry_id, [subentry dicts])."""
    lines = Path(path).read_text(encoding="latin-1").splitlines()
    entry_id, subs, cur, i = None, [], None, 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("ENTRY"):
            entry_id = l.split()[1]
        elif l.startswith("SUBENT"):
            cur = {"id": l.split()[1], "bib": {}, "common": None, "data": None}
            subs.append(cur)
        elif l.startswith("BIB") and cur is not None:
            j = i + 1
            while j < len(lines) and not lines[j].startswith("ENDBIB"):
                j += 1
            cur["bib"] = parse_bib(lines[i + 1:j])
            i = j
        elif (l.startswith("COMMON") or (l.startswith("DATA") and not l.startswith("DATA-"))) and cur is not None:
            kind = "common" if l.startswith("COMMON") else "data"
            tok = l.split()
            if len(tok) >= 3 and tok[1].isdigit():
                nc = int(tok[1])
                end = "ENDCOMMON" if kind == "common" else "ENDDATA"
                j = i + 1
                while j < len(lines) and not lines[j].startswith(end):
                    j += 1
                cur[kind] = parse_table(lines[i + 1:j], nc)
                i = j
        i += 1
    return entry_id, subs


RX = re.compile(r"(\d{1,3}-[A-Z]{1,2}-\d{1,3}(?:-[A-Z])?)\(([A-Za-z0-9+\-]+),([^()]*)\)([^,()]*)"
                r"((?:,(?:\([^()]*\)|[^,()])*)*)")


# every term of a reaction string, also those with a target that is not a nuclide (1-H-PLE polyethylene, 92-U-OXI uranium
# oxide, 6-C-CMP a carbon compound ...), which RX does not match: a sum with such a term is a complex reaction
RX_TERM = re.compile(r"\d{1,3}-[A-Z]{1,2}-[0-9A-Z]{1,4}(?:-[A-Z])?\(")


def match_reactions(rtext, target_code, selection):
    """List of matches (as dicts) of target(proj,...) with an accepted projectile in a reaction string."""
    found = RX.findall(rtext)
    n_terms = max(len(found), len(RX_TERM.findall(rtext)))
    out = []
    for tgt, proj, proc, prod, rest in found:
        if tgt != target_code:
            continue
        code = canon_code(proj)
        if not selection.accepts(code):
            continue
        parts = rest.split(",")[1:] if rest else []
        parts += [""] * (4 - len(parts))
        out.append({"code": code, "raw_code": proj, "process": proc, "product": prod,
                    "branch": parts[0].strip("()"), "param": parts[1], "modifier": parts[2],
                    "complex": n_terms > 1})
    return out


# --------------------------------------------------------------------------
# units and values
# --------------------------------------------------------------------------
ENERGY_UNITS = {"EV": 1e-6, "KEV": 1e-3, "MEV": 1.0, "GEV": 1e3, "TEV": 1e6,
                "MILLI-EV": 1e-9, "MICRO-EV": 1e-12, "NANO-EV": 1e-15}
NEUTRON_WAVELENGTH_MEV_A2 = 81.804e-9   # E[MeV] = 81.804e-9 / lambda[A]^2   (81.804 meV A^2)
B_PREFIX = {"B": 1e3, "MB": 1.0, "MILLI-B": 1.0, "MICRO-B": 1e-3, "MUB": 1e-3, "MU-B": 1e-3, "NANO-B": 1e-6,
            "NB": 1e-6, "PICO-B": 1e-9, "PB": 1e-9, "KILO-B": 1e6}


def convert_energy(v, unit, proj_a, is_neutron, allow_wavelength=True):
    """Convert an energy value to MeV.

    Returns (E_MeV total, E per nucleon in MeV, status) where status is
    'ok', 'need_mass' (per-nucleon energy but projectile mass unknown) or 'unsupported'.
    """
    u = unit.upper().strip()
    if u == "ANGSTROM":
        if allow_wavelength and is_neutron and v > 0:
            e = NEUTRON_WAVELENGTH_MEV_A2 / (v * v)
            return e, e, "ok"
        return None, None, "unsupported"
    per = False
    if u.endswith("/A") or u.endswith("/NUCL"):
        per, u = True, u.rsplit("/", 1)[0]
    f = ENERGY_UNITS.get(u)
    if f is None:
        return None, None, "unsupported"
    x = v * f
    if per:
        if proj_a:
            return x * proj_a, x, "ok"
        return None, x, "need_mass"
    return x, (x / proj_a if proj_a else None), "ok"


def convert_value(val, unit, param):
    """Convert val to mb, mb/sr or mb/MeV when possible; return (value, unit)."""
    if val is None:
        return None, unit
    u = unit.upper()
    m = re.fullmatch(r"((?:MILLI-|MICRO-|NANO-|PICO-|KILO-)?B|MB|MUB|MU-B|NB|PB)(/SR)?(/MEV)?", u)
    if m:
        fac = B_PREFIX.get(m.group(1))
        if fac is not None:
            std = "mb" + ("/sr" if m.group(2) else "") + ("/MeV" if m.group(3) else "")
            return val * fac, std
    return val, unit


def first_group(ref):
    """Text inside the first parenthesis group of an EXFOR reference, with nested parentheses kept."""
    ref = re.sub(r"\s*doi:.*$", "", ref.strip(), flags=re.I)
    if not ref.startswith("("):
        return None
    depth = 0
    for i, ch in enumerate(ref):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return ref[1:i]
    return None


def reference_year(ref):
    """Year of an EXFOR reference code such as (J,NIM/B,373,17,2016) or (J,NSE,110,289,199203)."""
    g = first_group(ref)
    m = re.match(r"([A-Z]),(.*)$", g or "")
    if not m:
        return ""
    last = m.group(2).split(",")[-1].strip()
    if re.fullmatch(r"\d{4}(\d{2})?", last):
        y = int(last[:4])
        if 1900 <= y <= 2100:
            return last[:4]
        yy = int(last[:2])                              # a few entries give the date as YYMM
        return ("19" if yy > 40 else "20") + last[:2]
    if re.fullmatch(r"\d{2}", last):
        return ("19" if int(last) > 40 else "20") + last
    return ""


def meta_of(sub0, sub):
    """Merge entry-level (subentry 001) and subentry-level bibliography."""
    bib = dict(sub0["bib"])
    bib.update(sub["bib"])

    def first(k):
        return bib[k][0]["text"] if k in bib and bib[k] else ""
    author = first("AUTHOR").strip("() ")
    first_author = author.split(",")[0].strip() if author else ""
    ref = first("REFERENCE")
    year = reference_year(ref)
    doi = ""
    m = re.search(r"doi:\s*([^\s]+)", ref, re.I)
    if m:
        doi = m.group(1)
    # STATUS codes: (TABLE), and the forms with a pointer to another subentry: (SPSDD,10135002), (DEP,10722002)
    st_items = re.findall(r"\(([A-Z]+)(?:,([0-9A-Z]{8}))?\)", " ".join(x["text"] for x in bib.get("STATUS", [])))
    status = ",".join(c for c, _ in st_items)
    status_ref = ";".join(f"{c}>{p}" for c, p in st_items if p)
    return {"title": first("TITLE"), "authors": author, "first_author": first_author,
            "reference": re.sub(r"\s*doi:.*$", "", ref, flags=re.I).strip(), "year": year, "doi": doi,
            "institute": first("INSTITUTE"), "facility": first("FACILITY"), "status": status,
            "status_ref": status_ref, "decay": parse_decay_data(bib.get("DECAY-DATA", []))}


def pick(cols, ptr, names):
    """First existing column among 'names' for pointer ptr (or no pointer)."""
    for n in names:
        for (cn, cp), idx in cols.items():
            if cn == n and cp in (ptr, ""):
                return idx
    return None


def pick_named(cols, ptr, names):
    """Like pick() but also returns the column name that was found."""
    for n in names:
        for (cn, cp), idx in cols.items():
            if cn == n and cp in (ptr, ""):
                return idx, n
    return None, None


def isomer_state(v):
    """State letter of an EXFOR ISOMER flag in a table of products: 0 ground state (G), 1 first isomer (M),
    2 second isomer (M2) ...; None for any other value (some entries use the column for something else)."""
    if v is None:
        return None
    r = round(v)
    if abs(v - r) > 1e-9 or r < 0 or r > 9:
        return None
    return "G" if r == 0 else ("M" if r == 1 else f"M{r}")


def extract(path, target_code, selection, quantities, emin, emax, psel=None):
    """Parse one entry file; return (datasets, points, warnings Counter)."""
    warnings = collections.Counter()
    if psel is not None:
        psel.set_target(target_code)
    entry_id, subs = parse_entry(path)
    if not subs:
        return [], [], warnings
    sub0 = subs[0]
    datasets, points = [], []
    for sub in subs[1:] if len(subs) > 1 else subs:
        if sub["data"] is None:
            continue
        rx_items = sub["bib"].get("REACTION") or sub0["bib"].get("REACTION") or []
        if not rx_items:
            continue
        meta = meta_of(sub0, sub)
        dcols, dunits, drows = sub["data"]
        # COMMON blocks: the one of subentry 001 applies to every subentry of the entry (for example a fixed
        # incident energy), the subentry's own COMMON adds to it or overrides it
        ccols, cunits, cvals = [], [], []
        for src in ([sub0["common"]] if (sub is not sub0 and sub0["common"]) else []) + \
                   ([sub["common"]] if sub["common"] else []):
            sc, su, sr = src
            for k_, c_ in enumerate(sc):
                val_ = sr[0][k_] if sr and k_ < len(sr[0]) else ""
                if c_ in ccols:
                    j_ = ccols.index(c_)
                    cunits[j_], cvals[j_] = su[k_], val_
                else:
                    ccols.append(c_)
                    cunits.append(su[k_])
                    cvals.append(val_)
        crows = [cvals]
        allcols = list(dcols) + list(ccols)
        allunits = list(dunits) + list(cunits)
        index = {}
        for k, c in enumerate(allcols):
            index.setdefault(c, k)
        for i_it, it in enumerate(rx_items):
            for i_mt, mt in enumerate(match_reactions(it["text"], target_code, selection)):
                ds_id = f"{sub['id']}.{i_it}.{i_mt}"          # identifies the dataset: reaction record of a subentry
                if quantities and mt["param"] not in quantities:
                    continue
                info = proj_info(mt["code"])
                proj_a, is_n = info["A"], mt["code"] == "N"
                pinfo = parse_product(mt["product"])
                filter_rows = psel is not None and not psel.is_all
                if filter_rows and pinfo["kind"] != "table" and not psel.accepts(pinfo):
                    continue                      # product known from the reaction field: skip the whole reaction
                ptr = it["ptr"]
                iE = pick(index, ptr, ["EN"])
                if iE is None and mt["param"] != "EN":
                    # resonance parameters (WID, WID/STR, ... as at n_TOF): the resonance energy is the DATA column of a
                    # sibling reaction item of the same subentry whose quantity is EN, for example (95-AM-243(N,0),,EN)
                    for it2 in rx_items:
                        if it2 is it:
                            continue
                        for tg2, pj2, pr2, pd2, rs2 in RX.findall(it2["text"]):
                            pp2 = (rs2.split(",")[1:] if rs2 else []) + ["", ""]
                            if tg2 == target_code and pp2[1] == "EN":
                                iE = pick(index, it2["ptr"], ["DATA"])
                                break
                        if iE is not None:
                            break
                iEmin = pick(index, ptr, ["EN-MIN"])
                iEmax = pick(index, ptr, ["EN-MAX"])
                iEmean = pick(index, ptr, ["EN-MEAN"])
                iEcm = pick(index, ptr, ["EN-CM"])
                idE, dE_name = pick_named(index, ptr, ["EN-ERR", "EN-RSL", "EN-RSL-HW", "EN-RSL-FW", "EN-ERR-D"])
                iV = pick(index, ptr, ["DATA"])
                if iV is None:
                    continue
                iErr = pick(index, ptr, ["ERR-T", "DATA-ERR"])
                iEs = pick(index, ptr, ["ERR-S"])
                iEsys = pick(index, ptr, ["ERR-SYS"])
                iAng = pick(index, ptr, ["ANG", "ANG-CM"])
                iEout = pick(index, ptr, ["E", "E-MEAN"])        # outgoing energy; E-MEAN when given as a bin mean
                iEoutMin = pick(index, ptr, ["E-MIN"])
                iEoutMax = pick(index, ptr, ["E-MAX"])
                if iEout is not None:
                    iEoutMin = iEoutMax = None
                iZ = pick(index, ptr, ["ELEMENT"]) if mt["product"].startswith("ELEM") else None
                iIso = pick(index, ptr, ["ISOMER"]) if mt["product"] == "ELEM/MASS" else None     # stays in 'extra' too
                iA = pick(index, ptr, ["MASS"]) if mt["product"] in ("ELEM/MASS", "MASS") else None
                used = {x for x in (iE, iEmin, iEmax, iEmean, iEcm, idE, iV, iErr, iEs, iEsys, iAng, iEout, iEoutMin, iEoutMax, iZ, iA)
                        if x is not None}
                n_pts, es = 0, []
                for r_ in drows:
                    row = list(r_) + list(crows[0] if crows else [])
                    row += [""] * (len(allcols) - len(row))

                    def num(i):
                        return exfor_float(row[i]) if i is not None and i < len(row) else None

                    def energy(i):
                        """(E_MeV, E_per_u, status) of column i for the current row."""
                        v = num(i)
                        if v is None:
                            return None, None, "empty"
                        return convert_energy(v, allunits[i], proj_a, is_n)

                    val = num(iV)
                    if val is None:
                        continue
                    product = mt["product"]
                    prow = pinfo
                    if pinfo["kind"] == "table":          # product given in the data table, row by row
                        if iZ is not None and num(iZ) is not None:
                            zz = int(round(num(iZ)))
                            sym = ELEMENTS[zz - 1].upper() if 0 < zz <= len(ELEMENTS) else str(zz)
                            aa = int(round(num(iA))) if iA is not None and num(iA) is not None else None
                            product = f"{zz}-{sym}" + (f"-{aa}" if aa else "")
                            if aa and iIso is not None:                  # ground state or isomer of the nuclide
                                st_ = isomer_state(num(iIso))
                                if st_:
                                    product += f"-{st_}"
                        elif iA is not None and num(iA) is not None:
                            product = f"MASS-{int(round(num(iA)))}"
                        prow = parse_product(product)
                        if filter_rows and not psel.accepts(prow):
                            continue
                    E = E_u = dE = None
                    e_src = e_unit = ""
                    if iE is not None:
                        E, E_u, st = energy(iE)
                        e_src, e_unit = "EN", allunits[iE]
                        if st == "unsupported":
                            warnings[("unit", e_unit)] += 1
                        elif st == "need_mass":
                            warnings[("per-nucleon energy without projectile mass", info["code"])] += 1
                    if E is None and E_u is None and iEmin is not None and iEmax is not None:
                        a, ua, s1 = energy(iEmin)
                        b, ub, s2 = energy(iEmax)
                        if a is not None and b is not None:
                            E, dE = (a + b) / 2.0, (b - a) / 2.0
                            E_u = (ua + ub) / 2.0 if ua is not None and ub is not None else None
                            e_src, e_unit = "EN-MIN/MAX", allunits[iEmin]
                    if E is None and E_u is None and iEmean is not None:
                        E, E_u, st = energy(iEmean)
                        if E is not None or E_u is not None:
                            e_src, e_unit = "EN-MEAN", allunits[iEmean]
                            if iEmin is not None and iEmax is not None:
                                a, _, _ = energy(iEmin)
                                b, _, _ = energy(iEmax)
                                if a is not None and b is not None:
                                    dE = (b - a) / 2.0
                    if dE is None and idE is not None and (E is not None):
                        v = num(idE)
                        if v is not None:
                            if allunits[idE].upper().strip() == "PER-CENT":
                                dE = abs(E) * v / 100.0
                            else:
                                dE, _, _ = convert_energy(v, allunits[idE], proj_a, is_n, allow_wavelength=False)
                            if dE is not None and dE_name == "EN-RSL-FW":
                                dE /= 2.0
                    if E is not None and ((emin is not None and E < emin) or (emax is not None and E > emax)):
                        continue
                    raw_unit = allunits[iV]
                    v_std, u_std = convert_value(val, raw_unit, mt["param"])

                    def err(i):
                        v = num(i)
                        if v is None:
                            return None
                        if allunits[i].upper() == "PER-CENT":
                            return abs(val) * v / 100.0 * (v_std / val if val else 1.0)
                        w, _ = convert_value(v, allunits[i], mt["param"])
                        return w
                    extra, extra_units = {}, {}
                    for k in range(len(allcols)):
                        if k in used or not row[k].strip():
                            continue
                        key_ = allcols[k][0] + (f"[{allcols[k][1]}]" if allcols[k][1] else "")
                        extra[key_] = row[k].strip()
                        extra_units[key_] = allunits[k]
                    if iEcm is not None and num(iEcm) is not None:
                        ecm, _, _ = energy(iEcm)
                        if ecm is not None:
                            extra["EN-CM_MeV"] = ecm
                            extra_units["EN-CM_MeV"] = "MEV"
                    e_out = None
                    if iEout is not None and num(iEout) is not None:
                        e_out, _, _ = convert_energy(num(iEout), allunits[iEout], None, False, allow_wavelength=False)
                    elif iEoutMin is not None and iEoutMax is not None and num(iEoutMin) is not None \
                            and num(iEoutMax) is not None:        # outgoing energy given as a bin: mid-point
                        a, _, _ = convert_energy(num(iEoutMin), allunits[iEoutMin], None, False, allow_wavelength=False)
                        b, _, _ = convert_energy(num(iEoutMax), allunits[iEoutMax], None, False, allow_wavelength=False)
                        if a is not None and b is not None:
                            e_out = (a + b) / 2.0
                    points.append({
                        "target": target_code, "projectile": info["label"], "projectile_code": info["code"],
                        "projectile_Z": info["Z"], "projectile_A": info["A"],
                        "process": mt["process"], "product": product, "product_label": prow["label"],
                        "product_Z": prow["Z"], "product_A": prow["A"], "product_state": prow["state"],
                        "branch": mt["branch"],
                        "quantity": mt["param"], "modifier": mt["modifier"],
                        "reaction_type": "complex" if mt["complex"] else "simple",
                        "entry": entry_id, "subentry": sub["id"], "first_author": meta["first_author"],
                        "year": meta["year"], "reference": meta["reference"], "status": meta["status"],
                        "E_MeV": E, "dE_MeV": dE, "E_per_u_MeV": E_u, "E_unit": e_unit, "E_source": e_src,
                        "value": v_std, "dvalue": err(iErr),
                        "value_unit": u_std, "raw_value": val, "raw_unit": raw_unit,
                        "err_stat": err(iEs), "err_sys": err(iEsys),
                        "angle_deg": num(iAng), "E_out_MeV": e_out,
                        "extra": json.dumps(extra, ensure_ascii=False) if extra else "",
                        "dataset": ds_id,
                        "extra_units": json.dumps(extra_units, ensure_ascii=False) if extra_units else "",
                    })
                    n_pts += 1
                    if E is not None:
                        es.append(E)
                if n_pts:
                    hint_s, hint_txt = decay_hint(meta.get("decay"), pinfo["Z"], pinfo["A"], pinfo["state"])
                    datasets.append({
                        "exfor_T12": hint_txt, "exfor_T12_s": hint_s,
                        "target": target_code, "projectile": info["label"], "projectile_code": info["code"],
                        "projectile_raw": mt["raw_code"], "projectile_Z": info["Z"], "projectile_A": info["A"],
                        "process": mt["process"], "product": mt["product"], "product_label": pinfo["label"],
                        "product_Z": pinfo["Z"], "product_A": pinfo["A"], "product_state": pinfo["state"],
                        "branch": mt["branch"],
                        "quantity": mt["param"], "reaction_type": "complex" if mt["complex"] else "simple",
                        "reaction_string": it["text"], "entry": entry_id, "subentry": sub["id"],
                        "n_points": n_pts, "E_min_MeV": min(es) if es else None, "E_max_MeV": max(es) if es else None,
                        "first_author": meta["first_author"], "authors": meta["authors"], "year": meta["year"],
                        "reference": meta["reference"],
                        "doi": meta["doi"], "facility": meta["facility"], "institute": meta["institute"],
                        "status": meta["status"], "status_ref": meta["status_ref"], "title": meta["title"],
                        "incident_energy_note": " ".join(
                            x["text"] for x in (sub["bib"].get("EN-SEL") or sub0["bib"].get("EN-SEL") or [])),
                        "dataset": ds_id,
                    })
    return datasets, points, warnings



# --------------------------------------------------------------------------
# references of the datasets
# --------------------------------------------------------------------------
JOURNALS = {
    "PR/C": "Phys. Rev. C", "PR/A": "Phys. Rev. A", "PR/B": "Phys. Rev. B", "PR/D": "Phys. Rev. D",
    "PR": "Phys. Rev.", "PRL": "Phys. Rev. Lett.", "NP/A": "Nucl. Phys. A", "NP/B": "Nucl. Phys. B",
    "NP": "Nucl. Phys.", "NSE": "Nucl. Sci. Eng.", "NIM/A": "Nucl. Instrum. Methods A",
    "NIM/B": "Nucl. Instrum. Methods B", "NIM": "Nucl. Instrum. Methods", "PL/B": "Phys. Lett. B",
    "PL": "Phys. Lett.", "ARI": "Appl. Radiat. Isot.", "RCA": "Radiochim. Acta", "EPJ/A": "Eur. Phys. J. A",
    "JIN": "J. Inorg. Nucl. Chem.", "JPJ": "J. Phys. Soc. Jpn.", "JP/G": "J. Phys. G", "ZP/A": "Z. Phys. A",
    "ZP": "Z. Phys.", "JRN": "J. Radioanal. Nucl. Chem.", "JRC": "J. Radioanal. Chem.", "CJP": "Can. J. Phys.",
    "ANE": "Ann. Nucl. Energy", "JNE": "J. Nucl. Energy", "JNE/AB": "J. Nucl. Energy A/B", "NC/A": "Nuovo Cim. A",
    "NC": "Nuovo Cim.", "HPA": "Helv. Phys. Acta", "NDS": "Nucl. Data Sheets", "JNST": "J. Nucl. Sci. Technol.",
    "JNM": "J. Nucl. Mater.", "ZN/A": "Z. Naturforsch. A", "JP/CS": "J. Phys. Conf. Ser.", "AUJ": "Aust. J. Phys.",
    "BAP": "Bull. Am. Phys. Soc.", "YF": "Yad. Fiz.", "SNP": "Sov. J. Nucl. Phys.", "AE": "At. Energ.",
    "SJA": "Sov. At. Energy", "ZET": "Zh. Eksp. Teor. Fiz.", "IZV": "Izv. Akad. Nauk SSSR, Ser. Fiz.",
    "BAS": "Bull. Acad. Sci. USSR, Phys. Ser.", "PAN": "Phys. At. Nucl.", "APP/B": "Acta Phys. Pol. B",
}
REF_TYPES = {"R": "Report", "C": "Conference", "T": "Thesis", "P": "Private communication", "B": "Book",
             "W": "Web", "S": "Source", "A": "Other", "X": "Other"}


def parse_reference(ref):
    """Split an EXFOR reference code into journal, volume, page and year and write it as a citation."""
    ref = re.sub(r"\s*doi:.*$", "", ref.strip(), flags=re.I)
    out = {"type": "", "journal": "", "volume": "", "page": "", "year": reference_year(ref), "text": ref}
    g = first_group(ref)
    m = re.match(r"([A-Z]),(.*)$", g or "")
    if not m:
        return out
    typ = m.group(1)
    parts = [p.strip() for p in m.group(2).split(",")]
    has_date = bool(parts) and re.fullmatch(r"\d{2}|\d{4}(\d{2})?", parts[-1]) is not None
    body = parts[:-1] if has_date else parts
    out["type"] = typ
    if typ == "J" and body:
        out["journal"] = JOURNALS.get(body[0], body[0])
        out["volume"] = body[1] if len(body) > 1 else ""
        out["page"] = body[2] if len(body) > 2 else ""
        txt = out["journal"] + (f" {out['volume']}" if out["volume"] else "") + (f" ({out['year']})" if out["year"] else "")
        out["text"] = txt + (f" {out['page']}" if out["page"] else "")
    else:
        what = REF_TYPES.get(typ, "Reference")
        bits = [b for b in body if b]
        txt = what + (" " + ", ".join(bits) if bits else "")
        out["text"] = txt + (f" ({out['year']})" if out["year"] else "")
    return out


def pretty_name(name):
    return re.sub(r"\.(?=[A-Za-z])", ". ", name.strip())


def format_authors(authors, n_auth=3):
    """'M.Avrigeanu,P.Bem,J.Mrazek' -> 'M. Avrigeanu, P. Bem and J. Mrazek' (first author et al. beyond n_auth)."""
    names = [pretty_name(a) for a in re.split(r"\s*,\s*", (authors or "").strip("() ")) if a.strip()]
    if not names:
        return ""
    if n_auth and len(names) > n_auth:
        return names[0] + " et al."
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def _ascii_key(first_author, year, entry):
    surname = re.split(r"[.\s]", (first_author or "EXFOR").strip())[-1] or "EXFOR"
    return re.sub(r"[^A-Za-z0-9]", "", surname) + (year or "") + "_" + entry


def reference_records(usage, meta, n_auth=3):
    """One record per EXFOR entry. usage: dicts with entry, projectile, product, quantity, e_lo, e_hi, n (and
    optionally first_author, year, reference); meta: {entry: dataset dict with title, doi, authors, ...}."""
    recs = collections.OrderedDict()
    for u in usage:
        e = u["entry"]
        m = meta.get(e, {})
        r = recs.setdefault(e, {
            "entry": e, "first_author": m.get("first_author") or u.get("first_author", ""),
            "authors": m.get("authors") or "", "year": str(m.get("year") or u.get("year") or "").split(".")[0],
            "reference_code": m.get("reference") or u.get("reference", ""), "doi": m.get("doi") or "",
            "title": m.get("title") or "", "institute": m.get("institute") or "",
            "projectiles": set(), "products": set(), "quantities": set(), "e_lo": None, "e_hi": None, "n": 0})
        r["projectiles"].add(u.get("projectile", ""))
        r["products"].add(u.get("product", ""))
        r["quantities"].add(u.get("quantity", ""))
        for k, fn in (("e_lo", min), ("e_hi", max)):
            v = u.get(k)
            if v is not None and v != "":
                v = float(v)
                r[k] = v if r[k] is None else fn(r[k], v)
        r["n"] += int(u.get("n") or 0)
    out = []
    for r in recs.values():
        pr = parse_reference(r["reference_code"])
        r["year"] = r["year"] or pr["year"]
        if r["authors"]:
            who = format_authors(r["authors"], n_auth)
        else:                                   # datasets file from an older version: only the first author is known
            who = (pretty_name(r["first_author"]) + " et al.") if r["first_author"] else ""
        r["citation"] = (", ".join(x for x in (who, pr["text"]) if x))
        r["pr"] = pr
        out.append(r)
    out.sort(key=lambda r: (r["year"] or "9999", r["first_author"], r["entry"]))
    return out


def _usage_line(r):
    prods = sorted(p for p in r["products"] if p)
    pr = ", ".join(prods[:6]) + (f", ... ({len(prods)} products)" if len(prods) > 6 else "")
    e = ""
    if r["e_lo"] is not None:
        e = f"; {r['e_lo']:.4g}-{r['e_hi']:.4g} MeV" if r["e_hi"] != r["e_lo"] else f"; {r['e_lo']:.4g} MeV"
    return (f"{', '.join(sorted(p for p in r['projectiles'] if p))} -> {pr or 'various'} "
            f"[{', '.join(sorted(q for q in r['quantities'] if q))}]{e}; {r['n']} points")


def write_references(folder, prefix, recs, formats, description=""):
    """Write the reference list as <prefix>_references.txt, .bib and .csv; returns the file names."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    names = []
    for fmt in formats:
        fn = f"{prefix}_references.{fmt}"
        if fmt == "txt":
            lines = [f"References of the EXFOR datasets used {description}".rstrip(),
                     f"{len(recs)} EXFOR entries. Generated from the bibliographic fields of EXFOR; check each "
                     f"reference against the original publication before citing it.", ""]
            for i, r in enumerate(recs, 1):
                lines.append(f"[{i}] {r['citation'] or 'EXFOR entry ' + r['entry']}.")
                if r["title"]:
                    lines.append(f"    Title: {r['title']}")
                ids = f"EXFOR entry {r['entry']}" + (f"   DOI: {r['doi']}" if r["doi"] else "")
                lines.append(f"    {ids}")
                lines.append(f"    Data used: {_usage_line(r)}")
                lines.append("")
            (folder / fn).write_text("\n".join(lines), encoding="utf-8")
        elif fmt == "bib":
            ent = []
            for r in recs:
                pr = r["pr"]
                kind = {"J": "article", "R": "techreport", "C": "inproceedings", "T": "phdthesis"}.get(pr["type"], "misc")
                f = [("author", " and ".join(pretty_name(a) for a in re.split(r"\s*,\s*", (r["authors"] or
                                                                                        r["first_author"]).strip("() ")) if a.strip())),
                     ("title", "{" + r["title"] + "}" if r["title"] else ""), ("year", r["year"])]
                if kind == "article":
                    f += [("journal", pr["journal"]), ("volume", pr["volume"]), ("pages", pr["page"])]
                else:
                    f += [("howpublished", r["reference_code"])]
                f += [("doi", r["doi"]), ("note", f"EXFOR entry {r['entry']}; data used: {_usage_line(r)}")]
                body = ",\n".join(f"  {k} = {{{v}}}" for k, v in f if v)
                ent.append(f"@{kind}{{{_ascii_key(r['first_author'], r['year'], r['entry'])},\n{body}\n}}")
            (folder / fn).write_text("\n\n".join(ent) + "\n", encoding="utf-8")
        elif fmt == "csv":
            cols = ["entry", "first_author", "authors", "year", "citation", "reference_code", "doi", "title", "institute",
                    "projectiles", "products", "quantities", "E_min_MeV", "E_max_MeV", "n_points"]
            with open(folder / fn, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=cols)
                w.writeheader()
                for r in recs:
                    w.writerow({"entry": r["entry"], "first_author": r["first_author"], "authors": r["authors"],
                                "year": r["year"], "citation": r["citation"], "reference_code": r["reference_code"],
                                "doi": r["doi"], "title": r["title"], "institute": r["institute"],
                                "projectiles": ";".join(sorted(r["projectiles"])), "products": ";".join(sorted(r["products"])),
                                "quantities": ";".join(sorted(r["quantities"])),
                                "E_min_MeV": "" if r["e_lo"] is None else r["e_lo"],
                                "E_max_MeV": "" if r["e_hi"] is None else r["e_hi"], "n_points": r["n"]})
        else:
            continue
        names.append(fn)
    return names


def parse_ref_formats(text):
    fmts = [f.strip().lower() for f in text.split(",") if f.strip()]
    bad = [f for f in fmts if f not in ("txt", "bib", "csv")]
    if bad:
        raise ValueError(f"unknown reference format '{bad[0]}' (use txt, bib, csv)")
    return fmts


def usage_from_datasets(datasets):
    """Reference usage rows from the dataset records."""
    out = []
    for d in datasets:
        label = d.get("product_label") or parse_product(d.get("product", ""))["label"]
        out.append({"entry": d["entry"], "projectile": d.get("projectile", ""), "product": label,
                    "quantity": d.get("quantity", ""), "e_lo": d.get("E_min_MeV"), "e_hi": d.get("E_max_MeV"),
                    "n": d.get("n_points", 0), "first_author": d.get("first_author", ""), "year": d.get("year", ""),
                    "reference": d.get("reference", "")})
    return out



# --------------------------------------------------------------------------
# names of quantities and units, and the emitted particle (labels of the ASCII files and of the plots)
# --------------------------------------------------------------------------
# name of a quantity in the first row of an ASCII file: EXFOR quantity code -> (readable name, ASCII name)
QTY_NAMES = {"SIG": ("Cross section", "sigma"), "DA": (r"$d\sigma/d\Omega$", "dsigma/dOmega"),
             "DE": (r"$d\sigma/dE$", "dsigma/dE"), "DA/DE": (r"$d^2\sigma/d\Omega dE$", "d2sigma/dOmega/dE"),
             "FY": ("Fission yield", "fission_yield"), "NU": (r"Neutron multiplicity $\bar{\nu}$", "nu"),
             "NU/DE": ("Neutron spectrum", "nu_spectrum"), "PN": ("Delayed-neutron emission probability", "Pn"),
             "PN/DE": ("Delayed-neutron spectrum", "Pn_spectrum"), "PY": ("Product yield", "yield"),
             "PY/DA/DE": ("Double-differential yield", "yield_dd"), "TTY": ("Thick-target yield", "thick_target_yield"),
             "TTY/PY/DA/DE": ("Thick-target double-differential yield", "thick_target_yield_dd"),
             "POL/DA": ("Polarisation", "polarisation"), "SIG/RAT": ("Cross-section ratio", "sigma_ratio"),
             "TRN": ("Transmission", "transmission"), "WID": ("Resonance width", "width"),
             "WID/STR": ("Resonance strength", "res_strength"), "WID/RED": ("Reduced width", "reduced_width"),
             "RYL": ("Reaction yield", "reaction_yield"), "RI": ("Resonance integral", "res_integral"),
             "STF": ("Strength function", "strength_function"), "INT": ("Integral", "integral"),
             "EN": ("Resonance energy", "res_energy")}
# EXFOR units that are written out whole: unit -> (readable text, ASCII text)
_UNIT_WHOLE = {"NO-DIM": ("", "-"), "ARB-UNITS": ("arb. units", "arb_units"),
               "PC/FIS": ("% per fission", "%/fission"), "PRD/FIS": ("products per fission", "products/fission"),
               "PRT/FIS": ("particles per fission", "particles/fission"),
               "PART/FIS": ("particles per fission", "particles/fission"),
               "PT/FIS/MEV": ("particles per fission per MeV", "particles/fission/MeV"), "PER-CENT": ("%", "%"),
               "PRD/INC": ("products per incident particle", "products/incident_particle"),
               "PRT/INC": ("particles per incident particle", "particles/incident_particle"),
               "PC/INC": ("% per incident particle", "%/incident_particle"),
               "PC/REAC": ("% per reaction", "%/reaction"), "PRD/REAC": ("products per reaction", "products/reaction"),
               "PRT/REAC": ("particles per reaction", "particles/reaction"),
               "P/IN/MEVSR": ("particles/(incident MeV sr)", "particles/(incident*MeV*sr)"),
               "PRD/MUC/SR": ("products/(\u00b5C sr)", "products/(uC*sr)"),
               "PRT/MUC/SR": ("particles/(\u00b5C sr)", "particles/(uC*sr)"),
               "PRD/MUCOUL": ("products/\u00b5C", "products/uC"), "FERMI": ("fm", "fm")}
# pieces of an EXFOR unit: EXFOR text -> (readable text, ASCII text); the longest piece is tried first
_UNIT_TOK = sorted([("MICRO-B", "\u00b5b", "ub"), ("MILLI-B", "mb", "mb"), ("MILLI-EV", "meV", "meV"), ("MUCOUL", "\u00b5C", "uC"), ("MUCI", "\u00b5Ci", "uCi"),
                    ("MU-B", "\u00b5b", "ub"), ("MUB", "\u00b5b", "ub"), ("MUA", "\u00b5A", "uA"),
                    ("MUC", "\u00b5C", "uC"), ("SR2", "sr\u00b2", "sr^2"), ("MEV2", "MeV\u00b2", "MeV^2"),
                    ("EV-SQ", "eV\u00b2", "eV^2"), ("RT-EV", "\u221aeV", "sqrt(eV)"), ("MEV", "MeV", "MeV"),
                    ("KEV", "keV", "keV"), ("GEV", "GeV", "GeV"), ("EV", "eV", "eV"), ("MBQ", "MBq", "MBq"),
                    ("KBQ", "kBq", "kBq"), ("MCI", "mCi", "mCi"), ("CI", "Ci", "Ci"), ("MB", "mb", "mb"),
                    ("NB", "nb", "nb"), ("SR", "sr", "sr"), ("B", "b", "b"), ("HR", "h", "h"), ("A", "A", "A"),
                    ("CM3", "cm\u00b3", "cm^3"), ("MOL", "mol", "mol"), ("DPS", "dps", "dps"), ("S", "s", "s"),
                    ("INC", "incident", "incident"), ("IN", "incident", "incident"), ("PRD", "products", "products"),
                    ("PRT", "particles", "particles"), ("PT", "particles", "particles"), ("P", "particles", "particles"), ("1", "1", "1")],
                   key=lambda t: -len(t[0]))
# the particle whose energy is the outgoing energy: EXFOR code -> (readable name, ASCII name)
EMITTED = {"N": ("Neutron", "neutron"), "P": ("Proton", "proton"), "D": ("Deuteron", "deuteron"),
           "T": ("Triton", "triton"), "A": ("Alpha particle", "alpha"), "HE3": ("3He", "3He"),
           "G": ("Photon", "gamma")}
_LABEL_TO_CODE = {"n": "N", "p": "P", "d": "D", "t": "T", "3He": "HE3", "alpha": "A", "gamma": "G"}
MASSIVE_CODES = {"N", "P", "D", "T", "A", "HE3"}


def unit_pretty(unit, ascii=False):
    """EXFOR unit as readable text (MB/SR/MEV -> mb/sr/MeV, P/MEVMUCSR -> particles/(MeV \u00b5C sr)), or, with
    ascii=True, as text for a column name without spaces and without non-ASCII characters
    (particles/(MeV*uC*sr)). A unit that is not known stays as EXFOR writes it."""
    u = (unit or "").strip()
    k = 1 if ascii else 0
    if not u:
        return "-" if ascii else ""
    if u in _UNIT_WHOLE:
        return _UNIT_WHOLE[u][k]
    if any(c.islower() for c in u):                     # already in the form of the converter (mb, mb/sr/MeV)
        return u
    out = []
    for part in u.split("/"):
        toks = []
        for piece in part.split("*"):                   # B*EV is a product
            rest = piece
            while rest:
                for t in _UNIT_TOK:
                    if rest.startswith(t[0]):
                        toks.append(t[1 + k])
                        rest = rest[len(t[0]):]
                        break
                else:
                    return u
        out.append(toks)
    joiner = "*" if ascii else " "
    text = ("*" if ascii else "\u00b7").join(out[0])
    for toks in out[1:]:
        text += "/" + (toks[0] if len(toks) == 1 else "(" + joiner.join(toks) + ")")
    return text


def emitted_code(rows):
    """EXFOR code (N, P, D, T, A, HE3, G) of the particle whose energy is the outgoing energy. EXFOR names the
    particle considered in the field after the quantity of the reaction (the modifier: G = gamma ray, N = neutron);
    without it the process, (d,n) -> N, or a light-particle product. It is worked out for every row, and it is given
    only when all the rows agree (the reactions to 30P with the process N and the neutron production with the product
    n are both neutron energies). None if it cannot be told."""
    codes = set()
    for r in rows:
        c = None
        for v in ((r.get("modifier") or "").upper(), (r.get("process") or "").upper()):
            if v in EMITTED:
                c = v
                break
        if c is None:
            c = _LABEL_TO_CODE.get(r.get("product_label"))
        codes.add(c)
    return next(iter(codes)) if len(codes) == 1 and None not in codes else None


def emitted_for_unit(rows):
    """The emitted particle for the unit of an emission spectrum: only when the reaction has no modifier."""
    return emitted_code(rows) if {(r.get("modifier") or "") for r in rows} == {""} else None


def unit_fits_quantity(qty, unit):
    """False when the unit that EXFOR gives for the data contradicts what the quantity code says: a cross section
    with a per-sr or per-energy unit, dsigma/dOmega without sr, dsigma/dE without a per-energy unit, d2sigma/dOmega/dE
    without both. In the EXFOR snapshot of the tests this is so for 601 of 137,042 subentries (0.4 per cent)."""
    U = (unit or "").upper()
    if U in ("ARB-UNITS", "NO-DIM", "", "PER-CENT") or "RAT" in U:
        return True
    per_e = any(t in U for t in ("MEV", "KEV", "/EV"))
    if qty == "SIG":
        return not ("/SR" in U or "/MEV" in U or "/KEV" in U)
    if qty == "DA":
        return "SR" in U
    if qty == "DE":
        return per_e
    if qty == "DA/DE":
        return "SR" in U and per_e
    return True


def quantity_name(qty, unit, has_eout, rows, ascii=True):
    """(name, unit text) of the value column. A cross section coded SIG, without a modifier, given against the
    energy of an emitted neutron, proton, deuteron, triton, 3He or alpha particle is an emission spectrum: it is
    named dsigma/dE and the unit gets /MeV (Section 14.13 of the manual). Gamma-ray lines and level cross sections
    coded SIG stay cross sections."""
    names = QTY_NAMES.get(qty)
    if names and not unit_fits_quantity(qty, unit):      # EXFOR's unit contradicts the code: show the code as it is
        names = None
    name = names[1 if ascii else 0] if names else (_safe_name((qty or "VALUE").replace("/", "_")) if ascii
                                                    else (qty or "VALUE"))
    u = unit_pretty(unit, ascii)
    if (qty == "SIG" and has_eout and emitted_code(rows) in MASSIVE_CODES
            and {(r.get("modifier") or "") for r in rows} == {""} and u not in ("", "-") and "arb" not in u
            and "eV" not in u):
        name, u = ("dsigma/dE" if ascii else r"$d\sigma/dE$"), u + "/MeV"
    return name, u

# --------------------------------------------------------------------------
# ASCII files (--ascii): one file per dataset, or fewer, longer files (--ascii-format)
# --------------------------------------------------------------------------
# independent variables that are columns of the CSV file: (field, label, unit, description)
CSV_VARS = [("E_MeV", "E", "MeV", "incident energy"),
            ("E_out_MeV", "Eout", "MeV", "outgoing energy (of the emitted particle)"),
            ("angle_deg", "angle", "deg", "angle"),
            ("product_Z", "Z_product", "-", "atomic number of the product"),
            ("product_A", "A_product", "-", "mass number of the product")]
# other EXFOR data headings that are independent variables: heading -> (label, description)
EXTRA_VARS = {
    "E-LVL": ("E_level", "excitation energy of the residual-nucleus level (EXFOR E-LVL)"),
    "E-EXC": ("E_excitation", "excitation energy (EXFOR E-EXC)"),
    "E-DGD": ("E_transfer", "energy transfer (EXFOR E-DGD)"),
    "E-CM": ("E_cm", "energy in the centre-of-mass system (EXFOR E-CM)"),
    "Q-VAL": ("Q_value", "Q-value (EXFOR Q-VAL)"),
    "COS": ("cos_theta", "cosine of the angle in the laboratory system (EXFOR COS)"),
    "COS-CM": ("cos_theta_cm", "cosine of the angle in the centre-of-mass system (EXFOR COS-CM)"),
    "LVL-NUMB": ("level_number", "number of the nuclear level (EXFOR LVL-NUMB)"),
    "MOMENTUM L": ("L", "orbital angular momentum (EXFOR MOMENTUM L)"),
    "SPIN J": ("J", "spin (EXFOR SPIN J)"),
    "KT": ("kT", "temperature as thermal energy kT, for Maxwellian averages (EXFOR KT)"),
    "TEMP": ("temperature", "temperature (EXFOR TEMP)"),
    "THICKNESS": ("thickness", "target thickness (EXFOR THICKNESS)"),
    "EN-DUMMY": ("E_dummy", "incident energy given as a dummy variable (EXFOR EN-DUMMY)"),
    "MASS": ("mass_number", "mass number (EXFOR MASS)"),
    "ELEMENT": ("atomic_number", "atomic number (EXFOR ELEMENT)"),
}
UNIT_NAMES = {"MEV": "MeV", "KEV": "keV", "EV": "eV", "GEV": "GeV", "MILLI-EV": "meV", "ADEG": "deg", "ARAD": "rad",
              "AMIN": "arcmin", "NO-DIM": "-", "": "-", "PER-CENT": "%", "DEG-K": "K", "DEG-C": "degC",
              "G/CM-SQ": "g/cm2", "ATOMS/B": "atoms/b", "B": "b", "MB": "mb"}


def _unit_name(u):
    u = (u or "").strip()
    return UNIT_NAMES.get(u.upper(), u or "-")


def _safe_name(s):
    return re.sub(r"[^A-Za-z0-9+.\-]+", "_", str(s)).strip("_")


def _num(v):
    return "nan" if v is None else format(float(v), ".10g")


def _jload(s):
    if isinstance(s, dict):
        return s
    if not s:
        return {}
    try:
        d = json.loads(s)
        return d if isinstance(d, dict) else {}
    except ValueError:
        return {}


VAR_ORDER = {"angle_deg": 0, "E_MeV": 1, "product_Z": 2, "E_out_MeV": 3, "product_A": 4}   # first column first


class AsciiWriter:
    """Write the datasets as plain-text files in columns; the first row has the column names with their units.

    mode 'dataset'  one file per dataset (a reaction record of a subentry). The columns are the independent
                    variables that vary in it (incident energy, outgoing energy, angle, product Z and A, or another
                    EXFOR heading with its proper label), then the value and its uncertainty. A 2D distribution is
                    one file with three columns plus the uncertainties (--ascii-no-errors leaves them out). The
                    uncertainties are, when the dataset gives them, the total (err_), the statistical (err_stat_) and
                    the systematic (err_sys_) uncertainty of the value and the uncertainty of the incident energy.
    mode 'entry'    one file per EXFOR entry (publication), quantity and unit: all its datasets stacked, one row per
                    point, with the columns entry/sub/product/branch that tell the datasets apart.
    mode 'quantity' one file per projectile, process, quantity and unit, with all the entries stacked.
    Variables that are constant in a dataset appear in the file name.

    In a file with two or more varying variables the first column is the one that labels the blocks (the angle, then
    the incident energy, then Z), and each block lists the following variables and the value; a blank line
    separates the blocks (not in the formats 'entry' and 'quantity')."""

    def __init__(self, folder, errors=True, limit=5000, mode="dataset", blank_lines=True, t12=None):
        self.folder, self.errors, self.limit, self.mode = Path(folder), errors, limit, mode
        self.blank_lines = blank_lines
        self.t12 = t12                      # function (Z, A, state) -> text of the half-life, or None
        self.index, self.names, self.skipped, self.no_unc = [], set(), 0, 0
        self.pending = collections.OrderedDict()

    def _key(self, r):
        base = (r.get("target"), r.get("projectile"), r.get("process"), r.get("quantity"), r.get("value_unit"))
        if self.mode == "quantity":
            return base
        if self.mode == "entry":
            return (r.get("entry"),) + base
        if r.get("dataset"):
            st = r.get("product_state") or ""
            return ("ds", r.get("target"), r["dataset"], r.get("projectile"), r.get("value_unit"),
                    "" if st in ("", "G") else st)       # isomers of a table of products: a file of their own
        return ("old", r.get("target"), r.get("entry"), r.get("subentry"), r.get("projectile"), r.get("process"),
                r.get("product"), r.get("branch"), r.get("quantity"), r.get("modifier"), r.get("reaction_type"),
                r.get("value_unit"))

    def add(self, points):
        groups = collections.OrderedDict()
        for r in points:
            if r.get("value") is not None:
                groups.setdefault(self._key(r), []).append(r)
        for key, pts in groups.items():
            if self.mode == "quantity":
                self.pending.setdefault(key, []).extend(pts)
            else:
                self._write(pts)

    @staticmethod
    def _extras(pts):
        """Numeric columns kept in 'extra': {heading: {'vals': [...], 'unit': EXFOR unit}}."""
        out = collections.OrderedDict()
        for i, p in enumerate(pts):
            d, u = _jload(p.get("extra")), _jload(p.get("extra_units"))
            for key, v in d.items():
                base = re.sub(r"\[[^\]]*\]$", "", key)
                if key.endswith("_MeV"):
                    continue
                try:
                    f = float(v)
                except (TypeError, ValueError):
                    continue
                e = out.setdefault(base, {"vals": [None] * len(pts), "unit": ""})
                e["vals"][i] = f
                if not e["unit"] and u.get(key):
                    e["unit"] = u[key]
        return out

    def _write(self, pts):
        if len(self.index) >= self.limit:
            self.skipped += 1
            return
        compact = self.mode != "dataset"
        r0 = pts[0]
        prod_varies = len({p.get("product") for p in pts}) > 1
        ex = self._extras(pts)
        have_units = any(p.get("extra_units") for p in pts)       # CSV files of older versions have none

        def distinct(vals):
            return len({v for v in vals if v is not None})

        cand = []                                           # the numeric independent variables present
        for fld, lab, unit, desc in CSV_VARS:
            if fld.startswith("product_") and not prod_varies:
                continue
            vals = [p.get(fld) for p in pts]
            if distinct(vals):
                cand.append({"fld": fld, "label": lab, "unit": unit, "desc": desc, "vals": vals})
        for base, e in ex.items():
            if base in EXTRA_VARS and distinct(e["vals"]) > 1:
                lab, desc = EXTRA_VARS[base]
                cand.append({"fld": "_ex:" + base, "label": lab, "unit": _unit_name(e["unit"]) if have_units else "?",
                             "desc": desc, "vals": e["vals"]})
        std = ("E_MeV", "E_out_MeV", "angle_deg")
        varying = [c for c in cand if distinct(c["vals"]) > 1]
        if compact:
            xcols = [c for c in cand if c["fld"] in std or c in varying]
        else:
            xcols = list(varying)
        if not xcols:                                       # nothing known varies: use any other varying heading
            other = [(b, e) for b, e in ex.items() if b not in EXTRA_VARS and distinct(e["vals"]) > 1
                     and not any(w in b.upper() for w in ("ERR", "MONIT", "FLAG", "ASSUM", "MISC"))][:2]
            for b, e in other:
                xcols.append({"fld": "_ex:" + b, "label": b.replace(" ", "_"),
                              "unit": _unit_name(e["unit"]) if have_units else "?",
                              "desc": f"EXFOR data heading {b}", "vals": e["vals"]})
            if not xcols:
                xcols = [c for c in cand if c["fld"] in std][:1]
        xcols = sorted(xcols, key=lambda c: VAR_ORDER.get(c["fld"], 5))      # the block variable first
        fixed = [c for c in cand if c["fld"] in std and c not in xcols and not compact]
        qty = _safe_name((r0.get("quantity") or "VALUE").replace("/", "_"))        # used in the file name
        unit = r0.get("value_unit") or "-"
        has_eout = any(c["fld"] == "E_out_MeV" for c in xcols)
        qname, qunit = quantity_name(r0.get("quantity"), r0.get("value_unit"), has_eout, pts)

        def sub3(p):
            return str(p.get("subentry") or "")[-3:]

        def who_of(p):
            nm = re.split(r"[.\s]", (p.get("first_author") or "").strip())[-1] if p.get("first_author") else ""
            return _safe_name(nm + str(p.get("year") or "")) or "unknown"

        cols = []                                           # (header, function of the row index)
        if compact:
            if self.mode == "quantity":
                cols += [("entry", lambda i: pts[i].get("entry") or "-"), ("author", lambda i: who_of(pts[i])),
                         ("sub", lambda i: sub3(pts[i]))]
            else:
                cols += [("sub", lambda i: sub3(pts[i]))]
            if prod_varies:
                cols.append(("product", lambda i: _safe_name(pts[i].get("product_label") or "none")))
            if len({p.get("branch") for p in pts}) > 1:
                cols.append(("branch", lambda i: pts[i].get("branch") or "-"))
        em = emitted_code(pts)
        for c in xcols:
            lab = f"E_{EMITTED[em][1]}" if (c["fld"] == "E_out_MeV" and em) else c["label"]
            c["shown"] = lab
            cols.append((f"{lab}[{c['unit']}]", lambda i, c=c: c["vals"][i]))
        # the uncertainties of the quantities that are plotted: of the incident energy (when it is a column) and of
        # the value, in every kind of file, whenever the dataset gives them
        has_dx = self.errors and any(c["fld"] == "E_MeV" for c in xcols) \
            and any(p.get("dE_MeV") is not None for p in pts)
        has_dy = self.errors and any(p.get("dvalue") is not None for p in pts)
        has_es = self.errors and any(p.get("err_stat") is not None for p in pts)     # statistical (ERR-S)
        has_esys = self.errors and any(p.get("err_sys") is not None for p in pts)    # systematic (ERR-SYS)
        if has_dx:
            cols.append(("err_E[MeV]", lambda i: pts[i].get("dE_MeV")))
        cols.append((f"{qname}[{qunit}]", lambda i: pts[i].get("value")))
        if has_dy:
            cols.append((f"err_{qname}[{qunit}]", lambda i: pts[i].get("dvalue")))
        if has_es:
            cols.append((f"err_stat_{qname}[{qunit}]", lambda i: pts[i].get("err_stat")))
        if has_esys:
            cols.append((f"err_sys_{qname}[{qunit}]", lambda i: pts[i].get("err_sys")))
        order = list(range(len(pts)))
        big = float("inf")
        key_cols = [c for c in xcols]
        if compact:
            order.sort(key=lambda i: (str(pts[i].get("entry")), sub3(pts[i]), str(pts[i].get("product")))
                       + tuple(big if c["vals"][i] is None else c["vals"][i] for c in key_cols))
        else:
            order.sort(key=lambda i: tuple(big if c["vals"][i] is None else c["vals"][i] for c in key_cols))
        rows = []
        for i in order:
            rows.append([(v if isinstance(v, str) else _num(v)) for v in (f(i) for _, f in cols)])
        header = [h for h, _ in cols]
        widths = [max([len(header[j])] + [len(r[j]) for r in rows]) for j in range(len(cols))]

        # ---- file name
        who = who_of(r0)
        unit_n = _safe_name(unit.replace("/", "-"))
        if self.mode == "quantity":
            parts = [target_dirname(r0["target"]), r0.get("projectile"), r0.get("process"), qty, unit_n, "all-entries"]
        elif self.mode == "entry":
            parts = [target_dirname(r0["target"]), r0.get("projectile"), r0.get("process"), qty, unit_n, who,
                     r0["entry"]]
        else:
            iso = (r0.get("product_state") or "") if prod_varies and (r0.get("product_state") or "") not in ("", "G") \
                else ""
            parts = [target_dirname(r0["target"]), r0.get("projectile"),
                     "products" if prod_varies else (r0.get("product_label") or "none"), qty]
            parts += [x for x in (r0.get("branch"), r0.get("modifier")) if x]
            parts += [who, f"{r0['entry']}-{sub3(r0)}"] + ([f"isomer-{iso}"] if iso else [])
            for c in fixed:
                v = next(x for x in c["vals"] if x is not None)
                parts.append(f"{c['label']}{format(v, '.4g')}{c['unit']}")
        stem = _safe_name("_".join(str(x) for x in parts if x))
        name, k = stem + ".dat", 2
        while name in self.names:
            name, k = f"{stem}_{k}.dat", k + 1
        self.names.add(name)
        self.folder.mkdir(parents=True, exist_ok=True)
        blocks = self.blank_lines and not compact and len(xcols) >= 2
        first = xcols[0]["vals"] if blocks else None
        with open(self.folder / name, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("  ".join(h.ljust(w) for h, w in zip(header, widths)).rstrip() + "\n")
            prev = None
            for i, r in zip(order, rows):
                if blocks and prev is not None and first[i] != prev:
                    fh.write("\n")                                   # a blank line between blocks
                prev = first[i] if blocks else None
                fh.write("  ".join(c.ljust(w) for c, w in zip(r, widths)).rstrip() + "\n")
        es = [p["E_MeV"] for p in pts if p.get("E_MeV") is not None]
        entries = sorted({p.get("entry") for p in pts})
        datasets = {p.get("dataset") or (p.get("subentry"), p.get("product")) for p in pts}
        one = len(entries) == 1
        self.index.append({
            "file": name, "format": self.mode, "target": target_dirname(r0["target"]), "projectile": r0.get("projectile"),
            "process": r0.get("process"),
            "product": "several" if prod_varies else r0.get("product_label"),
            "product_T12": (self.t12(r0.get("product_Z"), r0.get("product_A"), r0.get("product_state") or "")
                            if (self.t12 and not prod_varies and r0.get("product_Z") is not None and r0.get("product_A")) else ""),
            "quantity": r0.get("quantity"),
            "branch": r0.get("branch") if len({p.get("branch") for p in pts}) == 1 else "several",
            "entry": entries[0] if one else "several", "n_entries": len(entries), "n_datasets": len(datasets),
            "isomer": ((r0.get("product_state") or "") if prod_varies and (r0.get("product_state") or "") not in ("", "G")
                       and self.mode == "dataset" else ""),
            "first_author": r0.get("first_author") if one else "", "year": r0.get("year") if one else "",
            "reference": r0.get("reference") if one else "",
            "dimensions": len(xcols) if compact else len(varying) or len(xcols), "columns": " ".join(header),
            "uncertainty": ("+".join(n for n, f in (("total", has_dy), ("stat", has_es), ("sys", has_esys)) if f)
                            or ("none" if self.errors else "not written")),
            "variables": "; ".join(f"{c.get('shown', c['label'])}[{c['unit']}] = {c['desc']}" for c in xcols),
            "n_points": len(pts), "E_min_MeV": min(es) if es else "", "E_max_MeV": max(es) if es else "",
            "value_unit": unit})

    def finish(self):
        """Write the files held back (format 'quantity') and index.csv; return the number of files."""
        for pts in self.pending.values():
            self._write(pts)
        self.pending.clear()
        if not self.index:
            return 0
        fields = ["file", "format", "target", "projectile", "process", "product", "product_T12", "isomer", "quantity", "branch", "entry",
                  "n_entries", "n_datasets", "first_author", "year", "reference", "dimensions", "columns",
                  "uncertainty", "variables", "n_points", "E_min_MeV", "E_max_MeV", "value_unit"]
        with open(self.folder / "index.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            for r in self.index:
                w.writerow(_clean(r, fields))
        self.no_unc = sum(1 for r in self.index if r["uncertainty"] == "none")
        return len(self.index)



# --------------------------------------------------------------------------
# half-lives from the NUBASE2020 evaluation (SQLite database made by build_halflife_db.py)
# --------------------------------------------------------------------------
HALFLIFE_DB_DEFAULT = ""   # optional: fixed path of the half-life database
HL_MIN_ISOMER_S = 1e-3          # an isomer shorter than this cannot be measured by activation (Section 20 of the manual)
_T_UNITS = {"ys": 1e-24, "zs": 1e-21, "as": 1e-18, "fs": 1e-15, "ps": 1e-12, "ns": 1e-9, "us": 1e-6, "ms": 1e-3,
            "s": 1.0, "m": 60.0, "h": 3600.0, "d": 86400.0, "y": 365.25 * 86400.0,
            "ky": 365.25 * 86400.0 * 1e3, "My": 365.25 * 86400.0 * 1e6, "Gy": 365.25 * 86400.0 * 1e9,
            "Ty": 365.25 * 86400.0 * 1e12, "Py": 365.25 * 86400.0 * 1e15, "Ey": 365.25 * 86400.0 * 1e18,
            "Zy": 365.25 * 86400.0 * 1e21, "Yy": 365.25 * 86400.0 * 1e24}
_ISO_LETTERS = set("mnpqrx")    # NUBASE labels of isomers (and of levels with a half-life); i and j are analogue states
_DD_UNITS = {"SEC": 1.0, "S": 1.0, "MIN": 60.0, "M": 60.0, "HR": 3600.0, "H": 3600.0, "D": 86400.0,
             "YR": 365.25 * 86400.0, "Y": 365.25 * 86400.0, "MSEC": 1e-3, "USEC": 1e-6, "MICROSEC": 1e-6,
             "NSEC": 1e-9, "PSEC": 1e-12}


def _t_seconds(value, unit):
    """Half-life of a NUBASE row in seconds; None if it has no number (stable, particle-unstable, unknown)."""
    try:
        v = float(str(value).strip().replace("#", "").replace("~", "").lstrip("<>"))
    except ValueError:
        return None
    u = (unit or "").strip()
    return v * _T_UNITS[u] if u in _T_UNITS else None


def _num_or_none(text):
    try:
        return float(str(text).strip().replace("#", ""))
    except ValueError:
        return None


class HalfLives:
    """Half-lives of nuclides and of their isomers from the NUBASE2020 evaluation, and the assignment of the
    state of an EXFOR product (ground state, M, M1, M2 ...) to one of them (Section 20 of the manual)."""

    def __init__(self, path=None):
        self.path, self.con, self.cache, self.error = None, None, {}, ""
        cands = [path] if path else []
        cands += [HALFLIFE_DB_DEFAULT, os.environ.get("EXFOR_HALFLIFE_DB", ""),
                  str(Path(__file__).resolve().parent / "nuclear_halflives.db"),
                  str(Path(__file__).resolve().parent / "nuclear-data-files" / "nuclear_halflives.db")]
        for c in cands:
            if c and os.path.exists(c):
                try:
                    self.con = sqlite3.connect(f"file:{c}?mode=ro", uri=True)
                    self.con.execute("SELECT z, a, state, state_idx, exc_energy_kev, half_life, unit FROM halflives LIMIT 1")
                    self.path = c
                    break
                except sqlite3.Error as exc:
                    self.error = f"{c}: {exc}"
                    self.con = None
        if self.con is None and not self.error:
            self.error = "database not found"

    @property
    def available(self):
        return self.con is not None

    def rows(self, z, a):
        key = (z, a)
        if key not in self.cache:
            out = []
            if self.con is not None:
                cur = self.con.execute("SELECT state, state_idx, exc_energy_kev, half_life, unit FROM halflives "
                                       "WHERE z = ? AND a = ? ORDER BY state_idx ASC", (z, a))
                for state, idx, exc, hl, unit in cur.fetchall():
                    st = (state or "").strip()
                    letter = re.sub(r"\d+$", "", st.lower())
                    is_gs = (st.lower() == "g.s." or idx == 0)
                    kind = "gs" if is_gs else ("isomer" if (letter in _ISO_LETTERS or (idx or 99) <= 6) and
                                               letter not in ("i", "j") else "other")
                    out.append({"state": st, "idx": idx or 0, "exc": _num_or_none(exc), "exc_txt": (exc or "").strip(),
                                "hl": (hl or "").strip(), "unit": (unit or "").strip(),
                                "sec": _t_seconds(hl, unit), "stable": (hl or "").strip().upper() in ("STABLE", "STBL"),
                                "kind": kind})
            self.cache[key] = out
        return self.cache[key]

    @staticmethod
    def _text(r):
        if r["stable"]:
            return "stable"
        return f"{r['hl']} {r['unit']}".strip() if r["hl"] else ""

    def assign(self, z, a, state="", hint_s=None):
        """Half-life for the nuclide (z, a) in the EXFOR state '' (not given), 'G', 'M', 'M1', 'M2' ...
        Returns a dict {text, seconds, stable, basis, ambiguous} or None when no half-life can be given."""
        rows = self.rows(z, a)
        if not rows or z is None or not a:                  # Z = 0 is the neutron
            return None
        gs = next((r for r in rows if r["kind"] == "gs"), None)
        iso = [r for r in rows if r["kind"] == "isomer"]
        st = (state or "").upper().strip()

        def out(r, basis, amb=False):
            return {"text": self._text(r), "seconds": r["sec"], "stable": r["stable"], "basis": basis,
                    "ambiguous": amb}
        if st in ("", "G"):
            if gs is None:
                return None
            note = "ground state" if st == "G" else ("ground state (EXFOR gives no state)" if iso else "ground state")
            return out(gs, note)
        mm = re.fullmatch(r"M(\d?)", st)
        if not mm:
            return None                                        # L, G+M1, M+ ...: no half-life is assigned
        n = int(mm.group(1) or 1)
        cands = sorted([r for r in iso if r["sec"] is not None and r["sec"] >= HL_MIN_ISOMER_S],
                       key=lambda r: (r["exc"] if r["exc"] is not None else 1e12, r["idx"]))
        if not cands:
            return None
        desc = lambda r: f"isomer {r['state']}" + (f" {r['exc_txt']} keV" if r["exc_txt"] else "")
        if hint_s and len(cands) > 1:                          # the author's half-life decides between candidates
            best = min(cands, key=lambda r: abs(math.log10(r["sec"] / hint_s)))
            if abs(math.log10(best["sec"] / hint_s)) < 0.3:
                return out(best, f"{desc(best)}, chosen with the half-life given in the EXFOR entry")
        if len(cands) == 1:
            r = cands[0]
            return out(r, f"{desc(r)} (the only isomer with T1/2 >= 1 ms)")
        if n <= len(cands):
            r = cands[n - 1]
            others = ", ".join(f"{o['state']} {self._text(o)}" for o in cands if o is not r)
            return out(r, f"{desc(r)} (number {n} of the isomers with T1/2 >= 1 ms; others: {others})", amb=True)
        return None


def parse_decay_data(items):
    """Half-lives quoted in the DECAY-DATA field of an entry: {(Z, A, state): seconds}; the state is '' when none."""
    out = {}
    pat = re.compile(r"\((\d{1,3})-([A-Z]{1,2})-(\d{1,3})(?:-([A-Z0-9+]+))?,([0-9.]+(?:E[+-]?\d+)?)([A-Z]+)")
    for it in items or []:
        for m in pat.finditer(it.get("text", "") if isinstance(it, dict) else str(it)):
            z, _, a, st, val, unit = m.groups()
            if unit in _DD_UNITS:
                out.setdefault((int(z), int(a), st or ""), (float(val) * _DD_UNITS[unit], f"{val}{unit}"))
    return out


def decay_hint(decay, z, a, state):
    """The half-life that the entry quotes for the product: (seconds, text such as '10.15D') or (None, '')."""
    if not decay or not z or not a:
        return None, ""
    st = (state or "").upper()
    for k in [st] + {"": ["G"], "G": [""], "M": ["M1"], "M1": ["M"]}.get(st, []):
        v = decay.get((z, a, k))
        if v:
            return v
    return None, ""


def annotate_halflives(datasets, h):
    """Add the NUBASE half-life of the target and of the product to the dataset records."""
    for d in datasets:
        d.setdefault("product_T12", "")
        d.setdefault("product_T12_s", None)
        d.setdefault("product_T12_basis", "")
        d.setdefault("target_T12", "")
        if h is None:                           # half-lives not asked for: leave every half-life column empty
            d["exfor_T12"], d["exfor_T12_s"] = "", None
            continue
        if not h.available:
            continue
        tz, ta = _target_za(d.get("target"))
        if tz and ta:
            r = h.assign(tz, ta, "")
            if r:
                d["target_T12"] = r["text"]
        z, a = d.get("product_Z"), d.get("product_A")
        if z not in (None, "") and a and d.get("product") not in ("ELEM/MASS", "MASS", "ELEM"):
            r = h.assign(int(z), int(a), d.get("product_state") or "", d.get("exfor_T12_s"))
            if r:
                d["product_T12"] = r["text"] + ("?" if r["ambiguous"] else "")
                d["product_T12_s"] = r["seconds"]
                d["product_T12_basis"] = r["basis"]


def _target_za(code):
    m = re.match(r"(\d{1,3})-[A-Z]{1,2}-(\d{1,3})", code or "")
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def check_halflives(master, h):
    """--check-halflives: compare the assignment of NUBASE half-lives with the half-lives that all EXFOR entries quote
    in their DECAY-DATA fields, state by state."""
    if h is None or not h.available:
        print("No half-life database found: give it with --halflife-db or the variable EXFOR_HALFLIFE_DB.")
        return 1
    print(f"Half-life database: {h.path}\nReading the DECAY-DATA fields of the EXFOR entries ...", file=sys.stderr)
    items = collections.defaultdict(list)
    block = re.compile(r"^DECAY-DATA(.*(?:\n {11}.*)*)", re.M)
    n_entries = 0
    for path in sorted((master / "exforall").rglob("*.x4")):
        try:
            txt = path.read_text(encoding="latin-1")
        except OSError:
            continue
        got = False
        for m in block.finditer(txt):
            ls = m.group(0).split("\n")
            text = " ".join([ls[0][10:66]] + [x[11:66] for x in ls[1:]])
            for (z, a, st), (sec, _) in parse_decay_data([{"text": text}]).items():
                items[(z, a, st)].append(sec)
                got = True
        n_entries += got
    res = collections.defaultdict(lambda: [0, 0, 0, 0, 0])
    bad = []
    for (z, a, st), vals in items.items():
        if st not in ("", "G", "M", "M1", "M2") or not h.rows(z, a):
            continue
        T = statistics.median(vals)
        r, rh = h.assign(z, a, st), h.assign(z, a, st, T)
        ok = lambda x: bool(x and x["seconds"] and abs(math.log10(x["seconds"] / T)) < 0.15)
        c = res[st or "none"]
        c[0] += 1
        c[1] += ok(r)
        c[2] += ok(rh)
        c[3] += bool(r and r["ambiguous"])
        c[4] += r is None
        if not ok(r) and st in ("M", "M1", "M2"):
            bad.append((z, a, st, T, r["text"] if r else "-"))
    print(f"\n{len(items)} nuclide/state combinations quote a half-life in {n_entries} entries.")
    print("Agreement = the NUBASE half-life assigned to the EXFOR state is within 40 per cent of the median half-life "
          "quoted in the entries:\n")
    print(f"{'EXFOR state':12} {'nuclides':>9} {'rule':>8} {'with entry':>11} {'ambiguous':>10} {'no value':>9}")
    for st in ("G", "none", "M", "M1", "M2"):
        n, a1, a2, am, nv = res[st]
        if n:
            print(f"{st:12} {n:9d} {100 * a1 / n:7.1f}% {100 * a2 / n:10.1f}% {am:10d} {nv:9d}")
    if bad:
        print("\nIsomer states where the rule does not agree (nuclide, state, half-life in the entries in s, assigned):")
        for z, a, st, T, txt in sorted(bad)[:12]:
            print(f"  Z={z} A={a} {st:3} {T:.4g} s   {txt}")
    return 0


def t12_label(h, z, a, state, hint=None, product=False):
    """Short text for the console: '(T1/2 10.116 d)', '(stable)', with '?' when more than one isomer is possible.
    The light particles n, p, d, t, 3He and alpha get theirs like any other nuclide."""
    r = h.assign(z, a, state, hint) if (h is not None and h.available) else None
    if r is None:
        return ""
    return "(stable)" if r["stable"] else (f"(T1/2 {r['text']}{'?' if r['ambiguous'] else ''})" if r["text"] else "")

# --------------------------------------------------------------------------
# what is available: catalogue of a target, and search over all targets
# --------------------------------------------------------------------------
def _fmt(v, nd=4):
    return "" if v is None or v == "" else (f"{float(v):.{nd}g}")


def print_table(headers, rows, max_rows, file=sys.stdout):
    cols = list(zip(*([headers] + rows))) if rows else [[h] for h in headers]
    widths = [max(len(str(x)) for x in c) for c in cols]
    line = lambda r: "  ".join(str(x).ljust(w) if i < 3 else str(x).rjust(w) for i, (x, w) in enumerate(zip(r, widths)))
    print(line(headers), file=file)
    print("  ".join("-" * w for w in widths), file=file)
    for r in rows[:max_rows]:
        print(line(r), file=file)
    if len(rows) > max_rows:
        print(f"... {len(rows) - max_rows} more rows (see the CSV file, or raise --max-rows)", file=file)


def proj_rank(code):
    """Order of the projectiles in the tables: n, p, d, t, 3He, alpha, photons ... then heavy ions by Z and A."""
    order = [p[0] for p in PARTICLES]
    if code in order:
        return (0, order.index(code), 0)
    m = NUCL_CODE.match(code or "")
    return (1, int(m.group(1)), int(m.group(3))) if m else (2, 0, 0)


def projectile_summary(datasets):
    """Rows per projectile: entries, datasets, points (sorted by the order of proj_rank)."""
    g = {}
    for d in datasets:
        s_ = g.setdefault((d["projectile_code"], d["projectile"]), {"e": set(), "n": 0, "p": 0})
        s_["e"].add(d["entry"])
        s_["n"] += 1
        s_["p"] += d["n_points"]
    return [[lab, len(v["e"]), v["n"], v["p"]] for (code, lab), v in sorted(g.items(), key=lambda kv: proj_rank(kv[0][0]))]


def build_catalogue(datasets):
    """Rows (projectile, quantity, product) with the numbers of entries, datasets and points, energy range, years."""
    g = {}
    for d in datasets:
        k = (d["projectile"], d["quantity"], d.get("product_label") or "none")
        s = g.setdefault(k, {"entries": set(), "datasets": 0, "points": 0, "lo": None, "hi": None, "years": [], "t12": ""})
        s["t12"] = s["t12"] or d.get("product_T12", "")
        s["entries"].add(d["entry"])
        s["datasets"] += 1
        s["points"] += d["n_points"]
        for key, fn, v in (("lo", min, d.get("E_min_MeV")), ("hi", max, d.get("E_max_MeV"))):
            if v is not None and v != "":
                s[key] = v if s[key] is None else fn(s[key], v)
        if d.get("year"):
            s["years"].append(str(d["year"]))
    rows = []
    code_of = {d["projectile"]: d["projectile_code"] for d in datasets}
    for (proj, qty, prod), s in sorted(g.items(), key=lambda kv: (proj_rank(code_of[kv[0][0]]), kv[0][0], kv[0][1] != "SIG",
                                                                  kv[0][1], -kv[1]["points"])):
        rows.append({"projectile": proj, "quantity": qty, "product": prod, "T12": s["t12"], "entries": len(s["entries"]),
                     "datasets": s["datasets"], "points": s["points"], "E_min_MeV": s["lo"], "E_max_MeV": s["hi"],
                     "year_min": min(s["years"]) if s["years"] else "", "year_max": max(s["years"]) if s["years"] else ""})
    return rows


def build_entry_list(datasets):
    """One row per EXFOR entry with author, year, reference and what it contains."""
    g = collections.OrderedDict()
    for d in datasets:
        s = g.setdefault(d["entry"], {"author": d.get("first_author", ""), "year": str(d.get("year") or ""),
                                      "reference": d.get("reference", ""), "proj": set(), "qty": set(), "prod": set(),
                                      "points": 0, "lo": None, "hi": None})
        s["proj"].add(d["projectile"])
        s["qty"].add(d["quantity"])
        s["prod"].add(d.get("product_label") or "none")
        s["points"] += d["n_points"]
        for key, fn, v in (("lo", min, d.get("E_min_MeV")), ("hi", max, d.get("E_max_MeV"))):
            if v is not None and v != "":
                s[key] = v if s[key] is None else fn(s[key], v)
    rows = []
    for e, s in sorted(g.items(), key=lambda kv: (kv[1]["year"] or "9999", kv[0])):
        rows.append({"entry": e, "first_author": s["author"], "year": s["year"],
                     "reference": parse_reference(s["reference"])["text"], "projectiles": ";".join(sorted(s["proj"])),
                     "quantities": ";".join(sorted(s["qty"])), "n_products": len(s["prod"]), "points": s["points"],
                     "E_min_MeV": s["lo"], "E_max_MeV": s["hi"]})
    return rows


def parse_target_pattern(text):
    """Predicate on EXFOR target codes for --find: any, an element (Nb, Nb-*) or one isotope (Nb-93, Ti-nat)."""
    t = (text or "").strip()
    if t.lower() in ("", "any", "all", "*"):
        return (lambda code: True), "all targets"
    m = re.fullmatch(r"([A-Za-z]{1,2})(?:-?\*)?", t)
    if m and m.group(1).upper() in Z_OF and ("*" in t or not re.search(r"\d", t)):
        sym = m.group(1).upper()
        return (lambda code, sym=sym: code.split("-")[1] == sym), f"all isotopes of {sym.capitalize()}"
    code = parse_target(t)
    return (lambda c, code=code: c == code), target_dirname(code)


def find_scan(master, selection, psel, quantities, tpred, facility=None):
    """Light scan of all EXFOR entries (reaction fields only, no data tables): per target, the number of entries,
    reactions (datasets) and approximate data points, and the years of the entries."""
    stats = {}
    skipped_table = 0
    allfiles = facility_files(master, facility) if facility else sorted(str(p) for p in (master / "exforall").rglob("*.x4"))
    for path in allfiles:
        entry = year = None
        buf = None
        matches = []
        found = {}
        try:
            fh = open(path, encoding="latin-1")
        except OSError:
            continue
        with fh:
            for line in fh:
                if line.startswith("ENTRY"):
                    entry = line.split()[1]
                elif line.startswith("SUBENT"):
                    matches, buf = [], None
                elif line.startswith("REFERENCE") and year is None:
                    year = reference_year(line[11:66]) or ""
                elif line.startswith("REACTION"):
                    buf = [line[10:66]]
                elif buf is not None and line.startswith("           "):
                    buf.append(line[10:66])
                else:
                    if buf is not None:
                        for tgt, proj, proc, prod, rest in RX.findall("".join(x.strip() + " " for x in buf)):
                            if not tpred(tgt) or not selection.accepts(canon_code(proj)):
                                continue
                            parts = (rest.split(",")[1:] if rest else []) + ["", ""]
                            if quantities and parts[1] not in quantities:
                                continue
                            pinfo = parse_product(prod)
                            psel.set_target(tgt)
                            if not psel.is_all:
                                if pinfo["kind"] == "table":
                                    continue
                                if not psel.accepts(pinfo):
                                    continue
                            matches.append(tgt)
                        buf = None
                    if line.startswith("DATA ") and matches:
                        tok = line.split()
                        nl = int(tok[2]) if len(tok) > 2 and tok[2].isdigit() else 0
                        for tgt in matches:
                            found.setdefault(tgt, [0, 0])
                            found[tgt][0] += 1
                            found[tgt][1] += nl
                        matches = []
        for tgt, (n, pts) in found.items():
            s = stats.setdefault(tgt, {"entries": set(), "datasets": 0, "points": 0, "years": []})
            s["entries"].add(entry)
            s["datasets"] += n
            s["points"] += pts
            if year:
                s["years"].append(year)
    return stats


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
POINT_FIELDS = ["target", "projectile", "projectile_code", "projectile_Z", "projectile_A", "process", "product",
                "product_label", "product_Z", "product_A", "product_state", "branch", "quantity", "modifier", "reaction_type", "entry", "subentry", "first_author", "year",
                "reference", "status", "E_MeV", "dE_MeV", "E_per_u_MeV", "E_unit", "E_source", "value", "dvalue",
                "value_unit", "raw_value", "raw_unit", "err_stat", "err_sys", "angle_deg", "E_out_MeV", "extra",
                "dataset", "extra_units"]
DATASET_FIELDS = ["target", "projectile", "projectile_code", "projectile_raw", "projectile_Z", "projectile_A",
                  "process", "product", "product_label", "product_Z", "product_A", "product_state", "branch",
                  "quantity", "reaction_type", "reaction_string", "entry",
                  "subentry", "n_points", "E_min_MeV", "E_max_MeV", "first_author", "authors", "year", "reference", "doi",
                  "facility", "institute", "status", "title", "incident_energy_note", "dataset", "status_ref",
                  "exfor_T12", "exfor_T12_s", "product_T12", "product_T12_s", "product_T12_basis", "target_T12"]


def _clean(r, fields):
    return {k: ("" if r.get(k) is None else r.get(k)) for k in fields}


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Retrieve EXFOR data for a selectable set of projectiles on a given target isotope "
                    "(uses the IAEA-NDS exfor_master files).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Projectile examples:  d,p,he3,a  |  all  |  --projectiles=all,-n  |  n,g  |  12C,16O,Ne-*  |  light\n"
               "Product examples:     --product Nb-92m  |  92mNb,89Zr  |  \"Zr-*\"  |  n  |  none  |  all,-n\n"
               "List all accepted projectile names:  python exfor_retrieve.py --list-projectiles")
    ap.add_argument("--target", help="e.g. Nb-93, 93Nb, 41-NB-93, Ti-nat")
    ap.add_argument("--projectiles", default=None,
                    help="projectiles to retrieve: 'all' or a comma-separated list of particle names, heavy ions "
                         "(12C, Ne-*), groups (light, neutral, mesons, exotic, heavy-ions) and exclusions "
                         "(-n). Default: d,p,he3,a (all with --available and --find). Use --list-projectiles for "
                         "the full list.")
    ap.add_argument("--list-projectiles", action="store_true", help="print the accepted projectile names and exit")
    ap.add_argument("--product", "--products", dest="product", default="all",
                    help="final product(s) to keep: 'all' (default) or a comma-separated list such as Nb-92m,Zr-89, "
                         "92mNb, 41-NB-92-M, Zr-*, n, alpha, gamma, none; 'heavy' = every nuclide with Z>=3 (all "
                         "but n, p, d, t, 3He, alpha, gamma), 'residual' = heavy products except the target "
                         "nucleus itself; a leading - excludes (all,-n). A nuclide without a state letter "
                         "matches every state.")
    ap.add_argument("--product-exact", action="store_true",
                    help="match the EXFOR product code exactly as written (41-NB-92 then selects only data "
                         "with no state given)")
    ap.add_argument("--quantity", default="ALL",
                    help="EXFOR quantity code(s), e.g. SIG or SIG,DA (default ALL). The match is exact.")
    ap.add_argument("--facility", default=None,
                    help="only the entries measured at a facility: ntof (n_TOF at CERN), gelina, or a regular expression "
                         "searched in the FACILITY and INSTITUTE fields (for example 'LANSCE|WNR'). With --target all "
                         "(or without --target) every target of those entries is retrieved, one folder per target.")
    ap.add_argument("--emin", type=float, default=None, help="minimum incident energy in MeV")
    ap.add_argument("--emax", type=float, default=None, help="maximum incident energy in MeV")
    ap.add_argument("--master", default=None,
                    help="folder of the EXFOR master files. Default: MASTER_DEFAULT at the top of the script "
                         "(empty by default) if it exists, "
                         "else ./exfor_master, which is downloaded if it does not exist")
    ap.add_argument("--update", action="store_true", help="git pull the master files before the search")
    ap.add_argument("--master-info", action="store_true",
                    help="print the date of the latest data update of the master files, their git commit, and whether "
                         "GitHub has a newer snapshot; then exit")
    ap.add_argument("--out", default="data",
                    help="parent folder: the files of each target go to <out>/<target name>/ (default ./data)")
    ap.add_argument("--prefix", default=None, help="output file prefix (default EXFOR_<target>)")
    ap.add_argument("--json", action="store_true", help="also write <prefix>_datasets.json and <prefix>_data.jsonl")
    ap.add_argument("--summary-only", action="store_true",
                    help="parse everything and print the summary, but write no files (useful before --projectiles all)")
    ap.add_argument("--available", nargs="?", const="catalogue", choices=["catalogue", "entries"], default=None,
                    help="show what EXFOR has for the target, without retrieving the data: 'catalogue' (default) = one "
                         "row per projectile, quantity and product; 'entries' = one row per EXFOR entry. The table is "
                         "also written as a CSV file (not with --summary-only). Projectiles default to all.")
    ap.add_argument("--find", action="store_true",
                    help="search all targets: which targets have data for the projectiles, product and quantity "
                         "given? --target can limit it to an element (Nb-*); projectiles default to all")
    ap.add_argument("--ascii", action="store_true",
                    help="also write each dataset as its own ASCII file in columns, with the units in the first row "
                         "(2D distributions: one file with three columns), in <out>/<target>/ascii/")
    ap.add_argument("--ascii-format", choices=["dataset", "entry", "quantity"], default="dataset",
                    help="with --ascii: 'dataset' (default) one file per dataset; 'entry' one file per EXFOR entry, "
                         "quantity and unit; 'quantity' one file per projectile, process, quantity and unit. The last "
                         "two make far fewer files (fission yields, fragment tables) and add columns that tell the "
                         "datasets apart")
    ap.add_argument("--ascii-no-blanks", action="store_true",
                    help="with --ascii: do not put a blank line between the blocks of a 2D file (the default, which "
                         "reads well and is what gnuplot expects)")
    ap.add_argument("--ascii-dir", default=None, help="folder for the ASCII files (default <out>/<target>/ascii)")
    ap.add_argument("--ascii-no-errors", action="store_true",
                    help="with --ascii: leave out the uncertainty columns (the files have them by default, also the "
                         "2D files, when the dataset gives them)")
    ap.add_argument("--ascii-errors", action="store_true", help=argparse.SUPPRESS)       # kept: now the default
    ap.add_argument("--max-ascii", type=int, default=5000, help="maximum number of ASCII files (default 5000)")
    ap.add_argument("--halflife-db", default=None,
                    help="SQLite database of NUBASE2020 half-lives. Default: HALFLIFE_DB_DEFAULT at the top of the "
                         "half-life section (empty by default), then the environment variable EXFOR_HALFLIFE_DB, then a file next "
                         "to the script. Without a database no half-lives are shown")
    ap.add_argument("--halflife", action="store_true",
                    help="print the NUBASE2020 half-life next to each isotope (target, products) in the summaries, the "
                         "catalogue and the target search, and write it in the datasets file and the ASCII index. "
                         "Off by default; --halflife-db also switches it on")
    ap.add_argument("--check-halflives", action="store_true",
                    help="check the half-life assignment against the half-lives quoted in the DECAY-DATA fields of all "
                         "EXFOR entries (about a minute), print the agreement by state and exit")
    ap.add_argument("--max-rows", type=int, default=100, help="maximum rows printed by --available and --find "
                                                              "(default 100; the CSV files have all rows)")
    ap.add_argument("--references", action="store_true",
                    help="also write the list of references of the retrieved datasets (<prefix>_references.txt, "
                         ".bib and .csv; see --ref-format)")
    ap.add_argument("--ref-format", default="txt,bib", help="formats of the reference list: txt, bib, csv "
                                                           "(comma list, default txt,bib)")
    ap.add_argument("--ref-authors", type=int, default=3,
                    help="authors written in a reference: all if there are at most this many, otherwise the first "
                         "one and 'et al.' (default 3; 0 = always all)")
    ap.add_argument("--jobs", type=int, default=min(8, os.cpu_count() or 1), help="processes for the file scan")
    ap.add_argument("--version", action="version", version=f"exfor_retrieve {__version__} (build {__build__})")
    args = ap.parse_args(argv)
    args.master = args.master or default_master()

    if args.list_projectiles:
        print_projectile_table()
        return 0
    if args.master_info:
        if args.update:
            ensure_master(args.master, update=True)
        master_info(args.master)
        return 0
    all_targets = bool(args.facility) and (not args.target or args.target.strip().lower() in ("any", "all", "*"))
    if not args.target and not args.find and not args.check_halflives and not all_targets:
        ap.error("--target is required (or use --list-projectiles, --find, --check-halflives or --facility)")
    if args.projectiles is None:
        args.projectiles = ("all" if (args.available or args.find) else
                            "n" if re.fullmatch(r"n[-_ ]?tof|gelina", args.facility or "", re.I) else "d,p,he3,a")
    try:
        ref_formats = parse_ref_formats(args.ref_format)
        selection = Selection(args.projectiles)
        psel = ProductSelection(args.product, exact=args.product_exact)
        if args.find or all_targets:
            tpred, tdesc = parse_target_pattern(args.target)
        elif not args.check_halflives:
            target = parse_target(args.target)
    except ValueError as exc:
        ap.error(str(exc))
    quantities = None if args.quantity.upper() == "ALL" else {q.strip().upper() for q in args.quantity.split(",")}
    master = ensure_master(args.master, update=args.update)
    use_hl = args.halflife or bool(args.halflife_db)
    HL = HalfLives(args.halflife_db) if (use_hl or args.check_halflives) else None
    if args.check_halflives:
        return check_halflives(master, HL)
    if HL is not None and not HL.available:
        print(f"--halflife: no half-life database ({HL.error}). Give it with --halflife-db or the variable "
              f"EXFOR_HALFLIFE_DB (Section 10.2 of the manual).", file=sys.stderr)
    if all_targets and not args.find:
        # --facility without a target: find the targets of those entries and run the retrieval once per target
        stats = find_scan(master, selection, psel, quantities, tpred, args.facility)
        targets = sorted(stats, key=lambda c: (int(c.split("-")[0]), c))
        print(f"--facility {args.facility}: {len(targets)} targets with data: "
              + ", ".join(target_dirname(t) for t in targets), file=sys.stderr)
        base = list(sys.argv[1:] if argv is None else argv)
        base = [a for i, a in enumerate(base) if not (a == "--target" or a.startswith("--target=")
                or (i > 0 and base[i - 1] == "--target"))]
        rc = 0
        for t in targets:
            print(f"\n=== {target_dirname(t)} ===", file=sys.stderr)
            rc = max(rc, main(base + ["--target", t]) or 0)
        return rc
    if args.find:
        stats = find_scan(master, selection, psel, quantities, tpred, args.facility)
        rows = []
        for code, st in sorted(stats.items(), key=lambda kv: (int(kv[0].split("-")[0]), int(kv[0].split("-")[2]))):
            tz_, ta_ = _target_za(code)
            r_ = HL.assign(tz_, ta_, "") if (HL is not None and HL.available and ta_) else None
            rows.append([target_dirname(code), r_["text"] if r_ else "", len(st["entries"]), st["datasets"],
                         st["points"], min(st["years"]) if st["years"] else "",
                         max(st["years"]) if st["years"] else ""])
        print(f"Search over {tdesc}: projectiles {args.projectiles}, product {args.product}, quantity "
              f"{args.quantity}.\n{len(rows)} targets with data (entries counted once per target; datasets = reaction "
              f"records; points are counted from the data tables headers and are approximate; energy limits are "
              f"not applied).\n")
        print_table(["target", "T1/2", "entries", "datasets", "points~", "year_min", "year_max"], rows, args.max_rows)
        if not args.summary_only:
            out = Path(args.out)
            out.mkdir(parents=True, exist_ok=True)
            fn = out / ("EXFOR_find_" + re.sub(r"[^A-Za-z0-9+.-]+", "_", f"{args.target or 'all'}_{args.projectiles}_{args.product}_{args.quantity}") + ".csv")
            with open(fn, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["target", "T1/2", "entries", "datasets", "points_approx", "year_min", "year_max"])
                w.writerows(rows)
            print(f"\nTable written to {fn.resolve()}", file=sys.stderr)
        return 0
    out = Path(args.out) / target_dirname(target)
    prefix = args.prefix or f"EXFOR_{target.split('-', 1)[1]}"

    n_files, hits = find_candidate_files(master, build_prefilter(target), args.jobs, args.facility)
    prod_note = "" if psel.is_all else f"; products: {args.product}" + (" (exact codes)" if args.product_exact else "")
    print(f"Scanned {n_files} EXFOR entries (master files of {master_date(master) or 'unknown date'}): "
          f"{len(hits)} contain {target} as target"
          + (f" and pass --facility {args.facility}" if args.facility else "") + " "
          f"(projectiles requested: {args.projectiles}{prod_note}).", file=sys.stderr)

    if args.available:
        avail = []
        for f in hits:
            try:
                d, _, _ = extract(f, target, selection, quantities, args.emin, args.emax, psel)
            except Exception as exc:
                print(f"  warning: could not parse {f}: {exc}", file=sys.stderr)
                continue
            annotate_halflives(d, HL)
            avail += d
        entries_n = len({d["entry"] for d in avail})
        tz_, ta_ = _target_za(target)
        t_lab = t12_label(HL, tz_, ta_, "") if ta_ else ""
        print(f"\nWhat EXFOR has for {target_dirname(target)}{(' ' + t_lab) if t_lab else ''} (projectiles {args.projectiles}, product {args.product}, "
              f"quantity {args.quantity}): {entries_n} entries, {len(avail)} datasets, "
              f"{sum(d['n_points'] for d in avail)} data points.\n")
        print("By projectile:")
        print_table(["projectile", "entries", "datasets", "points"], projectile_summary(avail), 40)
        print()
        if args.available == "entries":
            rows = build_entry_list(avail)
            print_table(["entry", "author", "year", "reference", "projectiles", "quantities", "products", "points",
                         "E_min", "E_max"],
                        [[r["entry"], r["first_author"], r["year"], r["reference"], r["projectiles"], r["quantities"],
                          r["n_products"], r["points"], _fmt(r["E_min_MeV"]), _fmt(r["E_max_MeV"])] for r in rows],
                        args.max_rows)
            name, fields = f"{prefix}_entries.csv", ["entry", "first_author", "year", "reference", "projectiles",
                                                      "quantities", "n_products", "points", "E_min_MeV", "E_max_MeV"]
        else:
            rows = build_catalogue(avail)
            print_table(["projectile", "quantity", "product", "T1/2", "entries", "datasets", "points", "E_min", "E_max",
                         "years"],
                        [[r["projectile"], r["quantity"], r["product"], r["T12"], r["entries"], r["datasets"], r["points"],
                          _fmt(r["E_min_MeV"]), _fmt(r["E_max_MeV"]),
                          (f"{r['year_min']}-{r['year_max']}" if r["year_min"] else "")] for r in rows], args.max_rows)
            name, fields = f"{prefix}_catalogue.csv", ["projectile", "quantity", "product", "T12", "entries", "datasets",
                                                        "points", "E_min_MeV", "E_max_MeV", "year_min", "year_max"]
        if not args.summary_only:
            out.mkdir(parents=True, exist_ok=True)
            with open(out / name, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=fields)
                w.writeheader()
                for r in rows:
                    w.writerow(_clean(r, fields))
            print(f"\nTable written to {(out / name).resolve()}", file=sys.stderr)
        return 0

    write = not args.summary_only
    fh_data = fh_jsonl = writer = None
    if write:
        out.mkdir(parents=True, exist_ok=True)
        fh_data = open(out / f"{prefix}_data.csv", "w", newline="", encoding="utf-8")
        writer = csv.DictWriter(fh_data, fieldnames=POINT_FIELDS)
        writer.writeheader()
        if args.json:
            fh_jsonl = open(out / f"{prefix}_data.jsonl", "w", encoding="utf-8")

    ascii_w = None
    if args.ascii and write:
        ascii_w = AsciiWriter(Path(args.ascii_dir) if args.ascii_dir else out / "ascii", not args.ascii_no_errors,
                              args.max_ascii, args.ascii_format, not args.ascii_no_blanks,
                              t12=(lambda z, a, st: ((HL.assign(int(z), int(a), st) or {}).get("text", ""))) if (HL and HL.available) else None)
    datasets, n_points = [], 0
    warnings = collections.Counter()
    prod_pts, prod_entries = collections.Counter(), collections.defaultdict(set)
    prod_info = {}
    prod_hints = collections.defaultdict(list)       # half-lives that the entries quote, by product label
    try:
        for f in hits:
            try:
                d, p, w = extract(f, target, selection, quantities, args.emin, args.emax, psel)
            except Exception as exc:  # keep going if one malformed entry fails
                print(f"  warning: could not parse {f}: {exc}", file=sys.stderr)
                continue
            annotate_halflives(d, HL)
            for d_ in d:
                if d_.get("exfor_T12_s"):
                    prod_hints[d_["product_label"]].append(d_["exfor_T12_s"])
            datasets += d
            warnings.update(w)
            n_points += len(p)
            if ascii_w:
                ascii_w.add(p)
            for r in p:
                prod_pts[r["product_label"]] += 1
                prod_entries[r["product_label"]].add(r["entry"])
                if r["product_label"] not in prod_info and r.get("product_Z") is not None and r.get("product_A") \
                        and r["product"] not in ("ELEM/MASS", "MASS", "ELEM"):
                    prod_info[r["product_label"]] = (r["product_Z"], r["product_A"], r.get("product_state") or "")
            if write:
                for r in p:
                    writer.writerow(_clean(r, POINT_FIELDS))
                    if fh_jsonl:
                        fh_jsonl.write(json.dumps(r, ensure_ascii=False) + "\n")
    finally:
        for fh in (fh_data, fh_jsonl):
            if fh:
                fh.close()

    datasets.sort(key=lambda r: (r["projectile"], r["quantity"], r["product"], r["entry"], r["subentry"]))
    if write:
        with open(out / f"{prefix}_datasets.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=DATASET_FIELDS)
            w.writeheader()
            for r in datasets:
                w.writerow(_clean(r, DATASET_FIELDS))
        if args.json:
            with open(out / f"{prefix}_datasets.json", "w", encoding="utf-8") as fh:
                json.dump({"target": target, "projectiles": args.projectiles, "datasets": datasets},
                          fh, ensure_ascii=False, indent=1)

    # console summary
    tz_, ta_ = _target_za(target)
    t_lab = t12_label(HL, tz_, ta_, "") if ta_ else ""
    print(f"\nTarget {target}{(' ' + t_lab) if t_lab else ''}: {len(datasets)} datasets, {n_points} data points",
          file=sys.stderr)
    by_proj, by_qty = {}, collections.Counter()
    for d in datasets:
        s = by_proj.setdefault(d["projectile"], {"n": 0, "entries": set(), "pts": 0, "products": set(),
                                                 "code": d["projectile_code"]})
        s["n"] += 1
        s["entries"].add(d["entry"])
        s["pts"] += d["n_points"]
        s["products"].add(d["product"])
        by_qty[d["quantity"]] += d["n_points"]
    print(f"{'projectile':12} {'code':9} {'datasets':>8} {'entries':>8} {'points':>9} {'products':>8}", file=sys.stderr)
    for lab, s in sorted(by_proj.items(), key=lambda kv: -kv[1]["pts"]):
        print(f"{lab:12} {s['code']:9} {s['n']:8d} {len(s['entries']):8d} {s['pts']:9d} {len(s['products']):8d}",
              file=sys.stderr)
    if by_qty:
        top = ", ".join(f"{q or '(none)'}: {n}" for q, n in by_qty.most_common(8))
        print(f"\nPoints by quantity (top): {top}", file=sys.stderr)
    if prod_pts:
        labs = {lab: (t12_label(HL, *prod_info[lab], hint=(statistics.median(prod_hints[lab]) if prod_hints[lab] else None),
                                 product=True)
                      if lab in prod_info else "") for lab in prod_pts}
        if args.summary_only:
            wide = HL is not None and HL.available
            print(f"\n{'product':14} " + (f"{'T1/2':22}" if wide else "") + f"{'entries':>8} {'points':>9}   (top 40 products)",
                  file=sys.stderr)
            for lab, n in prod_pts.most_common(40):
                t_ = labs[lab][1:-1].replace("T1/2 ", "") if labs[lab] else ""
                print(f"{lab:14} " + (f"{t_:22}" if wide else "") + f"{len(prod_entries[lab]):8d} {n:9d}", file=sys.stderr)
        else:
            top = ", ".join(f"{lab}{(' ' + labs[lab]) if labs[lab] else ''}: {n}" for lab, n in prod_pts.most_common(8))
            print(f"Points by product (top): {top}", file=sys.stderr)
        if any(v.endswith("?)") for v in labs.values()):
            print("  ? = the state M could be more than one isomer of the nuclide; the half-life of the isomer chosen "
                  "by the rule is shown (Section 10.2 of the manual).", file=sys.stderr)
    for (kind, what), n in sorted(warnings.items(), key=lambda kv: -kv[1]):
        if kind == "unit":
            print(f"warning: {n} points have the incident energy in the unit '{what}', which cannot be converted "
                  f"to MeV: E_MeV left empty (see raw energy in the entry).", file=sys.stderr)
        else:
            print(f"warning: {n} points ({what}): {kind}; E_MeV left empty, E_per_u_MeV given.", file=sys.stderr)
    if write:
        names = [f"{prefix}_data.csv", f"{prefix}_datasets.csv"]
        if args.json:
            names += [f"{prefix}_datasets.json", f"{prefix}_data.jsonl"]
        if ascii_w:
            n_files = ascii_w.finish()
            what = {"dataset": "one per dataset", "entry": "one per entry, quantity and unit",
                    "quantity": "one per quantity and unit"}[ascii_w.mode]
            names.append(f"{ascii_w.folder}{os.sep}  ({n_files} ASCII files, {what}, and index.csv)")
            if ascii_w.no_unc:
                names.append(f"  {ascii_w.no_unc} of the {n_files} files have no uncertainty column because EXFOR gives "
                             f"none for those data (column uncertainty of index.csv)")
            if ascii_w.skipped:
                print(f"warning: the limit of {args.max_ascii} ASCII files was reached; {ascii_w.skipped} datasets "
                      f"have no ASCII file. Use --ascii-format entry (one file per publication) or quantity (one "
                      f"file per quantity), restrict the selection, or raise --max-ascii.", file=sys.stderr)
        if args.references:
            meta = {d["entry"]: d for d in datasets}
            recs = reference_records(usage_from_datasets(datasets), meta, args.ref_authors)
            names += write_references(out, prefix, recs, ref_formats,
                                      f"for {target_dirname(target)} (projectiles {args.projectiles}, product "
                                      f"{args.product}, quantity {args.quantity})")
        print(f"\nFiles written to {out.resolve()}:\n  " + "\n  ".join(names), file=sys.stderr)
    else:
        print("\n(--summary-only: no files written)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
