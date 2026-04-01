#!/usr/bin/env python
# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-03-31
Desc: 股票数据CLI
用法:
  jstock quote 601398                              # 行情
  jstock kline 601398 --start 2026-01-01          # K线
  jstock bonus 601398                              # 分红
  jstock shares 601398                             # 股本
  jstock position save 601398 --volume 1000 --cost 5.5  # 保存持仓
  jstock position list                             # 持仓列表
  jstock position get 601398                        # 持仓详情
  jstock position delete 601398                    # 删除持仓
  jstock position portfolio                         # 持仓汇总
"""

import argparse
import json
import sys
from typing import Optional

from jstock import StockAPI


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


def _position_to_dict(pos):
    """持仓转字典"""
    result = {
        "symbol": pos.symbol,
        "name": pos.name,
        "type": pos.type,
        "volume": pos.volume,
        "cost_price": pos.cost_price,
        "cost_amount": pos.cost_amount,
    }
    if pos.buy_date:
        result["buy_date"] = pos.buy_date
    if pos.current_price is not None:
        result.update({
            "current_price": pos.current_price,
            "market_value": pos.market_value,
            "profit": pos.profit,
            "profit_rate": pos.profit_rate,
        })
    return result


def cmd_position_save(args):
    """新建持仓"""
    from jstock import position_save
    try:
        position_save(args.symbol, args.volume, args.cost, args.name, args.type, args.buy_date)
        data = {
            "code": 0,
            "message": f"已新建持仓: {args.symbol}",
            "data": {
                "symbol": args.symbol,
                "volume": args.volume,
                "cost_price": args.cost,
                "name": args.name,
                "type": args.type,
                "buy_date": args.buy_date,
            }
        }
        print(json.dumps(data, ensure_ascii=False))
    except Exception as e:
        data = {"code": 1, "message": f"新建失败: {e}"}
        print(json.dumps(data, ensure_ascii=False))
        sys.exit(1)


def cmd_position_update(args):
    """更新持仓"""
    from jstock import position_update
    try:
        position_update(args.symbol, args.volume, args.cost, args.name, args.type, args.buy_date)
        data = {
            "code": 0,
            "message": f"已更新持仓: {args.symbol}",
            "data": {
                "symbol": args.symbol,
            }
        }
        print(json.dumps(data, ensure_ascii=False))
    except Exception as e:
        data = {"code": 1, "message": f"更新失败: {e}"}
        print(json.dumps(data, ensure_ascii=False))
        sys.exit(1)


def cmd_position_get(args):
    """查询单个持仓"""
    from jstock import position_get
    try:
        pos = position_get(args.symbol)
        if pos:
            data = {"code": 0, "data": _position_to_dict(pos)}
        else:
            data = {"code": 0, "data": None, "message": f"未找到持仓: {args.symbol}"}
        print(json.dumps(data, ensure_ascii=False))
    except Exception as e:
        data = {"code": 1, "message": f"查询失败: {e}"}
        print(json.dumps(data, ensure_ascii=False))
        sys.exit(1)


def cmd_position_list(args):
    """查询持仓列表"""
    from jstock import position_list
    try:
        positions = position_list(args.type)
        data = {"code": 0, "data": [_position_to_dict(p) for p in positions]}
        print(json.dumps(data, ensure_ascii=False))
    except Exception as e:
        data = {"code": 1, "message": f"查询失败: {e}"}
        print(json.dumps(data, ensure_ascii=False))
        sys.exit(1)


def cmd_position_delete(args):
    """删除持仓"""
    from jstock import position_delete
    try:
        deleted = position_delete(args.symbol)
        data = {
            "code": 0 if deleted else 1,
            "message": f"已删除: {args.symbol}" if deleted else f"持仓不存在: {args.symbol}"
        }
        print(json.dumps(data, ensure_ascii=False))
    except Exception as e:
        data = {"code": 1, "message": f"删除失败: {e}"}
        print(json.dumps(data, ensure_ascii=False))
        sys.exit(1)


def cmd_position_portfolio(args):
    """持仓汇总"""
    from jstock import portfolio_summary
    try:
        summary = portfolio_summary()
        data = {
            "code": 0,
            "data": {
                "count": summary["count"],
                "total_cost": summary["total_cost"],
                "total_market_value": summary["total_market_value"],
                "total_profit": summary["total_profit"],
                "profit_rate": summary["profit_rate"],
                "positions": [_position_to_dict(p) for p in summary["positions"]]
            }
        }
        print(json.dumps(data, ensure_ascii=False))
    except Exception as e:
        data = {"code": 1, "message": f"查询失败: {e}"}
        print(json.dumps(data, ensure_ascii=False))
        sys.exit(1)


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

    # position 子命令
    pos_sub = sub.add_parser("position", help="持仓管理")
    pos = pos_sub.add_subparsers(dest="pos_cmd")

    # position save
    p = pos.add_parser("save", help="新建持仓")
    p.add_argument("symbol", help="股票代码")
    p.add_argument("--volume", type=float, required=True, help="持仓数量")
    p.add_argument("--cost", type=float, required=True, help="成本价")
    p.add_argument("--name", help="名称")
    p.add_argument("--type", default="stock", help="类型 stock/etf/fund")
    p.add_argument("--buy-date", dest="buy_date", help="建仓时间 YYYY-MM-DD")
    
    # position update
    p = pos.add_parser("update", help="更新持仓")
    p.add_argument("symbol", help="股票代码")
    p.add_argument("--volume", type=float, help="持仓数量")
    p.add_argument("--cost", type=float, help="成本价")
    p.add_argument("--name", help="名称")
    p.add_argument("--type", help="类型 stock/etf/fund")
    p.add_argument("--buy-date", dest="buy_date", help="建仓时间 YYYY-MM-DD")

    # position get
    p = pos.add_parser("get", help="查询单个持仓")
    p.add_argument("symbol", help="股票代码")

    # position list
    p = pos.add_parser("list", help="查询持仓列表")
    p.add_argument("--type", help="类型过滤 stock/etf/fund")

    # position delete
    p = pos.add_parser("delete", help="删除持仓")
    p.add_argument("symbol", help="股票代码")

    # position portfolio
    p = pos.add_parser("portfolio", help="持仓汇总")

    args = parser.parse_args()

    if args.cmd == "quote":
        cmd_quote(args)
    elif args.cmd == "kline":
        cmd_kline(args)
    elif args.cmd == "bonus":
        cmd_bonus(args)
    elif args.cmd == "shares":
        cmd_shares(args)
    elif args.cmd == "position":
        if args.pos_cmd == "save":
            cmd_position_save(args)
        elif args.pos_cmd == "update":
            cmd_position_update(args)
        elif args.pos_cmd == "get":
            cmd_position_get(args)
        elif args.pos_cmd == "list":
            cmd_position_list(args)
        elif args.pos_cmd == "delete":
            cmd_position_delete(args)
        elif args.pos_cmd == "portfolio":
            cmd_position_portfolio(args)
        else:
            pos_sub.print_help()
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
