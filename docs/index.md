# PieTree Documentation

**PieTree** is a metadata-aware phylogenetic tree analysis and visualization library for Python.

## Overview

PieTree makes it easy to:
- **Build** phylogenetic trees from Newick, NEXUS, or PhyloXML files
- **Annotate** trees with metadata from CSV or JSON files
- **Query** trees using taxonomic or metadata-based searches
- **Visualize** trees with customizable layouts, colors, and styles
- **Export** publication-ready figures in SVG, PNG, or PDF formats

### Key Features

- 🌳 **Flexible Tree Building** - Construct trees programmatically or parse from standard formats
- 📊 **Metadata-First** - Attach arbitrary metadata to any node
- 🔍 **Powerful Querying** - Find clades, filter by metadata, compute distances
- 🎨 **Rich Styling** - CSS-like style rules, highlighting, panels
- 📈 **Multiple Layouts** - Phylogram, cladogram, ultrametric views
- 🖼️ **Publication Quality** - SVG vector graphics or high-res raster formats
- 💻 **CLI Tools** - Command-line interface for common workflows

---

## Installation

### From PyPI (when published)

```bash
pip install pietree
```

### From Source

```bash
git clone https://github.com/pedrocortes/pietree.git
cd pietree
pip install -e .
```

### Requirements

- Python 3.9+
- numpy, pandas, svgwrite, biopython, cairosvg

---

## Quick Start

### Python API

```python
from pietree import parse_newick
import pandas as pd

# Load tree
tree = parse_newick("examples/data/example.newick")

# Annotate with metadata
metadata = pd.read_csv("examples/data/metadata.csv")
tree.annotate(metadata, on="name")

# Query and select
brazil_tips = tree.nodes(country="Brazil")

# Visualize
tree.to_svg(path="tree.svg", mode="phylogram")
```

### Command Line

```bash
# Validate tree
pietree validate tree.newick

# Render to SVG
pietree render tree.newick -o tree.svg -m cladogram

# Query tips
pietree query tree.newick "tips" -o json

# Annotate with metadata
pietree annotate tree.newick metadata.csv -o annotated.newick
```

---

## Documentation Structure

### User Guide

Learn how to use PieTree:

- [Tree Construction](user_guide/tree_construction.md) - Building and loading trees
- [Metadata](user_guide/metadata.md) - Annotating and querying metadata
- [Querying](user_guide/querying.md) - Finding and selecting nodes
- [Styling](user_guide/styling.md) - Customizing appearance
- [Rendering](user_guide/rendering.md) - Layouts, highlights, and panels
- [Export](user_guide/export.md) - Saving figures and data
- [CLI](user_guide/cli.md) - Command-line tools

### API Reference

Detailed API documentation:

- [Tree Classes](api_reference/tree.md) - PieTree, PieNode, PieBranch
- [Metadata](api_reference/metadata.md) - PieMeta, MetadataView, inference
- [Query](api_reference/query.md) - Selection API
- [Style](api_reference/style.md) - Styling system
- [Render](api_reference/render.md) - Rendering pipeline
- [I/O](api_reference/io.md) - Parsing and serialization

### Developer Guide

For contributors and extenders:

- [Architecture](developer_guide/architecture.md) - Design overview
- [Extending PieTree](developer_guide/extending.md) - Custom parsers, renderers
- [Contributing](developer_guide/contributing.md) - Development guidelines

### Examples

Practical examples:

- [Basic Tree](examples/basic_tree.md) - Simple visualization
- [Metadata Annotation](examples/metadata_annotation.md) - Working with data
- [Clade Highlighting](examples/clade_highlighting.md) - Visual emphasis
- [Advanced Styling](examples/advanced_styling.md) - Complex styling

---

## Getting Help

- **Documentation:** You're reading it!
- **Issues:** [GitHub Issues](https://github.com/pedrocortes/pietree/issues)
- **Discussions:** [GitHub Discussions](https://github.com/pedrocortes/pietree/discussions)

---

## License

PieTree is released under the MIT License. See [LICENSE](../LICENSE) for details.

---

## Citation

If you use PieTree in your research, please cite:

```bibtex
@software{pietree,
  author = {Pedro Côrtes},
  title = {PieTree: Metadata-aware phylogenetic tree visualization},
  year = {2024},
  url = {https://github.com/pedrocortes/pietree}
}
```

---

## Next Steps

- Read the [Tree Construction Guide](user_guide/tree_construction.md)
- Explore [examples](examples/)
- Check the [API Reference](api_reference/tree.md)
