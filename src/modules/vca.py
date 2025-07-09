import random
import math
from pyo import Sig, Port
from .base_module import BaseModule


class VCA(BaseModule):
    """
    VCA (Voltage Controlled Amplifier)
    電圧制御アンプ - 音量・振幅を制御
    """

    # 制御曲線の種類
    CONTROL_CURVES = {"linear": "linear", "exponential": "exp", "logarithmic": "log"}  # リニア  # 指数的  # 対数的

    def __init__(self, name: str = "VCA", initial_gain: float = 1.0, control_curve: str = "exponential"):
        super().__init__(name)

        # 基本パラメータ
        self.set_parameter("gain", initial_gain)  # 基本ゲイン (0.0 ~ 2.0)
        self.set_parameter("control_curve", control_curve)  # 制御曲線
        self.set_parameter("cv_amount", 1.0)  # CV感度 (0.0 ~ 2.0)
        self.set_parameter("offset", 0.0)  # オフセット (-1.0 ~ 1.0)
        self.set_parameter("max_gain", 2.0)  # 最大ゲイン

        # 入力端子を定義
        self.add_input("audio_in", 0)  # オーディオ入力
        self.add_input("gain_cv", 0)  # ゲイン制御CV
        self.add_input("am_input", 0)  # AM変調入力
        self.add_input("gate_input", 0)  # ゲート入力
        self.add_input("velocity_cv", 0)  # ベロシティCV

        # 出力端子を定義
        self.add_output("audio_out")  # メイン音声出力
        self.add_output("envelope_out")  # エンベロープ出力（CV）

        # pyoオブジェクト
        self.multiplier = None
        self.current_gain = initial_gain
        self.smoothed_gain = None
        self.gain_signal = None

        # 内部状態
        self.last_gate_state = 0
        self.is_gated = False
        self.envelope_value = 0.0

        # スムージング用
        self.gain_smoother = None
        self.smoothing_time = 0.01  # 10ms

    def _initialize(self):
        """
        初期化処理 - pyoオブジェクトを作成
        """
        # ゲイン信号を作成（Sigオブジェクトから開始）
        self.gain_signal = Sig(self.current_gain)

        # ゲインのスムージング
        self.gain_smoother = Port(self.gain_signal, risetime=self.smoothing_time, falltime=self.smoothing_time)

        # 初期のマルチプライヤー（何も接続されていない場合は0）
        self.multiplier = Sig(0)

        # pyoオブジェクトリストに追加
        self.pyo_objects = [self.gain_signal, self.gain_smoother, self.multiplier]

        # 出力を設定
        self.outputs["audio_out"] = self.multiplier
        self.outputs["envelope_out"] = self.gain_smoother

    def _calculate_gain(self):
        """
        現在のゲインを計算
        """
        base_gain = self.get_parameter("gain")
        cv_amount = self.get_parameter("cv_amount")
        offset = self.get_parameter("offset")
        max_gain = self.get_parameter("max_gain")
        control_curve = self.get_parameter("control_curve")

        # CV入力の処理
        gain_cv = self.get_input_value("gain_cv", 0)
        if isinstance(gain_cv, (int, float)):
            cv_contribution = gain_cv * cv_amount
        else:
            cv_contribution = 0

        # ベロシティCV
        velocity_cv = self.get_input_value("velocity_cv", 0)
        if isinstance(velocity_cv, (int, float)):
            velocity_contribution = velocity_cv
        else:
            velocity_contribution = 1.0

        # AM変調入力
        am_input = self.get_input_value("am_input", 0)
        if isinstance(am_input, (int, float)):
            am_contribution = am_input
        else:
            am_contribution = 0

        # ゲート入力の処理
        gate_input = self.get_input_value("gate_input", 0)
        if isinstance(gate_input, (int, float)):
            gate_multiplier = 1.0 if gate_input > 0.5 else 0.0
            # ゲート状態の変化を検出
            if gate_input > 0.5 and not self.is_gated:
                self.is_gated = True
                self.last_gate_state = 1
            elif gate_input <= 0.5 and self.is_gated:
                self.is_gated = False
                self.last_gate_state = 0
        else:
            gate_multiplier = 1.0

        # 基本ゲインの計算
        calculated_gain = base_gain + cv_contribution + offset + am_contribution

        # ベロシティの適用
        calculated_gain *= velocity_contribution

        # ゲートの適用
        calculated_gain *= gate_multiplier

        # 制御曲線の適用
        if control_curve == "exponential":
            # 指数的な制御（一般的なVCAの特性）
            calculated_gain = calculated_gain**2
        elif control_curve == "logarithmic":
            # 対数的な制御
            if calculated_gain > 0:
                calculated_gain = math.log(calculated_gain + 1) / math.log(2)
            else:
                calculated_gain = 0
        # linear の場合はそのまま

        # 範囲制限
        calculated_gain = max(0.0, min(max_gain, calculated_gain))

        return calculated_gain

    def _update_audio_processing(self):
        """
        オーディオ処理を更新
        """
        audio_input = self.get_input_value("audio_in", 0)

        if audio_input is not None and hasattr(audio_input, "play"):
            # 音声入力がある場合
            current_gain = self._calculate_gain()

            # ゲイン信号を更新
            if self.gain_signal:
                self.gain_signal.setValue(current_gain)

            # 音声信号にゲインを適用（毎回新しいオブジェクトを作成しない）
            if self.multiplier is None or not hasattr(self.multiplier, "play"):
                self.multiplier = audio_input * self.gain_smoother
                # pyoオブジェクトリストに追加
                if self.multiplier not in self.pyo_objects:
                    self.pyo_objects.append(self.multiplier)

            # 出力を更新
            self.outputs["audio_out"] = self.multiplier
            self.outputs["envelope_out"] = self.gain_smoother

            self.current_gain = current_gain
            self.envelope_value = current_gain

        else:
            # 音声入力がない場合は無音
            if self.gain_signal:
                self.gain_signal.setValue(0)
            if self.multiplier is None or not hasattr(self.multiplier, "play"):
                self.multiplier = Sig(0)
                # pyoオブジェクトリストに追加
                if self.multiplier not in self.pyo_objects:
                    self.pyo_objects.append(self.multiplier)
            self.outputs["audio_out"] = self.multiplier
            self.current_gain = 0
            self.envelope_value = 0

    def process(self):
        """
        メイン処理 - 毎フレーム呼び出される
        """
        self._update_audio_processing()

    def set_gain(self, gain: float):
        """
        基本ゲインを設定

        Args:
            gain: ゲイン値（0.0 ~ 2.0）
        """
        gain = max(0.0, min(2.0, gain))
        self.set_parameter("gain", gain)

    def set_cv_amount(self, amount: float):
        """
        CV感度を設定

        Args:
            amount: CV感度（0.0 ~ 2.0）
        """
        amount = max(0.0, min(2.0, amount))
        self.set_parameter("cv_amount", amount)

    def set_offset(self, offset: float):
        """
        オフセットを設定

        Args:
            offset: オフセット値（-1.0 ~ 1.0）
        """
        offset = max(-1.0, min(1.0, offset))
        self.set_parameter("offset", offset)

    def set_control_curve(self, curve: str):
        """
        制御曲線を設定

        Args:
            curve: 制御曲線の種類
        """
        if curve in self.CONTROL_CURVES:
            self.set_parameter("control_curve", curve)
        else:
            print(f"Warning: Unknown control curve '{curve}', using 'exponential'")
            self.set_parameter("control_curve", "exponential")

    def set_max_gain(self, max_gain: float):
        """
        最大ゲインを設定

        Args:
            max_gain: 最大ゲイン値
        """
        max_gain = max(0.1, min(5.0, max_gain))
        self.set_parameter("max_gain", max_gain)

    def set_smoothing_time(self, time: float):
        """
        スムージング時間を設定

        Args:
            time: スムージング時間（秒）
        """
        self.smoothing_time = max(0.001, min(1.0, time))
        if self.gain_smoother:
            self.gain_smoother.setRiseTime(self.smoothing_time)
            self.gain_smoother.setFallTime(self.smoothing_time)

    def out_to_channel(self, channel: int):
        """
        指定されたチャンネルに出力

        Args:
            channel: 出力チャンネル番号（0, 1, 2, 3...）
        """
        if self.outputs["audio_out"]:
            self.outputs["audio_out"].out(chnl=channel)
            print(f"{self.name} output to channel {channel}")
        else:
            print(f"Warning: {self.name} has no audio output")

    def out_to_channels(self, channels: list):
        """
        複数のチャンネルに出力

        Args:
            channels: 出力チャンネル番号のリスト
        """
        if self.outputs["audio_out"]:
            self.outputs["audio_out"].out(chnl=channels)
            print(f"{self.name} output to channels {channels}")
        else:
            print(f"Warning: {self.name} has no audio output")

    def stop_output(self):
        """
        出力を停止
        """
        if self.outputs["audio_out"]:
            self.outputs["audio_out"].stop()
            print(f"{self.name} output stopped")

    def mute(self):
        """
        ミュート（ゲインを0にする）
        """
        self.set_gain(0.0)

    def unmute(self, gain: float = 1.0):
        """
        ミュート解除

        Args:
            gain: 設定するゲイン値
        """
        self.set_gain(gain)

    def get_current_gain(self) -> float:
        """
        現在のゲイン値を取得

        Returns:
            現在のゲイン値
        """
        return self.current_gain

    def get_envelope_value(self) -> float:
        """
        エンベロープ値を取得

        Returns:
            エンベロープ値
        """
        return self.envelope_value

    def is_gate_active(self) -> bool:
        """
        ゲートがアクティブかどうか

        Returns:
            ゲートの状態
        """
        return self.is_gated

    def randomize_parameters(self):
        """
        パラメータをランダムに設定
        """
        # ランダムなゲイン
        random_gain = random.uniform(0.3, 1.5)
        self.set_gain(random_gain)

        # ランダムなCV感度
        random_cv = random.uniform(0.5, 1.5)
        self.set_cv_amount(random_cv)

        # ランダムなオフセット
        random_offset = random.uniform(-0.2, 0.2)
        self.set_offset(random_offset)

        # ランダムな制御曲線
        random_curve = random.choice(list(self.CONTROL_CURVES.keys()))
        self.set_control_curve(random_curve)

        # ランダムなスムージング時間
        random_smoothing = random.uniform(0.005, 0.05)
        self.set_smoothing_time(random_smoothing)

        print(
            f"{self.name}: Randomized - gain:{random_gain:.2f}, cv:{random_cv:.2f}, offset:{random_offset:.2f}, curve:{random_curve}, smooth:{random_smoothing:.3f}"
        )

    def get_available_curves(self) -> list:
        """
        利用可能な制御曲線のリストを取得

        Returns:
            制御曲線名のリスト
        """
        return list(self.CONTROL_CURVES.keys())

    def apply_envelope(self, attack: float = 0.01, decay: float = 0.1, sustain: float = 0.7, release: float = 0.5):
        """
        簡単なADSRエンベロープを適用

        Args:
            attack: アタック時間（秒）
            decay: ディケイ時間（秒）
            sustain: サスティンレベル（0.0～1.0）
            release: リリース時間（秒）
        """
        # 簡単なADSRシミュレーション
        gate_input = self.get_input_value("gate_input", 0)

        if isinstance(gate_input, (int, float)) and gate_input > 0.5:
            # ゲートオン時
            if not self.is_gated:
                # アタック開始
                self.set_smoothing_time(attack)
                self.set_gain(1.0)
                self.is_gated = True
        else:
            # ゲートオフ時
            if self.is_gated:
                # リリース開始
                self.set_smoothing_time(release)
                self.set_gain(0.0)
                self.is_gated = False

    def _cleanup(self):
        """
        終了処理
        """
        super()._cleanup()

        # 追加の終了処理
        self.multiplier = None
        self.gain_smoother = None
        self.gain_signal = None
