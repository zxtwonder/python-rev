cmake_minimum_required(VERSION 3.15)
project(rev_rhsplib VERSION 2.1.0 LANGUAGES C CXX)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# ── librhsp ───────────────────────────────────────────────────────────────────
# Path to librhsp relative to this CMakeLists.txt (via the git submodule).
set(LIBRHSP_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../node-rhsplib/packages/rhsplib/librhsp"
    CACHE PATH "Path to the librhsp source tree")

# Build librhsp without its test suite.
option(RHSP_BUILD_TESTS "Build librhsp unit tests" OFF)
add_subdirectory("${LIBRHSP_DIR}" librhsp_build EXCLUDE_FROM_ALL)

# ── pybind11 ─────────────────────────────────────────────────────────────────
find_package(pybind11 3.0 REQUIRED)

# ── Python extension ─────────────────────────────────────────────────────────
pybind11_add_module(_rev_rhsplib src/_rev_rhsplib.cpp)

target_include_directories(_rev_rhsplib PRIVATE
    "${LIBRHSP_DIR}/include"
    "${LIBRHSP_DIR}/include/internal"
)

target_link_libraries(_rev_rhsplib PRIVATE rhsp)

# Place the built .so next to the Python package so it can be imported.
set_target_properties(_rev_rhsplib PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/rev_rhsplib"
)
