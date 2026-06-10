# Command-Line Interface

PieTree provides a comprehensive CLI for common phylogenetic workflows.

## Available Commands

- `pietree render` - Render trees to images
- `pietree query` - Query nodes and clades
- `pietree annotate` - Add metadata to trees
- `pietree convert` - Convert file formats
- `pietree validate` - Validate tree files
- `pietree info` - Show tree statistics

## Common Options

All commands support:
- `-f, --format` - Input format (auto-detected by default)
- `--help` - Show command help

## pietree render

Render phylogenetic trees to images.

```bash
pietree render TREE_FILE -o OUTPUT [OPTIONS]
```

### Options

- `-o, --output PATH` - Output file (format from extension)
- `-m, --mode STR` - Layout: phylogram|cladogram|ultrametric
- `--orientation STR` - horizontal|vertical
- `--metadata PATH` - CSV/JSON metadata file
- `--no-labels` - Hide tip labels
- `--no-scale` - Hide scale bar

### Examples

```bash
# Basic SVG
pietree render tree.newick -o tree.svg

# Cladogram as PNG
pietree render tree.newick -m cladogram -o tree.png

# With metadata
pietree render tree.newick --metadata data.csv -o annotated.svg
```

## pietree query

Query nodes and clades.

```bash
pietree query TREE_FILE EXPRESSION [OPTIONS]
```

### Expressions

- `tips` - List all tips
- `internal` - List internal nodes
- `count` - Count nodes
- `clade:TAXON` - Find taxonomic clade
- `metadata:FIELD=VALUE` - Find by metadata

### Options

- `-o, --output` - Output format: text|json|csv
- `--metadata PATH` - Annotate before querying

### Examples

```bash
# List tips as JSON
pietree query tree.newick "tips" -o json

# Find clade
pietree query tree.newick "clade:Mammalia"

# Count nodes
pietree query tree.newick "count"
```

## pietree annotate

Add metadata to trees.

```bash
pietree annotate TREE_FILE METADATA_FILE -o OUTPUT
```

### Options

- `--on FIELD` - Join field (default: name)

### Example

```bash
pietree annotate tree.newick samples.csv -o annotated.newick
```

## pietree validate

Check tree validity.

```bash
pietree validate TREE_FILE [OPTIONS]
```

### Options

- `--strict` - Warnings as errors
- `--check-bifurcating` - Check bifurcation
- `--check-ultrametric` - Check ultrametricity

### Example

```bash
pietree validate tree.newick --strict
```

## pietree convert

Convert between formats.

```bash
pietree convert INPUT OUTPUT
```

### Example

```bash
pietree convert tree.nex tree.newick
```

## pietree info

Show tree statistics.

```bash
pietree info TREE_FILE
```
