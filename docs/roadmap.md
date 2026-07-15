# Roadmap

This roadmap is ordered by dependency and evidence, not by promised dates. It
describes the intended product direction as of 15 July 2026.

## Product thesis

AT1 Stress Radar should become an open, provenance-first **contract-to-capital
scenario compiler**: a tool that translates instrument terms, market
assumptions, issuer capital disclosures, and stress paths into auditable cash
flow and capital-action consequences.

The north-star question is:

> How much value is at risk, why, and at which call, distribution, or capital
> threshold?

The differentiated feature is the evidence chain, not a more precise-looking
price. Public bank data usually stops at prudential ratios. Bond models usually
stop at cash flows. This project should connect them while exposing every
source, transformation, entity basis, and missing input.

```text
verified AT1 terms ----------\
market assumptions -----------\
issuer and entity mapping ------> scenario compiler --> state cash flows
official capital disclosures --/                          + value changes
official stress paths --------/                           + threshold distances
                                                           + evidence record
```

This is an inference about a useful open-source gap, not a claim that no
proprietary product covers similar ground.

## Product principles

1. **Evidence before estimation.** Every non-synthetic input records its source,
   reference date, retrieval time, units, transformation, and revision.
2. **Entity basis is part of the number.** Never join by bank name alone or
   compare a consolidated capital ratio with a solo-entity trigger silently.
3. **Explain components, not one stress score.** Keep extension economics,
   distribution headroom, contractual trigger distance, and valuation impact
   separate.
4. **Deterministic before probabilistic.** Build contractual states and
   sensitivity surfaces before fitting call or loss probabilities.
5. **Useful without licensed prices.** Support user-supplied market observations
   and public rate proxies; make commercial feeds optional adapters.
6. **Missing data stays missing.** Block or qualify a metric when required
   inputs, dates, or entity mappings do not reconcile.
7. **Model values stay model values.** The tool must not imply executable price,
   legal interpretation, regulatory determination, or investment advice.

## Milestone 0: transparent state pricer (`v0.1`, complete)

**User outcome:** inspect a synthetic AT1's terms and compare a first-call cash
flow state with one extension state.

Delivered:

- typed, defensive instrument and scenario YAML validation;
- issue-anchored fixed-to-reset cash-flow schedules;
- deterministic called and one-period-extended model values;
- CLI and Streamlit presentation layers;
- boundary-focused tests for dates, day counts, non-finite inputs, loaders, and
  valuation reconciliation.

Boundary: the scenario schema is validated but not applied. The project is not
yet a stress engine.

## Milestone 1: make the stress radar real (`v0.2`)

**User outcome:** run a named scenario and see exactly which assumptions drove
the change in value.

Build:

- split the flat discount input into a risk-free component and credit spread,
  preserving the current flat-rate mode for comparison;
- apply risk-free, spread, reset-rate, and call-state shocks from the existing
  scenario schema;
- return base value, stressed value, total change, and factor attribution with
  nonlinear interaction shown explicitly;
- add a `stress` CLI command, a Streamlit scenario waterfall, and CSV/JSON
  evidence-pack export;
- keep equity and CET1 shocks informational until an as-of-dated issuer base
  state exists.

Exit gate:

- direct stressed revaluation and reported decomposition reconcile to within
  one basis point of notional;
- base-case scenarios reproduce unshocked state values;
- order-dependent attribution is either eliminated or reported as an explicit
  interaction term;
- exported inputs, assumptions, model version, cash flows, and results reproduce
  the same run within documented numerical tolerances.

Not in this milestone: issuer probabilities, live market feeds, or capital
trigger mechanics.

## Milestone 2: extension-cliff workbench (`v0.3`)

**User outcome:** see how value and call economics change across the full set of
future call dates, rather than one arbitrary extension.

Build:

- generalise from two states to call horizons `0..N`;
- show price by call date, incremental extension loss, break-even reset rate,
  and refinancing-spread threshold;
- add rate, spread, and reset sensitivity surfaces;
- support valuation after the first call plus settlement and accrued-interest
  conventions needed for seasoned instruments;
- introduce a versioned result envelope with source, as-of date, units,
  assumptions, and model version;
- create a hand-verified pilot of 3-5 EU issuers and 10-20 instruments before
  attempting bulk real-terms ingestion.

Exit gate:

- every call horizon lands on a validated contractual schedule;
- extension ladders reconcile to their underlying cash-flow rows;
- at least one external or independently implemented golden valuation fixture
  checks each supported convention;
- no real instrument can load without a source URL, source hash, verification
  date, and explicit trigger basis.

Not in this milestone: call predictions or unattended prospectus extraction.

## Milestone 3: contract-to-capital radar (`v0.4`)

**User outcome:** connect an AT1's contractual terms to the correct issuer's
official capital position and see transparent threshold distances under an
official stress path.

Build:

- an identity model containing at least `issuer_lei`, `parent_lei`,
  `prudential_scope`, `trigger_entity`, `trigger_basis`, `resolution_entity`,
  and `reference_date`;
- adapters for the EBA Pillar 3 Data Hub, ECB Pillar 2 requirements, and EBA
  bank-level stress-test results that retain immutable, checksummed raw
  snapshots;
- an as-of-dated `IssuerState` with reported CET1, applicable disclosed capital
  requirements and buffers, and complete provenance;
- a capital ladder that displays reported headroom and contractual trigger
  distance only when entity basis and dates reconcile;
- deterministic coupon-cancellation, temporary/permanent write-down, and equity
  conversion states;
- official scenario replay that maps published bank capital paths into the
  contractual state engine without double-counting reported management actions.

Exit gate:

- the hand-verified pilot reconciles every displayed figure to an official
  source and documents any transformation;
- a mismatched consolidation scope blocks the comparison instead of producing
  a number;
- maximum distributable amount (MDA) proximity is shown only when the full
  applicable requirement, buffer, capital-stack, and entity inputs are present;
- official stress results are labelled counterfactual scenarios, never
  forecasts;
- coupon discretion is always visible, including when regulatory headroom is
  positive.

Not in this milestone: legal opinions, recovery estimates, or a single
probability of coupon cancellation, write-down, or conversion.

## Milestone 4: portfolio and lifecycle radar (`v0.5`)

**User outcome:** identify which holdings, issuers, and call dates drive a
portfolio's stress loss and what changed since the last evidence snapshot.

Build:

- same-currency holdings and portfolio aggregation first;
- loss attribution by instrument, issuer, call date, and stress channel;
- extension concentration and upcoming call/reset calendars;
- a versioned lifecycle registry for calls, non-calls, coupon decisions,
  amendments, and capital disclosures;
- source-diff review queues and local alerts that require human confirmation for
  extracted legal terms;
- shareable evidence packs with input snapshots, source hashes, missingness,
  transformations, results, and model version.

Exit gate:

- portfolio totals reconcile to instrument results within documented numerical
  tolerances;
- revised or stale source data is visible and never silently overwrites history;
- every alert links to the changed source and the field-level diff;
- mixed currencies remain blocked until FX methodology and source policy are
  explicit.

## Milestone 5: validated research release (`v1.0`)

**User outcome:** use a reproducible, independently checked research tool whose
failure modes and data rights are clear.

Build:

- historical evaluation against documented calls, non-calls, coupon actions,
  and capital events;
- independent pricing references and property-based schedule tests;
- UK support only after the EU entity and evidence model is stable;
- optional licensed market-price and spread adapters behind a provider
  interface;
- MREL/TLAC context without pretending to reconstruct non-public resolution
  plans;
- a published model card, data-source register, schema migration policy, and
  validation report.

Exit gate:

- all supported calculations have independent or golden references;
- historical event coverage and selection bias are quantified;
- any probabilistic call model is calibrated out of sample and adds value over
  transparent rules; otherwise the product remains scenario-based;
- redistribution and attribution rules are verified for every bundled source;
- deployment, authentication, and multi-user persistence are considered only
  after the local research workflow is proven useful.

## Data feasibility

The sources below make the product thesis practical, but they do not remove
the need for basis checks, revision history, or legal review.

| Source | Intended use | Important constraint |
|---|---|---|
| [EBA Pillar 3 Data Hub](https://www.eba.europa.eu/risk-and-data-analysis/pillar-3-data-hub) | Harmonised prudential disclosures and bulk XBRL-CSV snapshots | Templates and reporting frameworks evolve; retain raw files, checksums, and revision lineage. |
| [ECB bank-specific Pillar 2 requirements](https://www.bankingsupervision.europa.eu/activities/srep/pillar-2-requirement/html/index.en.html) | Disclosed P2R input to capital headroom | Decisions can change, consent can be withdrawn, and non-binding Pillar 2 guidance is different. |
| [EBA 2025 stress-test results](https://www.eba.europa.eu/eu-wide-stress-test-2025) | Bank-level official capital paths for scenario replay | Sample coverage is limited and the adverse path is a counterfactual, not a forecast. |
| [ECB yield curves and SDMX API](https://data.ecb.europa.eu/methodology/yield-curves) | Reproducible public rate curves and sensitivity inputs | Euro-area government curves are proxies, not contractual mid-swap reset rates. |
| [GLEIF LEI data](https://www.gleif.org/en/meta/lei-data-terms-of-use/) | CC0 legal-entity identity layer | LEIs do not encode prudential consolidation or contractual trigger basis. |
| Issuer prospectuses and disclosures | Instrument terms and lifecycle events | Store extracted facts, links, and hashes; do not assume the source documents may be republished. |
| User-supplied or licensed market data | Prices, spreads, and refinancing assumptions | Keep out of redistributable fixtures unless the licence explicitly allows bundling. |

Reuse must follow the [EBA legal notice](https://www.eba.europa.eu/find-out-about-us/legal-notice)
and [ECB reuse terms](https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html),
including attribution and disclosure of transformations.

## Continuous hardening

These items run alongside product milestones:

- commit the Streamlit `AppTest` smoke and run it in CI;
- add `uv build` and install-from-wheel smoke checks to CI;
- keep CLI and UI validation bounds identical;
- add property tests for schedule anchors and day-count edge cases;
- publish schema migrations for versioned input and result records;
- preserve raw external snapshots, checksums, retrieval metadata, and revisions;
- test stale, missing, revised, and mismatched-entity data paths directly.

## Decision gates

- **Licence:** choose and document a project licence before inviting external
  contributions or redistribution.
- **Pilot feasibility:** validate 3-5 issuers by hand before committing to a
  broad Pillar 3 or prospectus ingestion pipeline.
- **Market data:** decide between user-supplied observations and a licensed
  provider before any public price-history feature.
- **Geography:** keep the first real-data release EU-focused; add the UK only
  after entity, trigger-basis, and provenance rules survive the pilot.
- **Probabilities:** require a documented historical dataset and out-of-sample
  benchmark before presenting call or capital-action probabilities.

## Explicit non-goals

- executable pricing or trading;
- automated legal interpretation of prospectuses;
- regulator-grade capital forecasts;
- opaque machine-learning stress scores;
- scraping or redistributing a copyrighted document corpus;
- precise recovery or resolution-waterfall predictions from non-public plans.

## Success measures

- One run answers the next call dates, extension cliff, scenario value change,
  and available capital-threshold distances without a spreadsheet handoff.
- Every non-synthetic result is reproducible from a versioned source snapshot
  and model version.
- Every displayed external number has an as-of date, entity basis, source link,
  and transformation record.
- Missing or mismatched evidence removes or qualifies a metric instead of
  creating false precision.
- Scenario attribution and portfolio totals reconcile within their documented
  numerical tolerances.

## Related documentation

- [README](../README.md)
- [Architecture](architecture.md)
- [Methodology](methodology.md)
- [Data dictionary](data_dictionary.md)
