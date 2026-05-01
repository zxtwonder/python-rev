# rev-core

Common interfaces, data types, and error hierarchy for REV Robotics hub devices.
Pure Python — no native dependencies.

## Requirements

- Python 3.12+

## Install

```sh
pip install .
```

For development (editable install):

```sh
pip install -e .
```

With type-checking extras:

```sh
pip install -e ".[dev]"
```

## Type checking

```sh
pip install -e ".[dev]"   # installs mypy
mypy rev_core/
```

## Lint

```sh
pip install -e ".[dev]"   # installs ruff
ruff check rev_core/
```

## Compilation

No compilation step — this is a pure Python package.
