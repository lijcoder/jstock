# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-04-01
Desc: 我的持仓 API
"""

import logging
from typing import Optional, List

from jstock.model_db import DBPosition
from jstock.stock_db import StockDB, StockDBError
from jstock.models import Position
from jstock import quote

logger = logging.getLogger(__name__)

_db: Optional[StockDB] = None


def _get_db() -> StockDB:
    """获取数据库实例"""
    global _db
    if _db is None:
        try:
            _db = StockDB()
        except StockDBError as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    return _db


def position_save(symbol: str, volume: float, cost_price: float,
                 name: Optional[str] = None, type: str = "stock") -> bool:
    """
    保存持仓
    
    Args:
        symbol: 股票代码
        volume: 持仓数量
        cost_price: 成本价
        name: 名称（可选）
        type: 类型 stock/etf/fund（默认 stock）
    
    Returns:
        bool: 是否成功
    """
    try:
        db_pos = DBPosition(
            symbol=symbol,
            name=name,
            type=type,
            volume=volume,
            cost_price=cost_price
        )
        _get_db().save(db_pos)
        return True
    except StockDBError as e:
        logger.error(f"保存持仓失败: {e}")
        raise


def position_get(symbol: str, with_price: bool = True) -> Optional[Position]:
    """
    查询单个持仓
    
    Args:
        symbol: 股票代码
        with_price: 是否获取实时价格（默认 True）
    
    Returns:
        Position 或 None
    """
    try:
        db_pos = _get_db().get(symbol)
        if db_pos:
            return _to_position(db_pos, with_price)
        return None
    except StockDBError as e:
        logger.error(f"查询持仓失败: {e}")
        raise


def position_list(type: Optional[str] = None, with_price: bool = True) -> List[Position]:
    """
    查询持仓列表
    
    Args:
        type: 类型过滤 stock/etf/fund（可选）
        with_price: 是否获取实时价格（默认 True）
    
    Returns:
        Position 列表
    """
    try:
        db_positions = _get_db().list_all(type)
        positions = [_to_position(p, False) for p in db_positions]
        if with_price:
            _fill_prices(positions)
        return positions
    except StockDBError as e:
        logger.error(f"查询持仓列表失败: {e}")
        raise


def position_delete(symbol: str) -> bool:
    """
    删除持仓
    
    Args:
        symbol: 股票代码
    
    Returns:
        bool: 是否成功删除
    """
    try:
        return _get_db().delete(symbol)
    except StockDBError as e:
        logger.error(f"删除持仓失败: {e}")
        raise


def portfolio_summary() -> dict:
    """
    持仓汇总
    
    Returns:
        dict: 包含总投入、总市值、盈亏等
    """
    positions = position_list(with_price=True)
    
    total_cost = sum(p.cost_amount for p in positions)
    total_market = sum(p.market_value or 0 for p in positions)
    total_profit = total_market - total_cost
    
    return {
        "count": len(positions),
        "total_cost": total_cost,
        "total_market_value": total_market,
        "total_profit": total_profit,
        "profit_rate": (total_profit / total_cost * 100) if total_cost > 0 else 0,
        "positions": positions
    }


def _to_position(db_pos: DBPosition, with_price: bool) -> Position:
    """DBPosition -> Position"""
    pos = Position(
        symbol=db_pos.symbol,
        name=db_pos.name,
        type=db_pos.type,
        volume=db_pos.volume,
        cost_price=db_pos.cost_price
    )
    return pos


def _fill_prices(positions: List[Position]):
    """填充实时价格并计算盈亏"""
    for pos in positions:
        try:
            q = quote(pos.symbol)
            pos.current_price = q.current
            pos.name = pos.name or q.name
            pos.market_value = pos.current_price * pos.volume
            pos.profit = pos.market_value - pos.cost_amount
            pos.profit_rate = (pos.profit / pos.cost_amount * 100) if pos.cost_amount > 0 else 0
        except Exception as e:
            logger.warning(f"获取行情失败 {pos.symbol}: {e}")
