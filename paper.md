---
title: 'PieTree: metadata-first phylogenetic tree analysis and visualization in Python'
tags:
  - Python
  - phylogenetics
  - bioinformatics
  - data visualization
  - tree metadata
authors:
  - name: Pedro Côrtes-Barros
    affiliation: 1
affiliations:
  - name: "Genomics and Bioinformatics Laboratory, Leopoldo de Meis Institute of Medical Biochemistry, Federal University of Rio de Janeiro, Rio de Janeiro, Brazil"
    index: 1
date: 30 July 2026
bibliography: paper.bib
---

# Summary

`PieTree` is a Python package for annotating, querying, and rendering phylogenetic
trees around metadata rather than topology alone. Instead of treating a tree as a
bare graph of tip and internal nodes, `PieTree` attaches arbitrary per-node
metadata (taxonomy, sampling group, geographic origin, sequence quality, etc.)
as a first-class part of the tree object, and exposes this metadata through a
fluent, chainable API for selection, styling, and figure generation. A single
call such as `tree.metadata("taxonomy").highlight()` infers which clades
correspond to each taxonomic group via longest-common-prefix reasoning over tip
metadata, assigns colors, and renders shaded, labeled highlight regions —
replacing what is normally a multi-step sequence of tree traversal, most-recent-
common-ancestor computation, coordinate lookup, and manual drawing calls in
other tools. `PieTree` produces publication-ready SVG figures through a layered
rendering pipeline (background, highlights, branches, nodes, labels, metadata
panels, and scale bar), supports phylogram, cladogram, and ultrametric layouts
in both horizontal and vertical orientations, and includes a CSS-like style
engine for declarative, selector-based formatting of nodes, branches, and
labels.

# Statement of need

Phylogenetic visualization is a routine step in comparative biology, ecology,
epidemiology, and systematics, and most published trees are annotated with
external data — taxonomic classification, geographic origin, host species,
experimental group, or collection metadata — that is conceptually as important
as the tree topology itself. Existing Python tools for tree manipulation and
plotting (e.g. `ete3`, `biopython.Phylo`, `toytree`) generally treat metadata
as an add-on: the researcher must manually traverse the tree, identify tips
belonging to a group, compute the relevant clade or most recent common
ancestor, and only then call low-level drawing primitives to shade or label
that region. This means that expressing a single biological statement (e.g.
"highlight all Mammalia" or "label this clade by its sampling group") typically
requires many lines of imperative, coordinate-aware code, and repeating this
process across several metadata fields multiplies the effort further.

`PieTree` is designed to close this gap by making metadata a queryable,
inferable, and directly renderable part of the tree object. The package's
`MetadataView` API exposes per-field operations — highlighting, node labeling,
and side-panel rendering — that automatically resolve which internal nodes and
clades correspond to a given metadata value, without requiring the user to
compute ancestors or coordinates manually. A companion selection API
(`tree.nodes(...)`, `tree.tips`, `tree.tip_labels(...)`) supports the same
declarative, chainable style for renaming, restyling, and re-highlighting
based on metadata predicates. This lets researchers express figure intent in
terms they already use when discussing their data — clades, taxa, groups,
fields — rather than in terms of graph traversal and pixel coordinates,
lowering the barrier to producing clear, richly annotated, publication-quality
tree figures directly from a metadata table and a tree file.

# Overview of functionality

- **Tree construction and metadata attachment.** Trees can be parsed (e.g. from
  Newick) or built programmatically, and annotated in bulk from a `pandas`
  DataFrame joined on any node-level key (`tree.annotate(samples, on="mitogenome_id")`).
- **Hierarchical metadata inference.** For metadata stored as ordered taxonomic
  paths, `PieTree` infers the value for internal nodes via longest-common-prefix
  over descendant tips, without mutating the underlying tree, enabling
  automatic clade detection at any taxonomic depth.
- **Fluent querying and styling.** Node, tip-label, and branch selections
  support chained operations (`.style()`, `.rename()`, `.suffix()`,
  `.prefix()`, `.highlight()`), and a CSS-like selector/rule/resolver system
  allows declarative styling rules to be applied across the whole stylesheet.
- **Layered SVG rendering.** A `RenderContext`-driven pipeline composites
  background, highlights, branches, nodes, labels (tip, internal, support,
  branch, and metadata-derived), metadata panels, and an automatically scaled
  branch-length scale bar, with smart label placement that scores candidate
  positions against nearby branch segments and already-placed labels to reduce
  overlap.
- **Layout flexibility.** Phylogram (branch-length proportional), cladogram
  (equal branch length), and ultrametric (tip-aligned) layouts are supported in
  both horizontal and vertical orientations.
- **Command-line interface.** A `pietree` CLI exposes validation, rendering,
  querying, annotation, and format conversion for use in scripted pipelines.

# Example

```python
import pandas as pd
from pietree import parse_newick

tree = parse_newick("data/spiders.newick")
samples = pd.read_csv("data/spider_samples.csv", sep=";")
tree.annotate(samples, on="mitogenome_id")

tree.nodes(group="this_study").style(fill="red", radius=5)
tree.tip_labels(group="this_study").suffix(" *").style(font_weight="bold")

tree.metadata("taxonomy").highlight(depth=1, palette="tab10")
tree.metadata("group").panel(values=["Outgroup"])

tree.savefig("spiders_tree.svg")
```

This produces a phylogram with clades shaded and labeled by taxonomic group,
study samples marked and styled, and an outgroup metadata panel — all without
manual clade or coordinate computation.

# Acknowledgements

We thank early users who tested `PieTree` on real phylogenetic datasets and
provided feedback on the API design.

# References
