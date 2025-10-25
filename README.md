# Tradestation 自动化交易策略项目

## 项目描述
基于Tradestation平台的自动化交易策略系统，包含数据获取、MSS/FVG算法计算、策略执行和系统集成四个阶段。

## 技术栈
- Python 3.8+
- FastAPI (Web框架)
- SQLAlchemy (数据库ORM)
- Pandas (数据处理)
- NumPy (数值计算)
- Matplotlib/Plotly (图表显示)
- Streamlit (UI界面)
- Redis (缓存)
- PostgreSQL (数据存储)

## 安装依赖
```bash
pip install -r requirements.txt
```

## 项目结构
```
tradestation_project/
├── app/
│   ├── api/           # API接口
│   ├── core/          # 核心配置
│   ├── data/          # 数据处理模块
│   ├── models/        # 数据模型
│   ├── services/      # 业务逻辑
│   └── ui/            # 用户界面
├── config/            # 配置文件
├── tests/             # 测试文件
├── docs/              # 文档
└── requirements.txt   # 依赖文件
```

## 开发阶段
1. 第一阶段：数据获取与处理模块（基础建设）
2. 第二阶段：MSS引擎与FVG计算
3. 第三阶段：策略自动化控制与执行
4. 第四阶段：系统集成与优化

## API配置
- 平台：Tradestation
- API Key：7nTEG6CTvOomXQ4Fo9vGVkrDeRs0iFA5
- Secret：X18iJpHmso8Rt7rUhEBRQ9hUAufzQ1qKyLs-hHQVsVo-NaK5H9Bzp_UqTEE97Yg5
