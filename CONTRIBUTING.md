# Contributing to Spidermind

Thank you for your interest in contributing to Spidermind! We welcome contributions from the community.

## Code of Conduct

This project adheres to the Contributor Covenant [code of conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps which reproduce the problem**
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed after following the steps**
- **Explain which behavior you expected to see instead and why**
- **Include screenshots and animated GIFs if possible**
- **Include your OS and Python version**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a step-by-step description of the suggested enhancement**
- **Provide specific examples to demonstrate the steps**
- **Describe the current behavior and expected behavior**
- **Explain why this enhancement would be useful**

### Pull Requests

- Fill in the pull request template
- Follow the Python style guide (see below)
- Include appropriate test cases
- Update documentation as needed
- End all files with a newline

## Development Setup

### Clone the Repository

```bash
git clone https://github.com/caozuohua/spidermind.git
cd spidermind
```

### Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/
```

### Run Code Quality Checks

```bash
# Format code
black spidermind/ tests/

# Check code style
flake8 spidermind/ tests/

# Sort imports
isort spidermind/ tests/

# Type checking
mypy spidermind/
```

## Style Guide

### Python Code Style

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with the following tools:

- **black** - Code formatting (line length: 100)
- **isort** - Import sorting
- **flake8** - Linting
- **mypy** - Static type checking

### Commit Message Guidelines

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

### Documentation

- Use docstrings for all public modules, functions, classes, and methods
- Use Google-style docstrings
- Keep documentation up-to-date with code changes

## Testing

- Write tests for all new features and bug fixes
- Ensure all tests pass before submitting a pull request
- Aim for high code coverage (>80%)
- Run `pytest --cov=spidermind` to check coverage

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
6. Request review from maintainers
7. Address any requested changes

## Additional Notes

### Issue and Pull Request Labels

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Improvements or additions to documentation
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention is needed
- `question` - Further information is requested

## Questions?

Feel free to open an issue or reach out to the maintainers.
