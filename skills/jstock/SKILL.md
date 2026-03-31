---
name: jstock
description: A股股票数据查询工具。提供行情(K线/实时)、分红、股本变动等数据。自动计算换手率(成交量/流通股本)。
---

# jstock

股票数据统一 API，K线换手率基于流通股本自动计算。

## CLI
```bash
jstock quote 601398
jstock kline 601398 --start 2026-01-01 --end 2026-03-31
jstock bonus 601398
jstock shares 601398
```

## Python API
```python
from jstock import quote, kline, bonus, shares

q = quote("601398")           # 行情
k = kline("601398", start="2026-01-01")  # K线（含换手率、流通股本）
b = bonus("601398")           # 分红
s = shares("601398")          # 股本变动
```

## 返回格式
- **quote**: `{symbol, name, current, change, percent, volume(手), amount(元), pe_ttm, pb, market_cap...}`
- **kline**: `{symbol, period, records: [{date, open, close, high, low, volume(手), amount(元), float_shares(股), turnover(%), change, percent}]}`
- **bonus**: `{symbol, records: [{year, equity_date, ex_dividend_date, dividend_date, plan}]}`
- **shares**: `{symbol, records: [{date, total(股), float_a(股), float_h(股), reason}]}`

## 数据源
- quote/bonus/shares: 雪球
- kline: 同花顺
