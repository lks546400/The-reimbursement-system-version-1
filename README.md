# The-reimbursement-system-version-1

首版目标：飞书上传图片后，自动调用腾讯云 OCR 识别并回传结果。

## 1. 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. 配置环境变量

复制 `.env.example` 为 `.env`，填写：

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_VERIFICATION_TOKEN`
- `TENCENT_SECRET_ID`
- `TENCENT_SECRET_KEY`
- `TENCENT_REGION`（默认 `ap-guangzhou`）

## 3. 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 4. 飞书事件订阅

- 事件回调地址：`POST /feishu/events`
- 订阅事件：`im.message.receive_v1`
- 机器人权限至少包含：接收消息、读取消息资源、发送消息

## 5. 运行结果

- 图片归档目录：`storage/{年}/{月}/{分类}`
- 记录文件：`data/reimbursement_records.csv`
- 机器人会回复识别摘要（日期/金额/商户/分类/归档路径）
