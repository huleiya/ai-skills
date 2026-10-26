# 加密 DNS 分流

用于用户明确要求加密 DNS、DNS 泄漏修复或参考另一个订阅的 DNS 配置。与静态节点变更共用定位、备份、有限重试和回滚流程；只改指定订阅，不动其他订阅或路由器。

## 先确认实际配置与参考层

1. 从 `profiles.yaml.current` 定位目标及 `option.merge/script`；参考订阅也同时读源 YAML、专属 merge 和 script。源 YAML 的 DNS 不等于最终 DNS，例如 WgetCloud 的海外 DNS 分流曾放在专属 merge 中。
2. 检查 Clash 的全局/订阅 DNS 覆盖开关和 `dns_config.yaml`，确认应用生成顺序；不要为了一个订阅开启会影响所有订阅的全局覆盖。
3. 从实际控制 API 检查代理/组存在、选择链和可用性。海外 DNS 出口优先沿用用户指定或参考配置中已验证的出口；不要默认所有设备都有 `Todaylab`。出口是住宅链式节点时，检查其独立上游不回指主选择组。
4. 识别 `proxy-server-nameserver` 和 `proxy-server-nameserver-policy` 的机场专用解析器。它们可能返回公共解析器得不到的有效节点入口，必须保留专用 URL 和参数；不得打印含账号标识的路径、复制到技能或 Git。测试节点时也必须保留这些解析器，不能仅加载 `proxies` 后统一换成公共 DNS。

## 推荐参数

国内 DoH 直连，海外 DoH 经指定代理，引导 DNS 也加密。`海外DNS代理` 是占位符，替换为实时确认的节点/组名后才能落盘；其中的 `#` 后缀显式选择出口，不能把代理名当网卡名使用。模板中的 IP 型 DoH 避免解析 DNS 服务器域名时产生明文引导查询。

```yaml
dns:
  enable: true
  ipv6: false
  enhanced-mode: fake-ip
  respect-rules: true
  prefer-h3: false
  default-nameserver:
    - https://223.5.5.5/dns-query#DIRECT
    - https://223.6.6.6/dns-query#DIRECT
  nameserver-policy:
    'geosite:cn':
      - https://223.5.5.5/dns-query#DIRECT
      - https://223.6.6.6/dns-query#DIRECT
  nameserver:
    - https://1.1.1.1/dns-query#海外DNS代理
    - https://8.8.8.8/dns-query#海外DNS代理
  direct-nameserver: []
  fallback: []
```

- 必须保留原有 `proxy-server-nameserver` 专用加密端点；无指定出口时按实际需要补 `#DIRECT`，保留已有显式出口。仅在订阅没有专用解析需求时，才可采用国内 DoH 作为节点解析器。专用解析 URL、密钥或参数只留在用户私有 Clash 配置内。
- 保留原有 `nameserver-policy` 的其他用途，检查有无更具体的明文解析规则；国内 `geosite:cn` 必须有可用的本地 geosite 数据。未提供域名集时不要臆造集合名或 silently 改成全部国内解析。
- 国内 DoH 和海外 DoH 分别显式指定出口，避免被业务规则意外送往住宅节点或直连。`respect-rules: true` 应同时配置节点解析器，防止“先建立代理才能解析代理节点”的循环。
- `direct-nameserver: []` 让直连出口继承域名策略；不要额外给所有 DIRECT 域名强制配置国内解析器，否则非国内域名仍可能被国内解析。移除旧的明文 `nameserver/fallback`，不添加失败时转明文或 DIRECT 的备用路径。
- 保留目标原有 fake-ip 网段、监听地址、局域网/时间/音视频例外；可合并参考订阅过滤项并去重。不要因复制参考 DNS 改变节点、业务规则、控制密钥或当前组选择。
- `dns.ipv6: false` 与参考配置一致，用于不需要 AAAA 的场景；不是禁用系统 IPv6 的替代方法。保留用户显式 IPv6 需求并验证 TUN 捕获范围，别把返回空 AAAA 宣称为系统所有 IPv6 流量都已受控。
- 已启用 TUN 时检查现有 `dns-hijack` 和 DNS 流量是否被捕获。普通 UDP/TCP 53 与浏览器独立 DoH 是不同路径；仅系统代理模式不能保证系统 DNS 被接管。配置改动不自动扩展为路由器或浏览器设置变更。

## 持久化与验证

1. 在内存生成候选 DNS。使用 YAML 解析器，保留无关字段；有参考 merge 时以它的实际分流意图为准，不直接照抄参考源里的明文 DNS。
2. 在目标专属 merge 中持久化通用分流键；不要把专用解析凭据固定到通用技能或公共模板。原始订阅可同步当前 DNS，但不能只改下载文件——下一次更新会覆盖。
3. 需要强制覆盖多层 DNS 合并残留时，给原专属 `main` 追加有起止标记的 DNS wrapper：先调用原 main，再更新 DNS；保留原逻辑和专用解析器。重复执行只替换自己的区块。脚本中只固化通用分流参数，专用节点解析器从新的 `config.dns` 获取，防止订阅更新凭据后继续使用旧值。
4. 模拟原始订阅与专属增强链，检查新旧输出仅 DNS 发生预期变化、重复应用幂等、海外出口引用有效。应用若在脚本之后覆盖 DNS，也应处理该目标订阅的对应覆盖层；无法确认时如实记录生成验证限制。
5. 用当前 Mihomo `-t` 校验，重新确认目标 current 和文件 hash，再备份、写源/增强/当前运行配置。热重载后核验组选择没有改变；服务模式管道及 payload 重载见 [执行说明](operations.md#服务模式下的重载)。
6. 用本地控制 API 的 `/dns/query?name=<域名>&type=A` 对国内域名和非国内域名各做一次查询，通过临时 debug 日志检查实际 DNS 上游及 `using DIRECT` / `using <海外出口>`。可用随机子域名避免缓存；NXDOMAIN 是正常有效响应，不能把不存在的子域名当 DNS 故障。WebSocket 日志订阅完成后关闭；不得输出其他用户活动或私有解析器完整路径。
7. 使用目标节点再测一个用户关心的网站，分别报告配置校验、持久化模拟、实时 DNS 路由和实际节点结果。`-t` 成功不证明节点可用；DNS 路由验证也不等于全设备“零泄漏”。只有经过授权并实测泄漏检测/抓包后，才可报告对应范围内无泄漏。

## 性能选择

用户以减少明文查询和 DNS 出口分流为目标时，国内也默认用 DoH。明文 UDP 少了 TLS 握手，首次查询可能更快；DoH 复用 HTTP/2 连接和缓存后可减少这部分开销，具体差距应在同一网络、相同查询和缓存条件下测量。不要拿冷 DoH 与热 UDP 比较，也不要为了未经实测的性能差异自行加入明文 fallback。DoH 加密的是传输，所选解析服务仍能看到查询。

参数依据：[Mihomo DNS 文档](https://wiki.metacubex.one/config/dns/)，重点参阅 `default-nameserver`、`nameserver-policy`、`proxy-server-nameserver` 与 DNS 指定代理的附加参数。
