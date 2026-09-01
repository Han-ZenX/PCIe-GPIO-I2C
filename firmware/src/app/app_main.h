/**
 * @file app_main.h
 * @brief 应用层 - 主业务逻辑入口
 */

#ifndef APP_MAIN_H
#define APP_MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 应用层主循环
 *        包含业务逻辑、状态机、UI交互等
 */
void app_run(void);

/**
 * @brief 应用层初始化
 */
void app_init(void);

#ifdef __cplusplus
}
#endif

#endif /* APP_MAIN_H */
