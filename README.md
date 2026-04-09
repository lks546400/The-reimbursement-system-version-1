# The-reimbursement-system-version-1

面向“飞书里直接发票据图就能识别”的最小可用版本。

## 5分钟接入（先跑通飞书，不用腾讯云）

### 第1步：准备配置

1. 复制配置模板：

```bash
cp .env.example .env
```

2. 在 `.env` 里先填这 4 个值（必填）：

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_VERIFICATION_TOKEN`
- `OCR_MODE=mock`

> `mock` 模式下，不需要腾讯云密钥，先确保飞书链路跑通。

### 第2步：一键启动

```bash
bash scripts/start.sh
```

脚本会自动做：
- 创建虚拟环境
- 安装依赖
- 检查配置是否缺失
- 启动服务（`http://0.0.0.0:8000`）

### 第3步：飞书后台最少配置

在飞书开放平台应用里：

1. 开启 **事件订阅**
2. 请求地址填：`https://你的公网域名/feishu/events`
3. 订阅事件：`im.message.receive_v1`
4. 权限至少勾选：
   - 接收消息
   - 读取消息资源（图片）
   - 发送消息
5. Verification Token 与 `.env` 中 `FEISHU_VERIFICATION_TOKEN` 保持一致

## 本地联调（不依赖飞书）

### 健康检查

```bash
curl http://127.0.0.1:8000/health
```

### 模拟上传图片识别

```bash
curl -X POST "http://127.0.0.1:8000/debug/mock-image" \
  -F "file=@/你的测试图片.jpg"
```

## 切换到腾讯云 OCR（后续）

当你准备好腾讯云账号后，把 `.env` 改成：

```env
OCR_MODE=tencent
TENCENT_SECRET_ID=你的SecretId
TENCENT_SECRET_KEY=你的SecretKey
TENCENT_REGION=ap-guangzhou
```

## 运行产物

- 归档图片：`storage/{年}/{月}/{分类}/...jpg`
- 明细记录：`data/reimbursement_records.csv`

## 当前能力

- 飞书收到图片后自动下载
- `mock/tencent` 两种 OCR 模式
- 自动提取：日期 / 金额 / 商户 / 分类
- 自动归档并写入 CSV
- 在飞书回复识别摘要

## 常见问题

- 提示“缺少配置” → 运行 `python scripts/check_env.py` 查看缺哪项
- 飞书收不到回调 → 检查公网地址是否可访问 `/feishu/events`
- 图片处理失败 → 先确认飞书机器人权限、再确认 OCR 模式配置
