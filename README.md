# jstock

A 股股票数据查询工具，统一封装雪球、同花顺数据源，支持持仓管理。

## 特性

- 行情查询 (实时价格、涨跌幅、成交量等)
- K 线数据 (含换手率、流通股本)
- 分红数据
- 股本变动
- 持仓管理 (自动计算盈亏)

## 安装

```bash
uv pip install -e .
```

## 快速开始

### CLI

```bash
# 行情查询
jstock quote 601398                              # 行情
jstock kline 601398 --start 2026-01-01          # K线
jstock bonus 601398                              # 分红
jstock shares 601398                             # 股本

# 持仓管理
jstock position save 601398 --volume 1000 --cost 5.5    # 保存持仓
jstock position list                                    # 持仓列表
jstock position list --type etf                         # 只查 ETF
jstock position get 601398                              # 持仓详情
jstock position delete 601398                           # 删除持仓
jstock position portfolio                               # 持仓汇总
```

### Python API

```python
from jstock import quote, kline, bonus, shares
from jstock import position_save, position_get, position_list, position_delete, portfolio_summary

# 行情查询
q = quote("601398")
k = kline("601398", start="2026-01-01")
b = bonus("601398")
s = shares("601398")

# 持仓管理
position_save("601398", volume=1000, cost_price=5.5, name="工商银行", type="stock")
positions = position_list()     # 含实时盈亏
pos = position_get("601398")
summary = portfolio_summary()    # 汇总
position_delete("601398")
```

## 数据源

| 功能 | 数据源 |
|-----|-------|
| 行情/分红/股本 | 雪球 |
| K 线 | 同花顺 |
| 持仓 | SQLite (~/.jstock/db/positions.db) |

## 返回格式

所有 CLI 命令返回 JSON:

```json
{"code": 0, "data": {...}}
{"code": 1, "message": "错误信息"}
```

### 行情数据

```json
{
  "symbol": "601398",
  "name": "工商银行",
  "current": 7.63,
  "percent": 1.23,
  "volume": 1234567,
  "amount": 98765432.10
}
```

### K 线数据

```json
{
  "symbol": "601398",
  "period": "1d",
  "records": [
    {
      "date": "2026-01-01",
      "open": 5.50,
      "close": 5.60,
      "high": 5.70,
      "low": 5.45,
      "volume": 1234567,
      "turnover": 0.85
    }
  ]
}
```

## 项目结构

```
jstock/
├── __init__.py           # 包导出
├── config.py             # 配置 (User-Agent、数据库路径)
├── models.py             # 数据模型 (Quote, Kline, Bonus, Position)
├── model_db.py           # 数据库实体 (DBPosition)
├── stock_api.py          # 统一 API 门面
├── stock_ths.py          # 同花顺客户端
├── stock_xq.py           # 雪球客户端
├── stock_db.py           # 持仓数据库
└── stock_positions.py    # 持仓 API

cli/
└── __main__.py           # CLI 入口

tests/
├── test_api.py           # API 测试
└── test_db.py            # 持仓数据库测试

skills/
└── jstock/
    └── SKILL.md          # AI Agent 技能说明
```

## 开发

```bash
# 安装依赖
uv pip install -e .

# 运行测试
uv run pytest tests/

# 代码格式
uv run black jstock/ cli/ tests/
uv run ruff check jstock/ cli/ tests/
```
