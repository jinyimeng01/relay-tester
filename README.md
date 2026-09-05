# 🔬 LLM 中转站测试工具包 (relay-tester)

> 测试任意 **OpenAI 兼容中转站**的速度与"纯血度"——识别型号虚标、上下文造假、档位倒挂、身份伪装等猫腻。
> 2026-09-05 针对 `1.19848845.xyz` 的实测案例见 [`report_案例_1.19848845.xyz.md`](report_案例_1.19848845.xyz.md)。

## 目录结构

```
relay-tester/
├── README.md                          # 本文档(用法+方法论)
├── benchmark.py                       # 测速: 延迟 / tok/s / max_tokens 遵守
├── probe_suite.py                     # 深度指纹: 身份拆解 6 连测
├── report_案例_1.19848845.xyz.md      # 完整实测案例报告(含结论方法论)
└── requirements.txt                   # openai, pillow(可选)
```

## 快速开始

```bash
pip install openai            # 必须
pip install pillow            # 可选, 视觉验证用

# 1) 测速 (哪档快)
python benchmark.py --api-key sk-xxx --base-url https://your-relay.com/v1 \
                    --model your-model --rounds 3

# 2) 深度指纹 (是什么底模, 有没有猫腻)
python probe_suite.py --api-key sk-xxx --base-url https://your-relay.com/v1 \
                      --models model-a,model-b,model-c
```

也可以不传参数, 直接复用环境变量 `ANTHROPIC_AUTH_TOKEN` / `ANTHROPIC_BASE_URL` / `ANTHROPIC_DEFAULT_FABLE_MODEL`。

### 通用参数

| 参数 | 说明 |
|------|------|
| `--api-key` | API 密钥 |
| `--base-url` | 端点地址, **可不带 `/v1`**(脚本自动补全) |
| `--model(s)` | 模型名, 自动剥离 `[1M]` 等营销后缀 |
| `--rounds` | 每档测速轮数 (默认 3) |
| `--output` | JSON 结果文件 |

---

## 方法论: 怎么测才准

### 速度 (benchmark.py)

| 档位 | 作用 | 注意 |
|------|------|------|
| short / medium (短输出) | 看首字延迟 TTFT | **数值虚低, 无吞吐参考价值** |
| long (长输出 300+ tok) | 看真实吞吐 | **唯一可信的 tok/s 指标** |

- 顺带检测 **max_tokens 是否被遵守**: 超额输出 = 中转层(如 new-api)有手脚
- 要更精确的流式吞吐, 可自行加 `stream=True`, 用首 chunk 时间算 TTFT

### 纯血度 (probe_suite.py) — 6 连测

| # | 测试 | 抓什么猫腻 |
|---|------|-----------|
| 1 | **身份指纹** 5 问 | 自称、知识截止、上下文、对官方 API 的认知、是否会被系统提示洗脑 |
| 2 | **Tokenizer 指纹** | 同一文本的 prompt_tokens 计数。**同家族模型 tokenizer 同源**; 差 30%+ = 不同底模 |
| 3 | **能力梯度** (同一道 DP 难题) | 各档正确率; 最贵档答错 = **档位倒挂** |
| 4 | **System prompt 泄漏** | 诱导输出注入的提示词, 看中转商给它套了什么身份 |
| 5 | **视觉验证** (PIL 生成测试图) | 自称纯文本模型却能看图 → 图像被分流/伪视觉 |
| 6 | **交叉相似性** | 同问同参温度 0 对比; 高度重合 = 不同名字同后端(套皮) |

### 指纹判读速查表

| 指纹 | DeepSeek V3 | DeepSeek R1 | Qwen / GLM / Kimi | 备注 |
|------|:---:|:---:|:---:|------|
| 知识截止 | 2024-06/07 | 2024-07 | 各不同 (Qwen3≈2025) | **最强指纹**, 套不了假 |
| 自称 | DeepSeek-V3 | DeepSeek-R1 | 各自 | 会被 system prompt 伪造 |
| 上下文 | 128K | 128K | 视型号 | 虚标重灾区 (`[1M]` 多为假) |
| usage.reasoning_tokens | 无/0 | 有 | 视模型 | R1 系 API 结构特征 |
| 视觉 | ❌ 纯文本 | ❌ 纯文本 | 看型号 | R1/V3 能看图 = 必有分流 |

> ⚠️ 知识截止会随模型更新变化, 表中数值基于 2024-2025 年公开模型。**核心逻辑不变: 同系列模型指纹必然一致, 不一致就是拼装。**

---

## 常见猫腻清单 (实测验证过的)

1. **型号虚标**: 真实官方 API 不存在 "v4" 等新名字, 拿老模型贴新版本号溢价卖
2. **上下文造假**: 宣传 `[1M]`, 实测 128K (官方旧模型原值)
3. **档位收费与能力倒挂**: 最贵档能力反而最差 (见案例报告)
4. **身份系统伪装**: 注入 "你是 DeepSeek" 提示词, 问不出真实底模
5. **图像请求分流**: 纯文本模型也能"看图" = 图片被第三方视觉管道处理 ⚠️ 隐私风险
6. **中转层小动作**: 无视 max_tokens、剥离 reasoning_content (R1 思考过程被吃掉)
7. **报错指纹**: 报错含 `new_api_error` = 后端是 new-api/one-api 中转框架

## 安全提示

- ⚠️ **密钥不要硬编码进脚本** (本工具包默认从环境变量读)
- ⚠️ 野鸡中转无法保证数据只用官方 API; 敏感图片/代码/文档慎发
- ✅ 真要 DeepSeek: 官方 `platform.deepseek.com` (`deepseek-chat` / `deepseek-reasoner`) 便宜且无伪装

## 案例速览 (2026-09-05 实测)

三个 "deepseek-v4-*" 名字实为三个不同时代底模 (Tokenizer 899/308/587), 档位能力倒挂 (pro 答错 DP 题), `[1M]` 为假, 详见案例报告。

## 开源与引用

- License: MIT（见 `LICENSE`）
- 配套长文（vault）：`2文章研究/00-进行中/LLM中转站指纹检测完全指南/index.md`
- 发布到 GitHub 后，把仓库 URL 写进该文附录 A 的占位符 `https://github.com/<user>/relay-tester`
- 不要提交 `.env`、`probe_report.json`、未打码的密钥；案例报告里的 key 必须打码

本工具只对你已经持有合法 API 密钥的端点发对话补全请求，不是端口扫描器，也不是未授权测试框架。
