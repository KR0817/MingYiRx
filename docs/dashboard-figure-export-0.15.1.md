# Standalone figure export 0.15.1

Export the current annual chart and strict-cohort primary network as self-contained
SVG documents. Reuse the rendered geometry and canonical annual styles; do not
re-estimate statistics or add dependencies.

Acceptance:
- Each figure includes its item, cohort/stratum, denominator definition, analysis
  and dashboard versions, missingness/interpretation note, and embedded provenance.
- The network retains its independent strict cohort and identifies the displayed
  top-12 subset. Annual charts retain missing-year gaps and the selected metric.
- No-data states disable export, preventing stale or empty figures.
- SVGs require no external CSS, scripts, fonts, images, or dashboard fragment links.
- Long labels and provenance wrap without clipping. Download feedback is local to
  the relevant chart, and filenames identify type/group/item without unsafe characters.
- Test XML validity, escaped labels, metadata, cohort isolation, no-data behavior,
  retained chart geometry, download execution, and independent SVG rendering.
- Preserve earlier deliverables and all source aggregates; publish only a new local
  review artifact. Existing terminology/sequence-analysis boundaries remain in force.
