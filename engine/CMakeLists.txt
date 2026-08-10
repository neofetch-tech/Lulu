pybind11_add_module(lulu_core
    src/bindings.cpp
    src/lulu_engine.cpp
)

target_include_directories(lulu_core PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(lulu_core PRIVATE
    llama
)

target_compile_definitions(lulu_core PRIVATE
    VERSION_INFO=${PROJECT_VERSION}
)

# Install the compiled extension straight into the Python package so
# `import lulu_core` works after `pip install .`
install(TARGETS lulu_core DESTINATION .)
