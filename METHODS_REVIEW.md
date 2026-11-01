# Methods review: Stokey (1979) and Stokey (1981)

**Paper.** Nancy L. Stokey, "Intertemporal Price Discrimination," *Quarterly Journal of Economics* 93(3),
August 1979, pp. 355–371 (DOI 10.2307/1883163). Companion: Nancy L. Stokey, "Rational Expectations and Durable
Goods Pricing," *Bell Journal of Economics* 12(1), Spring 1981, pp. 112–128.

**Statistical focus.** The 1979 proposition that a seller who can commit to a price path, facing buyers who
share one discount rate and a cost that does not fall in real terms, charges one constant price and makes all of
its sales at the start; and the 1981 proposition that without commitment the equilibrium approaches the
competitive (Coase) outcome as the period between price changes shrinks.

**Review standard.** Internal consistency of the formal results, explicitness of assumptions, and the
testability of the predictions. Both papers are theory papers with no data.

**What was read.** The full text of neither paper is freely available, and I did not read it. I read the
publisher's abstract page for the 1979 paper (Oxford Academic, which gives the section outline and page
numbers), the RePEc/IDEAS records for both papers including the 1981 abstract, and three later papers that
restate the results: Anderson and Dana, "Integrating Models of Price Discrimination" (Kellogg working paper,
2006), Deb, "Intertemporal Price Discrimination with Stochastic Values" (working paper, 2014), and Besbes and
Lobel, "Intertemporal Price Discrimination: Structure and Computation of Optimal Policies," *Management
Science* 61(1), 2015. Everything below about the papers' content is extracted from those sources, and claims
that rest on a single secondary account are flagged.

## Methods summary

The 1979 paper is a continuous-time model of a monopolist selling a good that each buyer purchases at most once.
Buyers differ in a taste parameter. As Anderson and Dana restate it, a buyer of type θ who buys at date t gets
utility proportional to θ times a common discount factor raised to the power t, and the unit cost of production
is a constant times the same discount factor, so cost is constant except for the time value of money. The seller
announces a whole price path at date zero and is held to it. Each buyer chooses the date that maximizes her
discounted surplus. The paper has two substantive sections according to the outline: Section II, "No production
costs: 'pure' discrimination" (p. 357), and Section III, "Positive production costs" (p. 363), followed by a
conclusion (p. 367).

The result, as all three secondary sources state it, is that under these assumptions the seller's best path is
the constant static monopoly price, so every sale happens at the first instant and the seller forgoes later
sales. Deb adds that the seller's maximum profit equals what it could earn with a single selling period.
Anderson and Dana, following Salant (1989), restate the positive-cost case: if the seller's real production cost
falls over time, a declining price path that induces some buyers to wait becomes optimal; if cost rises, the
price stays constant and everyone buys at once.

The 1981 paper drops commitment. Per its abstract, requiring buyers' expectations to be fulfilled along the
equilibrium path does not by itself restrict the output path; requiring expectations to depend continuously on
the remaining stock yields a unique, stationary equilibrium in which the seller saturates the market at every
date, output follows the competitive path, and profit is zero. In discrete time the equilibrium is sensitive to
the period length, approaching the Coase outcome as periods shorten and the monopoly-renter outcome as they
lengthen.

## Statistics extraction table

| Statistic | Value and unit | Source location | What it measures | What it does not establish |
|---|---|---|---|---|
| Optimal committed price path | Constant at the static monopoly price for all t | 1979, Section II (p. 357 onward); restated by Deb (2014, p. 2) and Besbes and Lobel (2015, p. 93) | The seller's best announced path when buyers share a discount rate and cost is flat in real terms | That real sellers can commit, or that buyers share one discount rate |
| Timing of sales under commitment | All sales at t = 0 | 1979, Section II, per Deb (2014, p. 2) | Share of purchases at the first instant under the optimal path | Anything about markets with new buyers arriving over time, which the model excludes |
| Committed profit | Equal to one-period monopoly profit | 1979, per Deb (2014, Section 4.1) | Value of the extra selling dates to a committed seller (zero) | The size of profit in any real market |
| Positive-cost case | Declining price path optimal if and only if real unit cost falls over time | 1979, Section III (p. 363), as restated by Anderson and Dana (2006, pp. 17–18) | When intertemporal discrimination pays for a committed seller | I could not check this against the original text; see verification items |
| No-commitment equilibrium (continuous time, continuous expectations) | Unique, stationary; output on the competitive path; zero profit | 1981 abstract (RePEc) | The Coase outcome as a rational-expectations equilibrium | That every no-commitment equilibrium has this form; the abstract says fulfilled expectations alone do not restrict the path |
| No-commitment equilibrium (discrete time) | Approaches Coase outcome as period length falls; approaches monopoly-renter path and maximum profit as it rises | 1981 abstract (RePEc) | Sensitivity of the outcome to how often the seller can change price | Any specific numerical rate of convergence; none was visible in what I read |

## Interpretation notes

- Research design: formal theory. There is no sample, no data, and no estimation, so sampling strategy, sample
  size, inclusion and exclusion criteria, missing-data treatment, confidence intervals and p-values do not apply.
  The "statistics" are the propositions above.
- Independent and dependent variables, read as model primitives and outcomes: the primitives are the distribution
  of buyer tastes, the common discount rate, the cost path and the commitment regime; the outcomes are the price
  path, the timing of purchases and the seller's profit.
- Statistical methods: optimal control and equilibrium analysis in continuous time, with a discrete-time version
  in 1981.
- Reported effect sizes: the results are qualitative (constant versus declining paths; zero versus monopoly
  profit). No calibration or numerical example was visible in the sources I read.
- Stated limitations: the 1981 abstract states the dependence of the equilibrium on how expectations respond to
  the stock and on the period length. I could not read the 1979 conclusion, so I cannot report its stated
  limitations.
- The assumption that matters most for testing is the common discount rate. Besbes and Lobel (2015) show
  that with heterogeneous patience correlated with value and a steady arrival of new buyers, a committed seller
  optimally uses cyclic prices with periodic sales. Conlisk, Gerstner and Sobel (*QJE* 99(3), 1984) reached a
  cyclic-sales result for arriving cohorts. These are extensions of the model, not errors in it.
- The modern rerun in this repository uses Stokey's committed-seller benchmark as a null hypothesis for Steam
  list prices. It is a test of whether the benchmark describes a present-day market, not a reproduction of
  anything in the papers, which contain no data.

## Unanswered questions

- Which exact assumptions on the distribution of tastes are needed in the 1979 paper, and whether the
  no-discrimination result requires the multiplicative form θ times the discount factor or holds more generally.
- Whether the 1979 paper discusses buyers arriving over time or a finite horizon.
- What the 1981 paper's discrete-time example implies quantitatively for period lengths of a week or a month.

## Items requiring expert verification

- The positive-cost result (declining prices if and only if real cost falls) rests on Anderson and Dana's
  restatement, which they attribute partly to Salant (1989). It should be checked against Section III of the
  original.
- The statement that committed profit equals single-period monopoly profit rests on Deb (2014, Section 4.1).
- The utility specification θ times the discount factor to the power t rests on Anderson and Dana's restatement.
- Every row of the statistics extraction table rests on secondary restatements, the publisher's section outline
  and the 1981 abstract, not on the full text. The section and page locations attributed to the original papers
  should be checked against them.
- The README and the repository's illustration table use a stationary linear equilibrium with uniform values,
  solved in the script. Whether Stokey (1981) presents this exact example is unverified, and the repository does
  not attribute its numbers to her.
