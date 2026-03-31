# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-03-31
Desc: 股票数据统一返回结构定义
用于规范不同数据源的返回格式
"""

from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any


# ============ 股票行情 ============

@dataclass
class StockQuote:
    """股票行情数据"""
    # 基本信息
    name: Optional[str] = None                    # 名称
    symbol: Optional[str] = None                  # 代码
    time: Optional[str] = None                     # 时间
    
    # 行情数据
    current: Optional[float] = None               # 现价
    last_close: Optional[float] = None            # 昨收
    open: Optional[float] = None                  # 今开
    high: Optional[float] = None                  # 最高
    low: Optional[float] = None                   # 最低
    chg: Optional[float] = None                   # 涨跌
    percent: Optional[float] = None               # 涨跌幅(%)
    
    # 交易数据
    volume: Optional[float] = None                 # 成交量
    amount: Optional[float] = None                # 成交额
    turnover_rate: Optional[float] = None         # 换手率(%)
    
    # 估值指标
    pe_ttm: Optional[float] = None                 # 市盈率(TTM)
    pe_lyr: Optional[float] = None                 # 市盈率(静)
    pe_forecast: Optional[float] = None           # 市盈率(动)
    pb: Optional[float] = None                    # 市净率
    dividend_yield: Optional[float] = None        # 股息率(%)
    
    # 每股指标
    eps: Optional[float] = None                   # 每股收益
    navps: Optional[float] = None                 # 每股净资产
    
    # 市值
    market_capital: Optional[float] = None        # 总市值
    
    # 52周数据
    high52w: Optional[float] = None                # 52周最高
    low52w: Optional[float] = None                 # 52周最低

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def get(self, key: str, default: Any = None) -> Any:
        """字典风格访问"""
        return self.to_dict().get(key, default)
    
    def items(self):
        """字典风格遍历"""
        return self.to_dict().items()
    
    def keys(self):
        """获取所有键"""
        return self.to_dict().keys()
    
    def values(self):
        """获取所有值"""
        return self.to_dict().values()


# ============ 分红数据 ============

@dataclass
class BonusRecord:
    """分红记录"""
    dividend_year: Optional[str] = None           # 报告期
    equity_date: Optional[str] = None              # 股权登记日
    ex_dividend_date: Optional[str] = None         # 除权除息日
    dividend_date: Optional[str] = None           # 派息日
    plan_explain: Optional[str] = None             # 分红方案

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass  
class BonusHistory:
    """分红历史（包含多条记录）"""
    symbol: str                                    # 股票代码
    name: Optional[str] = None                     # 股票名称
    records: List[BonusRecord] = field(default_factory=list)  # 分红记录列表

    def to_list(self) -> List[Dict[str, Any]]:
        """转换为字典列表"""
        return [r.to_dict() for r in self.records]
    
    def __len__(self):
        return len(self.records)
    
    def __iter__(self):
        return iter(self.records)


# ============ 股本变动 ============

@dataclass
class SharesChangeRecord:
    """股本变动记录"""
    chg_date: Optional[str] = None                  # 变动日期
    total_shares: Optional[int] = None              # 总股本（股）
    float_shares_ashare: Optional[int] = None        # 流通A股（股）
    float_shares_hshare: Optional[int] = None       # 流通H股（股）
    chg_reason: Optional[str] = None                # 变动原因

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class SharesHistory:
    """股本变动历史"""
    symbol: str                                     # 股票代码
    records: List[SharesChangeRecord] = field(default_factory=list)  # 变动记录列表

    def to_list(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self.records]
    
    def __len__(self):
        return len(self.records)
    
    def __iter__(self):
        return iter(self.records)


# ============ K线数据 ============

@dataclass
class KlineRecord:
    """K线记录"""
    timestamp: Optional[str] = None                 # 时间
    open: Optional[float] = None                   # 开盘
    close: Optional[float] = None                  # 收盘
    high: Optional[float] = None                   # 最高
    low: Optional[float] = None                   # 最低
    volume: Optional[float] = None                 # 成交量
    amount: Optional[float] = None                # 成交额
    turnover: Optional[float] = None              # 换手率(%)
    float_shares: Optional[int] = None             # 流通股本（股）
    chg: Optional[float] = None                   # 涨跌
    percent: Optional[float] = None               # 涨跌幅(%)

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class KlineData:
    """K线数据"""
    symbol: str                                     # 股票代码
    period: str                                     # 周期
    records: List[KlineRecord] = field(default_factory=list)  # K线记录列表

    def to_list(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self.records]
    
    def __len__(self):
        return len(self.records)
    
    def __iter__(self):
        return iter(self.records)
