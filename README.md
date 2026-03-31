# jstock

A 股股票数据查询工具，统一封装雪球、同花顺数据源。

## 安装

```bash
uv pip install -e .
```

## CLI

```bash
jstock quote 601398                              # 行情
jstock kline 601398 --start 2026-01-01          # K线
jstock bonus 601398                              # 分红
jstock shares 601398                             # 股本
```

## Python API

```python
from jstock import quote, kline, bonus, shares

# 行情
q = quote("601398")
print(f"{q.name}: {q.current} ({q.percent:+.2f}%)")

# K线（含换手率、流通股本）
k = kline("601398", start="2026-01-01")
for r in k.records:
    print(f"{r.date} close={r.close} turnover={r.turnover}%")

# 分红
b = bonus("601398")
print(b.records[0].plan)

# 股本
s = shares("601398")
print(s.records[0].total)
```

## 数据源

| 功能 | 数据源 |
|-----|-------|
| quote | 雪球 |
| kline | 同花顺 |
| bonus | 雪球 |
| shares | 雪球 |

## 项目结构

```
jstock/
├── __init__.py       # 包导出
├── config.py         # 配置
├── models.py         # 数据模型
├── stock_api.py      # 统一API（门面）
├── stock_ths.py      # 同花顺客户端
└── stock_xq.py       # 雪球客户端

cli/
└── __main__.py       # CLI入口

tests/
├── test_api.py
├── test_ths.py
└── test_xq.py
```

## 开发

```bash
# 测试
uv run pytest tests/

# 代码格式
uv run black jstock/ cli/ tests/
uv run ruff check jstock/ cli/ tests/
```
