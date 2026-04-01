# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2026-04-01
Desc: 持仓数据库测试
"""

import os
import tempfile
import pytest
from pathlib import Path

from jstock.model_db import DBPosition
from jstock.stock_db import StockDB, StockDBError
from jstock import stock_positions


class TestStockDB:
    """数据库操作测试"""
    
    @pytest.fixture
    def db_path(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        # 清理
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def db(self, db_path):
        """创建数据库实例"""
        return StockDB(db_path)
    
    def test_init_db(self, db_path):
        """测试数据库初始化"""
        db = StockDB(db_path)
        assert os.path.exists(db_path)
        
        # 验证表已创建
        conn = db._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='positions'")
        row = cursor.fetchone()
        conn.close()
        assert row is not None
    
    def test_init_db_twice(self, db_path):
        """测试重复初始化不会报错"""
        db1 = StockDB(db_path)
        db2 = StockDB(db_path)  # 不应报错
        assert True
    
    def test_save_position(self, db):
        """测试保存持仓"""
        db_pos = DBPosition(
            symbol="600000",
            name="浦发银行",
            type="stock",
            volume=1000,
            cost_price=10.5,
            buy_date="2026-01-01"
        )
        assert db.save(db_pos) is True
        
        # 验证已保存
        saved = db.get("600000")
        assert saved is not None
        assert saved.symbol == "600000"
        assert saved.name == "浦发银行"
        assert saved.volume == 1000
        assert saved.cost_price == 10.5
        assert saved.buy_date == "2026-01-01"
    
    def test_save_position_new_must_have_buy_date(self, db):
        """测试新建持仓必须指定建仓时间"""
        from jstock.stock_db import StockDBError
        db_pos = DBPosition(
            symbol="600000",
            volume=1000,
            cost_price=10.5
        )
        with pytest.raises(StockDBError, match="新建持仓必须指定建仓时间"):
            db.save(db_pos)
    
    def test_update_position(self, db):
        """测试更新持仓"""
        # 先保存
        db.save(DBPosition(symbol="600000", volume=1000, cost_price=10.0, buy_date="2026-01-01"))
        
        # 更新
        db.save(DBPosition(symbol="600000", volume=2000, cost_price=11.0))
        
        # 验证更新
        saved = db.get("600000")
        assert saved.volume == 2000
        assert saved.cost_price == 11.0
        assert saved.buy_date == "2026-01-01"  # 保持原有值
    
    def test_get_position(self, db):
        """测试查询单个持仓"""
        db.save(DBPosition(symbol="600001", volume=500, cost_price=5.0, buy_date="2026-02-01"))
        
        # 查询存在
        pos = db.get("600001")
        assert pos is not None
        assert pos.symbol == "600001"
        
        # 查询不存在
        pos = db.get("999999")
        assert pos is None
    
    def test_list_positions(self, db):
        """测试查询所有持仓"""
        db.save(DBPosition(symbol="600001", volume=100, cost_price=1.0, buy_date="2026-01-01"))
        db.save(DBPosition(symbol="600002", volume=200, cost_price=2.0, type="etf", buy_date="2026-01-02"))
        
        # 全部
        positions = db.list_all()
        assert len(positions) == 2
        
        # 按类型过滤
        positions = db.list_all("etf")
        assert len(positions) == 1
        assert positions[0].symbol == "600002"
    
    def test_delete_position(self, db):
        """测试删除持仓"""
        db.save(DBPosition(symbol="600001", volume=100, cost_price=1.0, buy_date="2026-01-01"))
        
        # 删除存在
        assert db.delete("600001") is True
        assert db.get("600001") is None
        
        # 删除不存在
        assert db.delete("999999") is False
    
    def test_error_handling(self, db_path):
        """测试错误处理"""
        # 无效路径应该失败
        invalid_path = "/invalid/path/that/does/not/exist/test.db"
        with pytest.raises(StockDBError):
            StockDB(invalid_path)


class TestStockPositions:
    """持仓 API 测试"""
    
    @pytest.fixture
    def db_path(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        # 清理
        if os.path.exists(db_path):
            os.unlink(db_path)
        
        # 重置单例
        stock_positions._db = None
    
    @pytest.fixture
    def db(self, db_path):
        """创建数据库实例"""
        return StockDB(db_path)
    
    def test_position_save(self, db_path):
        """测试保存持仓"""
        # 替换单例
        stock_positions._db = StockDB(db_path)
        
        from jstock import position_save
        assert position_save("600000", 1000, 10.5, "浦发银行", "stock", "2026-01-01") is True
    
    def test_position_save_with_buy_date(self, db_path):
        """测试保存持仓（带建仓时间）"""
        stock_positions._db = StockDB(db_path)
        
        from jstock import position_save, position_get
        assert position_save("600001", 500, 5.0, "某股票", buy_date="2026-01-15") is True
        
        pos = position_get("600001", with_price=False)
        assert pos.buy_date == "2026-01-15"
    
    def test_position_get(self, db_path):
        """测试查询持仓"""
        stock_positions._db = StockDB(db_path)
        
        from jstock import position_save, position_get
        
        position_save("600001", 500, 5.0, "某股票", buy_date="2026-02-01")
        
        # 不获取价格
        pos = position_get("600001", with_price=False)
        assert pos is not None
        assert pos.symbol == "600001"
        assert pos.volume == 500
        assert pos.current_price is None  # 未获取价格
    
    def test_position_list(self, db_path):
        """测试查询持仓列表"""
        stock_positions._db = StockDB(db_path)
        
        from jstock import position_save, position_list
        
        position_save("600001", 100, 1.0, buy_date="2026-01-01")
        position_save("510001", 200, 2.0, type="etf", buy_date="2026-01-02")
        
        positions = position_list()
        assert len(positions) == 2
        
        positions = position_list("etf")
        assert len(positions) == 1
        assert positions[0].symbol == "510001"
    
    def test_position_delete(self, db_path):
        """测试删除持仓"""
        stock_positions._db = StockDB(db_path)
        
        from jstock import position_save, position_delete
        
        position_save("600001", 100, 1.0, buy_date="2026-01-01")
        assert position_delete("600001") is True
        assert position_delete("999999") is False


class TestPositionModel:
    """Position 模型测试"""
    
    def test_cost_amount(self):
        """测试成本金额计算"""
        from jstock.models import Position
        
        pos = Position(symbol="600000", volume=1000, cost_price=5.5)
        assert pos.cost_amount == 5500.0
    
    def test_position_defaults(self):
        """测试默认值"""
        from jstock.models import Position
        
        pos = Position(symbol="600000")
        assert pos.volume == 0.0
        assert pos.cost_price == 0.0
        assert pos.type == "stock"
        assert pos.name is None
