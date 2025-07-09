"""
CV演算モジュール
2つのCV信号を数学的に演算
"""

import sys
import os
import logging
from typing import Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.modules.base_module import BaseModule

logger = logging.getLogger(__name__)


class CVMath(BaseModule):
    """
    CV演算モジュール
    2つのCV信号を数学的に演算
    """

    def __init__(self, name: str = "CVMath", operation: str = "add"):
        super().__init__(name)

        # 入力端子
        self.add_input("input_a", 0)
        self.add_input("input_b", 0)

        # 出力端子
        self.add_output("output")

        # 演算パラメータ
        self.parameters["operation"] = operation  # "add", "subtract", "multiply", "divide"
        self.parameters["offset"] = 0.0  # 結果にオフセット追加
        self.parameters["scale"] = 1.0  # 結果のスケール

    def start(self):
        """pyoオブジェクトの初期化"""
        from pyo import Sig

        # 入力信号用のSigオブジェクト
        self.sig_a = Sig(0)
        self.sig_b = Sig(0)
        self.pyo_objects.extend([self.sig_a, self.sig_b])

        self.is_active = True
        logger.info(f"{self.name} started with operation: {self.parameters['operation']}")

    def process(self):
        """CV信号を演算"""
        if not self.is_active:
            return

        # 入力値を取得
        input_a = self.get_input_value("input_a")
        input_b = self.get_input_value("input_b")

        # Sigオブジェクトに値を設定
        self.sig_a.setValue(input_a)
        self.sig_b.setValue(input_b)

        # 演算実行
        operation = self.parameters["operation"]
        if operation == "add":
            result = self.sig_a + self.sig_b
        elif operation == "subtract":
            result = self.sig_a - self.sig_b
        elif operation == "multiply":
            result = self.sig_a * self.sig_b
        elif operation == "divide":
            # ゼロ除算防止
            result = self.sig_a / (self.sig_b + 0.001)
        else:
            result = self.sig_a

        # スケールとオフセット適用
        scale = self.parameters["scale"]
        offset = self.parameters["offset"]
        self.outputs["output"] = result * scale + offset

        logger.debug(f"{self.name} processed: {input_a} {operation} {input_b} = {result}")

    def set_operation(self, operation: str):
        """演算タイプを設定"""
        valid_ops = ["add", "subtract", "multiply", "divide"]
        if operation in valid_ops:
            self.parameters["operation"] = operation
            logger.info(f"{self.name} operation set to {operation}")
        else:
            logger.warning(f"{self.name} invalid operation: {operation}")

    def set_offset(self, offset: float):
        """オフセットを設定"""
        self.parameters["offset"] = offset
        logger.info(f"{self.name} offset set to {offset}")

    def set_scale(self, scale: float):
        """スケールを設定"""
        self.parameters["scale"] = scale
        logger.info(f"{self.name} scale set to {scale}")

    def get_info(self) -> Dict[str, Any]:
        """モジュール情報の取得"""
        info = super().get_info()
        info["operation"] = self.parameters["operation"]
        info["offset"] = self.parameters["offset"]
        info["scale"] = self.parameters["scale"]
        return info
