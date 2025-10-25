import numpy as np

def send_email(title, msg_nr, attachments):
    import smtplib
    from email.mime.image import MIMEImage
    from email.mime.text import MIMEText
    from email.utils import formataddr
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders
    import os
    msg_from = '16318015@qq.com'
    password = 'neotepdloordcaii'
    msg_to = ['2461490357@qq.com']
    msg = MIMEMultipart()
    msg['Subject'] = title
    msg['From'] = formataddr(('我的行情服务管家', msg_from))
    msg['To'] = ','.join(msg_to)
    msg.attach(MIMEText(msg_nr, 'plain', 'utf-8'))

    for attachment in attachments:
        filename = os.path.basename(attachment)  # 获取附件文件名
        with open(attachment, 'rb') as f:
            mime = MIMEBase('image', 'png', filename=filename)  # 设置附件名称为文件名
            mime.add_header('Content-Disposition', 'attachment', filename=filename)
            mime.add_header('Content-ID', '<0>')
            mime.add_header('X-Attachment-Id', '0')
            mime.set_payload(f.read())
            encoders.encode_base64(mime)
            msg.attach(mime)

    try:
        s = smtplib.SMTP_SSL("smtp.qq.com", 465)
        s.login(msg_from, password)
        s.sendmail(msg_from, msg_to, msg.as_string())
        print('邮件发送成功')
    except Exception as e:
        print(e)
    finally:
        s.quit()


def huatucs(data, code,table_name,zhibiaomc):
    from pyecharts.charts import Kline
    from pyecharts import options as opts
    from pyecharts.charts import Line
    from pyecharts.globals import ThemeType
    from pyecharts import options as opts
    from pyecharts.charts import Bar, EffectScatter
    import pandas as pd
    import webbrowser
    from pyecharts.charts import Grid  # 首先导入Grid类
    df = pd.DataFrame(data)
    # 把date作为日期索引
    df.index = pd.to_datetime(df.date)
    df.index = df.index.strftime('%Y-%m-%d %H:%M:%S').tolist()
    df = df.sort_index()
    # grid_chart = Grid(init_opts=opts.InitOpts(width="100%", height="100vh", theme=ThemeType.LIGHT))
    # 主图
    kline = Kline(init_opts=opts.InitOpts(width="100%", height="100vh", theme=ThemeType.LIGHT,
                                          animation_opts=opts.AnimationOpts(animation=False)))
    kline.add_xaxis(df.index.tolist())
    kline.add_yaxis("K线", df[['open', 'close', 'low', 'high']].values.tolist())
    # 在主图上叠加图标，表示不同的状态的点
    es_2 = EffectScatter()
    es_2_data = df[df['卖60'] == 1]
    if not es_2_data.empty:
        es_2.add_xaxis(es_2_data['date'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist())
        es_2.add_yaxis("卖60", df[df['卖60'] == 1]['high'], symbol="pin", symbol_size=8,
                       itemstyle_opts=opts.ItemStyleOpts(color="green"), label_opts=opts.LabelOpts(is_show=False))
    kline.overlap(es_2)

    es_1 = EffectScatter()
    es_1_data = df[df['买60'] == 1]
    if not es_1_data.empty:
        es_1.add_xaxis(es_1_data['date'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist())
        es_1.add_yaxis("买60", df[df['买60'] == 1]['low'], symbol="arrow", symbol_size=6,
                       itemstyle_opts=opts.ItemStyleOpts(color="red"), label_opts=opts.LabelOpts(is_show=False))
    kline.overlap(es_1)
    # 添加数据滚动条缩放配置
    # datazoom_opts = [
    #     opts.DataZoomOpts(
    #         type_="slider",
    #         xaxis_index=[0, 1,2],
    #         range_start=95,  # 起始百分比设置为 0
    #         range_end=100  # 结束百分比设置为 100
    #     ),
    #     opts.DataZoomOpts(
    #         type_="inside",
    #         xaxis_index=[0, 1,2],
    #         range_start=95,  # 起始百分比设置为 0
    #         range_end=100  # 结束百分比设置为 100
    #     )
    # ]

    kline.set_global_opts(
        title_opts=opts.TitleOpts(title="K线及均线" + code + table_name, pos_left='40%'),  # 标题位置
        legend_opts=opts.LegendOpts(pos_right="35%", pos_top="5%"),  # 图例位置

        # 设置滚动条
        datazoom_opts=[
            opts.DataZoomOpts(
                is_show=True,
                type_="inside",  # 内部缩放
                xaxis_index=[0, 1, 2, 3, 4, 5],  # 可缩放的x轴坐标编号多少个grid_chart加入，就需要设置几个编号3个设置0，1，2
                range_start=80, range_end=100,  # 初始显示范围
            ),
        ],
        yaxis_opts=opts.AxisOpts(
            is_scale=True,  # 缩放时是否显示0值
            splitarea_opts=opts.SplitAreaOpts(  # 分割显示设置
                is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)),
        ),
        tooltip_opts=opts.TooltipOpts(  # 提示框配置
            trigger="axis",  # 坐标轴触发提示
            axis_pointer_type="cross",  # 鼠标变为十字准星
            background_color="rgba(245, 245, 245, 0.8)",  # 背景颜色
            border_width=1, border_color="#ccc",  # 提示框配置
            textstyle_opts=opts.TextStyleOpts(color="#000"),  # 文字配置
        ),
        visualmap_opts=opts.VisualMapOpts(  # 视觉映射配置
            is_show=True, dimension=3,
            series_index=5, is_piecewise=True,
            pieces=[{"value": 1, "color": "#00da3c"}, {"value": -1, "color": "#ec0000"}, ],
        ),
        axispointer_opts=opts.AxisPointerOpts(  # 轴指示器配置
            is_show=True,
            link=[{"xAxisIndex": "all"}],
            label=opts.LabelOpts(background_color="#777"),  # 显示标签设置
        ),
        brush_opts=opts.BrushOpts(
            x_axis_index="all",  # 所有series
            brush_link="all",  # 不同系列选中后联动
            out_of_brush={"colorAlpha": 0.1},  # 高亮显示程度
            brush_type="lineX",  # 纵向选择
        ),
    )
    line = Line()
    line.add_xaxis(df.index.tolist())  # X轴数据
    # 为每条线单独指定线宽
    # line.add_yaxis('ma20', df.ma20.round(2).tolist(), is_smooth=False, is_symbol_show=False,
    #                itemstyle_opts=opts.ItemStyleOpts(color="red"),
    #                linestyle_opts=opts.LineStyleOpts(width=1))  # 指定线宽为 2
    # line.add_yaxis('ma60', df.ma60.round(2).tolist(), is_smooth=False, is_symbol_show=False,
    #                itemstyle_opts=opts.ItemStyleOpts(color="blue"),
    #                linestyle_opts=opts.LineStyleOpts(width=1))  # 指定线宽为 3
    # line.add_yaxis('junxa', df.junxa.round(2).tolist(), is_smooth=False, is_symbol_show=False,
    #                itemstyle_opts=opts.ItemStyleOpts(color="purple"),
    #                linestyle_opts=opts.LineStyleOpts(width=1))  # 指定线宽为 1
    # line.add_yaxis('junxb', df.junxb.round(2).tolist(), is_smooth=False, is_symbol_show=False,
    #                itemstyle_opts=opts.ItemStyleOpts(color="green"),
    #                linestyle_opts=opts.LineStyleOpts(width=1))  # 指定线宽为 4
    # line.add_yaxis('ma5', df.ma5.round(2).tolist(), is_smooth=False, is_symbol_show=False,
    #                itemstyle_opts=opts.ItemStyleOpts(color="white"),
    #                linestyle_opts=opts.LineStyleOpts(width=1))  # 指定线宽为 2
    # 可以在均线df.ma5上画不同颜色线段代表不同状态
    # y_上下穿多 = np.where(df['上下穿多'] == 1, df['上下穿多'].values * df.ma5.round(2).tolist(), None)
    # y_上下穿空 = np.where(df['上下穿空'] == 1, df['上下穿空'].values * df.ma5.round(2).tolist(), None)
    #
    # line.add_yaxis('y_多合并',  # 序列名称
    #                y_上下穿多.tolist(),
    #                is_smooth=True,  # 平滑曲线
    #                is_symbol_show=False,  # 不显示折线的小圆圈
    #                itemstyle_opts=opts.ItemStyleOpts(color="red"),
    #                linestyle_opts=opts.LineStyleOpts(width=3))
    #
    # line.add_yaxis('y_空合并',  # 序列名称
    #                y_上下穿空.tolist(),
    #                is_smooth=True,  # 平滑曲线
    #                is_symbol_show=False,  # 不显示折线的小圆圈
    #                itemstyle_opts=opts.ItemStyleOpts(color="blue"),
    #                linestyle_opts=opts.LineStyleOpts(width=3))

    line.set_series_opts(
        label_opts=opts.LabelOpts(is_show=False),  # 是否显示数据标签
    )
    line.set_global_opts(
        legend_opts=opts.LegendOpts(pos_right="20%", pos_top="5%"),  # 图例位置
        tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross")  # 趋势线设置
    )

    kline.overlap(line)

    # 添加dlx数据到图表


    # # 添加asset_list数据到图表
    # asset_list_line = Line()
    # asset_list_line.add_xaxis(df.index.tolist())  # X轴数据
    # asset_list_line.add_yaxis('利润',  # 序列名称
    #                           df['net_profit_list'].values.tolist(),
    #                           is_smooth=True,  # 平滑曲线
    #                           is_symbol_show=False,  # 不显示折线的小圆圈
    #                           itemstyle_opts=opts.ItemStyleOpts(color="#DEB887"),
    #                           )
    #
    # asset_list_line.set_series_opts(
    #     label_opts=opts.LabelOpts(is_show=False),  # 是否显示数据标签
    #     linestyle_opts=opts.LineStyleOpts(width=3),  # 线宽
    # )
    # asset_list_line.set_global_opts(
    #     xaxis_opts=opts.AxisOpts(is_scale=True),
    #     yaxis_opts=opts.AxisOpts(is_scale=True),
    #     tooltip_opts=None,
    #     axispointer_opts=opts.AxisPointerOpts(is_show=False),
    # )
    #
    # asset_es_1 = EffectScatter()
    # asset_es_1_data = df[df['多开_output'] == 1]
    # if not asset_es_1_data.empty:
    #     asset_es_1.add_xaxis(asset_es_1_data['date'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist())
    #     asset_es_1.add_yaxis("多开_output", df[df['多开_output'] == 1]['net_profit_list'], symbol="diamond",
    #                          symbol_size=4,
    #                          itemstyle_opts=opts.ItemStyleOpts(color="red"),
    #                          label_opts=opts.LabelOpts(is_show=False))
    # asset_list_line.overlap(asset_es_1)
    #
    # asset_es_2 = EffectScatter()
    # asset_es_2_data = df[df['空开_output'] == 1]
    # if not asset_es_2_data.empty:
    #     asset_es_2.add_xaxis(asset_es_2_data['date'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist())
    #     asset_es_2.add_yaxis("空开_output", df[df['空开_output'] == 1]['net_profit_list'], symbol="diamond",
    #                          symbol_size=4,
    #                          itemstyle_opts=opts.ItemStyleOpts(color="blue"),
    #                          label_opts=opts.LabelOpts(is_show=False))
    # asset_list_line.overlap(asset_es_2)
    #
    # asset_es_4 = EffectScatter()
    # asset_es_4_data = df[df['多开_output'] == 1]
    # if not asset_es_4_data.empty:
    #     asset_es_4.add_xaxis(asset_es_4_data['date'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist())
    #     asset_es_4.add_yaxis("多开_output", df[df['多开_output'] == 1]['net_profit_list'], symbol="diamond",
    #                          symbol_size=4,
    #                          itemstyle_opts=opts.ItemStyleOpts(color="red"),
    #                          label_opts=opts.LabelOpts(is_show=False))
    # asset_list_line.overlap(asset_es_4)
    #
    # asset_es_3 = EffectScatter()
    # asset_es_3_data = df[df['空仓_output'] == 1]
    # if not asset_es_3_data.empty:
    #     asset_es_3.add_xaxis(asset_es_3_data['date'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist())
    #     asset_es_3.add_yaxis("空仓_output", df[df['空仓_output'] == 1]['net_profit_list'], symbol="diamond",
    #                          symbol_size=4,
    #                          itemstyle_opts=opts.ItemStyleOpts(color="black"),
    #                          label_opts=opts.LabelOpts(is_show=False))
    # asset_list_line.overlap(asset_es_3)



    # 图像排列

    grid_chart = Grid(
        init_opts=opts.InitOpts(
            width="100%",  # 显示图形宽度
            height="100vh",
            animation_opts=opts.AnimationOpts(animation=False),  # 关闭动画
            page_title=f"{zhibiaomc}K线{code}"  # 自定义网页标题
        )
    )

    grid_chart.add(  # 加入均线图
        kline,
        grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", height="100%"),
    )

    # grid_chart.add(  # 加入资金曲线图
    #     asset_list_line,
    #     grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", height="100%"),
    # )
    # grid_chart.add(  # 加入动量图
    #     dlx_line,
    #     grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", pos_top="40%", height="20%"),
    # )
    # grid_chart.add(  # 加入动量图
    #     selljdx_line,
    #     grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", pos_top="60%", height="20%"),
    # )
    # grid_chart.add(  # 加入动量图
    #     dlx3_line,
    #     grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", pos_top="75%", height="15%"),
    # )
    #
    # grid_chart.add(  # 加入动量图
    #     dlx2_line,
    #     grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", pos_top="90%", height="10%"),
    # )
    # 生成 HTML 文件并嵌入 JavaScript 代码实现自动刷新
    html_content = grid_chart.render_embed()
    refresh_interval = 1 * 60  # 5 分钟，单位为秒
    refresh_script = f'<script>setInterval(function() {{ location.reload(); }}, {refresh_interval * 1000});</script>'
    full_html = f'<!DOCTYPE html><html><head><meta charset="UTF-8">{refresh_script}</head><body>{html_content}</body></html>'

    with open(f"kdj_chart_{code}{zhibiaomc}.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"网页地址：kdj_chart_{code}{zhibiaomc}.html")