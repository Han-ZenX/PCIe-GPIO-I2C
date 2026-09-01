/**
 * @file service_manager.h
 * @brief 服务层 - 统一管理通信/存储/OTA等服务
 */

#ifndef SERVICE_MANAGER_H
#define SERVICE_MANAGER_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 初始化并启动所有后台服务
 *        包括: 通信协议栈、数据存储、OTA升级等
 */
void service_manager_init(void);

/**
 * @brief 服务层主循环(若不使用RTOS任务)
 */
void service_manager_poll(void);

#ifdef __cplusplus
}
#endif

#endif /* SERVICE_MANAGER_H */
