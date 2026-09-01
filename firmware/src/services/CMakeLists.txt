add_library(services
    service_manager.c
)

target_include_directories(services PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/..)
