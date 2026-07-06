# Contributing

Thanks for your interest in contributing to KeyTik! Please take a moment to review this document before submitting a pull request.

This guide has some instructions and tips on how to set up KeyTik workspace. Please read it carefully if you're a new contributor or don't have any experience on the required languages and knowledges.

## Table of Contents

- [Requirements](#requirements)
- [Prerequisites](#prerequisites)
  - [Cloning the Repository](#cloning-the-repository)
  - [Dependency Management](#dependency-management)
    - [Install Dependencies](#install-dependencies)
    - [Adding New Dependencies](#adding-new-dependencies)
  - [Linting](#linting)
    - [Install Linter](#install-linter)
    - [Lint Command](#lint-command)
  - [Formatting](#formatting)
    - [Install Formatter](#install-formatter)
    - [Format Command](#format-command)
  - [Pre-Commit](#pre-commit)
    - [Install Pre-Commit](#install-pre-commit)
    - [Install Hook](#install-hook)
- [Submitting the changes](#submitting-the-changes)
  - [Pull Request checklist](#pull-request-checklist)

## Requirements

- [Python](https://www.python.org/downloads/) between v3.10 and v3.13
- [UV](https://docs.astral.sh/uv/getting-started/installation/)
- Integrated Development Environtment (IDE) of your choice

## Prerequisites

Before you start, please note that the ability to use following technologies is required:

- [Python](https://www.python.org/downloads)
- [AutoHotkey](https://www.autohotkey.com) (Optional)

#### Cloning the Repository

```
# Clone KeyTik
git clone https://github.com/Fajar-RahmadJaya/KeyTik

# Set directory
cd keytik
```

### Dependency Management

We use UV for dependency management. UV is an extremely fast Python package and project manager, written in Rust. For more information, please refer to [UV Documentation](https://docs.astral.sh/uv).

See project configuration on [pyproject.toml](https://github.com/Fajar-RahmadJaya/KeyTik/blob/main/pyproject.toml)

#### Install Dependencies

```
uv sync
```

#### Adding New Dependencies

```
uv add [package name]
```

### Linting

Linting highlights semantic and stylistic problems in code, which often helps to identify and correct subtle programming errors or coding practices that can lead to errors [Source](https://code.visualstudio.com/docs/python/linting). We use combination of [Ruff](https://docs.astral.sh/ruff) and [Pylint](https://www.pylint.org) to lint our code. Ruff is used for development because of its speed and Pylint is used for deeper analysis. See ruff configuration on [pyproject.toml](https://github.com/Fajar-RahmadJaya/KeyTik/blob/74b587a6f399e7cfc1ca5de680bb1640d69461d2/pyproject.toml#L56)

We require every pull request to **pass Pylint check** before allowing any merge. So, please check for any linting error before pushing any changes. You can use pre-commit to help this process, see [Pre-Commit](#pre-commit) for more info.

#### Install Linter

```
# Only install lint
uv sync --inexact --group lint
```

#### Lint Command

```
# Lint check using Pylint
pylint keytik

# Lint check using Ruff
ruff check

# Auto fix lint error using ruff if applicable
ruff check --fix
```

### Formatting

Formatting makes source code easier to read by human beings. By enforcing particular rules and conventions such as line spacing, indents, and spacing around operators, the code becomes more visually organized and comprehensible [Source](https://code.visualstudio.com/docs/python/formatting). We also use [Ruff](https://docs.astral.sh/ruff) to automatically format our code.

You can use pre-commit to help this process, see [Pre-Commit](#pre-commit) for more info.

#### Install Formatter

```
# Install ruff on lint group
uv sync --inexact --group lint
```

#### Format Command

```
# Format all code
ruff format
```

### Pre-Commit

Using pre-commit is optional, but we strongly recomend you to use pre-commit. Pre-commit is a framework for managing and maintaining multi-language pre-commit hooks. We use pre-commit for various tasks such as check for linting error, auto fix lint if applicable, format code, syncing dependencies, and other tasks. For more information, please refer to [pre-commit documentation](https://pre-commit.com).

See the configuration on [.pre-commit-config.yaml](https://github.com/Fajar-RahmadJaya/KeyTik/blob/main/.pre-commit-config.yaml).

#### Install Pre-Commit

```
# Only install pre-commit
uv sync --inexact --group hook --group lint
```

#### Install Hook

```
pre-commit install
```

## Submitting the changes

When you feel confident about your changes, submit a new Pull Request so your code can be reviewed and merged if it's approved. We encourage following a [GitHub Standard Fork & Pull Request Workflow](https://gist.github.com/Chaser324/ce0505fbed06b947d962) and following the good practices of the workflow, such as not committing directly to `master`: always create a new branch for your changes.

> [!IMPORTANT]
> Make sure all lint checks have passed before creating a pull request.
> Any merge will be blocked if there are any lint errors.

Please **do test your changes** by running it before submitting it. Obvious untested PRs will not be merged, such as ones created with the GitHub web interface. Also make sure to follow the PR checklist available in the PR body field when creating a new PR. As a reference, you can find it below.

### Pull Request checklist

- All lint checks have passed
- Have run `ruff format` manually or by pre-commit before submitting PR
- Have tested the modifications by running it
- Referenced all related issues in the PR body (e.g. "Closes #xyz")
- This PR is AI-assisted, I have reviewed the changes manually and confirmed they are not slop
