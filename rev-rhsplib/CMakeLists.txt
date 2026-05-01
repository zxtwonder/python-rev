cmake_minimum_required(VERSION 3.15)
project(rev_rhsplib LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)

set(LIBRHSP_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../node-rhsplib/packages/rhsplib/librhsp"
    CACHE PATH "Path to the librhsp source tree")

# Force static so librhsp is linked into _rev_rhsplib.so rather than a separate .so.
set(BUILD_SHARED_LIBS OFF CACHE BOOL "Build using shared libraries" FORCE)
option(RHSP_BUILD_TESTS "Build librhsp unit tests" OFF)
add_subdirectory("${LIBRHSP_DIR}" librhsp_build EXCLUDE_FROM_ALL)

find_package(pybind11 3.0 REQUIRED)

pybind11_add_module(_rev_rhsplib src/_rev_rhsplib.cpp)
target_link_libraries(_rev_rhsplib PRIVATE rhsp)

# Place the built extension next to the Python package for direct import.
set_target_properties(_rev_rhsplib PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/rev_rhsplib"
)
