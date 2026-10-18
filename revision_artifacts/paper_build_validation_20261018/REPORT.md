# P1–P6 technical validation completed without adopting a manuscript version

Checkpoint `checkpoint/paper-build-validation-20261018` points to `38baa8aa3a9abf64032dd21b677650b345614602`. This supersedes the earlier *uncompiled* technical-copy status. No original manuscript directory, desktop file, scientific result or adopted version was changed.

## Delivered and tested

- `paper_clean_technical.pdf`: **24 pages**; current source and tables unchanged.
- `paper_cumulative_technical.pdf`: **28 pages**; actual latexdiff comparison against the complete original ZIP, blue added prose/red deleted prose.
- `verified_paper_technical_package.zip`: 96 members, source, required image assets, build scripts, generated PDFs and exact original ZIP. Manifest is `DELIVERY_MANIFEST.json`.
- ZIP was extracted to a **new directory**, the two copied manuscript PDFs removed, and both rebuilt successfully. Page counts and every page's extracted text match the initial successful builds. Binary hashes differ because build metadata can change; text equality is verified, not binary reproducibility claimed.

Final logs show **no undefined references/citations, multiply defined references, missing characters or unavailable-font-shape findings** in either fresh build. All 48 clean / 50 marked PDF font resources are embedded. Recorder inventories in `VALIDATION.json` show no absolute dependency on the original project directory: absolute inputs are only the installed TeX Live distribution or the fresh build directory. No installation, font substitution or system permission change occurred.

The package is not a self-contained TeX installation. TeX Live 2025 supplies STIX2-Type1, fontenc, PGF/TikZ, tcolorbox, natbib and other class dependencies. Bundled OTF fonts do not replace those pdfLaTeX resources. `build_verified.py` checks key dependencies and every compiler return code. Full recorder dependency paths are retained for audit, not embedded as source references.

## Original baseline and cumulative comparison

The root original ZIP has 42 files. All restored member hashes match; main TeX SHA256 is `2b8334ed5e03824fef703598d6b57f43089df397ad4c3502d17d96f611baea9f`. The original was compiled successfully to **18 pages** using its own tables, bibliography and figures. Its original 42 members remain byte-identical after compilation; generated auxiliary files are additional.

Original input expansion uses all four original table files and the original compiled bibliography. Current input expansion uses current tables and bibliography. The earlier restored-original-TeX/new-table mixing risk is eliminated. `ORIGINAL_ZIP_MANIFEST.json` and `CURRENT_TEX_UNCHANGED.json` provide checks.

Technical repairs were limited to the independent build:

1. The first source-only copy omitted EPS/logo assets. Copying all existing image assets fixed the clean build; no body text changed.
2. Inline latexdiff across tables with different column counts caused a misplaced-noalign error. Whole table/figure environments are treated as opaque float objects. Current float contents are preserved; old float contents remain in the exact original package. The marked PDF is **not an inline redline of every table cell or changed vector figure**.
3. Building both bibliographies removed invalid markup around bibliography helper macros.
4. Deleted old cross-references/citations pointed at removed labels. Original compilation auxiliary data resolved these to explicit `original` numbers before diffing; `ORIGINAL_REFERENCE_RESOLUTION.json` records every transformation. They do not silently take current numbers. Color-only diff markup avoids requesting unavailable bold monospace shapes.

The unchanged current source has **5 figure environments / 19 table environments / 7 includegraphics calls** (two Notes panels explain extra graphics). Original source has **5 / 13 / 5**. These are source counts, not inferred engineering coverage. P3 Pending table files are copied unchanged. No research material was deleted to make compilation succeed.

## Visual checks and remaining layout limits

All-page contact sheets were rendered and inspected for both final outputs; selected full-resolution pages cover the title, tables, diagrams, Notes panels and references. No clipped body text, missing figure, black glyph blocks or overlapping main content was observed in these inspected views. Contact sheets and PNGs are retained.

The class still emits output-routine overfull-box warnings: clean 23 hbox/1 vbox, marked 27 hbox/1 vbox. They are reported, not relabelled as a clean zero-warning build. The wide-float pages retain substantial whitespace and marked prose changes pagination. This is a technically validated review package, **not a claim of publication-ready typography**. Scientific/version decisions remain untouched.

## P1–P6 closeout

| Item | Disposition |
|---|---|
| P1 public release mismatch | Report-only. No publishing, remote update or release replacement. |
| P2 routing 409/513 and grading 74/70 | Author/version decision remains; no scientific value changed. |
| P3 Pending tables | `table_blind_correct.tex` and `table_stage3.tex` preserved byte-for-byte; not deleted or filled with invented data. |
| P4 stale diff baseline | Complete original ZIP restored; cumulative latexdiff compiled and fresh-extraction rebuild verified, with explicit float-redline limitations above. |
| P5 fonts/dependencies | Required installed STIX2-Type1 and other TeX dependencies documented; clean/diff rebuilt with embedded fonts. No false self-contained claim. |
| P6 original recovery | Exact 42-member ZIP restoration verified, independently compiled to 18 pages; no original/current-table mixing. |

Protection checks: **366 historical + 256 additional file hashes unchanged**, including current manuscript/editable package and existing RAG artifacts. No code/API generation was part of this paper-build validation. Subsequent separately authorized model checks will have their own records.
