# jstock 开发指南

A 股股票数据查询工具，统一封装雪球、同花顺数据源。

## 项目结构

```
jstock/
├── AGENTS.md         # 本文件，开发指南
├── README.md         # 项目说明
├── pyproject.toml    # 项目配置
├── uv.lock           # 依赖锁定
├── jstock/           # 核心包
│   ├── __init__.py   # 包导出 (quote, kline, bonus, shares)
│   ├── config.py     # 配置 (User-Agent 等)
│   ├── models.py     # 数据模型 (Quote, Kline, Bonus, Shares)
│   ├── stock_api.py  # 统一 API 门面
│   ├── stock_ths.py  # 同花顺客户端 (K 线数据)
│   └── stock_xq.py   # 雪球客户端 (行情/分红/股本)
├── cli/              # 命令行入口
│   ├── __init__.py
│   └── __main__.py   # CLI 实现 (Typer)
├── skills/           # 技能定义 (AI Agent 使用)
│   └── jstock/
│       └── SKILL.md  # jstock 技能说明
└── tests/            # 测试
    ├── test_api.py   # API 测试
    ├── test_ths.py   # 同花顺测试
    └── test_xq.py    # 雪球测试
```

## 开发环境

```bash
# 安装依赖
uv pip install -e .

# 运行测试
uv run pytest tests/

# 代码格式
uv run black jstock/ cli/ tests/
uv run ruff check jstock/ cli/ tests/
```

## 核心 API

### Python API

```python
from jstock import quote, kline, bonus, shares

# 行情
q = quote("601398")
print(f"{q.name}: {q.current} ({q.percent:+.2f}%)")

# K 线（含换手率、流通股本）
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

### CLI

```bash
jstock quote 601398                              # 行情
jstock kline 601398 --start 2026-01-01          # K 线
jstock bonus 601398                              # 分红
jstock shares 601398                             # 股本
```

## 数据模型

### Quote (行情)
- `symbol`: 股票代码
- `name`: 股票名称
- `current`: 当前价
- `change`: 涨跌额
- `percent`: 涨跌幅
- `volume`: 成交量 (手)
- `amount`: 成交额 (元)
- `pe_ttm`: 市盈率 TTM
- `pb`: 市净率
- `market_cap`: 总市值

### Kline (K 线)
- `symbol`: 股票代码
- `period`: 周期 (1d/1w/1m)
- `records`: K 线记录列表
  - `date`: 日期
  - `open/close/high/low`: 开高低收
  - `volume`: 成交量 (手)
  - `amount`: 成交额 (元)
  - `float_shares`: 流通股本 (股)
  - `turnover`: 换手率 (%)
  - `change/percent`: 涨跌额/幅

### Bonus (分红)
- `symbol`: 股票代码
- `records`: 分红记录列表
  - `year`: 年份
  - `equity_date`: 股权登记日
  - `ex_dividend_date`: 除权除息日
  - `dividend_date`: 红利发放日
  - `plan`: 分红方案

### Shares (股本)
- `symbol`: 股票代码
- `records`: 股本记录列表
  - `date`: 日期
  - `total`: 总股本 (股)
  - `float_a`: 流通 A 股 (股)
  - `float_h`: 流通 H 股 (股)
  - `reason`: 变动原因

## 数据源

| 功能 | 数据源 | 文件 |
|-----|-------|------|
| quote | 雪球 | stock_xq.py |
| kline | 同花顺 | stock_ths.py |
| bonus | 雪球 | stock_xq.py |
| shares | 雪球 | stock_xq.py |

## 开发指南

### 添加新功能

1. 在 `jstock/models.py` 添加数据模型
2. 在对应客户端文件 (`stock_xq.py` 或 `stock_ths.py`) 实现数据获取
3. 在 `jstock/stock_api.py` 添加统一 API 入口
4. 在 `jstock/__init__.py` 导出新函数
5. 在 `cli/__main__.py` 添加 CLI 命令
6. 在 `tests/` 添加测试

### 代码风格

- 使用 Type Hints 标注类型
- 使用 dataclass 定义数据模型
- 异常处理：网络请求失败返回空结果或抛出明确异常
- 日志：使用 `logging` 模块

### 测试

```bash
# 运行所有测试
uv run pytest tests/

# 运行单个测试文件
uv run pytest tests/test_api.py -v

# 运行单个测试
uv run pytest tests/test_api.py::test_quote -v
```

## 常见问题

### 股票代码格式
- 支持 6 位代码 (如 `601398`)
- 支持带市场后缀 (如 `SH601398`, `SZ000001`)

### 换手率计算
换手率 = 成交量 / 流通股本 × 100%
- 成交量单位：手 (1 手=100 股)
- 流通股本单位：股

### 数据源限制
- 雪球：需要有效的 User-Agent
- 同花顺：K 线数据有频率限制
