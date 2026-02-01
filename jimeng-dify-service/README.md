# Jimeng Dify Service

提供一个可部署的 HTTP 服务，封装即梦图片生成，并以 `image_url` 形式返回给 Dify。

## 环境变量

- `JIMENG_API_TOKEN`：必填，即梦 sessionid/refresh_token
- `PORT`：可选，默认 `8080`
- `ALLOW_ORIGINS`：可选，CORS 允许来源。默认 `*`，也可用逗号分隔域名列表
- `PUBLIC_BASE_URL`：可选，用于把 `return_type=proxy` 返回的地址拼成完整公网 URL（例如 `https://xxx.railway.app`）
- `ENABLE_IMAGE_PROXY`：可选，是否启用 `/image` 代理接口（默认关闭）
- `PROXY_ALLOW_HOSTS`：可选，启用代理后允许的目标域名白名单（逗号分隔）

## 接口

- `GET /health`
- `POST /generate`
  - 请求示例
    ```json
    {
      "prompt": "一只戴墨镜的橘猫，写实摄影风格",
      "width": 1024,
      "height": 1024,
      "sample_strength": 0.5,
      "negative_prompt": "",
      "model": "jimeng-2.1",
      "return_type": "url"
    }
    ```
  - `return_type` 可选值
    - `url`：返回即梦图片直链 `image_url`
    - `proxy`：返回本服务的 `/image?url=...` 代理地址（需要开启 `ENABLE_IMAGE_PROXY`，并建议配置 `PROXY_ALLOW_HOSTS`）
    - `base64`：返回 `image_base64`（体积大，不推荐在 Dify 里默认使用）

- `GET /image?url=...`：图片直链代理下载

## Dify 使用方式

在工作流里用 “HTTP Request” 节点：

- Method: `POST`
- URL: `https://<你的服务域名>/generate`
- Body (JSON): `{"prompt":"{{input}}","return_type":"url"}`

把响应里的 `image_url` 作为后续节点的图片 URL 使用。
