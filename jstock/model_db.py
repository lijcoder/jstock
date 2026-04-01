# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-04-01
Desc: 数据库持仓实体
用于数据库表映射
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DBPosition:
    """数据库持仓实体"""
    symbol: str                     # 代码 (主键)
    name: Optional[str] = None      # 名称
    type: str = "stock"            # 类型：stock/etf/fund
    volume: float = 0.0            # 持仓数量（股）
    cost_price: float = 0.0        # 成本价
    buy_date: Optional[str] = None  # 建仓时间
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
