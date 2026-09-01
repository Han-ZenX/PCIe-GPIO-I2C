# 项目架构说明文档

## 1. 项目概述

本项目采用 **Monorepo + 分层模块化** 架构，将固件、硬件、上位机软件、工具链、文档和测试统一管理在同一个仓库中。

**设计目标：**
- 支持长期持续迭代（创业级产品生命周期）
- 硬件多版本并行开发
- 团队扩张后各模块可独立维护
- CI/CD 自动化构建与测试

---

## 2. 目录结构总览

```
project-template/
├── firmware/          # 嵌入式固件（MCU代码）
├── hardware/          # 硬件设计（原理图/PCB/BOM）
├── software/          # 上位机 / 配套软件
├── tools/             # 构建脚本与调试工具
├── docs/              # 项目文档
├── tests/             # 系统级测试
├── ci/                # CI/CD 流水线配置
├── .gitignore         # Git忽略规则
├── .gitattributes     # Git LFS 大文件管理
├── CHANGELOG.md       # 变更日志
└── LICENSE            # 许可证
```

---

## 3. 各目录详细说明

### 3.1 firmware/ — 嵌入式固件

固件采用四层分离架构，核心原则：**更换MCU只改HAL层，业务逻辑零修改**。

```
firmware/
├── CMakeLists.txt            # 顶层构建入口
├── src/
│   ├── main.c               # 入口点（初始化→主循环）
│   ├── app/                 # 【应用层】业务逻辑、状态机、UI
│   ├── hal/                 # 【硬件抽象层】GPIO/时钟/外设封装
│   ├── drivers/             # 【驱动层】具体外设驱动(SPI/I2C/UART)
│   └── services/            # 【服务层】通信协议/存储/OTA
├── boards/                  # 板级配置（不同硬件版本）
│   └── default/
│       └── board_config.h   # 引脚映射、时钟频率等
├── include/                 # 对外公开头文件
├── lib/                     # 第三方库（FreeRTOS/FatFS等）
└── tests/                   # 固件模块单元测试
```

#### 分层职责

| 层级 | 职责 | 可替换性 | 示例 |
|------|------|----------|------|
| **app** | 业务逻辑、产品功能 | 不可替换（产品核心） | 测试流程、数据算法、用户交互 |
| **hal** | 硬件抽象、引脚映射 | 换MCU时整体替换 | GPIO操作、时钟配置、中断管理 |
| **drivers** | 外设通信协议实现 | 随外设更换替换 | ADS1258驱动、TCA9548A驱动 |
| **services** | 后台持续运行的服务 | 可独立升级 | TCP通信、Flash存储、OTA升级 |

#### 构建方式

```bash
# Debug构建（默认板级）
cmake -B build -DBOARD=default
cmake --build build

# Release构建
cmake -B build -DBOARD=v2.0 -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

#### 新增板级

```bash
# 复制默认板级配置，修改引脚映射即可
cp -r boards/default boards/v2.0
# 编辑 boards/v2.0/board_config.h
cmake -B build -DBOARD=v2.0
```

---

### 3.2 hardware/ — 硬件设计

管理所有硬件设计文件，按版本号组织，支持多版本并行开发。

```
hardware/
├── schematic/               # 原理图
│   └── v1.0/               # 硬件版本1.0的原理图文件
├── pcb/                     # PCB Layout
│   └── v1.0/               # 硬件版本1.0的PCB文件
├── bom/                     # BOM物料清单（CSV/Excel）
├── gerber/                  # 送厂生产的Gerber文件
├── 3d/                      # 3D外壳/结构件模型
└── pinout/                  # 引脚分配表
    └── pinout.md            # MCU引脚功能对照表
```

#### 版本管理规则

| 规则 | 说明 |
|------|------|
| 原理图改版 | 新建 `schematic/v2.0/`，保留旧版本 |
| BOM变更 | 更新 `bom/` 中的文件，CHANGELOG记录 |
| pinout同步 | 每次硬件改版必须更新 `pinout.md` |
| 大文件管理 | `.SchDoc`/`.PcbDoc` 等通过 Git LFS 跟踪 |

---

### 3.3 software/ — 上位机 / 配套软件

```
software/
├── desktop/                 # PC桌面应用（Qt/Electron等）
├── mobile/                  # 移动端App（iOS/Android）
└── cloud/                   # 云端服务（数据平台/API）
```

各子项目独立维护，通过通信协议（TCP/BLE/MQTT）与固件交互。

---

### 3.4 tools/ — 工具链与脚本

```
tools/
├── scripts/                 # 自动化脚本
│   └── build.py            # 一键构建脚本
├── configs/                 # 通用配置模板
└── utilities/               # 辅助工具
                             # - 固件烧录器
                             # - 校准工具
                             # - 日志分析器
```

#### build.py 用法

```bash
python tools/scripts/build.py --board=default          # Debug构建
python tools/scripts/build.py --board=v2.0 --release   # Release构建
python tools/scripts/build.py --flash                  # 构建+烧录
python tools/scripts/build.py --clean                  # 清理
```

---

### 3.5 docs/ — 项目文档

```
docs/
├── architecture/            # 系统架构设计文档
├── api/                     # API接口文档（通信协议）
├── hardware/                # 硬件说明文档
├── manufacturing/           # 生产工艺/SOP文档
└── user-guide/              # 用户使用手册
```

---

### 3.6 tests/ — 系统级测试

```
tests/
├── unit/                    # 单元测试（纯软件，不需要硬件）
├── integration/             # 集成测试（模块间交互）
└── hwt/                     # 硬件在环测试（Hardware-in-the-Loop）
```

#### 测试策略

| 测试类型 | 运行环境 | 触发时机 | 覆盖范围 |
|----------|----------|----------|----------|
| unit | PC (Host) | 每次commit | 算法/逻辑函数 |
| integration | PC + 模拟器 | PR合并前 | 模块间通信 |
| hwt | 实际硬件 | 发版前 | 全链路验证 |

---

### 3.7 ci/ — CI/CD 流水线

```
ci/
└── workflows/
    └── build.yml            # GitHub Actions 构建配置
```

流水线自动执行：
1. 编译固件（多板级）
2. 运行单元测试
3. 生成二进制产物
4. （可选）自动烧录/部署

---

## 4. 核心架构原则

| 原则 | 实践方式 |
|------|----------|
| **Monorepo** | 硬件+固件+软件在同一仓库，版本一致 |
| **分层隔离** | app不直接调用寄存器，只通过hal/driver接口 |
| **板级抽象** | 引脚映射集中在 `boards/` 目录，代码中无硬编码 |
| **组件化** | 每个驱动/服务是独立编译单元（CMake library） |
| **测试前置** | 新增功能必须配套单元测试 |
| **二进制管理** | 原理图/PCB用Git LFS，避免仓库膨胀 |
| **版本关联** | 硬件版本与固件版本通过Git Tag关联 |

---

## 5. 开发工作流

### 5.1 新功能开发

```
1. 创建分支:  git checkout -b feat/xxx
2. 固件开发:  在 firmware/src/app/ 添加业务逻辑
3. 驱动开发:  在 firmware/src/drivers/ 添加外设驱动
4. 编写测试:  在 firmware/tests/ 或 tests/unit/ 添加测试
5. 本地验证:  python tools/scripts/build.py --board=default
6. 提交PR:    CI自动编译+测试
```

### 5.2 硬件改版

```
1. 新建版本:  cp -r hardware/schematic/v1.0 hardware/schematic/v2.0
2. 更新设计:  在EDA工具中修改v2.0原理图/PCB
3. 更新引脚:  修改 hardware/pinout/pinout.md
4. 新增板级:  cp -r firmware/boards/default firmware/boards/v2.0
5. 适配固件:  修改 boards/v2.0/board_config.h
6. 验证:      cmake -DBOARD=v2.0 编译通过
```

### 5.3 发版流程

```
1. 更新 CHANGELOG.md
2. Git Tag:   git tag v1.2.0-hw1.0 (固件版本-硬件版本)
3. CI自动:    编译Release固件 → 生成Gerber → 打包发布
```

---

## 6. 参考项目

本架构参考以下知名开源项目的组织方式：

| 项目 | 参考要素 |
|------|----------|
| ESP-IDF | components组件化、CMake构建系统 |
| Zephyr RTOS | boards板级抽象、Kconfig配置 |
| RIOT-OS | cpu/drivers/sys分层、pkg第三方包 |
| FreeRTOS | 内核源码单一副本、Demo目录分离 |

---

## 7. 技术选型建议

| 领域 | 推荐方案 |
|------|----------|
| 构建系统 | CMake + Ninja |
| 版本控制 | Git + Git LFS |
| CI/CD | GitHub Actions / GitLab CI |
| 测试框架 | Unity (C) / Google Test (C++) |
| 文档工具 | Doxygen + Sphinx |
| 硬件EDA | Altium Designer / KiCad |
| 通信协议 | 自定义二进制协议 / MQTT / SCPI |
