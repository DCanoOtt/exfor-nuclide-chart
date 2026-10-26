# User guide — using the EXFOR nuclide chart

The page is also documented inside itself: press **Instructions** (top of the page) and **Back** to return.

## 1. The chart

Each square is a target nuclide (x = neutron number N, y = atomic number Z). Its colour (and optionally the number in
it) shows the quantity chosen in **Count**: data sets, EXFOR entries, data points, or RP resonances. Dashed outline =
radioactive nuclide. Scroll to zoom, drag to move; element names and axis labels scale with the zoom. The tick
**element names** writes the element name left of the leftmost nuclide that has data under the current filters.
Palette, background, scale (and its top value) and the numbers in the cells are set in the display controls.

## 2. Filters

| Control | Meaning |
|---|---|
| Neutron-induced reaction type | EXFOR process, e.g. TOT, G (n,γ), F, EL, INL, ... *This menu decides what is counted.* |
| Quantity | tick one or several. The list starts with the combinations **SIG**, **RP**, **SIG+RP**, then every EXFOR code alphabetically. |
| Measurement method | all data / time-of-flight only (METHOD TOF) / everything except time-of-flight. |
| Minimum points per data set | only data sets with at least this many points. |
| Neutron energy range | in eV, keV or MeV (MeV default); modes *overlaps*, *lies inside*, *covers* the range. Data sets without an energy are excluded when the range is used. |
| Year range | publication year of the main reference; default is the full period. |

**SIG, RP and SIG+RP.** RP (resonance parameters) is not one EXFOR code but a family (`WID`, `J`, `L`, `GN`, `GG`, ...,
and `EN` in resonance-parameter reactions). The number for SIG+RP is the sum of both sets. "RP resonances" counts rows
of RP tables.

## 3. Reading a nuclide

Click a square. The **Selected** window lists, for the clicked nuclide, the numbers behind the square: data sets, points,
resonances, TOF, the largest data sets (right side) and, below, the **references** of the selected data sets (two
columns): first author, year, citation, title, entry/subentry. **Copy list** copies the references as text.

Why numbers differ from what you expect: the *Selected* window counts under the **current filters** only. A TOF count of 87
with filters on (n,γ) is not the count of all TOF sets of the nuclide.

## 4. Saving the figure

**Save image** → choose the resolution (dpi) → PNG. In Claude's viewer a confirmation appears; on GitHub Pages or a
local file the browser downloads it normally. A preview is shown below the button as a fallback (right-click →
save image).

## 5. Check the original

The page is an index, not a substitute for EXFOR. For any data set, open the entry in the
[IAEA EXFOR web retrieval](https://nds.iaea.org/exfor/) using the entry and subentry numbers listed.

## 6. Which data does my copy contain?

See the footer: it names the EXFOR master-file date and commit and the build date. The same information is in
`data-version.json` next to the page.

## 7. Citing

Cite EXFOR (N. Otuka et al., "Towards a More Complete and Accurate Experimental Nuclear Reaction Data Library (EXFOR): International Collaboration Between Nuclear Reaction Data Centres (NRDC)", Nuclear Data Sheets 120 (2014) 272), state the version from the footer, and the
repository. EXFOR data are CC BY 4.0.
