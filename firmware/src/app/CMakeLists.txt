add_library(app
    app_main.c
)

target_include_directories(app PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
