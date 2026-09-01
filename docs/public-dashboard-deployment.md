# Public dashboard deployment

## Objective

Publish the reviewed MingYiRx clinical aggregate dashboard at a public HTTPS URL while preserving the repository's clinical-data and evidence boundaries.

## Published surface

- Publish only the reviewed self-contained `clinical_review.html` dashboard.
- Do not publish raw inputs, patient-level derivatives, exact dates, pseudonymization keys, restricted run state, or `run_manifest.json`.
- Preserve the dashboard's minimum-cell suppression and interpretation warnings.
- Treat the website as an exploratory prescribing-pattern tool, not a clinical decision-support system or treatment recommendation.

## Delivery design

- Build a separate static Sites project under ignored `work/` storage so the hosting repository contains only the public artifact and minimal wrapper code.
- Serve the dashboard as a same-origin static asset from the site's root experience.
- Keep the deployment project ID in the Site project's `.openai/hosting.json`; never persist source credentials or tokens.

## Acceptance criteria

1. The source dashboard hash matches the reviewed artifact before packaging.
2. A focused scan finds no direct-identifier fields, common Chinese phone or identity-number patterns, exact ISO dates, email addresses, or local absolute paths.
3. The production build completes successfully and contains only the intended public site files.
4. The deployed access mode is `public` and the production URL loads without authentication.
5. The public page retains the original dashboard interactions and clinical-use limitations.

## Risks and controls

- Aggregate results may still be misinterpreted as individualized prescribing advice; retain prominent explanatory language and do not add recommendation claims.
- Public deployment is an external disclosure. Any future update must repeat the privacy scan and publish only from a validated aggregate artifact.
- The restricted run manifest may contain local paths and remains outside the deployment package.

## Current production deployment

- Public URL: `https://mingyirx-clinical-review.betzoqrcr9gfgp.chatgpt.site`
- Published source dashboard SHA-256: `f15d50123696acb01b8ebf2d2f49b4002d4cfb940874c7786e88c38bc7fe2bc9`
- The public HTML metadata requests `noindex, nofollow`; this reduces accidental search indexing but does not make the URL private.
- Unauthenticated HTTP checks returned status 200 for both the root page and dashboard asset. The hosting edge appends its own Cloudflare challenge script to served HTML, so a downloaded production response is not expected to be byte-identical to the source artifact.
