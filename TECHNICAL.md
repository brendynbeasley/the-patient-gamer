# Technical notes

Companion to the [README](README.md). Every table is in [results/FINDINGS.md](results/FINDINGS.md), and a
methods review of the original papers is in [METHODS_REVIEW.md](METHODS_REVIEW.md).

## The original study

Nancy L. Stokey, "Intertemporal Price Discrimination," *Quarterly Journal of Economics* 93(3), 1979,
pp. 355–371, and "Rational Expectations and Durable Goods Pricing," *Bell Journal of Economics* 12(1), 1981,
pp. 112–128. Both are theory papers with no data. The 1979 headline result, as restated by Deb (2014) and
Besbes and Lobel (2015), is that a monopolist who can commit to a price path, facing buyers with a common
discount rate and a cost that does not fall in real terms, charges the static monopoly price at every date and
makes all its sales at the start. The 1981 headline, from its abstract, is that without commitment and with
expectations that depend continuously on the remaining market, the unique equilibrium follows the competitive
path with zero profit, and in discrete time the outcome approaches that limit as the period between price
changes shrinks.

**Question.** Does a seller with a monopoly on a zero-marginal-cost durable good keep its launch price, as the
committed seller does, or cut toward cost, as the seller without commitment does?
**Test.** Log change in each Steam game's list price and paid price from launch, at 3 to 36 months.
**Paper's answer.** Committed seller: price ratio 1 at every horizon. No commitment, frequent moves: first price
near cost (8% of the committed price with weekly price changes in the linear example below).

## Headline results

| Statistic | Value |
|---|---|
| Games with a launch price | 143 (of 196 fresh launches) |
| Share at launch list price, 12 months | 0.926 (95% CI 0.866 to 0.961), N = 122 |
| Share at launch list price, 36 months | 0.731 (0.645 to 0.803), N = 119 |
| Share at launch list price, November 2026 | 0.659 (0.577 to 0.733), N = 138 |
| Log list-price change at 36 months | −0.086 (SE 0.020) |
| Log paid-price change at 36 months | −0.272 (SE 0.050), a 23.8% fall in the geometric mean |
| Share of capture days on sale, months 3 to 36 | 0.14 to 0.19 |
| Median launch share of first-three-year reviews | 0.220 (IQR 0.116 to 0.327), 143 games |
| Extension, publisher's cut record on launch share | −0.020 (SE 0.076), p = 0.80, 91 games, 24 publishers |
| Common Crawl vs Wayback list price, same game and date | identical in 140 of 140 pairs |

## Data

| File | Source | What it holds |
|---|---|---|
| `data/raw/steamspy_catalog.csv` | steamspy.com/api.php?request=all, pages 0 to 4 | 5,000 most-owned games |
| `data/raw/steam_appdetails.csv` | store.steampowered.com/api/appdetails, cc=us | Release date, publisher, today's price, 899 games |
| `data/raw/steam_review_months.csv` | store.steampowered.com/appreviewhistogram | Monthly review counts, 300 games |
| `data/raw/sample_appids.csv` | derived | The 196 fresh launches |
| `data/raw/steam_prices_commoncrawl.csv` | Common Crawl index and WARC files, data.commoncrawl.org | List and paid price per game and date |
| `data/raw/steam_prices_wayback.csv` | web.archive.org CDX API and raw captures | The same, 29 most-reviewed games |
| `data/raw/coverage_*.csv`, `DOWNLOADED.txt` | derived | Captures per game; download date, November 1, 2026 |

All are public and need no key. Raw responses (about 1 GB) are cached outside git.

## Method

The sample rules and horizons below were fixed before any price outcome was computed. The standard-edition
rule was refined afterward, when inspection showed DLC and bundle boxes being read as the game (DOOM Eternal's
expansion, a Resident Evil bundle), and Halo: The Master Chief Collection was added to the judgment list at that
stage because its launch page sold only one of the collection's games.

- **Sample.** Paid games released January 1, 2017 to October 31, 2023 (36 months of history before 2026), the
  300 most-reviewed. Drop a game if more than 2% of its reviews up to month 36 predate its release month
  (early access or a relisted page, 83 games) or if it is on a judgment list of 21 games first sold on another
  PC store or whose page changed product (`NOT_FRESH` in `src/fetch_steam.py`). Keep the top 196.
- **Launch price.** Standard-edition list price on the capture nearest release, from 75 days before (pre-orders)
  to 31 days after. Games without one (53) are dropped.
- **Later prices.** Capture nearest 3, 6, 12, 18, 24 and 36 months after release, within 30 days (Common Crawl)
  or 15 days (Wayback). Common Crawl preferred where both exist. "Today" is the store API price on the download
  date.
- **Standard edition.** The cheapest purchase box on the page whose title does not mark it as an add-on or
  premium edition (soundtrack, pass, pack, DLC, expansion, bundle, deluxe, ultimate, gold, and so on), with words
  in the game's own name ignored. Pages where every box is an add-on are skipped. USD pages only.
- **Unchanged.** List price within one cent of launch. **On sale.** Paid price below list price.
- **Launch share.** Reviews in the release month and the next, over reviews in months 0 to 35.
- **Main regression.** For game $`i`$ at horizon $`h`$,

```math
\ln\!\Big(\frac{P_{ih}}{P_{i0}}\Big) = \sum_{k} \beta_k\, \mathbf{1}[h = k] + \varepsilon_{ih},\qquad
k \in \{3, 6, 12, 18, 24, 36\}
```

  OLS, no constant, standard errors clustered by game, joint Wald F-test of $`\beta_k = 0`$. Run for the list
  price, the paid price, and an on-sale dummy.
- **Extension.** With $`\bar{c}_{-i,\text{pub}}`$ the mean, over the publisher's other sample games, of one minus
  the lowest paid-to-launch ratio seen in months 1 to 12,

```math
L_i = \alpha + \gamma\, \bar{c}_{-i,\text{pub}} + \delta \ln P_{i0} + \tau_{\text{year}(i)} + u_i
```

  OLS, standard errors clustered by publisher, $`H_0: \gamma = 0`$, Coase predicts $`\gamma < 0`$. Publishers are
  the first listed publisher, with spelling variants merged.
- **Theory illustration.** Stationary linear equilibrium with values uniform on [0, 1], zero cost, annual
  discount rate 10%, per-period factor $`\delta = e^{-0.10/n}`$ for $`n`$ price changes a year. Price is
  $`c`$ times the next cutoff and the cutoff falls by the factor $`b`$ each period, with

```math
c = \sqrt{1-\delta},\qquad b = \frac{1}{1 + \sqrt{1-\delta}},\qquad p_0 = c\,b
```

  The script checks this closed form against the equilibrium conditions. It is an illustration, not a table
  from either paper.

## Full test statistics

| Outcome | Month | Coefficient | SE | 95% CI | p |
|---|---|---|---|---|---|
| Log list price | 6 | 0.004 | 0.003 | −0.002 to 0.009 | 0.18 |
| Log list price | 12 | −0.016 | 0.008 | −0.032 to −0.001 | 0.04 |
| Log list price | 18 | −0.030 | 0.013 | −0.055 to −0.004 | 0.02 |
| Log list price | 24 | −0.074 | 0.018 | −0.109 to −0.039 | < 0.001 |
| Log list price | 36 | −0.086 | 0.020 | −0.126 to −0.046 | < 0.001 |
| Log paid price | 3 | −0.044 | 0.011 | −0.065 to −0.023 | < 0.001 |
| Log paid price | 12 | −0.122 | 0.024 | −0.168 to −0.075 | < 0.001 |
| Log paid price | 24 | −0.221 | 0.035 | −0.290 to −0.152 | < 0.001 |
| Log paid price | 36 | −0.272 | 0.050 | −0.370 to −0.175 | < 0.001 |
| On sale | 12 | 0.189 | 0.036 | 0.119 to 0.258 | < 0.001 |
| On sale | 36 | 0.143 | 0.032 | 0.080 to 0.206 | < 0.001 |

N = 729 captures from 143 games. At month 3 every list price equals launch, so that coefficient is exactly zero
and is left out of the joint test. Joint F: list price 6.03, paid price 16.83, on sale 21.08, all p < 0.001.

| Extension | Coefficient | SE | 95% CI | p | Games | Publishers |
|---|---|---|---|---|---|---|
| Launch share on publisher's cut record | −0.020 | 0.076 | −0.168 to 0.129 | 0.80 | 91 | 24 |
| Launch share on own first-year cut | −0.010 | 0.054 | −0.116 to 0.096 | 0.85 | 143 | 76 |
| First-year share on publisher's cut record | −0.007 | 0.062 | −0.129 to 0.115 | 0.91 | 91 | 24 |

## Reproducing the results

```bash
pip install -r requirements.txt
python src/stokey_steam.py                              # from the committed data/raw tables, seconds
python src/fetch_steam.py --source commoncrawl          # optional: rebuild data/raw, about an hour
python src/fetch_steam.py --source wayback --last 29    # optional: Wayback check, about an hour
```

A refetch will differ slightly, since current prices and review counts change daily.

## References

- Anderson & Dana (2006). Integrating models of price discrimination. Working paper, Kellogg School of
  Management, Northwestern University.
- Besbes, O. & Lobel, I. (2015). Intertemporal price discrimination: Structure and computation of optimal
  policies. *Management Science* 61(1), 92–110.
- Coase, R. H. (1972). Durability and monopoly. *Journal of Law and Economics* 15(1), 143–149.
- Conlisk, J., Gerstner, E. & Sobel, J. (1984). Cyclic pricing by a durable goods monopolist. *QJE* 99(3),
  489–505.
- Deb, R. (2014). Intertemporal price discrimination with stochastic values. Working paper, University of
  Toronto.
- Gul, F., Sonnenschein, H. & Wilson, R. (1986). Foundations of dynamic monopoly and the Coase conjecture.
  *Journal of Economic Theory* 39(1), 155–190.
- Stokey, N. L. (1979). Intertemporal price discrimination. *QJE* 93(3), 355–371.
- Stokey, N. L. (1981). Rational expectations and durable goods pricing. *Bell Journal of Economics* 12(1),
  112–128.
