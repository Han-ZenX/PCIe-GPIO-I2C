# Changelog

本文件记录项目所有重要变更。格式基于 [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- 上位机程序 `software/desktop/PCIe-GPIO-I2C`（Qt，Driver 动态库 + TOOL 界面）（2026-09-21）
  - PCIE-1751 DIO 模拟 I²C 主机，经 DS2482-100 读取 DS2431 64 位 ROM（含 CRC 校验）
  - 硬件诊断：DS2482 测试、I²C 地址扫描、SDA 回环自检、SCL/SDA 方波、SCL 高速翻转、SDA 外部拉低测试
  - 分级日志（Error / Info / Debug / Trace），位延时运行时可调
- I2C_PCIE1751 EVAL Board REV01 原理图与 PCB（2026-09-21）
- 文档（`docs/hardware/`）：验证板设计说明、故障排查记录、74HCT07 干扰机理分析，及其生成脚本 `tools/scripts/gen_*.py`（2026-09-21）

### Changed
- README 改写为 PCIE-1751 模拟 I²C 项目说明，补充接线、半字节方向冲突与 SDA 1.9 V 问题分析（2026-09-01）
- 故障排查记录补充复测结论：更换非问题批次 74HCT07 后通信恢复（2026-09-22）

### Removed
- 模板自带的 `firmware/` 固件工程（本项目为纯上位机工程）（2026-09-01）

### Fixed
- 验证板通信失败：根因为 U1 批次（ST 0AA709）实为推挽输出，更换其它批次 74HCT07 后 ROM 读取成功（2026-09-22）

## 2026-09-01 初始化
- 初始化项目模板结构、CI 构建流水线、构建辅助脚本 `tools/scripts/build.py`
