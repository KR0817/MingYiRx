# Frequency ordering and network presentation 0.15.3

Acceptance: all three medication selectors use descending all-visit usage, with
Chinese-name ties and undisclosed values last. Usage means one normalized item per
eligible visit, across the clinical analysis population (strict population fallback
when clinical mode is disabled). It is not a source-line count or patient count.
Require at least min_public_n distinct patients for disclosure. Do not sum overlapping
strata, annual first visits, or addition/removal counts. Retain selected items when
changing contexts. Non-medication selectors keep semantic ordering.

Add an optional public item_usage_totals.csv projection; old dashboards without it
show an explicit unavailable count, never an invented zero. Preserve source inputs
and existing aggregate files. Record configuration, dictionary, input and output
hashes. No statistical analysis or threshold changes.

Visual plan: a centered neighborhood with six evenly spaced associates per side,
curved edges encoding cosine by width, and readable count annotations. Palette:
ink #183c43, pine #28695f, slate #577986, mist #edf4f3, line #d4e3e0,
white #ffffff. Local Microsoft YaHei UI text, Georgia center display, tabular data.
Keep the surrounding dashboard design. No simulated force layout, inferred links,
or causal encoding. Top 12 cosine edges and full numeric table stay unchanged.
Use inline SVG styling for faithful export, visible keyboard focus and mobile
internal scrolling to preserve label readability.

Verify synthetic count/dedup/suppression tests, sorting and selection interaction
tests, existing suite, real aggregate preservation, SVG export, desktop/mobile
screenshots, empty state, and no script errors.
