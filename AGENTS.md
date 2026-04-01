# jstock 开发指南

本文件面向开发者，包含项目开发规范、代码风格、架构设计等指导。

## 项目规范

### 代码风格

- 使用 **Type Hints** 标注所有函数参数和返回值类型
- 使用 **dataclass** 定义数据模型
- 使用 **logging** 模块记录日志
- 异常处理：网络请求失败抛出明确异常

```python
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class Quote:
    symbol: str
    name: str
    current: float
    percent: float
```

### 文件组织

| 文件 | 职责 |
|------|------|
| `models.py` | 用户数据结构体 (含动态字段) |
| `model_db.py` | 数据库实体 (仅数据库字段) |
| `stock_*.py` | 数据源客户端实现 |
| `stock_api.py` | 统一 API 门面 |
| `stock_positions.py` | 持仓管理 API |

### 添加新功能流程

1. `models.py` - 添加数据模型
2. 对应客户端文件 - 实现数据获取
3. `stock_api.py` - 添加统一 API 入口
4. `__init__.py` - 导出新函数
5. `cli/__main__.py` - 添加 CLI 命令
6. `tests/` - 添加测试

## 数据模型设计

### 分离原则

- **DBPosition** (model_db.py): 仅包含数据库字段
- **Position** (models.py): 包含动态计算字段 (current_price, profit 等)

```python
# model_db.py - 数据库实体
@dataclass
class DBPosition:
    symbol: str
    name: Optional[str]
    type: str
    volume: float
    cost_price: float

# models.py - 用户结构体
@dataclass
class Position:
    symbol: str
    name: Optional[str]
    type: str
    volume: float
    cost_price: float
    
    # 动态字段 (自动计算)
    current_price: Optional[float] = None
    profit: Optional[float] = None
```

## 数据库规范

- 使用 **raw SQLite** (无 ORM)
- 使用 `CREATE TABLE IF NOT EXISTS` 避免重复创建
- 数据库路径: `~/.jstock/db/`
- 自定义异常: `StockDBError`

## CLI 规范

- 所有命令返回 **JSON 格式**
- 成功: `{"code": 0, "data": {...}}`
- 失败: `{"code": 1, "message": "错误信息"}`
- 删除操作需先查询并等待用户确认

## 测试规范

```bash
# 运行所有测试
uv run pytest tests/

# 运行单个测试文件
uv run pytest tests/test_db.py -v

# 运行单个测试
uv run pytest tests/test_db.py::TestStockDB::test_save_position -v
```

## 常见问题

### 股票代码格式
- 6 位代码: `601398`
- 带市场后缀: `SH601398`, `SZ000001`

### 换手率计算
```
换手率 = 成交量(手) × 100 / 流通股本(股) × 100%
```

### 数据源限制
- 雪球: 需要有效的 User-Agent
- 同花顺: K 线数据有频率限制
