#!/usr/bin/env python
# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-03-31
Desc: 股票数据CLI
用法:
  stock-cli quote 601398
  stock-cli kline 601398 --start 2026-01-01 --end 2026-03-31
  stock-cli bonus 601398
  stock-cli shares 601398
"""

import argparse
import json
import sys

from stock import StockAPI


def cmd_quote(args):
    api = StockAPI()
    q = api.quote(args.symbol)
    data = {
        "code": 0,
        "data": {
            "symbol": q.symbol,
            "name": q.name,
            "current": q.current,
            "change": q.chg,
            "percent": q.percent,
            "open": q.open,
            "high": q.high,
            "low": q.low,
            "volume": q.volume,
            "amount": q.amount,
            "turnover_rate": q.turnover_rate,
            "pe_ttm": q.pe_ttm,
            "pb": q.pb,
            "market_cap": q.market_capital,
        }
    }
    # 移除None值
    data["data"] = {k: v for k, v in data["data"].items() if v is not None}
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_kline(args):
    api = StockAPI()
    k = api.kline(args.symbol, start=args.start, end=args.end)
    data = {
        "code": 0,
        "data": {
            "symbol": k.symbol,
            "period": k.period,
            "count": len(k.records),
            "records": [
                {
                    "date": r.timestamp,
                    "open": r.open,
                    "close": r.close,
                    "high": r.high,
                    "low": r.low,
                    "volume": r.volume,
                    "amount": r.amount,
                    "float_shares": r.float_shares,
                    "turnover": r.turnover,
                    "change": r.chg,
                    "percent": r.percent,
                }
                for r in k.records
            ]
        }
    }
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_bonus(args):
    api = StockAPI()
    b = api.bonus(args.symbol)
    data = {
        "code": 0,
        "data": {
            "symbol": b.symbol,
            "count": len(b.records),
            "records": [
                {
                    "year": r.dividend_year,
                    "equity_date": r.equity_date,
                    "ex_dividend_date": r.ex_dividend_date,
                    "dividend_date": r.dividend_date,
                    "plan": r.plan_explain,
                }
                for r in b.records
            ]
        }
    }
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_shares(args):
    api = StockAPI()
    s = api.shares(args.symbol)
    data = {
        "code": 0,
        "data": {
            "symbol": s.symbol,
            "count": len(s.records),
            "records": [
                {
                    "date": r.chg_date,
                    "total": r.total_shares,
                    "float_a": r.float_shares_ashare,
                    "float_h": r.float_shares_hshare,
                    "reason": r.chg_reason,
                }
                for r in s.records
            ]
        }
    }
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="股票数据查询CLI")
    sub = parser.add_subparsers(dest="cmd")

    # quote
    p = sub.add_parser("quote", help="行情数据")
    p.add_argument("symbol", help="股票代码")

    # kline
    p = sub.add_parser("kline", help="K线数据")
    p.add_argument("symbol", help="股票代码")
    p.add_argument("--start", help="开始日期 YYYY-MM-DD")
    p.add_argument("--end", help="结束日期 YYYY-MM-DD")

    # bonus
    p = sub.add_parser("bonus", help="分红数据")
    p.add_argument("symbol", help="股票代码")

    # shares
    p = sub.add_parser("shares", help="股本变动")
    p.add_argument("symbol", help="股票代码")

    args = parser.parse_args()

    if args.cmd == "quote":
        cmd_quote(args)
    elif args.cmd == "kline":
        cmd_kline(args)
    elif args.cmd == "bonus":
        cmd_bonus(args)
    elif args.cmd == "shares":
        cmd_shares(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
