# Publication policy

Local verification proves only that the current checkout meets repository checks. Publication eligibility additionally requires an approved provider in `publication.json`, exact-artifact independent review, and a successful `make publish-check` without overrides.

The provider is currently unset, so the gate fails closed. GitHub Issues is the exact correction endpoint.

Eligibility still does not authorize release. Hosting, DNS, TLS, and publication are separate human decisions. The final origin must be checked for exact bytes, security headers, and a reachable correction link.

No credential, host inventory, provider procedure, private review material, or restricted record belongs in this repository. Approval evidence must remain in its authorized system rather than public task cards.
