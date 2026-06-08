# PieTree
<div align="center">

[![Current Release](https://img.shields.io/badge/Current%20Release-0.0.1-teal.svg)](package.json) 
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)

</div>

**Fluent, metadata-aware phylogenetic analysis and visualization for Python.**

> _"Work with trees the way you think about them."_

![Spider phylogeny rendered with PieTree](examples/spiders_tree.svg)

---

PieTree is a Python library for constructing, annotating, querying, and rendering phylogenetic trees. It is built around a single idea: **metadata and topology are equally important**, and the API should reflect that.

Instead of traversing node lists and computing clades manually, you express intent:

```python
tree.metadata("taxonomy").highlight(depth=1, palette="tab10")
tree.nodes(group="this_study").style(fill="red", radius=7)
tree.tip_labels(group="this_study").suffix(" *").style(font_weight="bold")
```

---

## Installation

```bash
pip install pietree
```

---

## Quick Example

```python
import pandas as pd
from pietree import PieTree

samples = pd.read_csv("data/spider_samples.csv", sep=";")
tree = PieTree.from_newick(path="data/spiders.newick")

tree.annotate(samples, on="mitogenome_id")
tree.tips.rename("{species} {mitogenome_id}")

tree.nodes(group="this_study").style(fill="red", radius=5)
tree.tip_labels(group="this_study").suffix(" *").style(font_weight="bold")

tree.metadata("taxonomy").highlight(depth=9, label_position="center_right", palette="tab10")
tree.metadata("taxonomy").label_nodes(show_duplicates=False)

tree.metadata("group").highlight(
    values=["this_study"],
    label="This study",
    colors={"this_study": "#7e7e7e"},
    label_position="center_right",
)
tree.metadata("group").panel(values=["Outgroup"])

tree.to_svg("spiders_tree.svg")
```

---

## Why PieTree?

Most phylogenetic libraries focus on either tree manipulation *or* tree rendering. PieTree focuses on the **connection between the two** — and on how metadata bridges them.

The typical workflow elsewhere looks like this: parse the tree, traverse nodes manually, extract tips for a clade of interest, compute the MRCA, pass coordinates to a plotting library, manually style elements. That's a lot of steps before anything biological is expressed.

In PieTree, the same workflow is:

```python
tree.clade_by_taxon("Mammalia").highlight(fill="lightblue")
```

The clade is inferred from hierarchical metadata via longest-common-prefix, styled, and registered for rendering — in one call.

---

## Core Concepts

### The Rendering Pipeline

```mermaid
flowchart LR
    A[PieTree] -->|to_render_spec| B[RenderSpec]
    B -->|build_layout| C[Coordinates]
    C --> D[RenderContext]

    D --> L1[Background]
    D --> L2[Highlights]
    D --> L3[Branches]
    D --> L4[Nodes]
    D --> L5[Labels]
    D --> L6[Panels]
    D --> L7[Scale bar]

    L1 & L2 & L3 & L4 & L5 & L6 & L7 --> SVG[SVG]
```

Layers are composited in order. Highlights render before branches and nodes so they sit underneath the tree. Each layer reads from `RenderContext` — a single source of truth for positions, options, registry state, and registered highlights.

---

## Key Features

### Metadata-First Annotation

Annotate from a DataFrame by any join key — not just node names:

```python
tree.annotate(samples, on="mitogenome_id")
```

Metadata is stored on each node as a `PieMeta` mapping and is available throughout the query and render pipeline.

### Hierarchical Inference

When metadata is stored as lists representing taxonomic paths (e.g. `["Animalia", "Arthropoda", "Insecta"]`), PieTree can infer the value for any internal node via **longest-common-prefix** across its descendant tips — without modifying the tree.

```python
tree.metadata("taxonomy").infer()  # → {node_id: [inferred, path], ...}
```

This inference drives both `.highlight()` and `.label_nodes()` automatically.

### Fluent Querying

```python
tree.nodes(group="this_study")           # NodeSelection
tree.tips                                # NodeSelection (all tips)
tree.tip_labels(country="Brazil")        # LabelSelection
tree.branches()                          # BranchSelection
```

Selections support chained styling, renaming, suffixing, and highlighting.

### Clade Highlights

Highlight clades manually or automatically from metadata:

```python
# Manual
tree.clade(["Tip_A", "Tip_B"]).highlight(fill="#4e79a7", label="Clade I")

# From metadata — one highlight per distinct taxon at depth 1
tree.metadata("taxonomy").highlight(depth=1, palette="set2")
```

### Metadata Panels

Side panels display categorical metadata as grouped bars alongside the tree, automatically positioned after tip labels:

```python
tree.metadata("group").panel(values=["Outgroup"])
```

### Layout Modes

```python
tree.to_svg("out.svg", mode="phylogram")    # branch-length proportional
tree.to_svg("out.svg", mode="cladogram")    # equal branch lengths
tree.to_svg("out.svg", mode="ultrametric")  # tips aligned to present
```

---

## Philosophy

PieTree is built on three principles.

**Biological semantics.** The API should reflect how biologists think about trees — in terms of clades, taxa, metadata fields, and study groups — not graph traversals and coordinate systems. `tree.clade_by_taxon("Insecta")` is a biological statement; it should work directly.

**Metadata as topology.** In most analyses, what matters is not just the shape of the tree but what the tips *represent*. PieTree treats metadata as a first-class component of the tree object, queryable, inferred, and renderable with the same fluency as topology.

**Fluent, composable operations.** Every operation returns something you can act on further. Selections can be styled, labeled, highlighted. Views can be highlighted, paneled, or iterated. The pipeline from data to publication figure should read like a description of the figure itself.

---

## Roadmap

**Current**
- Newick I/O (read and write)
- Hierarchical metadata inference (longest-common-prefix)
- Automatic clade highlighting from metadata
- Metadata side panels
- Fluent node / branch / label selections
- Phylogram, cladogram, and ultrametric layouts
- Horizontal and vertical orientations
- SVG rendering with layered pipeline
- Scale bar
- Style engine with per-node overrides

**Planned**
- Interactive HTML export
- CLI interface
- Comparative / tanglegram layouts
- Additional annotation geometry (arrows, brackets, icons)
- Analysis modules (diversity, patristic distances, ancestral state)

---

## Contributing

Contributions, bug reports, and feature requests are welcome. If you have ideas for new phylogenetic analyses, visualization styles, or metadata workflows, open an issue or pull request.

---

## License

MIT License.