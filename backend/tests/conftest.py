"""pytest 配置：设置 sys.path 以便测试导入 app 包。"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))