# PieTree

<div align="center">

**Open-source metadata-aware phylogenetic analyser and renderer**

[![Current Release](https://img.shields.io/badge/Current%20Release-0.0.1-teal.svg)](package.json)
[![Python](https://img.shields.io/badge/Python-3.13.x-blue.svg)](https://python.org)

</div>

****

### Framework Flowchart
```mermaid
flowchart TD

%% =========================================================
%% NODES
%% =========================================================

Newick[External Tree]
NodeList[PieNode List]

PieTree

%% =========================================================
%% FLOW
%% =========================================================

Newick --> PieTree
NodeList --> PieTree

PieTree --> Analysis
PieTree --> Style
Analysis --> Style

Style --> Export
Analysis --> Export

%% =========================================================
%% CLASSES
%% =========================================================

classDef input fill:#fff3b0,stroke:#b58900,color:#000;
classDef output fill:#eeeeee,stroke:#555,color:#000;

%% =========================================================
%% CLASS ASSIGNMENTS
%% =========================================================

class Newick,NodeList input;
class Export output;
```

****
### Abstraction Layers

```mermaid
flowchart TD

%% =========================================================
%% NODES
%% =========================================================

PieObject
Query

%% =========================================================
%% FLOW
%% =========================================================

PieObject --> PieObjectSelection
Query --> PieObjectSelection

PieObjectSelection --> RenderObject
PieStyle --> RenderObject

RenderObject --> Image

%% =========================================================
%% CLASSES
%% =========================================================

classDef input fill:#fff3b0,stroke:#b58900,color:#000;
classDef output fill:#eeeeee,stroke:#555,color:#000;

%% =========================================================
%% CLASS ASSIGNMENTS
%% =========================================================

class Newick,NodeList input;
class Export output;
```
****
### Project Structure

```
pietree/
│
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
│
├── docs/
│   ├── index.md
│   ├── installation.md
│   ├── quickstart.md
│   ├── api/
│   └── examples/
│
├── tests/
│   ├── test_parser.py
│   ├── test_layout.py
│   ├── test_render.py
│   ├── test_annotations.py
│   └── data/
│       ├── small.treefile
│       └── metadata.csv
│
├── examples/
│   ├── basic_tree.py
│   ├── metadata_tree.py
│   ├── taxonomy_tracks.py
│   └── spiders_example.py
│
├── assets/
│   ├── fonts/
│   ├── palettes/
│   └── icons/
│
├── src/
│   └── pietree/
│       ├── __init__.py
│       │
│       ├── core/
│       ├── io/
│       ├── layout/
│       ├── render/
│       ├── annotation/
│       ├── style/
│       ├── utils/
│       └── cli/
│
└── .github/
    └── workflows/
        └── tests.yml
```