# V2Board 用户端前端

## 运行时配置

前端会在浏览器运行时读取 `public/config.json`，用于配置后端 API 地址和落地页页脚内容。这个文件会以 `/config.json` 暴露，部署后修改该文件即可调整配置，不需要重新构建前端。

```json
{
  "apiBaseUrl": "https://api.example.com",
  "footer": {
    "description": "自定义页脚描述",
    "copyright": "Copyright © 2026 Example. All rights reserved.",
    "seoKeywords": ["VPN", "代理节点", "订阅节点", "套餐流量"],
    "links": [
      {
        "label": "官方网站",
        "href": "https://example.com"
      }
    ],
    "contacts": [
      {
        "label": "Telegram",
        "href": "https://t.me/example"
      },
      {
        "label": "邮箱",
        "text": "support@example.com"
      }
    ]
  }
}
```

`apiBaseUrl` 留空时，请求会使用当前前端域名作为同源 API 地址。
