cmake_minimum_required(VERSION 3.18)
project(lulu LANGUAGES CXX C)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# lulu_core is a shared object (Python extension module), so every static
# lib it links against — including llama.cpp/ggml — must be built with
# position-independent code, or the final link fails.
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# ---------------------------------------------------------------------------
# llama.cpp — pulled in as a real dependency, not vendored.
# Pin the tag so builds are reproducible; bump it deliberately when you want
# newer llama.cpp features.
# ---------------------------------------------------------------------------
include(FetchContent)

set(LLAMA_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_SERVER OFF CACHE BOOL "" FORCE)
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)

FetchContent_Declare(
    llama_cpp
    GIT_REPOSITORY https://github.com/ggerganov/llama.cpp.git
    GIT_TAG        b10333  # pin: bump deliberately, test after bumping
    GIT_SHALLOW    TRUE
)
FetchContent_MakeAvailable(llama_cpp)

# ---------------------------------------------------------------------------
# pybind11
# ---------------------------------------------------------------------------
find_package(pybind11 CONFIG QUIET)
if(NOT pybind11_FOUND)
    FetchContent_Declare(
        pybind11
        GIT_REPOSITORY https://github.com/pybind/pybind11.git
        GIT_TAG        v2.13.6
        GIT_SHALLOW    TRUE
    )
    FetchContent_MakeAvailable(pybind11)
endif()

add_subdirectory(engine)
