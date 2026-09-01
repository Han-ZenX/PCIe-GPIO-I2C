add_library(hal
    hal_init.c
)

target_include_directories(hal PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/..)
