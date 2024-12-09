# OIB Test Plugin

这是一个用于测试的 OIB 插件示例。

## 功能
- 提供一个简单的 `/hello` 接口
- 支持基本的配置修改
- WebSocket 消息处理示例

## 安装
1. 克隆仓库到 plugins 目录
2. 重启 OIB
3. 启用插件

## 配置
在 config.json 中可以修改：
- message: 自定义问候语
- interval: 定时消息间隔（秒）

## API
- GET /api/test/hello - 返回配置的问候语
- WS /ws/test - WebSocket 连接点
