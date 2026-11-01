# Stokey (1979, 1981) on Steam: findings

## In plain English

Nancy Stokey proved in 1979 that a monopolist who can promise never to cut its price, selling to a fixed group of
buyers, should charge one price forever and sell everything at once. In 1981 she showed that a monopolist who
cannot make that promise is driven toward cost, faster the more often it can change its price. Video games on
Steam cost nothing to copy and each is sold by the one publisher that owns it, so they are a clean test.

- **List prices mostly hold.** 93% of the 122 games observed a year after launch were still at their launch list
  price, and 73% at three years. Elden Ring (FromSoftware, Bandai Namco), Red Dead Redemption 2 (Rockstar) and
  God of War (PlayStation) never moved their list price. That looks like Stokey's committed seller, not the Coase collapse.
- **Big releases cut, small ones do not.** 40% of games launched at $40 or more had cut their list price by
  month 36, usually to two-thirds of launch (Monster Hunter: World from Capcom, DOOM Eternal and Starfield from
  Bethesda). None of the games launched under $15 had cut, and two had raised it.
- **The discounting happens in sales.** On a typical day 14% to 19% of games were on sale, and the price actually
  charged at three years was 24% below launch in geometric mean (16% below in simple average) against 8% for
  the list price. Hogwarts Legacy was caught at
  $8.99 against a $59.99 list.
- **Buyers do not seem to wait for publishers that cut.** Games from publishers with a record of deep first-year
  cuts (Electronic Arts, Ubisoft, Capcom) did not sell a smaller share at launch than games from publishers that
  rarely cut (SEGA, Focus Entertainment).

A friendlier tour is in the [README](../README.md). The rest of this page is every table the scripts produce.

**Key to the labels.** *Launch* = the archived store page nearest release (75 days before to 31 days after).
*mK* = the capture nearest K months after release. *today* = the Steam store API price on November 1, 2026.
*List* = the regular price; *paid* = the price charged that day. *Ratio* = price over launch list price.
*Launch share* = reviews in the release month and the next over reviews in months 0 to 35. *First-year cut* =
one minus the lowest paid-to-launch ratio seen at months 3, 6 and 12. *pub_cut_loo* = the publisher's average
first-year cut on its other games.

## Sample (`sample_flow.csv`)

| step | count |
|---|---|
| Most-reviewed paid games sent to the Steam store API | 899 |
| Released 2017-01-01 to 2023-10-31 (type game) | 472 |
| Shortlist: most-reviewed in the window | 300 |
| Dropped: >2% of reviews before release month (early access or relisted) | 83 |
| Dropped: sold on another PC store first, or product changed (judgment list) | 21 |
| Games in the sample (top fresh launches by reviews) | 196 |
| Dropped: no archived US store page within 75 days before to 31 days after release | 53 |
| Games with a launch list price | 143 |
| Games with review histograms over the first 36 months | 143 |
| Games whose publisher has another game in the sample (extension) | 91 |

Of the 140 game-dates captured by both Common Crawl and the Wayback Machine (`archive_cross_check.csv`), the list
price agreed in all of them. Paid prices agree less often because the two archives' nearest captures can fall
on different days, one inside a sale and one outside.

| pairs | games | share_same_list_price | share_same_paid_price |
|---|---|---|---|
| 140 | 28 | 1 | 0.857 |

## Price paths (`price_paths.csv`)

CI columns are 95% Wilson intervals for the share unchanged.

| horizon | months | games | share_list_unchanged | ci_lo | ci_hi | share_list_raised | median_list_ratio | mean_list_ratio | share_on_sale | median_paid_ratio | mean_paid_ratio | share_list_cut |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| launch | 0 | 143 | 1 | 0.974 | 1.000 | 0 | 1 | 1 | 0.112 | 1 | 0.980 | 0 |
| m3 | 3 | 130 | 1 | 0.971 | 1.000 | 0 | 1 | 1 | 0.138 | 1 | 0.963 | 0 |
| m6 | 6 | 122 | 0.984 | 0.942 | 0.995 | 0.016 | 1 | 1.004 | 0.172 | 1 | 0.935 | 0 |
| m12 | 12 | 122 | 0.926 | 0.866 | 0.961 | 0.016 | 1 | 0.987 | 0.189 | 1 | 0.911 | 0.057 |
| m18 | 18 | 119 | 0.866 | 0.793 | 0.916 | 0.025 | 1 | 0.981 | 0.168 | 1 | 0.902 | 0.109 |
| m24 | 24 | 117 | 0.812 | 0.732 | 0.872 | 0.009 | 1 | 0.943 | 0.188 | 1 | 0.850 | 0.179 |
| m36 | 36 | 119 | 0.731 | 0.645 | 0.803 | 0.034 | 1 | 0.938 | 0.143 | 1 | 0.845 | 0.235 |
| today | 74 | 138 | 0.659 | 0.577 | 0.733 | 0.080 | 1 | 0.943 | 0.167 | 1 | 0.836 | 0.261 |

## By launch price, at 36 months (`price_tiers.csv`)

| launch_tier | games | share_list_unchanged_36m | share_list_cut_36m | share_list_raised_36m | median_ratio_if_cut | mean_paid_ratio_36m |
|---|---|---|---|---|---|---|
| under $15 | 17 | 0.882 | 0 | 0.118 |  | 1.034 |
| $15 to $39.99 | 44 | 0.841 | 0.114 | 0.045 | 0.667 | 0.868 |
| $40 and up | 58 | 0.603 | 0.397 | 0 | 0.667 | 0.772 |
| All | 119 | 0.731 | 0.235 | 0.034 | 0.667 | 0.845 |

## Regression of log price change on months since release (`price_path_regression.csv`)

OLS without a constant, one dummy per horizon, standard errors clustered by game; 729 captures from 143 games.
The month-3 list-price coefficient is exactly zero (no game had moved) and is excluded from the joint test.
`sale` is a linear probability model for being on sale.

| outcome | term | coef | pct_change | se | ci_lo | ci_hi | p | joint_F_all_zero | joint_p |
|---|---|---|---|---|---|---|---|---|---|
| ln_list | m03 | 0.000 | 0 | 0.000 | 0.000 | 0.000 |  | 6.033 | 0.000 |
| ln_list | m06 | 0.004 | 0.004 | 0.003 | -0.002 | 0.009 | 0.176 | 6.033 | 0.000 |
| ln_list | m12 | -0.016 | -0.016 | 0.008 | -0.032 | -0.001 | 0.042 | 6.033 | 0.000 |
| ln_list | m18 | -0.030 | -0.029 | 0.013 | -0.055 | -0.004 | 0.024 | 6.033 | 0.000 |
| ln_list | m24 | -0.074 | -0.071 | 0.018 | -0.109 | -0.039 | < 0.001 | 6.033 | 0.000 |
| ln_list | m36 | -0.086 | -0.082 | 0.020 | -0.126 | -0.046 | < 0.001 | 6.033 | 0.000 |
| ln_paid | m03 | -0.044 | -0.043 | 0.011 | -0.065 | -0.023 | < 0.001 | 16.828 | 0.000 |
| ln_paid | m06 | -0.095 | -0.090 | 0.024 | -0.143 | -0.047 | < 0.001 | 16.828 | 0.000 |
| ln_paid | m12 | -0.122 | -0.115 | 0.024 | -0.168 | -0.075 | < 0.001 | 16.828 | 0.000 |
| ln_paid | m18 | -0.153 | -0.142 | 0.033 | -0.217 | -0.089 | < 0.001 | 16.828 | 0.000 |
| ln_paid | m24 | -0.221 | -0.198 | 0.035 | -0.290 | -0.152 | < 0.001 | 16.828 | 0.000 |
| ln_paid | m36 | -0.272 | -0.238 | 0.050 | -0.370 | -0.175 | < 0.001 | 16.828 | 0.000 |
| sale | m03 | 0.138 |  | 0.031 | 0.079 | 0.198 | < 0.001 | 21.075 | 0.000 |
| sale | m06 | 0.172 |  | 0.034 | 0.105 | 0.240 | < 0.001 | 21.075 | 0.000 |
| sale | m12 | 0.189 |  | 0.036 | 0.119 | 0.258 | < 0.001 | 21.075 | 0.000 |
| sale | m18 | 0.168 |  | 0.035 | 0.100 | 0.236 | < 0.001 | 21.075 | 0.000 |
| sale | m24 | 0.188 |  | 0.036 | 0.117 | 0.259 | < 0.001 | 21.075 | 0.000 |
| sale | m36 | 0.143 |  | 0.032 | 0.080 | 0.206 | < 0.001 | 21.075 | 0.000 |

## Purchase timing (`timing_summary.csv`, game-level detail in `purchase_timing.csv`)

| games | median_launch_share | p25_launch_share | p75_launch_share | share_of_games_above_half | median_first_year_share | pooled_launch_share |
|---|---|---|---|---|---|---|
| 143 | 0.220 | 0.116 | 0.327 | 0.070 | 0.511 | 0.271 |

## Named games (`named_games.csv`)

The lowest paid price is the lowest on the days the archives captured in the first 36 months, not the lowest
ever charged. Blank cells are dates with no usable capture.

| game | publisher | released | launch_list | list_12m | list_36m | list_today | lowest_paid_seen_36m | launch_share_of_36m_reviews |
|---|---|---|---|---|---|---|---|---|
| ELDEN RING | FromSoftware, Inc. | 2022-02-24 | 59.990 | 59.990 | 59.990 | 59.990 | 59.990 | 0.394 |
| Cyberpunk 2077 | CD PROJEKT RED | 2020-12-09 | 59.990 | 59.990 | 59.990 | 59.990 | 29.990 | 0.522 |
| Red Dead Redemption 2 | Rockstar Games | 2019-12-05 | 59.990 | 59.990 | 59.990 | 59.990 | 40.190 | 0.145 |
| Hogwarts Legacy | Warner Bros. Games | 2023-02-10 | 59.990 | 59.990 | 59.990 | 59.990 | 8.990 | 0.512 |
| Starfield | Bethesda Softworks | 2023-09-05 | 69.990 | 69.990 | 49.990 | 49.990 | 48.990 | 0.609 |
| Monster Hunter: World | CAPCOM Co., Ltd. | 2018-08-08 | 59.990 | 59.990 | 29.990 | 29.990 | 19.790 | 0.174 |
| DOOM Eternal | Bethesda Softworks | 2020-03-19 | 59.990 | 59.990 | 39.990 | 29.990 | 39.990 | 0.281 |
| STAR WARS Jedi: Fallen Order™ | Electronic Arts | 2019-11-14 | 59.990 | 59.990 | 39.990 | 39.990 | 5.990 | 0.331 |
| God of War | PlayStation Publishing LLC | 2022-01-14 | 49.990 | 49.990 | 49.990 | 49.990 | 39.990 | 0.272 |
| It Takes Two | Electronic Arts | 2021-03-25 | 39.990 | 39.990 | 39.990 | 39.990 | 15.990 | 0.128 |
| Stray | Annapurna Interactive | 2022-07-19 | 29.990 |  | 29.990 | 29.990 | 17.990 | 0.479 |
| Hollow Knight | Team Cherry | 2017-02-24 | 14.990 | 14.990 | 14.990 | 14.990 | 14.990 | 0.026 |
| Phasmophobia | Kinetic Games | 2020-09-18 | 13.990 | 13.990 | 13.990 | 19.990 | 13.990 | 0.124 |
| Among Us | Innersloth | 2018-11-16 | 4.990 | 4.990 | 4.990 | 4.990 | 4.990 | 0.000 |

## Publishers with two or more games (`publishers.csv`)

| publisher | games | median_launch_price | mean_first_year_cut | share_list_cut_by_12m | median_launch_share |
|---|---|---|---|---|---|
| Electronic Arts | 9 | 59.990 | 0.291 | 0 | 0.331 |
| CAPCOM Co., Ltd. | 8 | 59.990 | 0.271 | 0.333 | 0.207 |
| BANDAI NAMCO Entertainment | 7 | 59.990 | 0.119 | 0 | 0.197 |
| SEGA | 6 | 59.990 | 0 | 0 | 0.249 |
| PlayStation Publishing LLC | 6 | 49.990 | 0.210 | 0 | 0.286 |
| Xbox Game Studios | 5 | 29.990 | 0.070 | 0 | 0.265 |
| Devolver Digital | 5 | 16.990 | 0.173 | 0 | 0.260 |
| Focus Entertainment | 4 | 37.490 | 0 | 0 | 0.120 |
| Square Enix | 4 | 59.990 | 0.213 | 0 | 0.180 |
| Warner Bros. Games | 4 | 59.990 | 0.071 | 0.250 | 0.352 |
| Team17 | 4 | 24.990 | 0.063 | 0 | 0.141 |
| Ubisoft | 4 | 59.990 | 0.300 | 0 | 0.130 |
| Paradox Interactive | 3 | 49.990 | 0.067 | 0 | 0.307 |
| Bethesda Softworks | 2 | 64.990 | 0.150 | 0 | 0.445 |
| Annapurna Interactive | 2 | 24.990 | 0 | 0 | 0.276 |
| PlayWay S.A. | 2 | 19.990 | 0.225 | 0 | 0.155 |
| 505 Games | 2 | 34.990 | 0.250 | 0 | 0.367 |
| Landfall | 2 | 5.490 | 0 | 0 | 0.079 |
| KRAFTON, Inc. | 2 | 44.990 | 0 |  | 0.505 |
| Gamirror Games | 2 | 14.990 | 0.100 | 0 | 0.386 |
| GIANTS Software | 2 | 42.490 | 0.243 | 1 | 0.170 |
| Frontier Developments | 2 | 52.490 | 0.475 | 0 | 0.258 |
| 2K | 2 | 49.990 | 0.620 | 0 | 0.257 |
| Avalanche Studios | 2 | 32.490 | 0.143 | 0.500 | 0.116 |

## Extension: do buyers wait for publishers that cut? (`waiting_regression.csv`, data in `waiting_games.csv`)

OLS with log launch price and release-year effects, standard errors clustered by publisher. `effect_of_1sd`
is the change in the outcome for a one standard deviation change in the regressor.

| spec | term | coef | se | ci_lo | ci_hi | p | n_games | n_publishers | mean_outcome | sd_regressor | effect_of_1sd |
|---|---|---|---|---|---|---|---|---|---|---|---|
| publisher reputation (leave-one-out) | pub_cut_loo | -0.019 | 0.076 | -0.168 | 0.129 | 0.797 | 91 | 24 | 0.251 | 0.155 | -0.003 |
| own first-year cut (descriptive) | cut_y1 | -0.010 | 0.054 | -0.116 | 0.096 | 0.854 | 143 | 76 | 0.241 | 0.214 | -0.002 |
| publisher reputation, first-year share | pub_cut_loo | -0.007 | 0.062 | -0.129 | 0.115 | 0.908 | 91 | 24 | 0.508 | 0.155 | -0.001 |

## No-commitment linear example, computed here (`coase_simulation.csv`)

Stationary linear equilibrium of the no-commitment game studied in Stokey (1981), with values uniform on [0, 1],
zero cost and a 10% annual discount rate, solved by the script. It illustrates the logic and is not a table from
the paper. The committed seller charges 0.5 and earns 0.25.

| price_changes | periods_per_year | delta | first_price | first_price_vs_commitment | profit_vs_commitment | share_sold_first_period |
|---|---|---|---|---|---|---|
| once a year | 1 | 0.905 | 0.236 | 0.472 | 0.472 | 0.236 |
| once a quarter | 4 | 0.975 | 0.136 | 0.272 | 0.272 | 0.136 |
| once a month | 12 | 0.992 | 0.083 | 0.167 | 0.167 | 0.083 |
| once a week | 52 | 0.998 | 0.042 | 0.084 | 0.084 | 0.042 |
