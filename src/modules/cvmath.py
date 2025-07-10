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
        # 演算結果を保存するための変数
        self.current_result = None
        
        self.is_active = True
        logger.info(f"{self.name} started with operation: {self.parameters['operation']}")
        
        # 初期出力を構築
        self._rebuild_output()

    def _rebuild_output(self):
        """演算結果のpyoオブジェクトを再構築"""
        if not self.is_active:
            logger.warning(f"{self.name} _rebuild_output called but module is not active")
            return

        # 古いオブジェクトを削除
        if self.current_result is not None and self.current_result in self.pyo_objects:
            self.pyo_objects.remove(self.current_result)
            logger.debug(f"{self.name} removed old result from pyo_objects")

        # 入力値を取得
        input_a = self.get_input_value("input_a")
        input_b = self.get_input_value("input_b")
        
        logger.info(f"{self.name} rebuilding output: input_a={input_a} (type: {type(input_a)}), input_b={input_b} (type: {type(input_b)})")

        # 入力値をpyoオブジェクトに変換
        from pyo import Sig
        
        if hasattr(input_a, 'out'):  # pyoオブジェクトの場合
            sig_a = input_a
        else:  # 数値の場合
            sig_a = Sig(input_a)
            self.pyo_objects.append(sig_a)
            
        if hasattr(input_b, 'out'):  # pyoオブジェクトの場合
            sig_b = input_b
        else:  # 数値の場合
            sig_b = Sig(input_b)
            self.pyo_objects.append(sig_b)

        # 演算実行
        operation = self.parameters["operation"]
        scale = self.parameters["scale"]
        offset = self.parameters["offset"]
        
        logger.info(f"{self.name} rebuilding with operation={operation}, scale={scale}, offset={offset}")
        
        if operation == "add":
            result = sig_a + sig_b
        elif operation == "subtract":
            result = sig_a - sig_b
        elif operation == "multiply":
            result = sig_a * sig_b
        elif operation == "divide":
            # ゼロ除算防止
            result = sig_a / (sig_b + 0.001)
        else:
            result = sig_a

        # スケールとオフセット適用
        self.current_result = result * scale + offset
        self.pyo_objects.append(self.current_result)
        self.outputs["output"] = self.current_result

        logger.info(f"{self.name} rebuilt output successfully: operation={operation}, result_object={type(self.current_result)}")

    def process(self):
        """CV信号を演算"""
        if not self.is_active:
            logger.warning(f"{self.name} process called but module is not active")
            return

        logger.info(f"{self.name} process called - rebuilding output")
        self._rebuild_output()
        logger.info(f"{self.name} process completed")

    def set_operation(self, operation: str):
        """演算タイプを設定"""
        valid_ops = ["add", "subtract", "multiply", "divide"]
        if operation in valid_ops:
            logger.info(f"{self.name} changing operation from {self.parameters['operation']} to {operation}")
            self.parameters["operation"] = operation
            self._rebuild_output()
            logger.info(f"{self.name} operation set to {operation} and output rebuilt")
        else:
            logger.warning(f"{self.name} invalid operation: {operation}")

    def set_offset(self, offset: float):
        """オフセットを設定"""
        logger.info(f"{self.name} changing offset from {self.parameters['offset']} to {offset}")
        self.parameters["offset"] = offset
        self._rebuild_output()
        logger.info(f"{self.name} offset set to {offset} and output rebuilt")

    def set_scale(self, scale: float):
        """スケールを設定"""
        logger.info(f"{self.name} changing scale from {self.parameters['scale']} to {scale}")
        self.parameters["scale"] = scale
        self._rebuild_output()
        logger.info(f"{self.name} scale set to {scale} and output rebuilt")

    def get_info(self) -> Dict[str, Any]:
        """モジュール情報の取得"""
        info = super().get_info()
        info["operation"] = self.parameters["operation"]
        info["offset"] = self.parameters["offset"]
        info["scale"] = self.parameters["scale"]
        return info
