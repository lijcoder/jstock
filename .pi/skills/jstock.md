# jstock 股票数据查询工具

股票数据统一 API，支持行情、K线、分红、股本等数据查询。

## 环境准备

```bash
cd /Users/lijie/work/ai/jstock
```

## CLI 用法

```bash
# 行情
python jstock quote 601398

# K线
python jstock kline 601398 --start 2026-01-01 --end 2026-03-31

# 分红
python jstock bonus 601398

# 股本
python jstock shares 601398
```

## Python API

```python
from stock import quote, kline, bonus, shares, StockAPI

# 行情
q = quote("601398")
print(f"{q.name}: {q.current} ({q.percent:+.2f}%)")

# K线（含换手率、流通股本）
k = kline("601398", start="2026-01-01", end="2026-03-31")
for r in k.records:
    print(f"{r.timestamp} close={r.close} turnover={r.turnover}%")

# 分红
b = bonus("601398")
for r in b.records:
    print(f"{r.dividend_year}: {r.plan_explain}")

# 股本
s = shares("601398")
for r in s.records:
    print(f"{r.chg_date}: {r.total_shares}股")
```

## 数据源

| 功能 | 数据源 |
|-----|-------|
| quote | 雪球 |
| kline | 同花顺 |
| bonus | 雪球 |
| shares | 雪球 |

## 返回字段

### quote
```json
{
  "symbol": "SH601398",
  "name": "工商银行",
  "current": 7.64,
  "change": 0.07,
  "percent": 0.92,
  "open": 7.57,
  "high": 7.69,
  "low": 7.55,
  "volume": 362785776,
  "amount": 2768934295.53,
  "turnover_rate": 0.13,
  "pe_ttm": 7.388,
  "pb": 0.705,
  "market_cap": 2722943804160.0
}
```

### kline
```json
{
  "symbol": "SH601398",
  "period": "day",
  "records": [{
    "date": "2026-03-30",
    "open": 7.37,
    "close": 7.57,
    "high": 7.58,
    "low": 7.36,
    "volume": 371587580,
    "amount": 2775759222.6,
    "float_shares": 269612212539,
    "turnover": 0.1404,
    "change": 0.17,
    "percent": 2.3
  }]
}
```

### bonus
```json
{
  "symbol": "SH601398",
  "records": [{
    "year": "2025年报",
    "equity_date": "2026-05-12",
    "ex_dividend_date": "2026-05-13",
    "dividend_date": "2026-05-13",
    "plan": "10派1.689元(董事会预案)"
  }]
}
```

### shares
```json
{
  "symbol": "SH601398",
  "records": [{
    "date": "2015-02-12",
    "total": 356406257089,
    "float_a": 269612212539,
    "float_h": 86794044550,
    "reason": "可转债转股"
  }]
}
```
