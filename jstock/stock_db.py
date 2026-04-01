# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-04-01
Desc: 持仓数据库操作
"""

import sqlite3
import os
import logging
from typing import Optional, List

from jstock.model_db import DBPosition

logger = logging.getLogger(__name__)


class StockDBError(Exception):
    """数据库操作异常"""
    pass


class StockDB:
    """持仓数据库管理"""
    
    def __init__(self, db_path: Optional[str] = None):
        from jstock.config import DB_PATH
        self.db_path = db_path or DB_PATH
        self._init_db()
    
    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """初始化数据库表"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    symbol TEXT PRIMARY KEY,
                    name TEXT,
                    type TEXT DEFAULT 'stock',
                    volume REAL DEFAULT 0,
                    cost_price REAL DEFAULT 0,
                    buy_date TEXT,
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)
            # 兼容历史数据：如果 buy_date 列不存在，则添加
            cursor.execute("PRAGMA table_info(positions)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'buy_date' not in columns:
                cursor.execute("ALTER TABLE positions ADD COLUMN buy_date TEXT")
                logger.info("已添加 buy_date 列（历史数据兼容）")
            conn.commit()
            conn.close()
            logger.info(f"数据库初始化成功: {self.db_path}")
        except (sqlite3.Error, OSError) as e:
            error_msg = f"初始化数据库失败: {e}"
            logger.error(error_msg)
            raise StockDBError(error_msg)
    
    def save(self, db_pos: DBPosition) -> bool:
        """保存持仓（新增或更新）"""
        # 必填字段校验
        missing_fields = []
        if not db_pos.symbol:
            missing_fields.append("股票代码")
        if db_pos.volume is None or db_pos.volume <= 0:
            missing_fields.append("持仓数量")
        if db_pos.cost_price is None or db_pos.cost_price <= 0:
            missing_fields.append("成本价")
        if not db_pos.buy_date:
            missing_fields.append("建仓时间")
        
        # 新增时所有字段都必填
        existing = self.get(db_pos.symbol)
        if existing is None:
            if missing_fields:
                raise StockDBError(f"新建持仓缺少必填字段: {', '.join(missing_fields)}")
        # 更新时只校验被传入的空字段（原有值保留）
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # 如果更新时不传字段，保留原有值
            name = db_pos.name if db_pos.name is not None else existing.name if existing else None
            type_val = db_pos.type if db_pos.type is not None else existing.type if existing else "stock"
            buy_date = db_pos.buy_date if db_pos.buy_date is not None else existing.buy_date if existing else None
            
            cursor.execute("""
                INSERT INTO positions (symbol, name, type, volume, cost_price, buy_date)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    name=excluded.name,
                    type=excluded.type,
                    volume=excluded.volume,
                    cost_price=excluded.cost_price,
                    buy_date=excluded.buy_date,
                    updated_at=datetime('now', 'localtime')
            """, (db_pos.symbol, name, type_val,
                  db_pos.volume, db_pos.cost_price, buy_date))
            conn.commit()
            conn.close()
            logger.info(f"持仓已保存: {db_pos.symbol} {db_pos.volume}股 @ {db_pos.cost_price}")
            return True
        except sqlite3.Error as e:
            error_msg = f"保存持仓失败: {e}"
            logger.error(error_msg)
            raise StockDBError(error_msg)
    
    def delete(self, symbol: str) -> bool:
        """删除持仓"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM positions WHERE symbol=?", (symbol,))
            deleted = cursor.rowcount > 0
            conn.commit()
            conn.close()
            if deleted:
                logger.info(f"持仓已删除: {symbol}")
            return deleted
        except sqlite3.Error as e:
            error_msg = f"删除持仓失败: {e}"
            logger.error(error_msg)
            raise StockDBError(error_msg)
    
    def get(self, symbol: str) -> Optional[DBPosition]:
        """查询单个持仓"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM positions WHERE symbol=?", (symbol,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return DBPosition(
                    symbol=row["symbol"],
                    name=row["name"],
                    type=row["type"],
                    volume=row["volume"],
                    cost_price=row["cost_price"],
                    buy_date=row["buy_date"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
            return None
        except sqlite3.Error as e:
            error_msg = f"查询持仓失败: {e}"
            logger.error(error_msg)
            raise StockDBError(error_msg)
    
    def list_all(self, type_filter: Optional[str] = None) -> List[DBPosition]:
        """查询所有持仓"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            if type_filter:
                cursor.execute("SELECT * FROM positions WHERE type=? ORDER BY symbol", (type_filter,))
            else:
                cursor.execute("SELECT * FROM positions ORDER BY symbol")
            
            rows = cursor.fetchall()
            conn.close()
            
            return [DBPosition(
                symbol=row["symbol"],
                name=row["name"],
                type=row["type"],
                volume=row["volume"],
                cost_price=row["cost_price"],
                buy_date=row["buy_date"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            ) for row in rows]
        except sqlite3.Error as e:
            error_msg = f"查询持仓列表失败: {e}"
            logger.error(error_msg)
            raise StockDBError(error_msg)
