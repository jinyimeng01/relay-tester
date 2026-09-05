#!/usr/bin/env python3
"""
LLM 中转站测速工具 (通用版)
================================
测量任意 OpenAI 兼容中转端点的:
  - 每轮请求耗时 (latency)
  - 输出 tokens 数
  - tokens/second 吞吐
  - 是否遵守 max_tokens

依赖: pip install openai
用法示例:
  python benchmark.py --api-key sk-xxx --base-url https://example.com/v1 --model my-model
  python benchmark.py --api-key sk-xxx --base-url https://example.com --model m2 --rounds 5

注意:
  - base-url 可不带 /v1 (脚本自动补全)
  - 模型名带 [1M] 等后缀会自动剥离 (中转站注册名通常不带)
"""
import time
import json
import argparse
import sys
import os
from datetime import datetime

# 默认值优先从环境变量读取 (适配 Claude Code / 通用 AI 代理环境)
DEFAULT_API_KEY = os.getenv("ANTHROPIC_AUTH_TOKEN", os.getenv("OPENAI_API_KEY", ""))
DEFAULT_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", os.getenv("OPENAI_BASE_URL", ""))
DEFAULT_MODEL = os.getenv("ANTHROPIC_DEFAULT_FABLE_MODEL", os.getenv("LLM_MODEL", ""))

# 三档测试 prompt: short=看首字延迟, long=看真实吞吐
TEST_PROMPTS = [
    {"name": "short",  "content": "写一首5句的日本短诗",
     "expect_tokens": 20},
    {"name": "medium", "content": "解释一下什么是人工智能？用约200字说明",
     "expect_tokens": 50},
    {"name": "long",   "content": "详细解释Transformer神经网络架构的自注意力机制，包括其数学原理、计算复杂度以及在自然语言处理中的应用优势。请从注意力得分计算、多头注意力拼接、positional encoding等方面展开说明。",
     "expect_tokens": 300},
]

def ensure_openai():
    try:
        import openai
        return openai
    except ImportError:
        print("[提示] 未安装 openai 包, 正在安装...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "openai"])
        import openai
        return openai

def normalize_base_url(base_url: str) -> str:
    """保证 base_url 以 /v1 结尾 (OpenAI SDK 会拼接 /chat/completions)"""
    if not base_url:
        raise ValueError("--base-url 不能为空 (如 https://example.com/v1)")
    if not base_url.endswith("/v1"):
        base_url = base_url.rstrip("/") + "/v1"
    return base_url

def benchmark_model(openai, api_key, base_url, model, rounds=3, prompts=None):
    """对单个模型跑三档 prompt 测速, 返回 {prompt_name: [rounds...]}"""
    base_url = normalize_base_url(base_url)
    client = openai.OpenAI(api_key=api_key, base_url=base_url)
    full_results = {}

    for tp in (prompts or TEST_PROMPTS):
        name = tp["name"]
        print(f"\n[{name}] prompt: {tp['content'][:50]}...")
        results = []
        for i in range(rounds):
            print(f"  Round {i+1}/{rounds}...", end=" ", flush=True)
            t0 = time.time()
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": tp["content"]}],
                    max_tokens=tp["expect_tokens"],
                    temperature=0.1,
                )
                latency = time.time() - t0

                # 优先用服务端 usage (精确), 否则按字符粗估
                if getattr(resp, "usage", None) and resp.usage.completion_tokens:
                    out_tok = resp.usage.completion_tokens
                    in_tok = resp.usage.prompt_tokens
                else:
                    out_tok = len(resp.choices[0].message.content) / 0.75
                    in_tok = len(tp["content"]) / 0.75
                tok_s = out_tok / latency if latency > 0 else 0

                result = {
                    "round": i + 1,
                    "latency_s": round(latency, 3),
                    "input_tokens": int(in_tok),
                    "output_tokens": int(out_tok),
                    "tok_per_sec": round(tok_s, 1),
                    # 中转站是否无视 max_tokens (超额输出 = 猫腻信号)
                    "max_tokens_violated": bool(
                        getattr(resp, "usage", None)
                        and resp.usage.completion_tokens > tp["expect_tokens"] * 1.5
                    ),
                }
                print(f"✓ {latency:.2f}s | {out_tok} tok | {tok_s:.1f} tok/s"
                      + (" ⚠️无视max_tokens" if result["max_tokens_violated"] else ""))
            except Exception as e:
                result = {"round": i + 1, "error": str(e)}
                print(f"✗ {e}")
            results.append(result)
        full_results[name] = results
    return full_results

def print_summary(full_results):
    print("\n" + "=" * 70)
    print("汇总")
    print("=" * 70)
    for name, results in full_results.items():
        ok = [r for r in results if "error" not in r]
        if ok:
            avg_lat = sum(r["latency_s"] for r in ok) / len(ok)
            avg_out = sum(r["output_tokens"] for r in ok) / len(ok)
            avg_speed = sum(r["tok_per_sec"] for r in ok) / len(ok)
            viol = any(r.get("max_tokens_violated") for r in ok)
            print(f"[{name:8}] 均耗时 {avg_lat:.2f}s | 均输出 {avg_out:.0f} tok | "
                  f"{avg_speed:.1f} tok/s" + (" | ⚠️max_tokens被无视" if viol else ""))
        else:
            print(f"[{name:8}] 全部失败")
    # 解读提示
    print("\n解读: 短/中档速度被首字延迟(TTFT)摊薄, 无参考价值;")
    print("      真实吞吐看 long 档 (长输出) 的 tok/s。")

def main():
    p = argparse.ArgumentParser(description="LLM 中转站测速工具")
    p.add_argument("--api-key", default=DEFAULT_API_KEY, help="API key (默认读 ANTHROPIC_AUTH_TOKEN)")
    p.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL, 可不带 /v1 (默认读 ANTHROPIC_BASE_URL)")
    p.add_argument("--model", default=DEFAULT_MODEL, help="模型名 (默认读 ANTHROPIC_DEFAULT_FABLE_MODEL)")
    p.add_argument("--rounds", type=int, default=3, help="每档测试轮数 (默认3)")
    p.add_argument("--output", default="benchmark_results.json", help="结果输出文件")
    args = p.parse_args()

    if not args.api_key:
        p.error("缺少 --api-key (或设置 ANTHROPIC_AUTH_TOKEN 环境变量)")
    if not args.base_url:
        p.error("缺少 --base-url (或设置 ANTHROPIC_BASE_URL 环境变量)")
    if not args.model:
        p.error("缺少 --model")

    model = args.model.replace("[1M]", "")  # 剥离营销后缀

    print("=" * 70)
    print("LLM 中转站测速 (非流式)")
    print("=" * 70)
    print(f"Endpoint: {normalize_base_url(args.base_url)}")
    print(f"Model:    {model} (原始: {args.model})")
    print(f"API Key:  {args.api_key[:8]}...{args.api_key[-4:] if len(args.api_key) > 12 else '***'}")
    print(f"Rounds:   {args.rounds}")
    print(f"Time:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    openai = ensure_openai()
    results = benchmark_model(openai, args.api_key, args.base_url, model, args.rounds)
    print_summary(results)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "config": {"base_url": normalize_base_url(args.base_url), "model": model, "rounds": args.rounds},
            "results": results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存: {args.output}")

if __name__ == "__main__":
    main()