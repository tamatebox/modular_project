from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


class SignalType(Enum):
    """信号の種類"""

    AUDIO = "audio"  # オーディオ信号（可聴域）
    CV = "cv"  # コントロール電圧
    GATE = "gate"  # ゲート信号（ON/OFF）
    TRIGGER = "trigger"  # トリガー信号（瞬間的）


@dataclass
class Connection:
    """
    モジュール間の接続を表現するクラス
    """

    source_module: str  # 接続元モジュール名
    source_output: str  # 接続元出力端子名
    target_module: str  # 接続先モジュール名
    target_input: str  # 接続先入力端子名
    signal_type: SignalType  # 信号の種類
    attenuation: float = 1.0  # 減衰率（0.0-1.0）

    def __str__(self):
        return f"{self.source_module}.{self.source_output} -> {self.target_module}.{self.target_input} ({self.signal_type.value})"


class ConnectionManager:
    """
    接続を管理するクラス
    """

    def __init__(self):
        self.connections: List[Connection] = []
        self.modules: Dict[str, Any] = {}  # モジュール名 -> モジュールオブジェクト

    def register_module(self, module_name: str, module_obj: Any):
        """
        モジュールを登録

        Args:
            module_name: モジュール名
            module_obj: モジュールオブジェクト
        """
        self.modules[module_name] = module_obj
        print(f"Registered module: {module_name}")

    def connect(
        self,
        source_module: str,
        source_output: str,
        target_module: str,
        target_input: str,
        signal_type: SignalType = SignalType.AUDIO,
        attenuation: float = 1.0,
    ) -> bool:
        """
        モジュール間を接続

        Args:
            source_module: 接続元モジュール名
            source_output: 接続元出力端子名
            target_module: 接続先モジュール名
            target_input: 接続先入力端子名
            signal_type: 信号の種類
            attenuation: 減衰率

        Returns:
            成功したかどうか
        """
        # モジュールの存在確認
        if source_module not in self.modules:
            print(f"Error: Source module '{source_module}' not found")
            return False

        if target_module not in self.modules:
            print(f"Error: Target module '{target_module}' not found")
            return False

        source_mod = self.modules[source_module]
        target_mod = self.modules[target_module]

        # 出力端子の存在確認
        if source_output not in source_mod.outputs:
            print(f"Error: Output '{source_output}' not found in {source_module}")
            return False

        # 入力端子の存在確認
        if target_input not in target_mod.inputs:
            print(f"Error: Input '{target_input}' not found in {target_module}")
            return False

        # 既存の接続を確認（重複チェック）
        existing = self.find_connection(source_module, source_output, target_module, target_input)
        if existing:
            print(f"Warning: Connection already exists: {existing}")
            return False

        # 新しい接続を作成
        connection = Connection(
            source_module=source_module,
            source_output=source_output,
            target_module=target_module,
            target_input=target_input,
            signal_type=signal_type,
            attenuation=attenuation,
        )

        self.connections.append(connection)

        # 実際の接続処理
        self._apply_connection(connection)

        print(f"Connected: {connection}")
        return True

    def disconnect(self, source_module: str, source_output: str, target_module: str, target_input: str) -> bool:
        """
        接続を切断

        Args:
            source_module: 接続元モジュール名
            source_output: 接続元出力端子名
            target_module: 接続先モジュール名
            target_input: 接続先入力端子名

        Returns:
            成功したかどうか
        """
        connection = self.find_connection(source_module, source_output, target_module, target_input)
        if not connection:
            print(f"Error: Connection not found")
            return False

        self.connections.remove(connection)
        self._remove_connection(connection)

        print(f"Disconnected: {connection}")
        return True

    def find_connection(
        self, source_module: str, source_output: str, target_module: str, target_input: str
    ) -> Optional[Connection]:
        """
        指定された接続を検索
        """
        for conn in self.connections:
            if (
                conn.source_module == source_module
                and conn.source_output == source_output
                and conn.target_module == target_module
                and conn.target_input == target_input
            ):
                return conn
        return None

    def get_connections_for_module(self, module_name: str) -> List[Connection]:
        """
        指定されたモジュールに関連する接続を取得
        """
        return [
            conn for conn in self.connections if conn.source_module == module_name or conn.target_module == module_name
        ]

    def get_input_connections(self, module_name: str, input_name: str) -> List[Connection]:
        """
        指定された入力端子への接続を取得
        """
        return [
            conn for conn in self.connections if conn.target_module == module_name and conn.target_input == input_name
        ]

    def get_output_connections(self, module_name: str, output_name: str) -> List[Connection]:
        """
        指定された出力端子からの接続を取得
        """
        return [
            conn
            for conn in self.connections
            if conn.source_module == module_name and conn.source_output == output_name
        ]

    def _apply_connection(self, connection: Connection):
        """
        実際の接続処理を実行
        """
        source_mod = self.modules[connection.source_module]
        target_mod = self.modules[connection.target_module]

        # 出力から入力への信号の流れを設定
        source_signal = source_mod.outputs[connection.source_output]

        # 減衰を適用
        if connection.attenuation != 1.0 and source_signal is not None:
            # pyoオブジェクトに減衰を適用
            attenuated_signal = source_signal * connection.attenuation
            target_mod.inputs[connection.target_input] = attenuated_signal
        else:
            target_mod.inputs[connection.target_input] = source_signal

    def _remove_connection(self, connection: Connection):
        """
        接続を削除
        """
        target_mod = self.modules[connection.target_module]
        target_mod.inputs[connection.target_input] = None

    def update_all_connections(self):
        """
        すべての接続を更新
        """
        for connection in self.connections:
            self._apply_connection(connection)

    def get_all_connections(self) -> List[Connection]:
        """
        すべての接続を取得
        """
        return self.connections.copy()

    def clear_all_connections(self):
        """
        すべての接続をクリア
        """
        for connection in self.connections:
            self._remove_connection(connection)
        self.connections.clear()
        print("All connections cleared")

    def print_connections(self):
        """
        現在の接続状況を表示
        """
        if not self.connections:
            print("No connections")
            return

        print("Current connections:")
        for i, conn in enumerate(self.connections, 1):
            print(f"  {i}. {conn}")

    def validate_connections(self) -> List[str]:
        """
        接続の妥当性をチェック

        Returns:
            エラーメッセージのリスト
        """
        errors = []

        for conn in self.connections:
            # モジュールの存在確認
            if conn.source_module not in self.modules:
                errors.append(f"Source module '{conn.source_module}' not found")

            if conn.target_module not in self.modules:
                errors.append(f"Target module '{conn.target_module}' not found")

            # 端子の存在確認
            if conn.source_module in self.modules:
                source_mod = self.modules[conn.source_module]
                if conn.source_output not in source_mod.outputs:
                    errors.append(f"Output '{conn.source_output}' not found in {conn.source_module}")

            if conn.target_module in self.modules:
                target_mod = self.modules[conn.target_module]
                if conn.target_input not in target_mod.inputs:
                    errors.append(f"Input '{conn.target_input}' not found in {conn.target_module}")

        return errors
