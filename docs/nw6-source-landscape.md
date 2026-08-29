# Source Landscape — Stage 1 decision brief

**Boundary.** This is documentation-only discovery. I read public documentation, schemas/descriptions, and access/terms pages only; I did not inspect records, samples, live endpoints, feeds, archives, downloads, or query results. The supplied context names an aggregate question but does not include its exact wording, unit of analysis, time window, geography, or required output. Therefore “fit” below is only schema-level fit to the apparent question class: relating publicly visible registration changes to independently observed routing changes. Exact estimand fit is unknown.[unverified]

## A. Public registration-event documentation/data services

| Source class / named family | Documented scope and schema-level fit | Terms, access, limitations | Future access posture |
|---|---|---|---|
| **RIR statistics snapshots — NRO joint extended allocation/assignment; per-RIR delegated files** | Daily `delegated-extended` reporting is documented as distribution of IPv4 ranges, IPv6 ranges, and ASNs.[1] The exchange format documents allocation/assignment date, resource type/value/count, status (`allocated`/`assigned`), and registry-produced scope.[2] This can support coarse cohort/state aggregates, not a change-event log. | The format is explicitly a snapshot “without any transactional or historical details.”[2] Dates may represent the original date after transfer and may be `00000000` when unavailable.[2] Public statistics are the least access-friction option, but they cannot by themselves establish when a record changed. | **Consider only** as a low-risk denominator/context source if the question needs registry allocation state; not sufficient as the primary event source without explicit approval for snapshot retrieval and differencing. |
| **RIPE Database historical objects — RIPE Database history / RIPEstat Historical Whois** | RIPE documents that every object update saves the old version; history flags expose prior versions, while personal historical data is unavailable.[3] RIPEstat documents versioned objects, numerical or time-based version selection, `num_versions`, version list, object details, and referencing/referenced objects; its documented database support is currently RIPE DB only.[4] Strong schema-level fit for object-version/change timing and relationships within the RIPE service region. | Use is governed by RIPE Database terms and conditions surfaced in the documented output schema.[4] Coverage is RIPE DB, not a global RIR history; personal historical data is unavailable.[3] A version is an object-state history, not necessarily a validated business “registration event.” | **Consider first** for a narrowly scoped, non-personal RIPE-region event study, subject to a later authorization that specifies identifiers, time window, query protocol, retention, and review. |
| **ARIN WhoWas — historical NET/ASN/ORG/POC reports** | ARIN documents a requested IP/ASN history delivered as ZIP/TSV, with summary associations and per-object histories. Each object has `Action` (`CREATED`, `MODIFIED`, `REGISTRATION REMOVED`) and `Action Date`; fields include network ranges, handles, parent/type, organization, registration date, and POC references.[5] This is the clearest documented event-like schema for ARIN NET/ASN history. | Publication is subject to an approved request and the WhoWas Terms of Use.[5][16] The WhoWas terms state that ARIN reviews each application case by case and may approve access for specified research, operational, or related network-service purposes; they separately prohibit uses such as advertising, direct marketing, and republishing or reselling the data.[16] The generic ARIN Whois Terms of Use governs use of the Whois Service, including compilation, repackaging, dissemination, and other use of ARIN Whois data, and lists Internet operational or technical research purposes; it is incorporated into the WhoWas terms but is not the source of the WhoWas-specific access condition.[7][16] Bulk Whois is a separate service: ARIN describes access to a bulk copy for organizations using it for Internet operational or technical research purposes.[6] Reports are public-history fields but can contain organizational/contact relationships; ARIN recycling and object constraints complicate longitudinal identity interpretation.[5] | **Consider** for a minimal ARIN-only validation slice if the question requires explicit create/modify/remove actions; approval, account/request, permitted-use interpretation, and handling of contact data remain unresolved. |
| **APNIC Whowas — historical registration states** | APNIC documents prior states of IP and AS registration records back to 2008, plus history for domain and entity records (person, role, IRT); it is implemented as an RDAP extension with an API and experimental UI.[10] This is plausible for historical state/event reconstruction in the APNIC service region. | APNIC states the API follows a draft specification likely to change incompatibly and warns against relying on its current state for operational outcomes.[10] Bulk Whois access requires a signed Acceptable Use Policy; bulk reproduction/storage/transmission and onward bulk sharing require permission, and full-database access is restricted to approved Internet operational purposes.[8][9] | **Consider only** for a small, version-pinned APNIC feasibility test after explicit authorization; do not assume API stability or cross-RIR comparability. |

**A assessment.** For an event-sensitive aggregate, RIPE historical objects and ARIN WhoWas have the strongest documented action/version schemas.[3][5]
APNIC Whowas is promising but explicitly experimental.[10]
NRO/RIR statistics are useful as snapshots/denominators, not event evidence.[1][2]
No source documentation establishes globally complete, harmonized registration events across all five RIRs.[unverified]

## B. Independent routing-observation documentation/data services

| Source class / named family | Documented scope and schema-level fit | Terms, access, limitations | Future access posture |
|---|---|---|---|
| **RIPE RIS — MRT archive and RIS Live** | RIS documents route collectors receiving BGP data from peering volunteers and storing update/withdraw messages.[13] MRT documentation distinguishes periodic routing-state dumps (`bview`) from interval change files (`update`), with per-collector files; documented cadence is dumps every 8 hours and updates every 5 minutes.[11] This supports independently observed prefix visibility/origin/path change aggregates. | Collector perspective is non-exhaustive: collectors and peers are geographically/operationally distributed, with different IXP or multihop scopes.[12] MRT files encode observations, not ground truth, and the documentation does not guarantee complete global visibility or event-cause attribution.[11][12] RIS documentation links legal information, but precise reuse/publication terms for a proposed study remain unresolved from this landscape pass.[13] | **Consider** one or more documented RRC scopes plus a fixed interval only after authorization for protocol, data minimization, retention, and review. Prefer a derived observation metric over raw archive retention. |
| **RouteViews — collaborative collector archive / looking glass** | RouteViews documents current RIB/update access, a continuously growing archive, and a multi-perspective archive from collectors peering with ISPs, IXPs, academic/backbone networks, and hyperscalers.[14] Schema-level fit is BGP RIB/update observation and longitudinal prefix/AS-path visibility. | RouteViews says data are generally licensed CC BY 4.0 for operations/research with attribution; research publications should cite its DOI. Commercial use has additional terms.[14] Its many-peer, collector-based perspective still does not equal complete global routing; peer population, collector changes, and archive/API details for the selected interval are unknown. | **Consider** as an independent corroborating family, ideally paired with RIS rather than treated as ground truth; attribution and any commercial/publication interpretation need review. |
| **CAIDA BGPStream — analysis/access layer over RouteViews and RIS** | BGPStream documents Python access to BGP records/elements, filters by time, collector, record type, and prefix/peer, and supports `routeviews-stream` and `ris-live`; examples expose timestamps, collector/project, peer, prefix, AS path, and update/RIB distinctions.[15] This is a useful documented schema/access abstraction for reproducible derived routing observations. | BGPStream is a processing framework, not an independent measurement network; its results inherit provider coverage, retention, and licensing. The tutorial documents caching of downloaded MRT files, which would require explicit authorization here.[15] The selected version, broker/provider availability, raw-data retention, and output license obligations are unknown. | **Consider only** as implementation/access tooling after a source and protocol authorization; it does not replace approval for RIS or RouteViews data access. |

**B assessment.** RIS and RouteViews are the plausible independent observation families; BGPStream is a common access/normalization layer, not a third independent observer.[11][14][15]
Updates are closer to event observations; RIBs are state checkpoints.[11][15]
None documents causal attribution from a routing observation to a registry action.[unverified]

## Trade-offs and decision

- **Best event semantics:** ARIN WhoWas (explicit action/action date) and RIPE historical versions (version/time selection), but each is region/service-specific and access-controlled to different degrees.[3][5]
- **Best low-friction context:** NRO/RIR statistics, but snapshot-only and explicitly non-transactional.[1][2]
- **Best independent routing coverage:** a RIS + RouteViews pairing, because both are collector networks with distinct operational provenance; coverage remains viewpoint-dependent.[11][12][14]
- **Best reproducibility layer:** BGPStream’s documented filters and record/element fields, but it inherits provider terms and can cache raw MRT files.[15]
- **Main comparability risk:** registration object versions/actions and BGP observations have different clocks, identities, completeness, and semantics.[3][11][15] A temporal association would be an analysis decision, not a fact supplied by either documentation set.[unverified]

## Recommended minimal next authorization scope (not approved)

1. Confirm the exact aggregate question, target region(s)/RIR(s), resource identifier class (prefix/ASN/object), time window, aggregation unit, and whether personal/contact fields are categorically excluded.
2. Authorize **one registration family** first: either RIPE historical objects for RIPE-only scope or ARIN WhoWas for ARIN-only scope; do not authorize a global merge.
3. Authorize **one routing family** first (RIS *or* RouteViews), with a fixed collector/peer scope and explicit choice of updates versus RIB checkpoints. Add the second family only for corroboration.
4. Separately authorize the exact access protocol, request rate, permitted fields, raw/derived retention, deletion, local output location, and human review gate. BGPStream may be considered as tooling only after those permissions.
5. Require a pre-analysis schema/coverage review and a written licensing/privacy determination before any result leaves the workspace.

## Unknowns and explicit non-authorization

Unknown: the exact aggregate question and estimand; required population/denominator; target RIRs/regions; identifier normalization; time-window and clock rules; acceptable missingness; whether event dates mean object actions, allocation dates, or inferred diffs; collector/peer coverage needed; source version/cutoff; rate limits; authentication/account requirements; RIS legal/reuse terms for this purpose; RouteViews commercial/publication interpretation; APNIC draft API stability; cross-RIR field equivalence; retention/deletion; privacy treatment; and review/publication criteria.

**Protocol, output generation, review, publication, correlation, record retrieval, endpoint/API querying, downloading, streaming, archiving, retaining, and processing remain unauthorized.** This brief recommends possible future scope only; it grants no access approval and reports no records or computed findings.

## Sources

[1] https://www.nro.net/about/rirs/statistics
[2] https://www.apnic.net/about-apnic/corporate-documents/documents/resource-guidelines/rir-statistics-exchange-format
[3] https://docs.db.ripe.net/Updating-Objects-in-the-RIPE-Database/Historical-Data
[4] https://stat.ripe.net/docs/data-api/api-endpoints/historical-whois
[5] https://www.arin.net/reference/research/whowas/readme
[6] https://www.arin.net/reference/research/bulkwhois
[7] https://www.arin.net/resources/registry/whois/tou
[8] https://www.apnic.net/manage-ip/using-whois/bulk-access
[9] https://www.apnic.net/manage-ip/using-whois/bulk-access/copyright
[10] https://www.apnic.net/about-apnic/whois_search/whowas
[11] https://ris.ripe.net/docs/mrt
[12] https://ris.ripe.net/docs/route-collectors
[13] https://www.ripe.net/analyse/internet-measurements/routing-information-service-ris
[14] https://www.routeviews.org
[15] https://bgpstream.caida.org/docs/tutorials/pybgpstream
[16] https://www.arin.net/reference/research/whowas/tou — WhoWas Terms of Use - American Registry for Internet Numbers
