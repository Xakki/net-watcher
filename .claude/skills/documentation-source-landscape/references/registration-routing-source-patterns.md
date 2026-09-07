# Registration and routing source patterns

Condensed reusable notes from a documentation-only landscape review.

## Registration families

- **RIR statistics:** daily delegated allocation/assignment snapshots expose resource ranges, ASNs, dates, and status, but the exchange format is explicitly non-transactional and lacks historical detail.
- **RIPE historical objects / RIPEstat Historical Whois:** prior object versions, numerical or time-based selection, version counts, object details, and references; historical personal data is unavailable and RIPE DB is the documented database scope.
- **ARIN WhoWas:** requested IP/ASN history in TSV reports with explicit `CREATED`, `MODIFIED`, and `REGISTRATION REMOVED` actions plus action dates and NET/ASN/ORG/POC fields; access requires an approved request and terms acceptance.
- **APNIC Whowas:** historical IP/AS states back to 2008 plus domain/entity history through an RDAP extension; the API is documented as draft/experimental and bulk access is policy-controlled.

## Routing families

- **RIPE RIS:** route collectors receive BGP peer data; MRT `bview` files represent routing state and `update` files represent changes over intervals. Collector and peer scope is viewpoint-dependent.
- **RouteViews:** collaborative collectors provide current RIB/update access and a long-running archive; documented reuse is generally CC BY 4.0 with attribution, with additional commercial terms.
- **CAIDA BGPStream:** a parser/access layer over providers such as RIS and RouteViews, with documented time, collector, record-type, prefix, and peer filters. It is not an independent observer and raw-file caching requires separate authorization.

## Decision rule

For an event-sensitive study, prefer a documented version/action source over a
snapshot. Pair at most one narrowly scoped registration family with one routing
family first. Treat every routing observation as evidence of visibility from a
collector perspective, not proof of global reachability or causal linkage to a
registry action. Keep protocol, raw retention, correlation, review, and
publication behind explicit later authorization.
