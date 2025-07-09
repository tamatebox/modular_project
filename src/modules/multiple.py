"""
信号分岐モジュール
一つの入力信号を複数の出力に分岐する
"""

import sys
import os
import logging
from typing import Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.modules.base_module import BaseModule

logger = logging.getLogger(__name__)


class Multiple(BaseModule):
    """
    信号分岐モジュール
    一つの入力信号を複数の出力に分岐する
    """

    def __init__(self, name: str = "Multiple", outputs: int = 4):
        super().__init__(name)

        # 入力端子
        self.add_input("input", 0)

        # 出力端子（デフォルト4個）
        self.num_outputs = outputs
        for i in range(outputs):
            self.add_output(f"output{i}")

    def start(self):
        """pyoオブジェクトの初期化"""
        self.is_active = True
        # 分岐は単純なコピーなので特別なpyoオブジェクトは不要
        logger.info(f"{self.name} started with {self.num_outputs} outputs")

    def process(self):
        """入力信号を全出力にコピー"""
        if not self.is_active:
            return

        input_signal = self.get_input_value("input")
        
        # デバッグ情報を追加
        logger.debug(f"{self.name} input signal: {input_signal}")
        logger.debug(f"{self.name} input value type: {type(input_signal)}")

        # 全出力に同じ信号を設定
        for i in range(self.num_outputs):
            self.outputs[f"output{i}"] = input_signal

        logger.debug(f"{self.name} processed: input={input_signal}, outputs={self.num_outputs}")

    def get_info(self) -> Dict[str, Any]:
        """モジュール情報の取得"""
        info = super().get_info()
        info["num_outputs"] = self.num_outputs
        return info
