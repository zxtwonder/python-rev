# rev-rhsplib

Low-level Python/C++ bindings for [librhsp](../node-rhsplib/packages/rhsplib/librhsp)
(REV Hub Serial Protocol). Provides a synchronous C extension (`_rev_rhsplib`) and
async Python wrappers (`rev_rhsplib`).

## Requirements

- Python 3.12+
- CMake 3.15+
- A C11/C++17 compiler:
  - **Linux / macOS**: GCC 9+ or Clang 10+
  - **Windows**: Visual Studio 2019+ (with the "Desktop development with C++" workload)
    or MinGW-w64
- The `node-rhsplib` git submodule checked out (provides librhsp source)

## Submodule

librhsp is included as a git submodule. If you cloned the repository without
`--recurse-submodules`, initialise it first:

```sh
git submodule update --init --recursive
```

## Install

`scikit-build-core` invokes CMake automatically during `pip install`.

```sh
pip install rev-core          # required dependency
pip install .
```

For a development (editable) install — rebuilds the extension on each `pip install -e .`:

```sh
pip install -e . --no-build-isolation
```

> **Note on `--no-build-isolation`**: editable installs with scikit-build-core work
> best without build isolation so that the in-tree `rev_rhsplib/` directory is used
> directly. Omit the flag for a regular (non-editable) install.

### Linux — install build tools

```sh
# Debian / Ubuntu
sudo apt install cmake build-essential

# Fedora / RHEL
sudo dnf install cmake gcc g++
```

### macOS — install build tools

```sh
# Xcode command-line tools (provides clang)
xcode-select --install

# CMake via Homebrew
brew install cmake
```

### Windows — install build tools

1. Install [Visual Studio 2022](https://visualstudio.microsoft.com/) (Community
   edition is free) with the **"Desktop development with C++"** workload.
2. Install [CMake](https://cmake.org/download/) and add it to `PATH`.

Then build from a **Developer Command Prompt** (or any shell where `cl.exe` is on
`PATH`):

```cmd
pip install rev-core
pip install .
```

## Manual CMake build (for debugging)

If you need to run CMake directly:

```sh
pip install pybind11          # ensures pybind11 CMake config is available
cmake -S . -B build -DRHSP_BUILD_TESTS=OFF -DCMAKE_BUILD_TYPE=Release
cmake --build build
# The built _rev_rhsplib.so (or .pyd on Windows) is copied to rev_rhsplib/
```

## With type-checking extras

```sh
pip install -e ".[dev]"       # adds mypy
```
