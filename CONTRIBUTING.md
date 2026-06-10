# Contributing to PieTree

Thank you for your interest in contributing to PieTree! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Project Structure](#project-structure)

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- pip or poetry for package management

### Quick Start

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/yourusername/pietree.git
   cd pietree
   ```

2. **Install in development mode:**
   ```bash
   pip install -e .
   pip install pytest pytest-cov  # For testing
   ```

3. **Run tests to verify setup:**
   ```bash
   pytest
   ```

---

## Development Setup

### Installing Dependencies

PieTree uses standard Python packaging. Install in editable mode for development:

```bash
# Install package with dependencies
pip install -e .

# Install development dependencies
pip install pytest pytest-cov ruff mypy
```

### Project Dependencies

Core dependencies (see `pyproject.toml`):
- `numpy` - Numerical operations
- `pandas` - Metadata handling
- `svgwrite` - SVG generation
- `biopython` - Tree parsing (Newick, NEXUS)
- `cairosvg` - Rasterization (PNG, PDF, JPEG)

---

## Development Workflow

### 1. Create a Branch

Create a feature branch for your changes:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `test/` - Test additions/improvements
- `refactor/` - Code refactoring

### 2. Make Changes

- Write clear, focused commits
- Follow the code standards (see below)
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

Run the full test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pietree --cov-report=html

# Run specific test file
pytest tests/test_pienode.py -v
```

### 4. Commit Your Changes

Write clear commit messages:

```bash
git add .
git commit -m "Add feature: description of what changed"
```

Good commit message format:
```
Short summary (50 chars or less)

More detailed explanation if needed. Wrap at 72 characters.
Explain what changed and why, not how.

- Bullet points are okay
- Use present tense ("Add feature" not "Added feature")
```

---

## Code Standards

### Python Style

PieTree follows PEP 8 with some project-specific conventions:

- **Line length:** 100 characters (not the PEP 8 default of 79)
- **Indentation:** 4 spaces (no tabs)
- **Imports:** Grouped (stdlib, third-party, local) with blank lines between
- **Docstrings:** NumPy style for all public APIs

### Code Quality Tools

We use these tools to maintain code quality:

```bash
# Format code with ruff
ruff format .

# Lint code
ruff check .

# Type checking
mypy src/pietree
```

### Docstring Style

Use NumPy-style docstrings for all public functions and classes:

```python
def example_function(param1: str, param2: int = 0) -> bool:
    """
    Short one-line description.

    Longer description if needed. Can span multiple lines and provide
    more context about what the function does.

    Parameters
    ----------
    param1 : str
        Description of param1
    param2 : int, optional
        Description of param2, by default 0

    Returns
    -------
    bool
        Description of return value

    Examples
    --------
    >>> example_function("test", 5)
    True
    """
    pass
```

### Type Hints

- Add type hints to all new code
- Use `from __future__ import annotations` for forward references
- Use `typing` module types where appropriate

---

## Testing

### Test Organization

Tests are organized by module:

```
tests/
├── conftest.py              # Shared fixtures
├── test_pienode.py          # PieNode tests
├── test_pietree.py          # PieTree tests
├── test_tree_ops.py         # Tree operations
├── test_metadata.py         # Metadata system
├── test_parsing.py          # I/O parsing
├── test_rendering.py        # Rendering
├── test_query.py            # Query/selection
└── test_cli.py              # CLI commands
```

### Writing Tests

1. **Use pytest fixtures** from `conftest.py`
2. **Organize with classes** for related tests
3. **Test both success and failure cases**
4. **Use descriptive names** (`test_what_when_then`)

Example test structure:

```python
class TestFeatureName:
    """Test suite for FeatureName."""

    def test_basic_usage(self, fixture_name):
        """Test basic usage works correctly."""
        result = do_something(fixture_name)
        assert result == expected

    def test_edge_case(self):
        """Test edge case is handled."""
        with pytest.raises(ValueError):
            do_something_invalid()
```

### Test Coverage

We aim for >85% test coverage. Check coverage with:

```bash
pytest --cov=pietree --cov-report=html
open htmlcov/index.html
```

Priority areas for testing:
- Core tree operations: **95%+**
- Metadata and inference: **95%+**
- I/O operations: **90%+**
- Rendering pipeline: **80%+**

---

## Documentation

### Documentation Files

Update documentation when adding features:

- **Code docstrings:** NumPy style for all public APIs
- **User guide:** `docs/user_guide/` for user-facing features
- **API reference:** `docs/api_reference/` for detailed API docs
- **README.md:** Update examples if adding major features
- **CHANGELOG:** Add entry for notable changes

### Documentation Style

- Use **present tense** ("Returns" not "Returned")
- Be **concise** but **complete**
- Include **examples** where helpful
- Use **code blocks** with syntax highlighting

### Building Documentation

If using Sphinx (future enhancement):

```bash
cd docs
make html
open _build/html/index.html
```

---

## Submitting Changes

### Pull Request Process

1. **Update your branch** with latest main:
   ```bash
   git checkout main
   git pull upstream main
   git checkout your-branch
   git rebase main
   ```

2. **Push your branch:**
   ```bash
   git push origin your-branch
   ```

3. **Create Pull Request** on GitHub

4. **Fill out PR template** with:
   - Description of changes
   - Related issues (if any)
   - Testing performed
   - Screenshots (for UI changes)

5. **Wait for review** and address feedback

### PR Checklist

Before submitting, ensure:

- [ ] Tests pass (`pytest`)
- [ ] Code is formatted (`ruff format`)
- [ ] No linting errors (`ruff check`)
- [ ] Type hints added for new code
- [ ] Docstrings added/updated
- [ ] Documentation updated if needed
- [ ] CHANGELOG.md updated (for notable changes)
- [ ] Commit messages are clear

### Review Process

- Maintainers will review your PR
- Address feedback by pushing new commits
- Once approved, your PR will be merged
- Squash commits if requested

---

## Project Structure

### Module Organization

```
src/pietree/
├── core/              # Base abstractions (PieObject)
├── tree/              # Tree structure (PieTree, PieNode, mixins)
├── metadata/          # Metadata system (PieMeta, inference)
├── query/             # Selection API
├── label/             # Label system
├── style/             # Style engine (rules, selectors)
├── render/            # Rendering pipeline
│   └── layers/        # Layer renderers
├── io/                # I/O operations (parsing, serialization)
└── cli/               # Command-line interface
```

### Key Architectural Principles

1. **Separation of Concerns:** Each module has a focused purpose
2. **Mixin Pattern:** PieTree uses mixins for different operation types
3. **Abstract Base Classes:** Extensibility via base classes for parsers, renderers
4. **Metadata-First:** Metadata is a first-class citizen throughout
5. **Lazy Evaluation:** Render specs computed on-demand

### Adding New Features

#### Adding a New Tree Operation

1. Add method to appropriate mixin in `tree/tree_*.py`
2. Add tests in `tests/test_tree_ops.py`
3. Document in `docs/api_reference/tree.md`

#### Adding a New CLI Command

1. Create `cli/command_name.py` with `register_parser()` and `run()`
2. Register in `cli/main.py`
3. Add tests in `tests/test_cli.py`
4. Document in `docs/user_guide/cli.md`

#### Adding a New File Format

1. Create parser in `io/parsing.py` (inherit from `TreeParser`)
2. Create serializer in `io/serialization.py` (inherit from `TreeSerializer`)
3. Update format detection in CLI commands
4. Add tests in `tests/test_parsing.py`

---

## Getting Help

- **Questions:** Open a discussion on GitHub Discussions
- **Bug Reports:** Open an issue with reproduction steps
- **Feature Requests:** Open an issue with use case description
- **Chat:** Join our community (if available)

---

## Code of Conduct

Be respectful, inclusive, and collaborative. We're all here to make PieTree better!

---

## License

By contributing, you agree that your contributions will be licensed under the same license as PieTree (check LICENSE file).

---

## Recognition

Contributors are recognized in:
- Git history (Co-Authored-By in commits)
- Release notes
- Contributors section in README

Thank you for contributing to PieTree! 🎉
