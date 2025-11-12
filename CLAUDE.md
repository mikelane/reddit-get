# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

reddit-get is a Python CLI tool that retrieves posts from Reddit using the PRAW (Python Reddit API Wrapper) library. The tool authenticates with Reddit's API and fetches posts from specified subreddits with customizable sorting, time filtering, and output formatting.

## Technology Stack

- **Language**: Python 3.11+ (tested on 3.11, 3.12, 3.13, 3.14)
- **CLI Framework**: Google Fire (automatic CLI generation from Python classes)
- **Reddit API**: PRAW 7.7.0
- **Package Manager**: Poetry
- **Testing**: pytest with extensive plugins
- **Code Quality**: Black, isort, Ruff, mypy with strict type checking

## Repository Structure

```
reddit_get/
├── cli.py           # Main RedditCli class with Fire integration
├── utils.py         # Helper functions for config loading, query building, formatting
└── types/
    ├── __init__.py  # Type exports including CallMap, PrawQuery
    └── enums.py     # Custom enum classes (SortingOption, TimeFilterOption)

tests/
├── conftest.py      # pytest fixtures and mock PRAW objects
├── test_*.py        # Test modules mirroring source structure
└── .*               # Test fixture files (invalid configs, example configs)
```

## Essential Commands

### Setup and Installation
```bash
# Install dependencies
poetry install

# Install with all groups (including dev dependencies)
poetry install --with lint,test
```

### Running Tests
```bash
# Run all tests with coverage (90% minimum required)
poetry run pytest -vvv --force-sugar --tb=native --cov=reddit_get --cov-fail-under=90 --cov-report=xml:docs/coverage/integration/report.xml --numprocesses=auto --color=yes --code-highlight=yes --durations=10

# Run tests in parallel with pytest-xdist
poetry run pytest -n auto

# Run single test file
poetry run pytest tests/test_utils.py

# Run single test function
poetry run pytest tests/test_utils.py::test_function_name

# Run tests across multiple Python versions
tox
```

### Code Quality
```bash
# Format code with Black (line length 110)
poetry run black reddit_get/ tests/

# Sort imports with isort
poetry run isort reddit_get/ tests/

# Lint with Ruff (auto-fix enabled)
poetry run ruff check reddit_get/ tests/

# Type checking with mypy (strict mode)
poetry run mypy reddit_get/
```

### Running the CLI Locally
```bash
# Run from source during development
poetry run python -m reddit_get.cli post --subreddit showerthoughts --post_sorting top --limit 10

# Or use the installed entry point
poetry run reddit-get post --help
```

## Architecture Notes

### Configuration System
- Uses TOML config files (default: `~/.redditgetrc`)
- Config loading in `utils.py:load_configs()` returns tuple of (Path, dict)
- Required fields: client_id, client_secret, user_agent, username, password
- Config validation happens on RedditCli initialization

### Query Function Pattern
The `get_reddit_query_function()` in utils.py uses a functional approach:
- Returns partially applied functions for time-sensitive queries (controversial, top)
- Uses `CallMap` type alias mapping `SortingOption` enums to `PrawQuery` callables
- Enables deferred execution with consistent interface across all sorting methods

### Custom Enum Implementation
The codebase uses custom enum classes with metaclass magic:
- `MetaEnum` metaclass overrides `__contains__` for value checking
- `BaseEnum` and `StrEnum` provide string-based enums with value validation
- Used by `SortingOption` and `TimeFilterOption` for CLI argument validation

### Template System
Both headers and post output use Python string formatting with template validation:
- `get_template_keys()` extracts format variables from template strings
- Validates against allowed variables before formatting
- Supports any PRAW Submission attribute in output templates

### Testing Strategy
- **Session-scoped fixtures**: Mock entire PRAW library to avoid network calls
- **MonkeyPatch persistence**: Custom `monkeysession` fixture for session-level patching
- **Mock hierarchy**: MockReddit → MockSubreddit → MockSubmission
- Test naming convention: `test_*` or `it_*` functions (pytest configured for both)

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/integrate.yml`) runs on:
- Matrix: Python 3.11, 3.12, 3.13, 3.14 × Ubuntu, macOS, Windows
- Steps: checkout → setup Python → install Poetry → cache deps → install → pytest with coverage
- Coverage uploaded to Codecov (90% minimum enforced)

## Code Quality Standards

### Type Checking (mypy strict mode)
- `disallow_untyped_defs = true`
- `disallow_any_unimported = true`
- All functions must have complete type annotations
- Return types are mandatory

### Ruff Configuration
- Extensive rule set enabled (see pyproject.toml lines 99-135)
- Auto-fix enabled for most rules
- Special exclusions for tests: no docstrings, S101 (assert) allowed
- Required import: `from __future__ import annotations` in all files

### Testing Requirements
- Minimum 90% coverage enforced in CI (95% in tox)
- Parallel test execution with pytest-xdist
- Console scripts testing via pytest-console-scripts
- Doctests enabled for all modules

## Common Development Patterns

### Adding New Sorting Options
1. Add enum value to `SortingOption` in types/enums.py
2. Add mapping in `RedditCli.valid_header_variables['sorting']`
3. Add callable to `call_map` in `get_reddit_query_function()`
4. Add test case in test_utils.py and test_RedditCli.py

### Error Handling
- Use `fire.core.FireError` for user-facing errors (exits with code 255)
- Validation happens early: config loading, enum parsing, template validation
- Network errors from PRAW bubble up with Fire's exception handling

### Template Variables
- Header templates support: `{sorting}`, `{time}`, `{subreddit}`
- Post templates support any PRAW Submission attribute
- Validation uses `string.Formatter().parse()` to extract variables
- Unknown template keys raise FireError before API calls
