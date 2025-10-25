# 彭彭数字货币超级趋势指标

基于Python实现的超级趋势指标（Super Trend Indicator）分析工具，用于数字货币趋势分析。

## 功能特点

- 实现完整的超级趋势指标算法
- 支持自定义ATR周期和倍数参数
- 使用mplfinance绘制专业的K线图和指标线
- 支持真实数据和模拟数据测试

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 运行演示版本（使用模拟数据）

```bash
python demo_supertrend.py
```

### 2. 运行完整版本（支持真实数据）

```bash
python super_trend_indicator.py
```

## 参数说明

- `atr_period`: ATR周期，默认34
- `multiplier`: ATR倍数，默认3.0

## 指标说明

超级趋势指标通过以下步骤计算：

1. 计算ATR（平均真实波幅）
2. 计算上下轨：
   - 上轨 = (最高价 + 最低价) / 2 + (ATR × 倍数)
   - 下轨 = (最高价 + 最低价) / 2 - (ATR × 倍数)
3. 根据价格与上下轨的关系判断趋势方向

## 图形说明

- 绿色线：上轨（Final Upperband）
- 红色线：下轨（Final Lowerband）
- 当价格在上轨上方时，趋势为上升
- 当价格在下轨下方时，趋势为下降

## 文件说明

- `super_trend_indicator.py`: 完整版本，支持真实数据获取
- `demo_supertrend.py`: 演示版本，使用模拟数据
- `requirements.txt`: 依赖包列表
- `开发备忘录.md`: 项目开发记录

## 注意事项

- 超级趋势指标在趋势市场中表现良好，但在震荡市场中可能产生较多错误信号
- 建议结合其他技术指标使用以提高准确性
- 参数设置需要根据具体市场和时间周期进行调整
