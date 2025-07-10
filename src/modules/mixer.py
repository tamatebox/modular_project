"""
信号ミキシングモジュール
複数の入力信号を重み付けして一つの出力に混合
"""

import sys
import os
import logging
from typing import Dict, Any
from pyo import Sig, Mix

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

        # 混合出力オブジェクト
        self.mixed_output = None

    def start(self):
        """pyoオブジェクトの初期化"""
        # 各入力用のSigオブジェクト
        self.input_sigs = []
        for i in range(self.num_inputs):
            sig = Sig(0)  # 初期値0
            self.input_sigs.append(sig)
            self.pyo_objects.append(sig)

        # 初期の無音出力を設定
        self.mixed_output = Sig(0)
        self.outputs["output"] = self.mixed_output
        self.pyo_objects.append(self.mixed_output)

        self.is_active = True
        logger.info(f"{self.name} started with {self.num_inputs} inputs")

    def process(self):
        """入力信号を混合"""
        if not self.is_active:
            logger.warning(f"{self.name} process() called but module is not active")
            return

        logger.info(f"=== {self.name} process() start ===")
        
        # 接続されている入力を収集
        active_inputs = []
        for i in range(self.num_inputs):
            input_val = self.get_input_value(f"input{i}")
            level = self.parameters[f"level{i}"]
            
            logger.info(f"{self.name} input{i}: type={type(input_val)}, value={input_val}, level={level}")
            
            if hasattr(input_val, "out") and input_val != 0 and level > 0:  # PyoObjectで接続され、レベルが0より大きい場合
                # レベル調整して追加（ArithmeticDummyを回避）
                scaled_input = Sig(input_val, mul=level)
                active_inputs.append(scaled_input)
                logger.info(f"{self.name} input{i} added to active_inputs (scaled by {level})")
            else:
                logger.info(f"{self.name} input{i} skipped - not valid PyoObject or level=0")

        logger.info(f"{self.name} total active_inputs: {len(active_inputs)}")

        if active_inputs:
            # pyoのMixで混合
            mixed = Mix(active_inputs, voices=1)
            master_level = self.parameters["master_level"]
            logger.info(f"{self.name} created Mix object with {len(active_inputs)} inputs, master_level={master_level}")

            # 既存の出力を新しい混合結果に更新
            if self.mixed_output:
                # 古い出力を新しい混合結果に置き換え（Mixオブジェクトに直接mulを適用）
                mixed.setMul(master_level)
                new_output = mixed
                self.outputs["output"] = new_output
                # pyoオブジェクトリストを更新
                if self.mixed_output in self.pyo_objects:
                    self.pyo_objects.remove(self.mixed_output)
                self.mixed_output = new_output
                self.pyo_objects.append(self.mixed_output)
                logger.info(f"{self.name} output updated with Mix object, setMul({master_level})")
        else:
            # 無音を出力
            if self.mixed_output and self.mixed_output in self.pyo_objects:
                self.pyo_objects.remove(self.mixed_output)
            self.mixed_output = Sig(0)
            self.outputs["output"] = self.mixed_output
            self.pyo_objects.append(self.mixed_output)
            logger.warning(f"{self.name} no active inputs - output set to silence")

        logger.info(f"=== {self.name} process() end - output: {self.outputs['output']} ===")

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
