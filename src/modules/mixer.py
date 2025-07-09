"""
信号ミキシングモジュール
複数の入力信号を重み付けして一つの出力に混合
"""

import sys
import os
import logging
from typing import Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.modules.base_module import BaseModule

logger = logging.getLogger(__name__)


class Mixer(BaseModule):
    """
    信号ミキシングモジュール
    複数の入力信号を重み付けして一つの出力に混合
    """

    def __init__(self, name: str = "Mixer", inputs: int = 4):
        super().__init__(name)

        # 入力端子とレベル調整パラメータ
        self.num_inputs = inputs
        for i in range(inputs):
            self.add_input(f"input{i}", 0)
            self.parameters[f"level{i}"] = 0.5  # 0.0-1.0

        # 出力端子
        self.add_output("output")

        # マスターレベル
        self.parameters["master_level"] = 0.8

    def start(self):
        """pyoオブジェクトの初期化"""
        from pyo import Sig

        # 各入力用のSigオブジェクト
        self.input_sigs = []
        for i in range(self.num_inputs):
            sig = Sig(0)  # 初期値0
            self.input_sigs.append(sig)
            self.pyo_objects.append(sig)

        self.is_active = True
        logger.info(f"{self.name} started with {self.num_inputs} inputs")

    def process(self):
        """入力信号を混合"""
        if not self.is_active:
            return

        from pyo import Mix

        # 接続されている入力を収集
        active_inputs = []
        for i in range(self.num_inputs):
            input_val = self.get_input_value(f"input{i}")
            level = self.parameters[f"level{i}"]

            if input_val != 0:  # 接続されている場合
                # レベル調整して追加
                self.input_sigs[i].setValue(input_val)
                active_inputs.append(self.input_sigs[i] * level)

        if active_inputs:
            # pyoのMixで混合
            mixed = Mix(active_inputs, voices=1)
            master_level = self.parameters["master_level"]
            self.outputs["output"] = mixed * master_level
        else:
            self.outputs["output"] = 0

        logger.debug(f"{self.name} processed: {len(active_inputs)} active inputs")

    def set_input_level(self, input_index: int, level: float):
        """入力レベルを設定"""
        if 0 <= input_index < self.num_inputs:
            self.parameters[f"level{input_index}"] = max(0.0, min(1.0, level))
            logger.info(f"{self.name} input{input_index} level set to {level}")

    def set_master_level(self, level: float):
        """マスターレベルを設定"""
        self.parameters["master_level"] = max(0.0, min(1.0, level))
        logger.info(f"{self.name} master level set to {level}")

    def get_info(self) -> Dict[str, Any]:
        """モジュール情報の取得"""
        info = super().get_info()
        info["num_inputs"] = self.num_inputs
        info["input_levels"] = {f"level{i}": self.parameters[f"level{i}"] for i in range(self.num_inputs)}
        info["master_level"] = self.parameters["master_level"]
        return info
