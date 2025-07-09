import time
import sys
import os
import logging
from typing import Dict, List, Any

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.connection import ConnectionManager

logger = logging.getLogger(__name__)


class BaseModule:
    """
    モジュラーシンセの基本クラス
    すべてのモジュール（VCO, VCF, LFO, VCA, ENV）の基底クラス
    """

    def __init__(self, name: str = "BaseModule"):
        self.name = name
        self.is_active = False

        # 入力端子の定義（辞書形式）
        self.inputs: Dict[str, Any] = {}

        # 出力端子の定義（辞書形式）
        self.outputs: Dict[str, Any] = {}

        # パラメータの定義
        self.parameters: Dict[str, Any] = {}

        # 処理に使用するpyoオブジェクト
        self.pyo_objects: List[Any] = []

        # 最後に更新された時刻
        self.last_update = time.time()

    def add_input(self, name: str, default_value: Any = None):
        """
        入力端子を追加

        Args:
            name: 入力端子名
            default_value: デフォルト値
        """
        self.inputs[name] = default_value

    def add_output(self, name: str):
        """
        出力端子を追加

        Args:
            name: 出力端子名
        """
        self.outputs[name] = None

    def connect_to(self, input_name: str, source_module: "BaseModule", output_name: str):
        """
        他のモジュールからの接続を設定

        Args:
            input_name: 自分の入力端子名
            source_module: 接続元のモジュール
            output_name: 接続元の出力端子名
        """
        if input_name not in self.inputs:
            raise ValueError(f"Input '{input_name}' not found in {self.name}")

        if output_name not in source_module.outputs:
            raise ValueError(f"Output '{output_name}' not found in {source_module.name}")

        # 接続を設定
        self.inputs[input_name] = source_module.outputs[output_name]
        logger.info(f"Connected {source_module.name}.{output_name} to {self.name}.{input_name}")

    def disconnect(self, input_name: str):
        """
        入力端子の接続を切断

        Args:
            input_name: 切断する入力端子名
        """
        if input_name in self.inputs:
            self.inputs[input_name] = None
            logger.info(f"Disconnected {self.name}.{input_name}")

    def get_input_value(self, input_name: str, default_value: Any = 0):
        """
        入力値を取得

        Args:
            input_name: 入力端子名
            default_value: 接続がない場合のデフォルト値

        Returns:
            入力値（接続がない場合はdefault_value）
        """
        if input_name not in self.inputs:
            return default_value

        input_value = self.inputs[input_name]
        if input_value is None:
            return default_value

        return input_value

    def set_parameter(self, param_name: str, value: Any):
        """
        パラメータを設定

        Args:
            param_name: パラメータ名
            value: 設定値
        """
        self.parameters[param_name] = value
        logger.info(f"Set {self.name}.{param_name} = {value}")

    def get_parameter(self, param_name: str, default_value: Any = 0):
        """
        パラメータを取得

        Args:
            param_name: パラメータ名
            default_value: デフォルト値

        Returns:
            パラメータ値
        """
        return self.parameters.get(param_name, default_value)

    def start(self):
        """
        モジュールの処理を開始
        """
        if not self.is_active:
            self.is_active = True
            self._initialize()
            logger.info(f"{self.name} started")

    def stop(self):
        """
        モジュールの処理を停止
        """
        if self.is_active:
            self.is_active = False
            self._cleanup()
            logger.info(f"{self.name} stopped")

    def set_connection_manager(self, connection_manager: ConnectionManager):
        """接続マネージャーを設定"""
        self.connection_manager = connection_manager

    def get_connected_inputs(self) -> List[str]:
        """接続されている入力端子のリストを取得"""
        if not hasattr(self, "connection_manager"):
            return []

        connected = []
        for input_name in self.inputs:
            connections = self.connection_manager.get_input_connections(self.name, input_name)
            if connections:
                connected.append(input_name)
        return connected

    def _initialize(self):
        """
        初期化処理（子クラスでオーバーライド）
        """
        pass

    def _cleanup(self):
        """
        終了処理（子クラスでオーバーライド）
        """
        for obj in self.pyo_objects:
            if hasattr(obj, "stop"):
                obj.stop()

    def process(self):
        """
        メイン処理（子クラスで実装）
        """
        raise NotImplementedError("process method must be implemented by subclass")

    def update(self):
        """
        定期的な更新処理
        """
        if self.is_active:
            self.process()
            self.last_update = time.time()

    def get_info(self) -> Dict[str, Any]:
        """
        モジュールの情報を取得

        Returns:
            モジュール情報の辞書
        """
        return {
            "name": self.name,
            "is_active": self.is_active,
            "inputs": list(self.inputs.keys()),
            "outputs": list(self.outputs.keys()),
            "parameters": self.parameters,
            "last_update": self.last_update,
        }

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def __repr__(self) -> str:
        return self.__str__()
