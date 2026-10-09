# 虚拟定位风险检测：最小可运行演示

这是一个用于比赛演示的服务端风险评分原型：客户端提交定位、环境、传感器和完整性信号；服务端计算多项风险并返回建议动作。项目只依赖 Python 3 标准库。

评分服务通过 `LocationProvider` 接口读取 GPS 坐标。默认 HTTP 适配器从请求中读取坐标；单元测试可注入固定虚拟坐标，评分规则无需连接真实 GPS。后续 Android 采集端可实现相同接口并封装真机 GPS 数据。

## 启动

在项目目录运行：

```bash
python3 server.py
```

另开终端运行合成轨迹演示：

```bash
python3 demo_client.py
```

运行依赖注入单元测试：

```bash
python3 -m unittest discover -s tests -v
```

健康检查：`GET http://127.0.0.1:8000/health`。评分接口：`POST http://127.0.0.1:8000/score`。

## 请求示例

```json
{
  "mock_location": false,
  "integrity": {"verified": true, "device_verdicts": ["MEETS_DEVICE_INTEGRITY"]},
  "gps_location": {"lat": 51.4545, "lon": -2.5879},
  "ip_location": {"lat": 51.5072, "lon": -0.1276},
  "wifi": {"environment_changed": false},
  "sensor_state": "stationary",
  "trajectory": [
    {"lat": 51.4545, "lon": -2.5879, "timestamp_s": 1000},
    {"lat": 51.5072, "lon": -0.1276, "timestamp_s": 1005}
  ]
}
```

风险分区间为 0–29 常规监测、30–59 增加采样、60–79 重新验证、80–100 拒绝位置敏感操作。IP 与 GPS 偏差只加少量分，Wi-Fi 只上传环境摘要，不上传原始 BSSID。

## 当前边界

- `demo_client.py` 发送的是合成数据；本项目还没有 Android 采集端。
- `integrity.verified` 不能由客户端自行声明后直接信任。正式接入时，Android 客户端需要申请 Play Integrity token，后端向 Google 解码/校验 token，再从校验结果提取 verdict。当前服务仅为了本地演示评分规则。
- Root、Hook、模拟器、IP 归属地和 Wi-Fi 变化都存在合法场景与误报可能，分数只能支持风险处置，不能单信某个字段作永久封禁依据。
- 本地服务只绑定 `127.0.0.1`，适合演示，不应直接暴露到公网。生产环境还需认证、TLS、速率限制、数据留存策略和模型阈值验证。
