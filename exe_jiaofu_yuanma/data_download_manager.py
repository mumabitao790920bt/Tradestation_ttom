#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的数据下载管理界面
支持多合约数据下载，每个合约独立数据库
"""

import sys
import os
import json
import threading
import time
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QTextEdit, QListWidget, QListWidgetItem, QMessageBox, QGroupBox, QGridLayout, QProgressBar, QSpinBox, QCheckBox
from binance_data_collector_fixed import BinanceDataCollectorFixed


class DataDownloadWorker(QThread):
    """数据下载工作线程"""
    status_update = pyqtSignal(str)  # 状态更新信号
    progress_update = pyqtSignal(str, int)  # 进度更新信号 (symbol, progress)
    error_occurred = pyqtSignal(str, str)  # 错误信号 (symbol, error_msg)
    
    def __init__(self, symbol, db_path, use_futures=True):
        super().__init__()
        self.symbol = symbol
        self.db_path = db_path
        self.use_futures = use_futures
        self.collector = None
        self.is_running = False
        
    def run(self):
        """运行数据收集"""
        try:
            self.status_update.emit(f"开始收集 {self.symbol} 数据...")
            
            # 创建修复版数据收集器
            self.collector = BinanceDataCollectorFixed(
                db_path=self.db_path,
                symbol=self.symbol,
                use_futures=self.use_futures
            )
            
            self.is_running = True
            self.status_update.emit(f"{self.symbol} 数据收集已启动")
            
            # 开始收集数据 - 收集多个时间周期
            self.collector.start_collection(['1m', '3m', '5m', '15m', '30m', '1h'])
            
            # 持续运行
            while self.is_running:
                self.progress_update.emit(self.symbol, 100)  # 表示正在运行
                time.sleep(1)
                
        except Exception as e:
            self.error_occurred.emit(self.symbol, str(e))
        finally:
            if self.collector:
                self.collector.stop_collection()
            self.status_update.emit(f"{self.symbol} 数据收集已停止")
    
    def stop(self):
        """停止数据收集"""
        self.is_running = False
        if self.collector:
            self.collector.stop_collection()


class DataDownloadManager(QMainWindow):
    """数据下载管理主界面"""
    
    def __init__(self):
        super().__init__()
        self.download_workers = {}  # 存储下载工作线程
        self.max_concurrent_downloads = 10  # 最大并发下载数
        self.main_symbol = None  # 主界面选择的合约
        self.config_file = "download_config.json"
        
        self.init_ui()
        self.load_config()
        self.load_main_symbol()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("数据下载管理器 - 币安永续合约")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 1. 主合约显示区域
        main_symbol_group = QGroupBox("主交易合约")
        main_symbol_layout = QHBoxLayout(main_symbol_group)
        
        self.main_symbol_label = QLabel("主交易合约: 未设置")
        self.main_symbol_label.setStyleSheet("font-weight: bold; color: blue;")
        main_symbol_layout.addWidget(self.main_symbol_label)
        
        main_symbol_layout.addStretch()
        
        self.refresh_main_symbol_btn = QPushButton("刷新主合约")
        self.refresh_main_symbol_btn.clicked.connect(self.load_main_symbol)
        main_symbol_layout.addWidget(self.refresh_main_symbol_btn)
        
        main_layout.addWidget(main_symbol_group)
        
        # 2. 合约管理区域
        symbol_management_group = QGroupBox("合约管理")
        symbol_management_layout = QGridLayout(symbol_management_group)
        
        # 手动输入合约
        symbol_management_layout.addWidget(QLabel("手动添加合约:"), 0, 0)
        self.symbol_input = QTextEdit()
        self.symbol_input.setMaximumHeight(80)
        self.symbol_input.setPlaceholderText("输入合约名称，多个合约用逗号分隔\n例如: ETHUSDT,ADAUSDT,SOLUSDT")
        symbol_management_layout.addWidget(self.symbol_input, 0, 1)
        
        # 添加按钮
        self.add_symbols_btn = QPushButton("添加合约")
        self.add_symbols_btn.clicked.connect(self.add_symbols)
        symbol_management_layout.addWidget(self.add_symbols_btn, 0, 2)
        
        # 合约列表
        symbol_management_layout.addWidget(QLabel("下载合约列表:"), 1, 0)
        self.symbol_list = QListWidget()
        self.symbol_list.setMaximumHeight(150)
        symbol_management_layout.addWidget(self.symbol_list, 1, 1, 1, 2)
        
        # 删除选中合约按钮
        self.remove_symbol_btn = QPushButton("删除选中合约")
        self.remove_symbol_btn.clicked.connect(self.remove_selected_symbol)
        symbol_management_layout.addWidget(self.remove_symbol_btn, 2, 1)
        
        main_layout.addWidget(symbol_management_group)
        
        # 3. 下载控制区域
        download_control_group = QGroupBox("下载控制")
        download_control_layout = QHBoxLayout(download_control_group)
        
        # 启动/停止按钮
        self.start_download_btn = QPushButton("启动数据下载")
        self.start_download_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        self.start_download_btn.clicked.connect(self.start_download)
        download_control_layout.addWidget(self.start_download_btn)
        
        self.stop_download_btn = QPushButton("停止数据下载")
        self.stop_download_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; }")
        self.stop_download_btn.clicked.connect(self.stop_download)
        self.stop_download_btn.setEnabled(False)
        download_control_layout.addWidget(self.stop_download_btn)
        
        # 最大并发数设置
        download_control_layout.addWidget(QLabel("最大并发数:"))
        self.max_concurrent_spin = QSpinBox()
        self.max_concurrent_spin.setRange(1, 10)
        self.max_concurrent_spin.setValue(10)
        self.max_concurrent_spin.valueChanged.connect(self.update_max_concurrent)
        download_control_layout.addWidget(self.max_concurrent_spin)
        
        download_control_layout.addStretch()
        
        main_layout.addWidget(download_control_group)
        
        # 4. 下载状态区域
        status_group = QGroupBox("下载状态")
        status_layout = QVBoxLayout(status_group)
        
        # 状态显示
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(200)
        self.status_text.setReadOnly(True)
        status_layout.addWidget(self.status_text)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(status_group)
        
        # 5. 底部按钮区域
        bottom_layout = QHBoxLayout()
        
        self.save_config_btn = QPushButton("保存配置")
        self.save_config_btn.clicked.connect(self.save_config)
        bottom_layout.addWidget(self.save_config_btn)
        
        self.load_config_btn = QPushButton("加载配置")
        self.load_config_btn.clicked.connect(self.load_config)
        bottom_layout.addWidget(self.load_config_btn)
        
        bottom_layout.addStretch()
        
        self.clear_log_btn = QPushButton("清空日志")
        self.clear_log_btn.clicked.connect(self.clear_log)
        bottom_layout.addWidget(self.clear_log_btn)
        
        main_layout.addLayout(bottom_layout)
        
        # 设置定时器用于更新状态
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # 每秒更新一次
        
    def load_main_symbol(self):
        """从主界面配置加载主交易合约"""
        try:
            if os.path.exists("strategy_config.json"):
                with open("strategy_config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                    main_symbol = config.get("trading_symbol", "")
                    if main_symbol:
                        self.main_symbol = main_symbol
                        self.main_symbol_label.setText(f"主交易合约: {main_symbol}")
                        self.log_message(f"已加载主交易合约: {main_symbol}")
                        
                        # 确保主合约在下载列表中
                        if main_symbol not in self.get_symbol_list():
                            self.add_symbol_to_list(main_symbol)
                            self.log_message(f"已将主合约 {main_symbol} 添加到下载列表")
                    else:
                        self.main_symbol_label.setText("主交易合约: 未设置")
                        self.log_message("主界面未设置交易合约")
            else:
                self.log_message("未找到主界面配置文件")
        except Exception as e:
            self.log_message(f"加载主合约失败: {str(e)}")
    
    def add_symbols(self):
        """添加合约到下载列表"""
        text = self.symbol_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "警告", "请输入合约名称")
            return
        
        # 解析输入的合约名称
        symbols = [s.strip().upper() for s in text.split(",") if s.strip()]
        
        added_count = 0
        for symbol in symbols:
            if symbol and symbol not in self.get_symbol_list():
                self.add_symbol_to_list(symbol)
                added_count += 1
        
        if added_count > 0:
            self.log_message(f"已添加 {added_count} 个合约: {', '.join(symbols)}")
            self.symbol_input.clear()
        else:
            QMessageBox.information(self, "提示", "所有合约已存在于列表中")
    
    def add_symbol_to_list(self, symbol):
        """添加单个合约到列表"""
        item = QListWidgetItem(symbol)
        if symbol == self.main_symbol:
            item.setBackground(QtGui.QColor(200, 255, 200))  # 绿色背景表示主合约
            item.setToolTip("主交易合约（不可删除）")
        self.symbol_list.addItem(item)
    
    def remove_selected_symbol(self):
        """删除选中的合约"""
        current_item = self.symbol_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请选择要删除的合约")
            return
        
        symbol = current_item.text()
        
        # 检查是否是主合约
        if symbol == self.main_symbol:
            QMessageBox.warning(self, "警告", "主交易合约不能删除")
            return
        
        # 检查是否正在下载
        if symbol in self.download_workers:
            QMessageBox.warning(self, "警告", f"合约 {symbol} 正在下载中，请先停止下载")
            return
        
        # 确认删除
        reply = QMessageBox.question(self, "确认删除", f"确定要删除合约 {symbol} 吗？")
        if reply == QMessageBox.Yes:
            self.symbol_list.takeItem(self.symbol_list.row(current_item))
            self.log_message(f"已删除合约: {symbol}")
    
    def get_symbol_list(self):
        """获取当前合约列表"""
        symbols = []
        for i in range(self.symbol_list.count()):
            symbols.append(self.symbol_list.item(i).text())
        return symbols
    
    def start_download(self):
        """启动数据下载"""
        symbols = self.get_symbol_list()
        if not symbols:
            QMessageBox.warning(self, "警告", "请先添加要下载的合约")
            return
        
        # 检查并发数限制
        if len(symbols) > self.max_concurrent_downloads:
            QMessageBox.warning(self, "警告", f"合约数量超过最大并发数限制 ({self.max_concurrent_downloads})")
            return
        
        # 启动下载
        started_count = 0
        for symbol in symbols:
            if symbol not in self.download_workers:
                db_path = f"{symbol.lower()}_futures_data.db"
                worker = DataDownloadWorker(symbol, db_path, use_futures=True)
                
                # 连接信号
                worker.status_update.connect(self.log_message)
                worker.progress_update.connect(self.update_progress)
                worker.error_occurred.connect(self.handle_error)
                
                # 启动工作线程
                worker.start()
                self.download_workers[symbol] = worker
                started_count += 1
        
        if started_count > 0:
            self.log_message(f"已启动 {started_count} 个合约的数据下载")
            self.start_download_btn.setEnabled(False)
            self.stop_download_btn.setEnabled(True)
            self.progress_bar.setVisible(True)
        else:
            QMessageBox.information(self, "提示", "所有合约已在下载中")
    
    def stop_download(self):
        """停止数据下载"""
        if not self.download_workers:
            QMessageBox.information(self, "提示", "没有正在下载的合约")
            return
        
        # 停止所有下载
        for symbol, worker in self.download_workers.items():
            worker.stop()
            worker.wait()  # 等待线程结束
        
        self.download_workers.clear()
        self.log_message("已停止所有数据下载")
        
        self.start_download_btn.setEnabled(True)
        self.stop_download_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
    
    def update_progress(self, symbol, progress):
        """更新进度"""
        # 这里可以根据需要实现进度显示
        pass
    
    def handle_error(self, symbol, error_msg):
        """处理错误"""
        self.log_message(f"❌ {symbol} 下载错误: {error_msg}")
    
    def update_status(self):
        """更新状态显示"""
        if self.download_workers:
            active_count = sum(1 for worker in self.download_workers.values() if worker.is_running)
            self.progress_bar.setValue(active_count * 10)  # 简单的进度显示
            self.progress_bar.setFormat(f"正在下载: {active_count}/{len(self.download_workers)} 个合约")
    
    def log_message(self, message):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.status_text.append(formatted_message)
        
        # 自动滚动到底部
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """清空日志"""
        self.status_text.clear()
    
    def update_max_concurrent(self, value):
        """更新最大并发数"""
        self.max_concurrent_downloads = value
        self.log_message(f"最大并发数已设置为: {value}")
    
    def save_config(self):
        """保存配置"""
        try:
            config = {
                "symbols": self.get_symbol_list(),
                "max_concurrent": self.max_concurrent_downloads,
                "main_symbol": self.main_symbol
            }
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            self.log_message("配置已保存")
            QMessageBox.information(self, "成功", "配置已保存")
            
        except Exception as e:
            self.log_message(f"保存配置失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")
    
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                # 加载合约列表
                symbols = config.get("symbols", [])
                self.symbol_list.clear()
                for symbol in symbols:
                    self.add_symbol_to_list(symbol)
                
                # 加载最大并发数
                max_concurrent = config.get("max_concurrent", 10)
                self.max_concurrent_spin.setValue(max_concurrent)
                
                # 加载主合约
                main_symbol = config.get("main_symbol", "")
                if main_symbol:
                    self.main_symbol = main_symbol
                    self.main_symbol_label.setText(f"主交易合约: {main_symbol}")
                
                self.log_message("配置已加载")
            else:
                self.log_message("未找到配置文件，使用默认配置")
                
        except Exception as e:
            self.log_message(f"加载配置失败: {str(e)}")
    
    def closeEvent(self, event):
        """关闭事件处理"""
        if self.download_workers:
            reply = QMessageBox.question(self, "确认关闭", 
                                       "有合约正在下载中，确定要关闭吗？\n关闭将停止所有下载。",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.stop_download()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("数据下载管理器")
    app.setApplicationVersion("1.0")
    
    # 创建主窗口
    window = DataDownloadManager()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
