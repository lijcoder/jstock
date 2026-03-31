# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-03-31
Desc: 股票数据统一API - 门面模式
自动选择数据源，调用方无需关心底层实现
"""

from datetime import datetime, timedelta
from typing import Optional

from stock import models
from stock.stock_xq import XueqiuClient, normalize_symbol
from stock.stock_ths import daily_kline as ths_daily_kline

# 导出统一的数据模型
__all__ = [
    'quote',
    'kline',
    'bonus',
    'shares',
    'StockAPI',
]
StockQuote = models.StockQuote
BonusHistory = models.BonusHistory
SharesHistory = models.SharesHistory
KlineData = models.KlineData


# ============ 便捷函数 ============
_quote_client = None
_api_client = None


def _get_quote_client() -> XueqiuClient:
    """获取行情客户端（延迟初始化）"""
    global _quote_client
    if _quote_client is None:
        _quote_client = XueqiuClient()
    return _quote_client


def _get_api() -> 'StockAPI':
    """获取StockAPI实例"""
    global _api_client
    if _api_client is None:
        _api_client = StockAPI()
    return _api_client


def quote(symbol: str, market: str = None) -> StockQuote:
    """
    获取股票行情
    
    :param symbol: 股票代码，支持 601398、SH601398 等格式
    :param market: 指定市场，可选 'SH'/'SZ'
    :return: StockQuote 对象
    """
    return _get_api().quote(symbol, market)


def kline(
    symbol: str,
    period: str = "day",
    years: int = None,
    start: str = None,
    end: str = None,
    market: str = None,
) -> KlineData:
    """
    获取K线数据
    
    :param symbol: 股票代码
    :param period: 周期，day/week/month/quarter/year，默认 day
    :param years: 最近N年，如 5 表示最近5年
    :param start: 开始日期，YYYY-MM-DD 格式
    :param end: 结束日期，YYYY-MM-DD 格式
    :param market: 指定市场
    
    使用示例:
        kline("601398", years=5)           # 最近5年
        kline("601398", start="2025-01-01", end="2025-12-31")  # 2025全年
        kline("601398", period="month")     # 月K线，默认最近5年
    
    :return: KlineData 对象
    """
    return _get_api().kline(symbol, period=period, years=years, start=start, end=end, market=market)


def bonus(symbol: str, market: str = None) -> BonusHistory:
    """获取分红历史"""
    return _get_api().bonus(symbol, market)


def shares(symbol: str, market: str = None) -> SharesHistory:
    """获取股本变动"""
    return _get_api().shares(symbol, market)


# ============ 工具函数 ============
def _parse_date(date_str: str) -> datetime:
    """解析日期字符串"""
    if date_str is None:
        return None
    
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except ValueError:
            continue
    
    raise ValueError(f"无法解析日期: {date_str}，请使用 YYYY-MM-DD 格式")


def _date_to_timestamp(dt: datetime) -> int:
    """日期转时间戳(毫秒)"""
    return int(dt.timestamp() * 1000)


def _count_from_years(years: int, period: str) -> int:
    """根据年数估算K线数量"""
    # 每年的交易日约250天
    trading_days_per_year = 250
    
    if period == "day":
        return -years * trading_days_per_year
    elif period == "week":
        return -years * 52
    elif period == "month":
        return -years * 12
    elif period == "quarter":
        return -years * 4
    elif period == "year":
        return -years
    else:
        return -years * trading_days_per_year


# ============ 主类 ============
class StockAPI:
    """
    股票数据统一API - 门面类
    
    自动选择最优数据源，调用方无需关心底层实现。
    优先使用雪球数据，失败时切换到其他数据源。
    
    使用示例：
        from stock import StockAPI, quote, kline, bonus, shares
        
        api = StockAPI()
        
        # 获取行情
        q = api.quote("601398")
        print(q.name, q.current)
        
        # 获取K线 - 最近5年
        k = api.kline("601398", years=5)
        
        # 获取K线 - 日期范围
        k = api.kline("601398", start="2025-01-01", end="2025-12-31")
        
        # 月K线 - 最近2年
        k = api.kline("601398", period="month", years=2)
        
        # 便捷函数
        k = kline("601398", years=5)
    """

    def __init__(self, primary: str = "xq"):
        """
        初始化
        
        :param primary: 首选数据源，"xq" 或 "ths"
        """
        self.primary = primary
        self._xq_client = None

    @property
    def xq(self) -> XueqiuClient:
        """雪球客户端（延迟初始化）"""
        if self._xq_client is None:
            self._xq_client = XueqiuClient()
        return self._xq_client

    def quote(self, symbol: str, market: str = None) -> StockQuote:
        """
        获取股票行情
        
        :param symbol: 股票代码，支持 601398、SH601398 等格式
        :param market: 指定市场，可选 'SH'/'SZ'
        :return: StockQuote 对象
        """
        try:
            return self.xq.stock_quote(symbol, market)
        except Exception as e:
            raise RuntimeError(f"获取行情失败: {e}")

    def kline(
        self,
        symbol: str,
        period: str = "day",
        years: int = None,
        start: str = None,
        end: str = None,
        market: str = None,
    ) -> KlineData:
        """
        获取K线数据
        
        :param symbol: 股票代码
        :param period: 周期，day/week/month/quarter/year，默认 day
        :param years: 最近N年，如 5 表示最近5年
        :param start: 开始日期，YYYY-MM-DD 格式
        :param end: 结束日期，YYYY-MM-DD 格式
        :param market: 指定市场
        
        使用示例:
            kline("601398", years=5)           # 最近5年
            kline("601398", start="2025-01-01", end="2025-12-31")  # 2025全年
            kline("601398", period="month")     # 月K线，默认最近5年
        
        :return: KlineData 对象
        
        注意：THS仅支持日K线
        """
        # 规范化代码
        symbol = normalize_symbol(symbol, market)
        
        # 自动判断市场（从规范化后的代码提取）
        market = symbol[:2]

        # 处理日期参数
        if start or end:
            # 使用日期范围（传递给_xq_kline处理，count在_xq_kline中计算）
            count = -2500  # 默认值，实际在_xq_kline中根据日期范围重新计算
        elif years:
            count = _count_from_years(years, period)
        else:
            count = _count_from_years(5, period)

        if self.primary == "xq":
            # 优先雪球
            try:
                return self._xq_kline(symbol, market, period, count, start, end)
            except Exception as e:
                # 保留错误，尝试THS fallback
                last_error = e
        
        # Fallback 到同花顺（仅支持日K）
        if period != "day":
            raise ValueError(f"获取K线失败，雪球: {last_error if 'last_error' in dir() else '未知错误'}，THS仅支持日K线")
        
        try:
            market_prefix = "sh" if market == "SH" else "sz"
            return ths_daily_kline(symbol, market_prefix)
        except Exception as e:
            error_msg = str(last_error) if 'last_error' in dir() else "未知错误"
            raise RuntimeError(f"获取K线失败: 雪球={error_msg}, THS={e}")

    def _xq_kline(
        self,
        symbol: str,
        market: str,
        period: str,
        count: int = -250,
        start: str = None,
        end: str = None,
    ) -> KlineData:
        """雪球K线接口"""
        # 解析日期
        start_dt = _parse_date(start) if start else None
        end_dt = _parse_date(end) if end else None
        
        # 计算需要获取的数据量
        if start_dt and end_dt:
            # 根据日期范围估算数量
            days = (end_dt - start_dt).days
            if period == "day":
                count = max(-days - 50, -2500)  # 多取一些避免周末问题
            elif period == "week":
                count = max(-days // 7 - 10, -500)
            elif period == "month":
                count = max(-days // 30 - 5, -200)
            else:
                count = max(-days - 50, -2500)
        
        end_ts = int(datetime.now().timestamp() * 1000)
        
        params = {
            "symbol": symbol,
            "begin": str(end_ts),
            "period": period,
            "type": "before",
            "count": str(count),
        }
        
        url = "https://stock.xueqiu.com/v5/stock/chart/kline.json"
        data = self.xq._request(url, params)
        
        if 'data' not in data or not data['data']:
            return KlineData(symbol=symbol, period=period, records=[])
        
        cols = data["data"].get("column", [])
        items = data["data"].get("item", [])
        if not items:
            return KlineData(symbol=symbol, period=period, records=[])
        
        idx = {col: i for i, col in enumerate(cols)}
        
        records = [
            models.KlineRecord(
                timestamp=_ts_to_date(int(item[idx["timestamp"]])) if item[idx.get("timestamp")] else None,
                open=item[idx.get("open")],
                close=item[idx.get("close")],
                high=item[idx.get("high")],
                low=item[idx.get("low")],
                volume=item[idx.get("volume")],
                amount=item[idx.get("amount")],
                turnover=item[idx.get("turnoverrate")],
                chg=item[idx.get("chg")],
                percent=item[idx.get("percent")],
            )
            for item in items
        ]
        
        # 按日期过滤
        if start_dt:
            records = [r for r in records if r.timestamp and datetime.strptime(r.timestamp, "%Y-%m-%d").date() >= start_dt.date()]
        if end_dt:
            records = [r for r in records if r.timestamp and datetime.strptime(r.timestamp, "%Y-%m-%d").date() <= end_dt.date()]
        
        return KlineData(symbol=symbol, period=period, records=records)

    def bonus(self, symbol: str, market: str = None) -> BonusHistory:
        """
        获取分红历史
        
        :param symbol: 股票代码
        :param market: 指定市场
        :return: BonusHistory 对象
        """
        try:
            return self.xq.stock_bonus(symbol, market)
        except Exception as e:
            raise RuntimeError(f"获取分红历史失败: {e}")

    def shares(self, symbol: str, market: str = None) -> SharesHistory:
        """
        获取股本变动
        
        :param symbol: 股票代码
        :param market: 指定市场
        :return: SharesHistory 对象
        """
        try:
            return self.xq.stock_shares(symbol, market)
        except Exception as e:
            raise RuntimeError(f"获取股本变动失败: {e}")


def _ts_to_date(timestamp_ms: int) -> str:
    """时间戳 -> YYYY-MM-DD"""
    return datetime.fromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d")


# ============ 主程序 ============
if __name__ == "__main__":
    api = StockAPI()

    print("=" * 50)
    print("测试股票统一API - K线接口")
    print("=" * 50)

    # 最近5年
    print("\n📈 最近5年K线:")
    k = api.kline("601398", years=5)
    print(f"  {k.symbol} 共 {len(k.records)} 条")
    if k.records:
        print(f"  从 {k.records[0].timestamp} 到 {k.records[-1].timestamp}")

    # 日期范围
    print("\n📈 2025全年K线:")
    k = api.kline("601398", start="2025-01-01", end="2025-12-31")
    print(f"  {k.symbol} 共 {len(k.records)} 条")
    if k.records:
        print(f"  从 {k.records[0].timestamp} 到 {k.records[-1].timestamp}")

    # 月K线
    print("\n📈 最近2年月K线:")
    k = api.kline("600519", period="month", years=2)
    print(f"  {k.symbol} 共 {len(k.records)} 条")
    for r in k.records[-6:]:
        print(f"    {r.timestamp}: 收={r.close}")

    print("\n✅ 完成")
