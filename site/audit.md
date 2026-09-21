# Net Watcher product and market audit

**Research date:** 2026-09-08 (UTC)
**Status:** assessment and recommendation, not a product launch decision

## Executive verdict

Net Watcher is currently a static, synthetic-only research landing and governance scaffold, not a monitoring product, dataset, API, or hosted service. Its present value is methodological: it explains why registration events, routing observations, and validation snapshots must not be collapsed into one causal story. No user-base evidence is available in the scoped material, and no demand measurement or revenue evidence was found.

The public evidence supports category overlap, not a measured claim of a saturated market. BGPalerter, RIPE routing services, and RouteViews document route-change visibility and historical context.[1][4][7]
BGPStream documents source processing.[27]
Hurricane Electric's toolkit documents additional routing tools and source caveats.[22][23]
IRR Explorer documents registration-policy inspection and related routing context.[25][26]
That overlap is enough to reject an undifferentiated alert, lookup, or dashboard pivot. It does not prove total saturation, high demand, or an unmet niche.

The bounded recommendation is **narrow and validate**, not build a broad service. The most testable hypothesis is an own-network explanation job: help an operator explain a change affecting customer-owned or explicitly authorised prefixes or autonomous systems, with a concise evidence chain, viewpoint labels, missingness, and uncertainty. An open-source local provenance toolkit is a separate implementation axis, not proof of demand. A public aggregate research or education atlas should remain a separate governance decision because current policy bars research-derived flow into product or commercial systems.

## Users, jobs, and present value

A plausible first user is a small network operator, security engineer, or incident investigator who already receives a route-change signal and needs to answer: what changed, which independent viewpoints observed it, what registration or policy context is relevant, what is missing, and what remains uncertain? The job is explanation and triage, not attribution. Existing operational products make route monitoring a credible problem category, but they do not establish demand for this particular explanation format.[1][8][9]

A second possible audience is a researcher or educator comparing registration-event, routing-observation, and validation-snapshot clocks. The current landing is useful to that audience as a clear boundary and interpretation rule. It is not yet useful as an end-user tool because it offers no data, findings, API, dashboard, or operational alerting.

The qualitative assessment is therefore direction-specific rather than a claim about a market. Maintenance would be continuous once live: source adapters, parser changes, historical corrections, rate limits, retention policy, terms review, and explanation quality all become operator responsibilities. No user interviews, conversion data, pricing study, or market-size estimate should be inferred from this assessment.

## Direction comparison and current policy feasibility

The three directions below are intentionally distinct. A may use the same local provenance components as C, but its job and decision boundary remain different; B is a separate aggregate research or education publication. The judgments are qualitative and express present confidence, not fabricated market metrics.

| Direction | Value / need | Importance | Demand confidence | Key features | Effort | Free / freemium / OSS viability | Prospects | Current policy feasibility | Future strategic merit |
|---|---|---|---|---|---|---|---|---|---|
| A — own-network explanation job | Plausible need for an authorised operator who must explain a route change, not attribute it. | Potentially high in a live incident; unproven outside that job. | Low until operator conversations test repeat use. | Evidence chain, viewpoint labels, missingness, uncertainty, authorised scope. | Moderate for synthetic proof; high for reliable source integrations. | Free or self-hosted is plausible; freemium adds account, abuse, privacy, billing, support, and lock-in burden; OSS core is plausible. | Conditional on a recurring operator job and safe source terms. | Most feasible for a synthetic experiment; real collection still needs separate governance and terms review. | Strongest first hypothesis because it has a narrow job and bounded scope. |
| B — public aggregate research / education atlas | Useful for comparing clocks, viewpoints, and uncertainty for research or teaching. | Educational value may be meaningful; operational importance is unproven. | Low without evidence of a recurring audience or publication use. | Aggregate views, provenance notes, uncertainty, correction path, no row-level records. | High for durable curation, source review, and maintenance. | Free public output is the natural fit; freemium and closed commercial service are poor fits under the current boundary; OSS tooling may support it. | Dependent on a separate publication decision and sustainable curation. | Not currently feasible as an authorised product flow because policy bars research-derived output from product or commercial systems. | Potentially valuable as a governed public research artifact, but not a product decision. |
| C — local provenance toolkit | Plausible need for reproducible local investigation without a hosted dependency. | Important for reproducibility and operator control; user value is unproven. | Low until synthetic users can complete the workflow and request adapters. | Local schema, CLI, synthetic fixtures, source-version records, reproducible explanation export. | Moderate for a narrow local core; high for adapters and long-term compatibility. | OSS is the clearest fit; free self-hosted use is plausible; freemium is optional but not assumed. | Good if setup and reproduction costs are demonstrably lower than alternatives. | Feasible for synthetic local fixtures; real source access remains subject to governance, privacy, and terms review. | A credible enabling axis and possible complement to A, not evidence of standalone demand. |

Current policy feasibility is a constraint on what may be done now; future strategic merit is a hypothesis about what may be worth validating later. Neither column approves collection, publication, hosting, pricing, or licensing.

## Alternatives and competitive context

| Alternative | Documented job or capability | Implication |
|---|---|---|
| BGPalerter | Open-source route-change monitoring and alerting.[1] | Monitoring is established; alerts alone are not a differentiator. |
| RIPE RIS / RIPEstat | Historical routing status, visibility, origin, neighbours, and multiple datasets with visualisation.[7][24] | History and temporal context already exist. |
| RouteViews | Archived public routing views from many collectors and viewpoints; its terms specify attribution and other conditions for commercial use.[4][5] | Observations are viewpoint-dependent and source terms are material. |
| BGPStream | A framework for processing and accessing diverse BGP data sources; its repository identifies GPL-2.0 code.[19][20][27] | The enabling layer exists; integration and redistribution need review. |
| Hurricane Electric BGP Toolkit | Prefix and peer reports, looking glass, traceroute, RPKI/ASPA, exchange, and related tools; its Super Looking Glass describes multiple sources and possible delay.[22][23] | “Many sources” is not novel; source disclosure and workflow matter. |
| NLNOG IRR Explorer | Near-real-time exploration of IRR objects and relations, RPKI status, BGP origins, and registry statistics; the repository is BSD-2-Clause.[25][26] | Broad IRR/BGP/RPKI joining already exists. |

These are category evidence, not a complete competitor census or proof that users prefer one option. The differentiated hypothesis is narrower: a reproducible explanation record that keeps clocks, viewpoints, source versions, uncertainty, and citations visible in one investigation workflow. Existing history and explanation-adjacent surfaces mean this is a hypothesis about usefulness, not a demonstrated gap.

The relevant switching costs are not only interface familiarity. They include existing alert integrations, local data retention, operator trust, source coverage, reproducibility, and the legal and operational cost of adding another collector. A new tool must reduce investigation time or interpretation error enough to justify those costs; that has not been measured.

## Licensing, hosting, and sustainability

The repository's current code licence is MIT. That permits broad reuse of repository code subject to its notice and disclaimer, but it does not grant rights to third-party data, source services, trademarks, logos, hosted APIs, or future contributions. Code licence and data or service terms must be reviewed separately.

RouteViews describes CC BY 4.0 with additional attribution, link, logo, boilerplate, revocation, and no-warranty conditions for products or derivative works.[4]
For commercial use, the RIPE RIS terms state that the RIPE NCC grants default revocable permission subject to conditions including acceptance of applicable service terms and acknowledgement of RIPE NCC and RIPE RIS as the source; this is conditional permission, not a legal guarantee, and any future use would require a current terms review.[6]
“Licensed code” therefore does not mean “cleared data.” BGPStream's GPL-2.0 code also creates architecture and redistribution questions before embedding it in a closed hosted service.[19][20]

A free self-hosted toolkit could avoid central collection and make provenance inspectable, but users pay in setup, upgrades, source credentials where applicable, storage, and their own incident response. A capped hosted service could simplify setup while limiting retention, source coverage, query volume, or alert history; those limits would be product choices, not evidence of a viable price. A freemium service adds account, abuse, privacy, billing, support, and lock-in costs. An open-core model could separate a permissive local core from hosted conveniences, but the boundary would require an explicit future decision and contributor-rights review. No pricing or funding model is adopted here.

Any live collection would also face source drift, schema changes, quota exhaustion, abuse against lookup endpoints, privacy risk from logs, storage cost, and the burden of explaining stale or conflicting observations. Public routing data can expose visitor or subject network identifiers during access; the future artifact must not retain such identifiers merely because a source page or request made them visible. These are sustainability constraints, not reasons to claim a market.

## Staged validation and stop conditions

1. Build a clickable mockup using only synthetic identifiers. Compare a raw alert, a route timeline, and a route-plus-context explanation. Stop if reviewers cannot distinguish evidence from inference.
2. Conduct 5–8 structured conversations with small operators or security engineers, without accessing research records. Measure recalled investigation time, interpretation errors, desired deployment boundary, and whether the explanation changes a decision. Treat enthusiasm, sign-ups, and stated budgets as signals, not demand proof.
3. Test a local open-source schema and command-line workflow with synthetic events. Record setup time, fixture clarity, requested source adapters, and whether users can reproduce an explanation without a hosted dependency.
4. Before any real source access, complete governance, terms, privacy, retention, and publication review. Do not use this audit to authorize collection or a commercial pipeline.

Stop or pause if fewer than the agreed validation participants can describe a recurring job, if the explanation does not reduce confusion or time, if source terms prevent the intended workflow, if maintenance exceeds the operator capacity, or if privacy and provenance cannot be made legible. Proceed only to the next narrow experiment if the evidence improves on all three dimensions: user job, reproducibility, and safe operating boundary.

The next decision gate is first to choose A, B, or C with the owner using the matrix above and to define the success and stop criteria for that direction. Only after that choice should the corresponding validation experiment be run: A's synthetic explanation mockup and operator conversations, B's governed aggregate research/education prototype, or C's local synthetic schema and CLI workflow. Only after experiment evidence should feature scope, pricing posture, or licence choices be considered. Nothing in this report approves any of those steps.

## Conclusion

Net Watcher has a credible methodological foundation and a plausible narrow operational job, but it has no demonstrated product-market fit. Keep “high demand,” “strongly saturated,” and “unmet niche” out of public claims. The defensible position is: established alternatives cover much of the category; a provenance-first explanation workflow may be useful; and that usefulness must be tested before infrastructure, hosted data, pricing, or product strategy is adopted.

## Sources

[1] https://github.com/nttgin/BGPalerter
[4] https://www.routeviews.org/routeviews/licenses
[5] https://www.routeviews.org/routeviews/faq
[6] https://www.ripe.net/analyse/internet-measurements/routing-information-service-ris/commercial-use
[7] https://stat.ripe.net/docs/data-api/api-endpoints/routing-status
[8] https://www.thousandeyes.com/product/platform
[9] https://www.thousandeyes.com/solutions/bgp-and-route-monitoring
[19] https://github.com/CAIDA/bgpstream/blob/master/LICENSE
[20] https://github.com/CAIDA/bgpstream
[22] https://bgp.he.net
[23] https://bgp.he.net/super-lg
[24] https://stat.ripe.net
[25] https://nlnog.net/tools
[26] https://github.com/NLNOG/irrexplorer
[27] https://bgpstream.caida.org/docs/overview
