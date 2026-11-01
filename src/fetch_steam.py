"""Build the Steam price and purchase-timing panel that src/stokey_steam.py analyzes.

Public sources, none needing a key:
  1. SteamSpy's ranked catalog (steamspy.com/api.php?request=all) to find the most-reviewed paid games.
  2. Steam's store API (store.steampowered.com/api/appdetails) for release date, publisher and today's price.
  3. Steam's review histogram (store.steampowered.com/appreviewhistogram) for monthly counts of new reviews,
     the usual public stand-in for monthly unit sales.
  4. Archived copies of each game's US store page, which record the list price and any sale price on the day
     the page was crawled: Common Crawl (read through its public index files on data.commoncrawl.org) for the
     whole sample, and the Internet Archive's Wayback Machine for the 29 most-reviewed games, as a check and to
     fill gaps. The Wayback Machine allows about 15 requests a minute, which is why it was not used for all.

Raw responses are cached under data/cache/ (ignored by git) so a rerun only fetches what is missing. The
parsed tables written to data/raw/ are committed, so the analysis runs offline without this script.

Usage (from the repository root):
    python src/fetch_steam.py --source commoncrawl          # about an hour on a first run
    python src/fetch_steam.py --source wayback --last 29    # about an hour; Wayback Machine rate limits
"""

import argparse
import gzip
import hashlib
import html as htmlmod
import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
CACHE = ROOT / "data" / "cache"

SPY_PAGES = 5                      # SteamSpy pages of 1,000 games each, ranked by estimated owners
CANDIDATES = 900                   # most-reviewed paid games sent to the store API for a release date
SHORTLIST = 300                    # most-reviewed games in the release window whose review history is fetched
SAMPLE = 200                       # most-reviewed fresh launches kept for the price history
PRE_RELEASE_MAX = 0.02             # a game with more than 2% of its reviews dated before its release month was
                                   # already on sale (early access, or a relisted store page): not a fresh launch
NOT_FRESH = {  # judgment list: sold on another PC store for six months or more before Steam, or product changed
    1238810: "Battlefield V (Origin, 2018)", 1238840: "Battlefield 1 (Origin, 2016)", 1238860: "Battlefield 4 (Origin)",
    1237950: "Star Wars Battlefront II (Origin, 2017)", 1237970: "Titanfall 2 (Origin, 2016)",
    1222680: "Need for Speed Heat (Origin, 2019)", 1222700: "A Way Out (Origin, 2018)", 397540: "Borderlands 3 (Epic)",
    412020: "Metro Exodus (Epic, 2019)", 1151340: "Fallout 76 (Bethesda.net, 2018)", 753640: "Outer Wilds (Epic)",
    1222140: "Detroit: Become Human (Epic, 2019)", 1172620: "Sea of Thieves (Microsoft Store, 2018)",
    495420: "State of Decay 2 (Microsoft Store, 2018)", 12210: "GTA IV (Steam, 2008; relisted)",
    360430: "Mafia III (Steam, 2016; relisted)", 1938090: "Call of Duty HQ (sells a different game each year)",
    2000950: "Call of Duty: Modern Warfare (Battle.net, 2019)", 1985810: "Black Ops Cold War (Battle.net, 2020)",
    870780: "Control (Epic, 2019)", 1659040: "Hitman 3 (Epic, 2021)", 2231380: "Ghost Recon Breakpoint (Ubisoft, 2019)",
    8980: "Borderlands GOTY (Steam, 2009; relisted)", 638230: "Journey (Epic, 2019)", 2344520: "Diablo IV (Battle.net)",
    1850570: "Death Stranding Director's Cut (original on Steam, 2020)", 1922560: "PvZ Garden Warfare 2 (Origin)",
    976730: "Halo: The Master Chief Collection (launched selling one component game)",
}
RELEASE_FROM = "2017-01-01"        # window chosen so every game has 36 months of history before 2026
RELEASE_TO = "2023-10-31"
SNAP_MONTHS = [3, 6, 12, 18, 24, 36]   # months after release to sample (the Wayback Machine allows ~15 requests/min)
SNAP_TOLERANCE_DAYS = 15           # Wayback: a capture must fall within this many days of the target date
CC_TOLERANCE_DAYS = 30             # Common Crawl crawls are monthly or rarer, so the window is wider
LAUNCH_WINDOW = (-75, 31)          # days around release in which a capture counts as the launch price
HEADERS = {"User-Agent": "Brendyn Beasley research 83249437+brendynbeasley@users.noreply.github.com"}
PAUSE = {"steamspy": 1.0, "store": 1.6, "wayback": 4.5, "ccindex": 1.5, "ccdata": 0.15}   # seconds per request
CC_COLLINFO = "https://index.commoncrawl.org/collinfo.json"     # list of Common Crawl crawls and their dates
CC_DATA = "https://data.commoncrawl.org/"
CC_SECTION = ("com,steampowered,store)/app/", "com,steampowered,store)/app0")   # index keys of store app pages


def get(url, kind, params=None, byte_range=None, gz=True, cache=True):
    """GET with a disk cache, polite pacing and retries. Returns text, or None after repeated failure.
    With byte_range=(start, length) it fetches that slice of a file (a gzip member unless gz=False)."""
    key = url + json.dumps(params, sort_keys=True) + (str(byte_range) if byte_range else "")
    key = hashlib.sha1(key.encode()).hexdigest()
    path = CACHE / kind / key
    if cache and path.exists():
        return path.read_text(encoding="utf-8", errors="ignore")
    for attempt in range(5):
        time.sleep(PAUSE[kind] * (1 + 2 * attempt))
        try:
            headers = dict(HEADERS)
            if byte_range:
                headers["Range"] = f"bytes={byte_range[0]}-{byte_range[0] + byte_range[1] - 1}"
            r = requests.get(url, params=params, headers=headers, timeout=90)
        except requests.RequestException:
            time.sleep(60 * (attempt + 1))
            continue
        if r.status_code in (200, 206):
            text = gzip.decompress(r.content).decode("utf-8", "ignore") if byte_range and gz else r.text
            if not cache:
                return text
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            tmp.write_text(text, encoding="utf-8")
            tmp.rename(path)
            return text
        if r.status_code == 404:
            return None
        time.sleep((60 if r.status_code == 429 else 10) * (attempt + 1))
    return None


def steamspy_catalog():
    rows = []
    for page in range(SPY_PAGES):
        txt = get("https://steamspy.com/api.php", "steamspy", {"request": "all", "page": page})
        rows += list(json.loads(txt).values())
    d = pd.DataFrame(rows)
    d["reviews"] = d.positive + d.negative
    print(f"SteamSpy: {len(d)} games on {SPY_PAGES} pages")
    return d


def appdetails(appid):
    txt = get("https://store.steampowered.com/api/appdetails", "store",
              {"appids": appid, "cc": "us", "l": "english"})
    if txt is None:
        return None
    entry = json.loads(txt).get(str(appid), {})
    if not entry.get("success"):
        return None
    d = entry["data"]
    po = d.get("price_overview") or {}
    box = today_price(d)
    return {
        "appid": appid, "name": d.get("name"), "type": d.get("type"), "is_free": d.get("is_free"),
        "release_date": pd.to_datetime(d.get("release_date", {}).get("date", ""), errors="coerce", format="mixed"),
        "publisher": "; ".join(d.get("publishers", [])), "developer": "; ".join(d.get("developers", [])),
        "genres": "; ".join(g["description"] for g in d.get("genres", [])),
        "currency_now": po.get("currency"), "base_now_cents": box[1] if box else None,
        "final_now_cents": box[2] if box else None, "edition_now": box[0] if box else None,
    }


def review_months(appid):
    txt = get(f"https://store.steampowered.com/appreviewhistogram/{appid}", "store",
              {"l": "english", "review_score_preference": 0})
    if txt is None:
        return []
    res = json.loads(txt).get("results", {})
    out = []
    for r in res.get("rollups", []):
        month = datetime.fromtimestamp(r["date"], tz=timezone.utc).strftime("%Y-%m")
        out.append({"appid": appid, "month": month, "up": r["recommendations_up"],
                    "down": r["recommendations_down"]})
    return out


def cdx_list(appid, start, end):
    """Every archived capture (one per day) of the game's store page between two dates."""
    txt = get("https://web.archive.org/cdx/search/cdx", "wayback", {
        "url": f"store.steampowered.com/app/{appid}*", "from": start.strftime("%Y%m%d"),
        "to": end.strftime("%Y%m%d"), "output": "json", "filter": "statuscode:200",
        "collapse": "timestamp:8", "fl": "timestamp,original"})
    if not txt:
        return []
    rows = json.loads(txt)[1:]
    pat = re.compile(rf"store\.steampowered\.com(:80)?/app/{appid}(/|$|\?)", re.I)
    return [(ts, orig) for ts, orig in rows if pat.search(orig) and "cc=" not in orig.lower()]


ADD_ON = re.compile(r"soundtrack|season pass|\bpass\b|\bpacks?\b|\bdlc\b|expansion|bundle|upgrade|deluxe|ultimate|"
                    r"premium|collector|gold edition|legendary|gourmet|fighterz edition|final hours|&amp;|&|"
                    r"\bpart (one|two)\b|demo|free to play|play for free|free weekend", re.I)
# A store page can show several purchase boxes: the game, its deluxe editions, bundles and DLC. The standard
# edition is taken to be the cheapest box whose title does not mark it as an add-on or a premium edition.


def to_cents(s):
    return int(round(float(s.replace("$", "").replace(",", "").split()[0]) * 100))


def choose_box(boxes, name=""):
    """boxes: list of (title, base_cents, paid_cents). Returns the standard-edition box, or None when every
    box is an add-on (the capture is then skipped and the next one tried). Words in the game's own name
    ("Mass Effect Legendary Edition", "Command & Conquer") do not count as add-on markers."""
    own = re.sub(r"[™®]", "", name).lower().strip()
    clean = lambda title: re.sub(r"[™®]", "", title).lower().replace(own, " ") if own else title
    plain = [b for b in boxes if b[0].strip() and not ADD_ON.search(clean(b[0]))]
    return min(plain, key=lambda b: b[1]) if plain else None


def parse_store_page(html, name=""):
    """List price and paid price of the standard edition's purchase box on an archived store page."""
    starts = [m.start() for m in re.finditer(r'class="game_area_purchase_game[" ]', html)]
    boxes, other_currency = [], False
    for k, s in enumerate(starts):
        block = html[s: starts[k + 1] if k + 1 < len(starts) else s + 8000]
        title = re.search(r"<h[12][^>]*>\s*(.*?)\s*</h[12]>", block, re.S)
        title = htmlmod.unescape(re.sub(r"\s+", " ", title.group(1))) if title else ""
        plain = re.search(r'game_purchase_price price"[^>]*>\s*([^<]*?)\s*<', block, re.S)
        disc = re.search(r'discount_original_price">\s*([^<]*?)\s*<.*?discount_final_price">\s*([^<]*?)\s*<',
                         block, re.S)
        if plain and (not disc or plain.start() < disc.start()):
            base_txt = paid_txt = plain.group(1)
        elif disc:
            base_txt, paid_txt = disc.group(1), disc.group(2)
        else:
            continue
        if not (base_txt.startswith("$") and paid_txt.startswith("$")):
            other_currency = other_currency or bool(re.search(r"\d", base_txt))
            continue
        try:
            boxes.append((title, to_cents(base_txt), to_cents(paid_txt)))
        except ValueError:
            continue
    box = choose_box(boxes, name)
    if box is None:
        return {"title": "", "currency": "other", "base_cents": None, "paid_cents": None} if other_currency else None
    return {"title": box[0], "currency": "USD", "base_cents": box[1], "paid_cents": box[2], "boxes": len(boxes)}


def today_price(data):
    """Today's list and paid price of the standard edition, from the store API's purchase options."""
    boxes = []
    for group in [g for g in data.get("package_groups", []) if g.get("name") == "default"]:
        for sub in group.get("subs", []):
            text = re.sub(r"<[^>]+>", " ", sub.get("option_text", ""))
            prices = re.findall(r"\$[\d,]+\.\d\d", text)
            if not prices:
                continue
            title = re.split(r"\s-\s+\$", text)[0].strip()
            boxes.append((title, to_cents(prices[0]), int(sub.get("price_in_cents_with_discount", 0))))
    return choose_box(boxes, data.get("name", ""))


def pick_snapshots(caps, release):
    """Nearest capture to the launch and to each target month; returns (label, timestamp, url)."""
    dated = [(datetime.strptime(ts[:8], "%Y%m%d").date(), ts, url) for ts, url in caps]
    picks = []
    lo, hi = release + timedelta(days=LAUNCH_WINDOW[0]), release + timedelta(days=LAUNCH_WINDOW[1])
    launch = [c for c in dated if lo <= c[0] <= hi]
    launch.sort(key=lambda c: (c[0] > release, abs((c[0] - release).days)))
    picks += [("launch", c[1], c[2]) for c in launch[:3]]          # up to three, in case one fails to parse
    for m in SNAP_MONTHS:
        target = release + timedelta(days=round(30.44 * m))
        near = [c for c in dated if abs((c[0] - target).days) <= SNAP_TOLERANCE_DAYS]
        near.sort(key=lambda c: abs((c[0] - target).days))
        picks += [(f"m{m}", c[1], c[2]) for c in near[:2]]          # the second is a fallback only
    return picks


def price_history(appid, release, name=""):
    caps = cdx_list(appid, release + timedelta(days=LAUNCH_WINDOW[0]), release + timedelta(days=round(30.44 * 37)))
    rows, done = [], set()
    for label, ts, url in pick_snapshots(caps, release):
        if label in done:
            continue
        html = get(f"https://web.archive.org/web/{ts}id_/{url}", "wayback")
        parsed = parse_store_page(html, name) if html else None
        if parsed and parsed["currency"] == "USD":
            rows.append({"appid": appid, "label": label, "timestamp": ts, **parsed})
            done.add(label)
    return rows, len(caps)


def pre_release_share(short, months):
    """Share of each game's reviews (to 36 months after release) dated before its release month."""
    m = months.merge(short[["appid", "release_date"]], on="appid")
    rel = (pd.to_datetime(m.month).dt.to_period("M") - pd.to_datetime(m.release_date).dt.to_period("M"))
    m["rel"] = rel.apply(lambda x: x.n)
    m["n"] = m.up + m.down
    m = m[m.rel < 36]
    pre = m[m.rel < 0].groupby("appid").n.sum()
    return (pre / m.groupby("appid").n.sum()).reindex(short.appid).fillna(0)


def fresh_launches(short, months):
    """Drop games already on sale before their Steam release date; keeps the review-rank order."""
    share = pre_release_share(short, months)
    early = set(share[share > PRE_RELEASE_MAX].index)
    elsewhere = set(NOT_FRESH) & set(short.appid)
    print(f"  dropped {len(early)} games with >{PRE_RELEASE_MAX:.0%} of reviews before release (early access "
          f"or relisted) and {len(elsewhere - early)} on the judgment list", flush=True)
    return short[~short.appid.isin(early | elsewhere)]


def cc_crawls():
    """Common Crawl crawls with their start and end dates."""
    info = json.loads(get(CC_COLLINFO, "ccindex"))
    out = []
    for c in info:
        lo, hi = (datetime.fromisoformat(c[k][:19]).date() for k in ("from", "to"))
        out.append((c["id"], lo, hi))
    return out


def cc_lower_bound(idx_url, key, size):
    """Binary search, by byte ranges, for the position of the first index line at or after key."""
    lo, hi = 0, size
    while hi - lo > 8192:
        mid = (lo + hi) // 2
        chunk = get(idx_url, "ccdata", byte_range=(mid, 4096), gz=False, cache=False)
        if chunk is None:
            return None
        line = chunk.split("\n")[1]
        lo, hi = (mid, hi) if line.split(" ")[0] < key else (lo, mid)
    return lo


def cc_section(crawl, memo={}):
    """The slice of a crawl's top-level index (cluster.idx) that covers Steam store app pages."""
    if crawl not in memo:
        idx_url = f"{CC_DATA}cc-index/collections/{crawl}/indexes/cluster.idx"
        key = hashlib.sha1(idx_url.encode()).hexdigest()
        path = CACHE / "ccsection" / key
        if not path.exists():
            head = requests.head(idx_url, headers=HEADERS, timeout=60)
            if head.status_code != 200:
                memo[crawl] = []
                return []
            size = int(head.headers["content-length"])
            lo, hi = (cc_lower_bound(idx_url, k, size) for k in CC_SECTION)
            if lo is None or hi is None:
                return []
            text = get(idx_url, "ccdata", byte_range=(lo, hi + 8192 - lo), gz=False, cache=False)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text or "", encoding="utf-8")
        rows = []
        for line in path.read_text(encoding="utf-8").split("\n")[1:-1]:
            f = line.split("\t")
            if len(f) >= 4:
                rows.append((f[0].split(" ")[0], f[1], int(f[2]), int(f[3])))
        memo[crawl] = rows
    return memo[crawl]


def cc_records(crawl, appid):
    """Every capture of the game's store page in one crawl, read from the crawl's compressed index blocks."""
    sec = cc_section(crawl)
    prefix = f"com,steampowered,store)/app/{appid}"
    starts = [i for i, r in enumerate(sec) if r[0] < prefix]
    if not starts:
        return []
    blocks = [starts[-1]] + [i for i in range(starts[-1] + 1, len(sec)) if sec[i][0] <= prefix + "~"]
    pat = re.compile(rf"^com,steampowered,store\)/app/{appid}(/|$|\?)")
    recs = []
    for i in blocks:
        _, shard, off, length = sec[i]
        txt = get(f"{CC_DATA}cc-index/collections/{crawl}/indexes/{shard}", "ccdata", byte_range=(off, length))
        for line in (txt or "").splitlines():
            surt, ts, js = line.split(" ", 2)
            if pat.match(surt):
                r = json.loads(js)
                r["timestamp"] = ts
                if r.get("status") == "200" and "cc=" not in r["url"].lower():
                    recs.append(r)
    return recs


def cc_price_history(appid, release, crawls, name=""):
    """Launch and target-month prices from Common Crawl's archive of the US store page."""
    targets = [("launch", release + timedelta(days=LAUNCH_WINDOW[0]), release + timedelta(days=LAUNCH_WINDOW[1]),
                release)]
    for m in SNAP_MONTHS:
        mid = release + timedelta(days=round(30.44 * m))
        targets.append((f"m{m}", mid - timedelta(days=CC_TOLERANCE_DAYS), mid + timedelta(days=CC_TOLERANCE_DAYS),
                        mid))
    rows, tried = [], 0
    for label, lo, hi, mid in targets:
        near = [c for c in crawls if c[1] <= hi and c[2] >= lo]
        near.sort(key=lambda c: abs((c[1] + (c[2] - c[1]) / 2 - mid).days))
        for crawl, _, _ in near[:4]:
            tried += 1
            recs = [r for r in cc_records(crawl, appid)
                    if lo <= datetime.strptime(r["timestamp"][:8], "%Y%m%d").date() <= hi]
            recs.sort(key=lambda r: (r.get("languages", "") != "eng",
                                     abs((datetime.strptime(r["timestamp"][:8], "%Y%m%d").date() - mid).days)))
            parsed = None
            for r in recs[:4]:
                warc = get(f"{CC_DATA}{r['filename']}", "ccdata",
                           byte_range=(int(r["offset"]), int(r["length"])))
                parsed = parse_store_page(warc, name) if warc else None
                if parsed and parsed["currency"] == "USD":
                    rows.append({"appid": appid, "label": label, "timestamp": r["timestamp"], **parsed})
                    break
                parsed = None
            if parsed:
                break
    return rows, tried


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["commoncrawl", "wayback"], default="commoncrawl")
    ap.add_argument("--last", type=int, default=SAMPLE, help="fetch prices for the first N games of the sample")
    args = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    spy = steamspy_catalog()
    spy.to_csv(RAW / "steamspy_catalog.csv", index=False,
               columns=["appid", "name", "developer", "publisher", "owners", "positive", "negative",
                        "reviews", "price", "initialprice"])
    paid = spy[pd.to_numeric(spy.initialprice, errors="coerce").fillna(0) > 0]
    print(f"Paid today: {len(paid)}; dropped {len(spy) - len(paid)} free-to-play or delisted entries")
    cand = paid.sort_values("reviews", ascending=False).head(CANDIDATES)

    details = []
    for i, appid in enumerate(cand.appid):
        row = appdetails(int(appid))
        if row:
            details.append(row)
        if i % 100 == 0:
            print(f"  store API {i}/{len(cand)}")
    det = pd.DataFrame(details).merge(cand[["appid", "reviews", "owners"]], on="appid")
    det.to_csv(RAW / "steam_appdetails.csv", index=False)

    ok = det[(det.type == "game") & det.release_date.notna()].copy()
    ok["release_date"] = pd.to_datetime(ok.release_date)
    in_window = ok[ok.release_date.between(RELEASE_FROM, RELEASE_TO)]
    short = in_window.sort_values("reviews", ascending=False).head(SHORTLIST)
    print(f"Store API answered for {len(det)}; games with a release date: {len(ok)}; "
          f"released {RELEASE_FROM} to {RELEASE_TO}: {len(in_window)}; shortlisted the top {len(short)} by reviews",
          flush=True)

    months = []
    for appid in short.appid:
        months += review_months(int(appid))
    months = pd.DataFrame(months)
    months.to_csv(RAW / "steam_review_months.csv", index=False)
    print(f"Review histograms: {len(months)} game-months for {months.appid.nunique()} games", flush=True)

    fresh = fresh_launches(short, months)
    sample = fresh.head(SAMPLE)
    sample[["appid"]].to_csv(RAW / "sample_appids.csv", index=False)
    print(f"Kept the top {len(sample)} fresh launches by reviews", flush=True)

    order = list(sample.head(args.last).itertuples())
    crawls = cc_crawls() if args.source == "commoncrawl" else None
    out = RAW / f"steam_prices_{args.source}.csv"
    snaps, caps_log = [], []
    for i, r in enumerate(order):
        if args.source == "wayback":
            rows, ncap = price_history(int(r.appid), r.release_date.date(), r.name)
        else:
            rows, ncap = cc_price_history(int(r.appid), r.release_date.date(), crawls, r.name)
        snaps += rows
        caps_log.append({"appid": r.appid, "source": args.source, "captures_or_crawls_checked": ncap,
                         "parsed": len(rows)})
        print(f"  [{i + 1}/{len(order)}] {r.name}: {ncap} archived days or crawls, {len(rows)} prices parsed",
              flush=True)
    pd.DataFrame(snaps).to_csv(out, index=False)
    pd.DataFrame(caps_log).to_csv(RAW / f"coverage_{args.source}.csv", index=False)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    (RAW / "DOWNLOADED.txt").write_text(f"Steam, SteamSpy, Common Crawl and Wayback data fetched {stamp} (UTC)\n")
    print(f"Saved {len(snaps)} parsed price captures for {len(order)} games to {out.name}")


if __name__ == "__main__":
    main()
