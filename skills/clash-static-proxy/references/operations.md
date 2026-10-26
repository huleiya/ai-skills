# 执行说明

## 变换 helper

需要 Node.js；helper 无第三方依赖。YAML 读写另外使用当前环境可用的 `yaml`、`js-yaml` 或 Python PyYAML。不要把 motu 项目的 node_modules 路径硬编码进技能。未找到 YAML 解析器时先发现运行时/依赖，不能用全文件正则修改复杂 YAML。

```js
const { transform, buildEnhancer } = require('/技能目录/scripts/transform.cjs');
const entries = [{
  node: { type: 'socks5', name: '住宅代理示例', server: '192.0.2.10',
          port: 1080, username: 'example-user', password: 'example-password' },
  preferred: '美国示例节点',
  direct: false
}];
const candidate = transform(parsedRuntimeConfig, entries);
const persistentScript = buildEnhancer(originalProfileScript, entries);
```

示例仅用保留地址和假凭据。真实输入只留在私有配置目录，勿复制进技能源码。`transform` 不改输入对象；`buildEnhancer` 保留原 main 并合并受管理节点。未来订阅删掉旧首选上游时，选择剩余物理节点的第一个；执行当次应从实时选择确认上游并报告变化。

对 `persistentScript` 在 Node `vm` 或等效 JS 环境模拟调用 `main`，比较其输出与预期。原脚本若依赖 Clash 特有 API 或异步行为，不用不兼容的模拟结果覆盖配置；在应用支持的环境验证。不要从技能执行任意下载脚本。

## Mihomo 本地控制

Node 原生 `http.request` 支持 Windows 命名管道：

```js
const options = {
  socketPath: runtime['external-controller-pipe'],
  method: 'GET', path: '/proxies',
  headers: { Authorization: 'Bearer ' + runtime.secret }
};
```

请求必须设置超时（例如 10 秒）、处理非 2xx 状态、网络错误和 JSON 解析失败。没有管道则尝试实际配置的回环 HTTP 控制地址。不要打印完整请求头或运行配置。

- `GET /proxies`：返回 `proxies[组名].all` 与 `.now`。
- `PUT /configs`：请求体 `{"path":"配置绝对路径"}`；重载当前生效配置，非选择订阅的 API。
- `PUT /proxies/${encodeURIComponent(groupName)}`：请求体 `{"name":"节点名"}`。

PUT JSON 需设置 `Content-Type: application/json`，`Content-Length` 用 `Buffer.byteLength(body)`，不能使用中文字符串字符数。

## 断言与回滚

### 服务模式下的重载

配置里的管道名可能指向未启动的 sidecar。连接返回 `ENOENT` 时，枚举实际命名管道并确认对应的用户/内核实例，用 `GET /proxies` 核对；不要硬编码管道名或用户哈希。

若 `PUT /configs` 使用文件路径返回 `path is not subpath of home directory or SAFE_PATHS`，改用同一已验证配置文本的 JSON `{ "payload": "完整 YAML 文本" }` 重载。无需修改 SAFE_PATHS 或受保护服务目录；不要打印带凭据的 payload。原有备份、有限重试和失败回滚规则仍适用。

### UDP 持久化验证

`transform` 对未指定 `udp` 的 SOCKS5 节点默认设置 `true`，保留显式 `false`，不为 HTTP 节点添加字段。仅调整现有节点参数时，不调用会重建组成员的全组变换；在原节点和受管理 entries 中更新字段即可。用原始订阅与相关增强步骤模拟重新生成，确认 `udp: true` 保留且无关配置未变。重载后核验内核的 UDP 标志及原有组选择；实际 UDP 收发能力需另行验证服务端、上游和目标端口。

- 重复应用后配置完全一致；同名改端口不增加重复节点。
- 住宅节点 → 专属上游 → 无 dialer 的物理节点；主组 → 住宅节点，不能反向连回主组。
- 静态节点模式下，规则、DNS、监听地址和控制密钥不变；普通组的原始成员顺序保留，住宅节点追加在末尾。
- 备份记录每个原文件与新建文件，回滚只恢复本次修改；不得用整个配置目录的递归删除处理失败。
- 写入前记录文件 hash，写入前重新比对；配置发生并发更新则重新构造，不覆盖他人改动。
- 用户只要求生成技能时只跑隔离测试，不能重载真实代理。
