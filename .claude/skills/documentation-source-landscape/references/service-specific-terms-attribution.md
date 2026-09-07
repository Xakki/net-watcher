# Service-Specific Terms Attribution

Use this review pattern when adjacent provider services have different access
conditions (for example, bulk data versus historical lookup):

1. Identify the exact service named by the claim.
2. Fetch the first-party service documentation and the direct service-specific
   Terms of Use page; do not rely on a generic policy page for a narrower claim.
3. Split conflated prose into separate claims and cite each claim to its exact
   source. Keep a generic policy citation only for the service scope it
   explicitly governs.
4. Register the new URL in the grounded-citations ledger, render the Sources
   block mechanically, and run `verify --strict`.
5. If strict verification reports over-cited sentences, put separately cited
   sentences on separate physical Markdown lines; the verifier's sentence
   splitter operates per line and citations immediately after punctuation can
   prevent expected splitting.

This preserves the distinction between documentation discovery and any later
access authorization; it does not authorize records, endpoints, downloads, or
queries.
