# Contributing to AI-SAST

First off, thank you for considering contributing to AI-SAST! It's people like you that make AI-SAST such a great tool.

## Code of Conduct

### Our Pledge

We as members, contributors, and leaders pledge to make participation in our community a harassment-free experience for everyone, regardless of age, body size, visible or invisible disability, ethnicity, sex characteristics, gender identity and expression, level of experience, education, socio-economic status, nationality, personal appearance, race, caste, color, religion, or sexual identity and orientation.

### Our Standards

Examples of behavior that contributes to a positive environment:
* Demonstrating empathy and kindness toward other people
* Being respectful of differing opinions, viewpoints, and experiences
* Giving and gracefully accepting constructive feedback
* Accepting responsibility and apologizing to those affected by our mistakes
* Focusing on what is best for the overall community

Examples of unacceptable behavior:
* The use of sexualized language or imagery, and sexual attention or advances
* Trolling, insulting or derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information without explicit permission
* Other conduct which could reasonably be considered inappropriate

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported via GitHub issues or discussions. All complaints will be reviewed and investigated promptly and fairly.

---

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title** for the issue
* **Describe the exact steps to reproduce the problem**
* **Provide specific examples** to demonstrate the steps
* **Describe the behavior you observed** and what you expected to see
* **Include screenshots or logs** if applicable
* **Include your environment details**: Python version, OS, Google Cloud setup

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* **Use a clear and descriptive title**
* **Provide a detailed description** of the suggested enhancement
* **Explain why this enhancement would be useful**
* **List any alternatives** you've considered

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** with clear, concise commits
3. **Follow the existing code style** (PEP 8 for Python)
4. **Add tests** if applicable
5. **Update documentation** as needed
6. **Ensure all tests pass**
7. **Submit a pull request**

## Development Setup

1. Fork and clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/ai-sast.git
cd ai-sast
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install pytest black flake8 mypy
```

4. Set up your Google Cloud credentials:
```bash
export GOOGLE_CLOUD_PROJECT="your-test-project-id"
gcloud auth application-default login
```

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some exceptions:

* **Line length**: 120 characters maximum
* **Use type hints** where applicable
* **Write docstrings** for all public functions and classes
* **Keep functions focused** and small

### Example

```python
def scan_file(self, file_path: str) -> Dict[str, Any]:
    """
    Scan a single file for security vulnerabilities.
    
    Args:
        file_path: Path to the source code file
        
    Returns:
        Dictionary containing vulnerability analysis results
        
    Raises:
        FileNotFoundError: If the file does not exist
    """
    # Implementation here
    pass
```

### Code Formatting

We use `black` for code formatting:

```bash
black src/
```

### Linting

Run `flake8` to check for issues:

```bash
flake8 src/ --max-line-length=120
```

### Type Checking

We use `mypy` for static type checking:

```bash
mypy src/
```

## Testing

### Running Tests

```bash
pytest tests/
```

### Writing Tests

* Place test files in the `tests/` directory
* Name test files `test_*.py`
* Use descriptive test function names
* Include both positive and negative test cases

Example:

```python
def test_scanner_detects_sql_injection():
    """Test that the scanner correctly identifies SQL injection vulnerabilities."""
    scanner = SecurityScanner()
    code = """
    def get_user(user_id):
        query = f"SELECT * FROM users WHERE id = {user_id}"
        return execute_query(query)
    """
    result = scanner.scan_code_content(code, "test.py", "python")
    assert "SQL" in result["analysis"].upper()
```

## Git Commit Messages

* **Use the present tense** ("Add feature" not "Added feature")
* **Use the imperative mood** ("Move cursor to..." not "Moves cursor to...")
* **Limit the first line to 72 characters**
* **Reference issues and pull requests** after the first line

Example:
```
Add support for Rust language scanning

- Implement Rust file pattern detection
- Add Rust-specific vulnerability patterns
- Update documentation

Fixes #123
```

## Documentation

* **Update the README.md** if you change functionality
* **Add docstrings** to all public functions and classes
* **Include examples** in docstrings where helpful
* **Update the changelog** for notable changes

## Project Structure

```
ai-sast/
├── src/
│   ├── core/           # Core scanning functionality
│   │   ├── scanner.py  # Main scanner class
│   │   ├── vertex.py   # Vertex AI integration
│   │   ├── report.py   # Report generation
│   │   └── config.py   # Configuration management
│   └── __init__.py
├── tests/              # Test files
├── examples/           # Example scripts
├── .github/
│   └── workflows/      # GitHub Actions workflows
└── docs/               # Additional documentation
```

## Review Process

1. All submissions require review before merging
2. We may suggest changes, improvements, or alternatives
3. Please be patient - reviews take time
4. Address feedback and update your PR
5. Once approved, a maintainer will merge your PR

## Recognition

Contributors will be recognized in:
* The project README
* Release notes
* GitHub contributors page

## Questions?

Feel free to:
* Open an issue for questions
* Start a discussion in GitHub Discussions
* Reach out to maintainers

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

---

Thank you for contributing to AI-SAST! 🎉

