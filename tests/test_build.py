#!/usr/bin/env python3
"""Self-test of build_nuclide_chart.py on one small real EXFOR entry (tests/data, entry 40087, Pu-239).

Run from the repository root:   python tests/test_build.py      (standard library only, takes about a second)
Checks the parsing rules (is_rp, year, numbers), a complete build, and the offline property of the page.
"""
import json, re, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build_nuclide_chart as B  # noqa: E402


class Rules(unittest.TestCase):
    def test_rp(self):
        for q in ("WID", "WID/RED", "WID/STR", "J", "L", "GN", "GG", "KRM", "RES"):
            self.assertTrue(B.is_rp("0", q), q)
        self.assertTrue(B.is_rp("0", "EN"))          # resonance energies
        self.assertFalse(B.is_rp("F", "EN"))          # an energy column alone is not RP
        for q in ("D", "STF", "RI", "SIF", "DATA"):
            self.assertFalse(B.is_rp("0", q), q)

    def test_years(self):
        self.assertEqual(B.year_from_token("1970"), 1970)
        self.assertEqual(B.year_of("(C,70HELSINKI,1,339,1970)"), 1970)
        self.assertEqual(B.year_of("(J,NSE,39,123,197003)"), 1970)

    def test_numbers(self):
        self.assertAlmostEqual(B.exfor_number("1.003  -01"), 0.1003)
        self.assertAlmostEqual(B.exfor_number("1.5-3"), 1.5e-3)


class Build(unittest.TestCase):
    def test_build(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "index.html"
            master = Path(d) / "master" / "exforall" / "400"          # work on a private copy of the one test entry
            master.mkdir(parents=True)
            shutil.copy(ROOT / "tests" / "data" / "exforall" / "400" / "40087.x4", master)
            r = subprocess.run([sys.executable, str(ROOT / "build_nuclide_chart.py"), "--master", str(Path(d) / "master"),
                                "--out", str(out)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            v = json.loads((Path(d) / "data-version.json").read_text())
            self.assertEqual((v["nuclides"], v["data_sets"], v["entries"]), (1, 9, 1))
            html = out.read_text(encoding="utf-8")
            for ph in ("__DATA__", "__QLIST__", "__ENTS__", "__MDATE__", "__BUILDINFO__", "__PROJECT_URL__"):
                self.assertNotIn(ph, html, ph)
            m = re.search(r"const DATA = (\[.*?\]);\n", html, re.S)
            rows = json.loads(m.group(1))
            self.assertEqual({(r[0], r[1]) for r in rows}, {(94, 239)})
            self.assertEqual(sum(len(r[3]) for r in rows), 9)

    def test_page_is_offline(self):
        html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        ext = re.findall(r"""(?:src|href)\s*=\s*["'](https?://[^"']+)""", html)
        self.assertEqual([u for u in ext if "fonts.g" in u or "cdn" in u], [], "page must not load external resources")
        self.assertNotIn("/Users/", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
