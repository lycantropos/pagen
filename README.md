pagen
=====

[![](https://github.com/lycantropos/pagen/workflows/CI/badge.svg)](https://github.com/lycantropos/pagen/actions/workflows/ci.yml "Github Actions")
[![](https://codecov.io/gh/lycantropos/pagen/branch/master/graph/badge.svg)](https://codecov.io/gh/lycantropos/pagen "Codecov")
[![](https://img.shields.io/github/license/lycantropos/pagen.svg)](https://github.com/lycantropos/pagen/blob/master/LICENSE "License")
[![](https://badge.fury.io/py/pagen.svg)](https://badge.fury.io/py/pagen "PyPI")
[![](https://img.shields.io/crates/v/pagen.svg)](https://crates.io/crates/pagen "crates.io")

In what follows `python` is an alias for `python3.10` or `pypy3.10`
or any later version (`python3.11`, `pypy3.11` and so on).

Installation
------------

Install the latest `pip` & `setuptools` packages versions

```bash
python -m pip install --upgrade pip setuptools
```

### User

Download and install the latest stable version from `PyPI` repository

```bash
python -m pip install --upgrade pagen
```

### Developer

Download the latest version from `GitHub` repository

```bash
git clone https://github.com/lycantropos/pagen.git
cd pagen
```

Install

```bash
python setup.py install
```

Development
-----------

### Bumping version

#### Preparation

Install [bump-my-version](https://github.com/callowayproject/bump-my-version#installation).

#### Release

Choose which version number category to bump following [semver
specification](http://semver.org/).

Test bumping version

```bash
bump-my-version bump --dry-run --verbose $CATEGORY
```

where `$CATEGORY` is the target version number category name, possible
values are `patch`/`minor`/`major`.

Bump version

```bash
bump-my-version bump --verbose $CATEGORY
```

This will set version to `major.minor.patch`.

### Running tests

Install dependencies

```bash
python -m pip install -r requirements-tests.txt
```

Plain

```bash
pytest
```

Inside `Docker` container:

- with `CPython`
  ```bash
  docker-compose --file docker-compose.cpython.yml up
  ```
- with `PyPy`
  ```bash
  docker-compose --file docker-compose.pypy.yml up
  ```

`Bash` script:

- with `CPython`
  ```bash
  ./run-tests.sh
  ```
  or
  ```bash
  ./run-tests.sh cpython
  ```

- with `PyPy`
  ```bash
  ./run-tests.sh pypy
  ```

`PowerShell` script:

- with `CPython`
  ```powershell
  .\run-tests.ps1
  ```
  or
  ```powershell
  .\run-tests.ps1 cpython
  ```
- with `PyPy`
  ```powershell
  .\run-tests.ps1 pypy
  ```
