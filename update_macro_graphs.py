import csv
import os
import subprocess
import urllib.request
import zipfile
from collections import defaultdict
from datetime import date
from io import BytesIO

ROOT = "/Users/alessiaroot/Downloads/EC22_start"
OUT = os.path.join(ROOT, "EC22Data", "Graphs_updated")
BUILD = os.path.join(OUT, "_build")
os.makedirs(BUILD, exist_ok=True)


def fetch_series(ids):
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + ",".join(ids)
    with urllib.request.urlopen(url, timeout=60) as response:
        raw = response.read()
    if raw[:2] == b"PK":
        with zipfile.ZipFile(BytesIO(raw)) as zf:
            csv_name = next(name for name in zf.namelist() if name.lower().endswith(".csv"))
            raw = zf.read(csv_name)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    rows = list(csv.DictReader(text.splitlines()))
    data = []
    for row in rows:
        d = date.fromisoformat(row["observation_date"])
        rec = {"date": d}
        for sid in ids:
            value = row.get(sid, "")
            rec[sid] = None if value in ("", ".") else float(value)
        data.append(rec)
    return data


def year_frac(d):
    return d.year + (d.month - 1) / 12.0


def annualize_by_year(rows, ids):
    grouped = defaultdict(lambda: defaultdict(list))
    for row in rows:
        for sid in ids:
            if row[sid] is not None:
                grouped[row["date"].year][sid].append(row[sid])
    out = []
    for year in sorted(grouped):
        rec = {"year": year}
        if all(grouped[year][sid] for sid in ids):
            for sid in ids:
                vals = grouped[year][sid]
                rec[sid] = sum(vals) / len(vals)
            out.append(rec)
    return out


def latest_nonmissing(rows, sid):
    for row in reversed(rows):
        if row[sid] is not None:
            return row["date"], row[sid]
    raise ValueError(sid)


def write_table(name, columns, rows):
    path = os.path.join(BUILD, name + ".dat")
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for row in rows:
            writer.writerow(["" if row.get(c) is None else row.get(c) for c in columns])
    return path


def tex_escape(s):
    return s.replace("_", "\\_").replace("%", "\\%").replace("&", "\\&")


COLORS = ["blue", "red", "green!60!black", "orange!80!black", "purple", "cyan!60!black"]
AXIS_SIZE = [
    "width=6.4in",
    "height=4.8in",
    "grid=major",
    "major grid style={densely dotted, gray!70}",
    "axis line style={gray!70}",
    "tick label style={font=\\large, /pgf/number format/fixed, /pgf/number format/precision=0, /pgf/number format/1000 sep={}}",
    "label style={font=\\Large}",
    "title style={font=\\LARGE, text=blue!35!black}",
]


def compile_tex(base, body):
    tex = rf"""\documentclass[tikz,border=2pt]{{standalone}}
\usepackage{{pgfplots}}
\usepgfplotslibrary{{groupplots}}
\usetikzlibrary{{calc}}
\pgfplotsset{{compat=1.18}}
\definecolor{{blue}}{{RGB}}{{0,114,178}}
\definecolor{{red}}{{RGB}}{{213,94,0}}
\definecolor{{green}}{{RGB}}{{0,158,115}}
\begin{{document}}
{body}
\end{{document}}
"""
    tex_path = os.path.join(BUILD, base + ".tex")
    with open(tex_path, "w") as f:
        f.write(tex)
    subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", os.path.basename(tex_path)],
        cwd=BUILD,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        check=True,
    )
    os.replace(os.path.join(BUILD, base + ".pdf"), os.path.join(OUT, base + ".pdf"))


def line_graph(base, title, ylabel, data_path, series, xmin=None, logy=False):
    opts = [
        *AXIS_SIZE,
        f"title={{{tex_escape(title)}}}",
        f"ylabel={{{tex_escape(ylabel)}}}",
        "xlabel={Year}",
        "xtick distance=5",
        "legend style={font=\\Large, at={(1.02,0.05)}, anchor=south west, fill=white, draw=none}",
        "unbounded coords=jump",
    ]
    if xmin is not None:
        opts.append(f"xmin={xmin}")
    if logy:
        opts.append("ymode=log")
        opts.append("log ticks with fixed point")
    body = "\\begin{tikzpicture}\n\\begin{axis}[" + ",".join(opts) + "]\n"
    legends = []
    for i, (col, label) in enumerate(series):
        body += rf"\addplot+[mark=none, very thick, color={COLORS[i % len(COLORS)]}] table [x=x, y={col}, col sep=comma] {{{data_path}}};" + "\n"
        legends.append(tex_escape(label))
    if len(legends) > 1:
        body += "\\legend{" + ",".join(legends) + "}\n"
    body += "\\end{axis}\n\\end{tikzpicture}\n"
    compile_tex(base, body)


def bar_graph(base, title, ylabel, data_path, col, xmin=None):
    opts = [
        *AXIS_SIZE,
        "ybar",
        "bar width=1.5pt",
        f"title={{{tex_escape(title)}}}",
        f"ylabel={{{tex_escape(ylabel)}}}",
        "xlabel={Year}",
        "xtick distance=5",
        "unbounded coords=jump",
    ]
    if xmin is not None:
        opts.append(f"xmin={xmin}")
    body = "\\begin{tikzpicture}\n\\begin{axis}[" + ",".join(opts) + "]\n"
    body += rf"\addplot+[fill=blue, draw=blue] table [x=x, y={col}, col sep=comma] {{{data_path}}};"
    body += "\n\\end{axis}\n\\end{tikzpicture}\n"
    compile_tex(base, body)


def scatter_fit_graph(base, title, ylabel, data_path, slope, intercept, xmin, xmax):
    body = rf"""\begin{{tikzpicture}}
\begin{{axis}}[
width=6.4in,height=4.8in,grid=major,major grid style={{densely dotted, gray!70}},
title={{{tex_escape(title)}}}, xlabel={{Change in Unemployment Rate}}, ylabel={{{tex_escape(ylabel)}}},
tick label style={{font=\large, /pgf/number format/fixed, /pgf/number format/precision=0, /pgf/number format/1000 sep={{}}}}, label style={{font=\Large}}, title style={{font=\LARGE, text=blue!35!black}},
legend style={{draw=none, fill=white, font=\Large, at={{(1.02,0.05)}}, anchor=south west}},
]
\addplot+[only marks, mark=*, mark size=1.1pt, color=blue] table [x=x, y=y, col sep=comma] {{{data_path}}};
\addlegendentry{{observations}}
\addplot+[very thick, color=red, domain={xmin}:{xmax}, samples=2] {{{intercept:.6f} + {slope:.6f}*x}};
\addlegendentry{{linear fit}}
\end{{axis}}
\end{{tikzpicture}}
"""
    compile_tex(base, body)


def group_two_graph(base, title, ylabel, data_path, left_col, left_title, right_col, right_title, xmin=None):
    xmin_opt = "" if xmin is None else f",xmin={xmin}"
    body = rf"""\begin{{tikzpicture}}
\begin{{groupplot}}[
group style={{group size=2 by 1, horizontal sep=1.2cm}},
width=3.1in,height=4.45in,grid=major,major grid style={{densely dotted, gray!70}},
tick label style={{font=\large, /pgf/number format/fixed, /pgf/number format/precision=0, /pgf/number format/1000 sep={{}}}}, label style={{font=\Large}},
ylabel={{{tex_escape(ylabel)}}}, xlabel={{Year}},
title style={{font=\Large, text=blue!35!black}},
unbounded coords=jump{xmin_opt}
,xtick distance=5
]
\nextgroupplot[title={{{tex_escape(left_title)}}}]
\addplot+[mark=none, very thick, color=blue] table [x=x, y={left_col}, col sep=comma] {{{data_path}}};
\nextgroupplot[title={{{tex_escape(right_title)}}}]
\addplot+[mark=none, very thick, color=red] table [x=x, y={right_col}, col sep=comma] {{{data_path}}};
\end{{groupplot}}
\node[font=\LARGE, text=blue!35!black] at ($(group c1r1.north)!0.5!(group c2r1.north)+(0,0.55cm)$) {{{tex_escape(title)}}};
\end{{tikzpicture}}
"""
    compile_tex(base, body)


def ols(xs, ys):
    xbar = sum(xs) / len(xs)
    ybar = sum(ys) / len(ys)
    slope = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / sum((x - xbar) ** 2 for x in xs)
    return slope, ybar - slope * xbar


def main():
    gdpca_rows = fetch_series(["GDPCA"])
    pop_rows = fetch_series(["POP"])
    pop_by_year = {}
    for r in pop_rows:
        if r["POP"] is not None:
            pop_by_year.setdefault(r["date"].year, []).append(r["POP"])
    annual_rows = []
    for row in gdpca_rows:
        year = row["date"].year
        if row["GDPCA"] is not None and pop_by_year.get(year):
            pop = sum(pop_by_year[year]) / len(pop_by_year[year])
            annual_rows.append({"x": year, "gdp_pc": 1_000_000 * row["GDPCA"] / pop / 1000})
    path = write_table("gdpa_per_cap_log1870_data", ["x", "gdp_pc"], annual_rows)
    line_graph("gdpa_per_cap_log1870", "Real US GDP per capita", "1000 US 2017 dollars", path, [("gdp_pc", "Real GDP per capita")], xmin=1952, logy=True)

    nipa = fetch_series(["GDP", "PCEC", "GPDI", "GCE", "EXPGS", "IMPGS"])
    rows = []
    for r in annualize_by_year(nipa, ["GDP", "PCEC", "GPDI", "GCE", "EXPGS", "IMPGS"]):
        gdp = r["GDP"]
        rows.append({"x": r["year"], "c": 100 * r["PCEC"] / gdp, "i": 100 * r["GPDI"] / gdp, "g": 100 * r["GCE"] / gdp, "nx": 100 * (r["EXPGS"] - r["IMPGS"]) / gdp})
    path = write_table("nipa_components_data", ["x", "c", "i", "g", "nx"], rows)
    line_graph("nipa_c_i_g_nx1945", "Components of GDP", "Percentage of GDP", path, [("c", "C"), ("i", "I"), ("nx", "NX"), ("g", "G")], xmin=1945)

    cpi_rows = fetch_series(["CPIAUCSL"])
    gdpd_rows = fetch_series(["GDPDEF"])
    gdpd_by_month = {r["date"]: r["GDPDEF"] for r in gdpd_rows if r["GDPDEF"] is not None}
    rows, prev_cpi, prev_gdpd = [], {}, {}
    for r in cpi_rows:
        d = r["date"]
        cpi_yoy = 100 * (r["CPIAUCSL"] - prev_cpi[(d.year - 1, d.month)]) / prev_cpi[(d.year - 1, d.month)] if r["CPIAUCSL"] is not None and (d.year - 1, d.month) in prev_cpi else None
        gdpd_val = gdpd_by_month.get(d)
        gdpd_yoy = 100 * (gdpd_val - prev_gdpd[(d.year - 1, d.month)]) / prev_gdpd[(d.year - 1, d.month)] if gdpd_val is not None and (d.year - 1, d.month) in prev_gdpd else None
        if cpi_yoy is not None or gdpd_yoy is not None:
            rows.append({"x": year_frac(d), "cpi": cpi_yoy, "gdpd": gdpd_yoy})
        if r["CPIAUCSL"] is not None:
            prev_cpi[(d.year, d.month)] = r["CPIAUCSL"]
        if gdpd_val is not None:
            prev_gdpd[(d.year, d.month)] = gdpd_val
    path = write_table("inflation_data", ["x", "cpi", "gdpd"], rows)
    line_graph("inflation_cpi_gdpd1950", "US Inflation - 12 month price change", "Percent", path, [("cpi", "CPI"), ("gdpd", "GDPD")], xmin=1950)

    unemp = fetch_series(["UNRATE", "UNRATENSA", "CLF16OV"])
    rows = [{"x": year_frac(r["date"]), "ur": r["UNRATE"], "ur_nsa": r["UNRATENSA"], "adj": None if r["UNRATE"] is None or r["UNRATENSA"] is None else r["UNRATE"] - r["UNRATENSA"], "lf": None if r["CLF16OV"] is None else r["CLF16OV"] / 1000} for r in unemp]
    path = write_table("unemployment_data", ["x", "ur", "ur_nsa", "adj", "lf"], rows)
    line_graph("UR1995", "Unemployment Rate", "Percent", path, [("ur", "Unemployment rate")], xmin=1995)
    line_graph("labor_force1998", "Labor Force Size", "Millions", path, [("lf", "Labor force")], xmin=1998)
    line_graph("ur_season2005", "Seasonal Adjustments", "Unemployment Rate", path, [("ur", "Seasonally adjusted"), ("ur_nsa", "Not seasonally adjusted")], xmin=2005)
    line_graph("ur_season2012", "Seasonal Adjustments", "Unemployment Rate", path, [("ur", "Seasonally adjusted"), ("ur_nsa", "Not seasonally adjusted")], xmin=2012)
    bar_graph("ur_season_adjustment2005", "Size of Seasonal Adjustments", "Percentage points", path, "adj", xmin=2005)

    lfpr = fetch_series(["CIVPART", "LNS11300001", "LNS11300002"])
    rows = [{"x": year_frac(r["date"]), "lfpr": r["CIVPART"], "male": r["LNS11300001"], "female": r["LNS11300002"]} for r in lfpr]
    path = write_table("lfpr_data", ["x", "lfpr", "male", "female"], rows)
    line_graph("lfpr_1945", "Labor Force Participation Rate", "Percent", path, [("lfpr", "All")], xmin=1945)
    line_graph("lfpr_1980", "Labor Force Participation Rate", "Percent", path, [("lfpr", "All")], xmin=1980)
    group_two_graph("lfpr_both1945", "LFPR by Gender", "Percent", path, "male", "Male", "female", "Female", xmin=1945)

    q_gdp = fetch_series(["GDPC1"])
    q_ur = fetch_series(["UNRATE"])
    byq = defaultdict(lambda: {"GDPC1": [], "UNRATE": []})
    for r in q_gdp:
        q = (r["date"].year, (r["date"].month - 1) // 3 + 1)
        if r["GDPC1"] is not None:
            byq[q]["GDPC1"].append(r["GDPC1"])
    for r in q_ur:
        q = (r["date"].year, (r["date"].month - 1) // 3 + 1)
        if r["UNRATE"] is not None:
            byq[q]["UNRATE"].append(r["UNRATE"])
    qrows, prev_gdp, prev_ur = [], None, None
    for key in sorted(byq):
        vals = byq[key]
        if vals["GDPC1"] and vals["UNRATE"]:
            gdp = sum(vals["GDPC1"]) / len(vals["GDPC1"])
            ur = sum(vals["UNRATE"]) / len(vals["UNRATE"])
            if prev_gdp is not None and prev_ur is not None:
                qrows.append({"x": ur - prev_ur, "y": 100 * (gdp - prev_gdp) / prev_gdp})
            prev_gdp, prev_ur = gdp, ur
    qpath = write_table("okun_quarterly_data", ["x", "y"], qrows)
    xs, ys = [r["x"] for r in qrows], [r["y"] for r in qrows]
    slope, intercept = ols(xs, ys)
    scatter_fit_graph("okun_quarterly", "Okun's Law on Quarterly Data", "Quarterly GDP Growth", qpath, slope, intercept, min(xs), max(xs))

    ann_gdp = annualize_by_year(fetch_series(["GDPCA"]), ["GDPCA"])
    ann_ur = annualize_by_year(fetch_series(["UNRATE"]), ["UNRATE"])
    ur_by_year = {r["year"]: r["UNRATE"] for r in ann_ur}
    ann = []
    for r in ann_gdp:
        if r["year"] in ur_by_year:
            ann.append({"year": r["year"], "GDPCA": r["GDPCA"], "UNRATE": ur_by_year[r["year"]]})
    yrows, prev_gdp, prev_ur = [], None, None
    for r in ann:
        if r["year"] < 1950:
            continue
        if prev_gdp is not None and prev_ur is not None:
            yrows.append({"x": r["UNRATE"] - prev_ur, "y": 100 * (r["GDPCA"] - prev_gdp) / prev_gdp})
        prev_gdp, prev_ur = r["GDPCA"], r["UNRATE"]
    ypath = write_table("okun_yearly_data", ["x", "y"], yrows)
    xs, ys = [r["x"] for r in yrows], [r["y"] for r in yrows]
    slope, intercept = ols(xs, ys)
    scatter_fit_graph("okun_yearly", "Okun's Law on Yearly Data", "Yearly GDP Growth", ypath, slope, intercept, min(xs), max(xs))

    gdpa = fetch_series(["GDPA"])
    unrate = fetch_series(["UNRATE"])
    cpi = fetch_series(["CPIAUCSL"])
    core = fetch_series(["CPILFESL"])
    gdpa_d, gdpa_v = latest_nonmissing(gdpa, "GDPA")
    ur_d, ur_v = latest_nonmissing(unrate, "UNRATE")
    cpi_d, _ = latest_nonmissing(cpi, "CPIAUCSL")
    core_d, _ = latest_nonmissing(core, "CPILFESL")
    with open(os.path.join(OUT, "fred_update_notes.txt"), "w") as f:
        f.write(f"FRED data refreshed on {date.today().isoformat()}.\n")
        f.write(f"Latest nominal GDP annual observation: {gdpa_d}: {gdpa_v} billions.\n")
        f.write(f"Latest unemployment rate observation: {ur_d}: {ur_v}%.\n")
        f.write(f"Latest CPI observation: {cpi_d}.\n")
        f.write(f"Latest core CPI observation: {core_d}.\n")


if __name__ == "__main__":
    main()
