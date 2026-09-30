# Dashboard 0.14.2 local review

Date: 2026-09-08. Status: LOCAL_REVIEW_READY; not deployed or pushed.

The revision fixes search/trajectory consistency and preserves annual medication
selection across metric changes. An unavailable state keeps annual controls
usable when the selected medication has no public values. CSV loading projects
declared fields only and rejects identifier headers, duplicate/blank headers,
and malformed row widths. This is structural validation, not de-identification.

Validation: 23 Python tests passed, including three Node.js interaction cases;
no tests skipped. Regression failures were reproduced before implementation.
Python compilation, generated JavaScript syntax, and diff whitespace checks
passed. Synthetic CLI validation and execution retained expected warnings.
All 28 original aggregate hashes are unchanged. Every retained dashboard field
matches the prior payload, and repeat HTML builds are byte-identical.

Desktop 1440 px and mobile 390 px browser checks exercised search, clearing and
focus restoration, annual metric switching, and independently scrolling annual
charts. Screenshots were inspected; document widths were 1425 and 375 px,
respectively, with zero console errors observed. This was focused coverage.

The reviewed HTML SHA-256 is
`542998603d723fa6bd0f74f73aa850b722ffcf0f24a94cbbe4b940c252820f96`.
Size decreased from 7,505,504 to 5,535,598 bytes by omitting unused fields.
The real pipeline, scientific estimands, raw sources, and production website
were not modified. Delivery and machine-readable checks are in the continuation
workspace's outputs directory. The original project MEMORY.md was not edited.
