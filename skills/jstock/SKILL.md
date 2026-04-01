---
name: jstock
description: A股股票数据查询工具。提供行情(K线/实时)、分红、股本变动、持仓管理。自动计算换手率(成交量/流通股本)和持仓盈亏。
---

# jstock

股票数据统一 API，支持行情查询和持仓管理。

## CLI

```bash
# 行情查询
jstock quote 601398                              # 行情（实时查询，返回最新数据）
jstock kline 601398 --start 2026-01-01          # K线
jstock bonus 601398                              # 分红
jstock shares 601398                             # 股本

# 持仓管理
jstock position save 601398 --volume 1000 --cost 5.5 --buy-date 2026-01-01  # 保存持仓（带建仓时间）
jstock position list                                    # 持仓列表
jstock position list --type etf                         # 只查 ETF
jstock position get 601398                              # 持仓详情
jstock position delete 601398                           # 删除持仓
jstock position portfolio                               # 持仓汇总
```

## Python API

```python
from jstock import quote, kline, bonus, shares
from jstock import position_save, position_get, position_list, position_delete, portfolio_summary

# 行情查询
q = quote("601398")           # 行情
k = kline("601398", start="2026-01-01")  # K线（含换手率、流通股本）
b = bonus("601398")           # 分红
s = shares("601398")          # 股本变动

# 持仓管理
position_save("601398", volume=1000, cost_price=5.5, name="工商银行", type="stock", buy_date="2026-01-01")
position_save("510300", volume=500, cost_price=3.8, type="etf")
positions = position_list()   # 含实时盈亏
pos = position_get("601398")  # 单个持仓
position_delete("601398")     # 删除持仓
summary = portfolio_summary()  # 汇总
```

## 返回格式

### 行情数据
- **quote**: `{symbol, name, current, change, percent, volume(手), amount(元), pe_ttm, pb, market_cap...}`
- **kline**: `{symbol, period, records: [{date, open, close, high, low, volume(股), amount(元), float_shares(股), turnover(%), change, percent}]}`
- **bonus**: `{symbol, records: [{year, equity_date, ex_dividend_date, dividend_date, plan}]}`
- **shares**: `{symbol, records: [{date, total(股), float_a(股), float_h(股), reason}]}`

### 持仓数据
- **position**: `{symbol, name, type(stock/etf/fund), volume(股), cost_price, buy_date, cost_amount, current_price, market_value, profit, profit_rate}`
- **portfolio_summary**: `{count, total_cost, total_market_value, total_profit, profit_rate, positions[]}`

## 数据源
- quote/bonus/shares: 雪球
- kline: 同花顺
- 持仓: SQLite (~/.jstock/db/positions.db)

## CLI 返回格式
所有命令返回 JSON：
```json
{"code": 0, "data": {...}}
{"code": 1, "message": "错误信息"}
```

## 注意事项

1. **删除持仓前**：必须先查询并展示持仓详情，等待用户确认后再执行删除命令
2. **数据来源**：行情数据来自雪球/同花顺
3. **持仓存储**：本地 SQLite 数据库 (~/.jstock/db/positions.db)
4. **股/手换算**：1手 = 100股。quote的volume是手，kline/持仓/shares的volume都是股
5. **quote 必须实时查询**：每次查询都要向数据源发起请求，返回最新行情数据，不要使用之前查询过的缓存数据
