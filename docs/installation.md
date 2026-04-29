# Installation Guide

## Requirements

- Python 3.8 or higher
- pip or poetry

## Installation Methods

### From PyPI (Recommended)

```bash
pip install spidermind
```

### From Source

```bash
git clone https://github.com/caozuohua/spidermind.git
cd spidermind
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/caozuohua/spidermind.git
cd spidermind
pip install -e ".[dev]"
```

## Verification

To verify the installation was successful:

```python
import spidermind
print(spidermind.__version__)
```

## Troubleshooting

If you encounter any issues during installation, please:

1. Check that you have Python 3.8+: `python --version`
2. Upgrade pip: `pip install --upgrade pip`
3. Open an issue on [GitHub](https://github.com/caozuohua/spidermind/issues)
