"""Stokey (1979, 1981) on Steam: do sellers of zero-marginal-cost games hold their launch price?

Stokey (1979) shows that a monopolist who can commit to a price path, selling to buyers who share one
discount rate, at a cost that does not fall over time, charges the static monopoly price forever and makes all
of its sales at the start. A digital copy of a video game costs nothing to produce, and each game is sold by
the one publisher that owns it, so a flat price path is the benchmark. Stokey (1981) shows that a seller who
cannot commit is pushed toward marginal cost, faster the more often it can change its price.

This script reads the committed tables in data/raw/ (built by src/fetch_steam.py) and writes:
  results/price_paths.csv          list price and paid price against the launch price, by months since release
  results/price_tiers.csv          list-price cuts by month 36, by launch price tier
  results/price_path_regression.csv  log price change on months-since-release bins, clustered by game
  results/purchase_timing.csv      how concentrated each game's reviews (purchases) are around launch
  results/timing_summary.csv       summary of the same across games
  results/publishers.csv           launch price, cuts and timing by publisher
  results/named_games.csv          the table of well-known games used in the README
  results/waiting_regression.csv   extension: do buyers wait for publishers known to cut?
  results/waiting_games.csv        the game-level data behind that regression
  results/coase_simulation.csv     no-commitment linear equilibrium (uniform values) by period length
  results/sample_flow.csv          rows loaded, kept and dropped at each step
  results/archive_cross_check.csv  agreement of Common Crawl and Wayback captures of the same game and date
  results/fig_price_paths.png, results/fig_waiting.png

Usage (from the repository root):
    python src/stokey_steam.py
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parent))   # sample rules live in fetch_steam.py
import fetch_steam as fs  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "results"

SOURCES = ["commoncrawl", "wayback"]          # archives of the store page, in order of preference
HORIZONS = fs.SNAP_MONTHS                     # months after release sampled from the archives (3 to 36)
LAUNCH_MONTHS = 2                             # release month plus the next one count as "at launch"
TIMING_MONTHS = 36                            # purchases are counted over the first three years
TIERS = [0, 15, 40, 1000]                    # launch list price tiers in dollars (indie, mid-price, full price)
TIER_LABELS = ["under $15", "$15 to $39.99", "$40 and up"]
FLAT_TOL_CENTS = 1                            # a list price within one cent of launch counts as unchanged
ANNUAL_RATE = 0.10                            # discount rate for the Stokey (1981) illustration (judgment)
NAMED = ["ELDEN RING", "Cyberpunk 2077", "Red Dead Redemption 2", "Hogwarts Legacy", "Starfield",
         "Monster Hunter: World", "Resident Evil Village", "DOOM Eternal", "STAR WARS Jedi: Fallen Order™",
         "God of War", "It Takes Two", "Stray", "Hollow Knight", "Phasmophobia", "Lethal Company", "Among Us"]


def wilson(k, n, z=1.96):
    if n == 0:
        return np.nan, np.nan
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def load(flow):
    det = pd.read_csv(RAW / "steam_appdetails.csv", parse_dates=["release_date"])
    ids = pd.read_csv(RAW / "sample_appids.csv")
    months = pd.read_csv(RAW / "steam_review_months.csv")
    fetched = pd.Timestamp((RAW / "DOWNLOADED.txt").read_text().split("fetched ")[1][:10])

    ok = det[(det.type == "game") & det.release_date.notna()]
    window = ok[ok.release_date.between(fs.RELEASE_FROM, fs.RELEASE_TO)]
    short = window.sort_values("reviews", ascending=False).head(fs.SHORTLIST)
    pre = fs.pre_release_share(short, months)
    early = int((pre > fs.PRE_RELEASE_MAX).sum())
    elsewhere = len((set(fs.NOT_FRESH) & set(short.appid)) - set(pre[pre > fs.PRE_RELEASE_MAX].index))
    flow += [("Most-reviewed paid games sent to the Steam store API", len(det)),
             (f"Released {fs.RELEASE_FROM} to {fs.RELEASE_TO} (type game)", len(window)),
             ("Shortlist: most-reviewed in the window", len(short)),
             (f"Dropped: >{fs.PRE_RELEASE_MAX:.0%} of reviews before release month (early access or relisted)", early),
             ("Dropped: sold on another PC store first, or product changed (judgment list)", elsewhere)]

    parts = []
    both = [pd.read_csv(RAW / f"steam_prices_{s}.csv") for s in SOURCES]
    pairs = both[0].merge(both[1], on=["appid", "label"], suffixes=("_cc", "_wb"))
    pd.DataFrame([{"pairs": len(pairs), "games": pairs.appid.nunique(),
                   "share_same_list_price": (pairs.base_cents_cc == pairs.base_cents_wb).mean(),
                   "share_same_paid_price": (pairs.paid_cents_cc == pairs.paid_cents_wb).mean()}]
                 ).to_csv(OUT / "archive_cross_check.csv", index=False)
    print(f"Archive cross-check: {len(pairs)} game-dates captured in both archives, list price identical in "
          f"{(pairs.base_cents_cc == pairs.base_cents_wb).mean():.1%}")
    for source in SOURCES:
        f = RAW / f"steam_prices_{source}.csv"
        if f.exists():
            parts.append(pd.read_csv(f, dtype={"timestamp": str}).assign(source=source))
    snaps = pd.concat(parts)
    snaps["rank"] = snaps.source.map({s: i for i, s in enumerate(SOURCES)})
    snaps = snaps.sort_values("rank").drop_duplicates(["appid", "label"]).drop(columns="rank")
    games = det[det.appid.isin(ids.appid)].copy()
    games["publisher"] = games.publisher.fillna("Unknown").str.split(";").str[0].str.strip()
    # one spelling per publisher ("BANDAI NAMCO Entertainment" and "Bandai Namco Entertainment Inc." are one firm)
    key = games.publisher.str.lower().str.replace(r"[.,]|\b(inc|ltd|co|llc)\b", "", regex=True).str.strip()
    games["publisher"] = key.map(games.groupby(key).publisher.first())
    flow.append(("Games in the sample (top fresh launches by reviews)", len(games)))
    print(f"Loaded {len(games)} sample games, {len(snaps)} archived price captures "
          f"({snaps.source.value_counts().to_dict()}), {len(months)} game-months of review counts; "
          f"store prices fetched {fetched.date()}")
    return games, snaps, months, fetched


def build_panel(games, snaps, fetched, flow):
    """One row per game and observation date: list and paid price relative to the launch list price."""
    s = snaps.copy()
    s["month"] = s.label.map(lambda lab: 0 if lab == "launch" else int(lab[1:]))
    launch = s[s.label.eq("launch")].set_index("appid").base_cents.rename("launch_cents")
    g = games.join(launch, on="appid")
    dropped = g.launch_cents.isna().sum()
    g = g[g.launch_cents.notna()].copy()
    flow.append(("Dropped: no archived US store page within 75 days before to 31 days after release", int(dropped)))
    flow.append(("Games with a launch list price", len(g)))
    print(f"Launch price found for {len(g)} games; dropped {dropped} with no archived launch-window page")

    today = g[["appid", "release_date", "base_now_cents", "final_now_cents", "currency_now"]].copy()
    today = today[today.currency_now.eq("USD")]
    today["month"] = ((fetched - today.release_date).dt.days / 30.44).round().astype(int)
    today = today.rename(columns={"base_now_cents": "base_cents", "final_now_cents": "paid_cents"})
    today["label"] = "today"
    p = pd.concat([s[s.appid.isin(g.appid)][["appid", "label", "month", "base_cents", "paid_cents"]],
                   today[["appid", "label", "month", "base_cents", "paid_cents"]]])
    p = p.merge(g[["appid", "name", "publisher", "launch_cents", "release_date"]], on="appid")
    p["base_ratio"] = p.base_cents / p.launch_cents
    p["paid_ratio"] = p.paid_cents / p.launch_cents
    p["flat"] = (p.base_cents - p.launch_cents).abs() <= FLAT_TOL_CENTS
    p["on_sale"] = p.paid_cents < p.base_cents - FLAT_TOL_CENTS
    return g, p


def price_paths(p):
    rows = []
    labels = [("launch", 0)] + [(f"m{h}", h) for h in HORIZONS] + [("today", None)]
    for lab, h in labels:
        d = p[p.label.eq(lab)]
        n, k = len(d), int(d.flat.sum())
        lo, hi = wilson(k, n)
        rows.append({
            "horizon": lab, "months": h if h is not None else round(d.month.median()), "games": n,
            "share_list_unchanged": k / n, "ci_lo": lo, "ci_hi": hi,
            "share_list_raised": ((~d.flat) & (d.base_ratio > 1)).mean(),
            "share_list_cut": ((~d.flat) & (d.base_ratio < 1)).mean(),
            "median_list_ratio": d.base_ratio.median(), "mean_list_ratio": d.base_ratio.mean(),
            "share_on_sale": d.on_sale.mean(), "median_paid_ratio": d.paid_ratio.median(),
            "mean_paid_ratio": d.paid_ratio.mean(),
        })
    t = pd.DataFrame(rows)
    return t[[c for c in t.columns if c != "share_list_cut"] + ["share_list_cut"]]


def by_tier(p):
    """Game-level summary by launch price tier: was the list price cut by month 36, and how far."""
    d = p[p.label.eq("m36")].copy()
    d["tier"] = pd.cut(d.launch_cents / 100, TIERS, labels=TIER_LABELS, right=False)
    rows = []
    for tier, x in list(d.groupby("tier", observed=True)) + [("All", d)]:
        cut = x[x.base_ratio < 1 - 1e-6]
        rows.append({"launch_tier": tier, "games": len(x), "share_list_unchanged_36m": x.flat.mean(),
                     "share_list_cut_36m": len(cut) / len(x), "share_list_raised_36m": (x.base_ratio > 1 + 1e-6).mean(),
                     "median_ratio_if_cut": cut.base_ratio.median(), "mean_paid_ratio_36m": x.paid_ratio.mean()})
    return pd.DataFrame(rows)


def path_regression(p):
    d = p[(p.label != "today") & (p.month > 0)].copy()
    d["bin"] = d.month.map(lambda m: f"m{m:02d}")
    d["ln_list"] = np.log(d.base_ratio)
    d["ln_paid"] = np.log(d.paid_ratio)
    d["sale"] = d.on_sale.astype(float)
    rows = []
    for y in ["ln_list", "ln_paid", "sale"]:
        m = smf.ols(f"{y} ~ C(bin) - 1", data=d).fit(cov_type="cluster", cov_kwds={"groups": d.appid})
        live = (m.bse > 1e-9).to_numpy()         # a horizon where every game is unchanged has no variance
        joint = m.wald_test(np.eye(len(m.params))[live], scalar=True, use_f=True)
        for name in m.params.index:
            ci = m.conf_int().loc[name]
            rows.append({"outcome": y, "term": name.replace("C(bin)[", "").rstrip("]"), "coef": m.params[name],
                         "pct_change": np.expm1(m.params[name]) if y != "sale" else np.nan,
                         "se": m.bse[name], "ci_lo": ci[0], "ci_hi": ci[1], "p": m.pvalues[name],
                         "n_obs": int(m.nobs), "n_games": d.appid.nunique(),
                         "joint_F_all_zero": float(joint.fvalue), "joint_p": float(joint.pvalue)})
    return pd.DataFrame(rows), d


def purchase_timing(g, months):
    m = months.merge(g[["appid", "release_date"]], on="appid")
    m["rel"] = (pd.to_datetime(m.month).dt.to_period("M") - m.release_date.dt.to_period("M")).apply(lambda x: x.n)
    m["reviews"] = m.up + m.down
    m = m[m.rel.between(0, TIMING_MONTHS - 1)]
    t = m.groupby("appid").apply(lambda x: pd.Series({
        "reviews_36m": x.reviews.sum(), "launch_reviews": x.loc[x.rel < LAUNCH_MONTHS, "reviews"].sum(),
        "launch_share": x.loc[x.rel < LAUNCH_MONTHS, "reviews"].sum() / x.reviews.sum(),
        "first_year_share": x.loc[x.rel < 12, "reviews"].sum() / x.reviews.sum(),
        "months_observed": x.rel.nunique()}), include_groups=False).reset_index()
    return t[t.reviews_36m > 0]


def first_year_cuts(p):
    """Per game: list-price ratio at 12 months and the lowest paid price seen in months 1 to 12."""
    y1 = p[(p.label != "today") & p.month.between(1, 12)]
    out = y1.groupby("appid").agg(min_paid_y1=("paid_ratio", "min"), captures_y1=("paid_ratio", "size"),
                                  sale_share_y1=("on_sale", "mean"))
    out["list12"] = p[p.label.eq("m12")].set_index("appid").base_ratio
    return out.reset_index()


def waiting_test(g, timing, cuts):
    """Extension: are launches less concentrated for games whose publishers cut their other games deeply?"""
    d = g[["appid", "name", "publisher", "launch_cents", "release_date"]].merge(timing, on="appid")
    d = d.merge(cuts, on="appid", how="left")
    d["cut_y1"] = 1 - d.min_paid_y1
    pub = d.groupby("publisher").cut_y1.agg(["sum", "count"])
    d = d.join(pub, on="publisher")
    d["pub_cut_loo"] = (d["sum"] - d.cut_y1.fillna(0)) / (d["count"] - d.cut_y1.notna().astype(int))
    d.loc[(d["count"] - d.cut_y1.notna().astype(int)) < 1, "pub_cut_loo"] = np.nan
    d["year"] = d.release_date.dt.year
    d["ln_price"] = np.log(d.launch_cents / 100)
    rows = []
    specs = {
        "publisher reputation (leave-one-out)": ("launch_share ~ pub_cut_loo + ln_price + C(year)", "pub_cut_loo"),
        "own first-year cut (descriptive)": ("launch_share ~ cut_y1 + ln_price + C(year)", "cut_y1"),
        "publisher reputation, first-year share": ("first_year_share ~ pub_cut_loo + ln_price + C(year)",
                                                   "pub_cut_loo"),
    }
    for label, (f, term) in specs.items():
        dd = d.dropna(subset=[term, "launch_share"])
        m = smf.ols(f, data=dd).fit(cov_type="cluster", cov_kwds={"groups": dd.publisher})
        ci = m.conf_int().loc[term]
        rows.append({"spec": label, "term": term, "coef": m.params[term], "se": m.bse[term], "ci_lo": ci[0],
                     "ci_hi": ci[1], "p": m.pvalues[term], "n_games": int(m.nobs),
                     "n_publishers": dd.publisher.nunique(), "r2": m.rsquared,
                     "mean_outcome": dd[f.split(" ~")[0]].mean(), "sd_regressor": dd[term].std(),
                     "effect_of_1sd": m.params[term] * dd[term].std()})
    return pd.DataFrame(rows), d


def coase_equilibrium(delta):
    """Stationary linear equilibrium, values uniform on [0,1], zero cost (Stokey 1981; Gul et al. 1986).
    Price = c * next cutoff, next cutoff = b * current cutoff, seller value = w * cutoff^2. The closed form
    is checked against the three equilibrium conditions before it is used."""
    c = np.sqrt(1 - delta)
    b = 1 / (1 + c)
    w = c * b * (1 - b) / (1 - delta * b * b)
    residuals = [1 - c - delta * (1 - c * b), b - c / (2 * (c - delta * w)), w - c * b * (1 - b) / (1 - delta * b * b)]
    assert max(abs(r) for r in residuals) < 1e-9, residuals
    return c, b, w


def coase_table():
    rows = []
    for label, per_year in [("once a year", 1), ("once a quarter", 4), ("once a month", 12), ("once a week", 52)]:
        delta = np.exp(-ANNUAL_RATE / per_year)
        c, b, w = coase_equilibrium(delta)
        rows.append({"price_changes": label, "periods_per_year": per_year, "delta": delta,
                     "first_price": c * b, "first_price_vs_commitment": c * b / 0.5,
                     "profit_vs_commitment": w / 0.25, "share_sold_first_period": 1 - b})
    return pd.DataFrame(rows)


def named_table(g, p, timing):
    rows = []
    for name in NAMED:
        gg = g[g.name.eq(name)]
        if gg.empty:
            continue
        a = gg.appid.iloc[0]
        pp = p[p.appid.eq(a)]
        get = lambda lab, col: pp.loc[pp.label.eq(lab), col].iloc[0] if (pp.label == lab).any() else np.nan
        tm = timing[timing.appid.eq(a)]
        rows.append({"game": name, "publisher": gg.publisher.iloc[0], "released": gg.release_date.iloc[0].date(),
                     "launch_list": gg.launch_cents.iloc[0] / 100, "list_12m": get("m12", "base_cents") / 100,
                     "list_36m": get("m36", "base_cents") / 100, "list_today": get("today", "base_cents") / 100,
                     "lowest_paid_seen_36m": pp[pp.label != "today"].paid_cents.min() / 100,
                     "launch_share_of_36m_reviews": tm.launch_share.iloc[0] if len(tm) else np.nan})
    return pd.DataFrame(rows)


def figures(p, wait):
    d = p[p.label != "today"]
    grid = sorted(d.month.unique())
    on_sale = [d[d.month.eq(m)].on_sale.mean() for m in grid]
    mean_paid = [d[d.month.eq(m)].paid_ratio.mean() for m in grid]
    flat = [d[d.month.eq(m)].flat.mean() for m in grid]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.plot(grid, flat, "o-", color="#1f5a96", label="Share of games still at launch list price")
    ax.plot(grid, mean_paid, "s-", color="#c0504d", label="Average price paid on capture day, vs launch")
    ax.plot(grid, on_sale, "^--", color="#6b6b6b", label="Share of games on sale on capture day")
    ax.axhline(1, color="black", lw=0.6)
    ax.set_xlabel("Months since release")
    ax.set_ylabel("Share / ratio to launch list price")
    ax.set_ylim(0, 1.08)
    ax.set_title("A committed Stokey seller would stay at 1.0 on the top two lines and 0 on the third")
    ax.legend(frameon=False, fontsize=9, loc="center left")
    fig.tight_layout()
    fig.savefig(OUT / "fig_price_paths.png", dpi=150)
    plt.close(fig)

    w = wait.dropna(subset=["pub_cut_loo"])
    fig, ax = plt.subplots(figsize=(7, 4.6))
    ax.scatter(100 * w.pub_cut_loo, 100 * w.launch_share, s=18, color="#1f5a96", alpha=0.7)
    b = np.polyfit(100 * w.pub_cut_loo, 100 * w.launch_share, 1)
    xs = np.linspace(0, 100 * w.pub_cut_loo.max(), 50)
    ax.plot(xs, b[1] + b[0] * xs, color="#c0504d")
    ax.set_xlabel("Publisher's average first-year price cut on its other games (%)")
    ax.set_ylabel("Share of 3-year reviews in launch months (%)")
    ax.set_title("Launch concentration against the publisher's record of cuts (line: raw fit, no controls)", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "fig_waiting.png", dpi=150)
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    flow = []
    games, snaps, months, fetched = load(flow)
    g, p = build_panel(games, snaps, fetched, flow)

    paths = price_paths(p)
    paths.to_csv(OUT / "price_paths.csv", index=False)
    print(paths[["horizon", "games", "share_list_unchanged", "median_list_ratio", "share_on_sale",
                 "mean_paid_ratio"]].round(3).to_string(index=False))

    tiers = by_tier(p)
    tiers.to_csv(OUT / "price_tiers.csv", index=False)
    print(tiers.round(3).to_string(index=False))

    reg, reg_data = path_regression(p)
    reg.to_csv(OUT / "price_path_regression.csv", index=False)
    print(f"Regression panel: {len(reg_data)} captures from {reg_data.appid.nunique()} games")

    timing = purchase_timing(g, months)
    timing.merge(g[["appid", "name", "publisher"]], on="appid").to_csv(OUT / "purchase_timing.csv", index=False)
    flow.append(("Games with review histograms over the first 36 months", len(timing)))
    pd.DataFrame([{"games": len(timing), "median_launch_share": timing.launch_share.median(),
                   "p25_launch_share": timing.launch_share.quantile(0.25),
                   "p75_launch_share": timing.launch_share.quantile(0.75),
                   "share_of_games_above_half": (timing.launch_share > 0.5).mean(),
                   "median_first_year_share": timing.first_year_share.median(),
                   "pooled_launch_share": timing.launch_reviews.sum() / timing.reviews_36m.sum()}]
                 ).to_csv(OUT / "timing_summary.csv", index=False)
    print(f"Purchase timing for {len(timing)} games: median launch-months share "
          f"{timing.launch_share.median():.3f}, median first-year share {timing.first_year_share.median():.3f}")

    cuts = first_year_cuts(p)
    wreg, wait = waiting_test(g, timing, cuts)
    wreg.to_csv(OUT / "waiting_regression.csv", index=False)
    wait.to_csv(OUT / "waiting_games.csv", index=False,
                columns=["appid", "name", "publisher", "year", "launch_cents", "launch_share", "first_year_share",
                         "cut_y1", "list12", "captures_y1", "pub_cut_loo"])
    flow.append(("Games whose publisher has another game in the sample (extension)",
                 int(wait.pub_cut_loo.notna().sum())))
    print(wreg.round(4).to_string(index=False))

    pubs = wait.groupby("publisher").agg(games=("appid", "size"), median_launch_price=("launch_cents", "median"),
                                         mean_first_year_cut=("cut_y1", "mean"),
                                         share_list_cut_by_12m=("list12", lambda x: (x.dropna() < 0.999).mean()),
                                         median_launch_share=("launch_share", "median")).reset_index()
    pubs["median_launch_price"] /= 100
    pubs.sort_values("games", ascending=False).to_csv(OUT / "publishers.csv", index=False)

    named_table(g, p, timing).to_csv(OUT / "named_games.csv", index=False)
    coase_table().to_csv(OUT / "coase_simulation.csv", index=False)
    pd.DataFrame(flow, columns=["step", "count"]).to_csv(OUT / "sample_flow.csv", index=False)
    figures(p, wait)
    print("Wrote results/*.csv and two figures")


if __name__ == "__main__":
    main()
