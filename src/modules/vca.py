import random
import math
import logging
from typing import Dict, List, Tuple
from pyo import Sig, Port, PyoObject
from .base_module import BaseModule

logger = logging.getLogger(__name__)


class VCA(BaseModule):
    """
    VCA (Voltage Controlled Amplifier)
    電圧制御アンプ - 音量・振幅を制御します。
    オーディオ信号の音量を、ゲインパラメータと複数のCV入力によって変調します。
    """

    # --- 定数の定義 ---
    CONTROL_CURVES: Dict[str, str] = {
        "linear": "linear",
        "exponential": "exp",
        "logarithmic": "log",
    }

    # パラメータのデフォルト範囲
    GAIN_RANGE: Tuple[float, float] = (0.0, 2.0)
    CV_AMOUNT_RANGE: Tuple[float, float] = (0.0, 2.0)
    OFFSET_RANGE: Tuple[float, float] = (-1.0, 1.0)
    MAX_GAIN_RANGE: Tuple[float, float] = (0.1, 5.0)
    SMOOTHING_TIME_RANGE: Tuple[float, float] = (0.001, 1.0)

    def __init__(self, name: str = "VCA", initial_gain: float = 1.0, control_curve: str = "exponential"):
        super().__init__(name)

        # --- パラメータの初期化 ---
        self.set_parameter("gain", initial_gain)
        self.set_parameter("control_curve", control_curve)
        self.set_parameter("cv_amount", 1.0)
        self.set_parameter("offset", 0.0)
        self.set_parameter("max_gain", 2.0)
        self.set_parameter("smoothing_time", 0.01)

        # --- 入出力ポートの定義 ---
        self.add_input("audio_in", 0)
        self.add_input("gain_cv", 0)
        self.add_input("am_input", 0)
        self.add_input("gate_input", 1.0)
        self.add_input("velocity_cv", 1.0)

        self.add_output("audio_out")
        self.add_output("envelope_out")

        # --- pyoオブジェクトと内部状態の初期化 ---
        self.gain_signal: Sig | None = None
        self.gain_smoother: Port | None = None
        self.initial_output: Sig | None = None  # 初期出力用の無音信号
        self.current_audio_input: PyoObject | None = None

        self.is_gated: bool = False

    def _initialize(self):
        """
        初期化処理 - pyoオブジェクトを作成し、参照を保持します。
        """
        self.gain_signal = Sig(self.get_parameter("gain"))
        self.gain_smoother = Port(
            self.gain_signal,
            risetime=self.get_parameter("smoothing_time"),
            falltime=self.get_parameter("smoothing_time"),
        )
        self.initial_output = Sig(0)

        # ガベージコレクションを防ぐために参照を保持
        self.pyo_objects = [self.gain_signal, self.gain_smoother, self.initial_output]

        # 固定出力オブジェクトを作成
        self.create_fixed_output("audio_out", 0)
        self.outputs["envelope_out"] = self.gain_smoother

    def _calculate_gain(self) -> float:
        """
        各種パラメータと入力値から、最終的なゲイン値を計算します。
        """
        # パラメータを取得
        base_gain = self.get_parameter("gain")
        cv_amount = self.get_parameter("cv_amount")
        offset = self.get_parameter("offset")
        max_gain = self.get_parameter("max_gain")
        control_curve = self.get_parameter("control_curve")

        # --- CV入力の処理 ---
        gain_cv = self.get_input_value("gain_cv", 0)
        if isinstance(gain_cv, (int, float)):
            cv_contribution = gain_cv * cv_amount
        elif isinstance(gain_cv, PyoObject):
            # PyoObjectの場合は、cv_amountを乗算したオブジェクトを作成
            cv_contribution = gain_cv * cv_amount
        else:
            cv_contribution = 0

        am_input = self.get_input_value("am_input", 0)
        am_contribution = am_input if isinstance(am_input, (int, float)) else 0

        # --- ゲインの基本計算 ---
        if isinstance(cv_contribution, PyoObject):
            # PyoObjectの場合は、base_gainとoffsetを加算したオブジェクトを作成
            calculated_gain = cv_contribution + (base_gain + offset + am_contribution)
        else:
            calculated_gain = base_gain + cv_contribution + offset + am_contribution

        # --- ベロシティとゲートの適用 ---
        velocity_cv = self.get_input_value("velocity_cv", 1.0)
        velocity_multiplier = velocity_cv if isinstance(velocity_cv, (int, float)) else 1.0

        gate_input = self.get_input_value("gate_input", 1.0)
        gate_multiplier = 0.0
        if isinstance(gate_input, (int, float)):
            gate_multiplier = 1.0 if gate_input > 0.5 else 0.0
            self.is_gated = gate_multiplier > 0.5
        else:  # PyoObjectなど数値以外の入力
            gate_multiplier = 1.0
            self.is_gated = True

        calculated_gain *= velocity_multiplier
        calculated_gain *= gate_multiplier

        # --- 制御曲線の適用 ---
        if control_curve == "exponential" and calculated_gain > 0:
            calculated_gain = calculated_gain**2
        elif control_curve == "logarithmic" and calculated_gain > 0:
            calculated_gain = math.log1p(calculated_gain) / math.log(2)

        # --- 最終的な範囲制限 ---
        return self._clip_value(calculated_gain, 0.0, max_gain)

    def _update_audio_processing(self):
        """
        オーディオ信号の流れを更新（固定出力オブジェクト版）
        """
        logger.info(f"=== {self.name} _update_audio_processing() start ===")

        current_gain = self._calculate_gain()
        audio_input = self.get_input_value("audio_in")
        is_valid_input = isinstance(audio_input, PyoObject)

        if is_valid_input:
            # 新しい信号を作成（入力とゲインを組み合わせ）
            if isinstance(current_gain, PyoObject):
                new_signal = Sig(audio_input, mul=current_gain)
            else:
                if self.gain_signal:
                    self.gain_signal.setValue(current_gain)
                new_signal = Sig(audio_input, mul=self.gain_smoother)
            
            # 固定出力オブジェクトを更新
            self.update_fixed_output("audio_out", new_signal)
            self.current_audio_input = audio_input
            logger.info(f"{self.name} updated fixed audio output")
        else:
            # 入力なし：無音に設定
            self.update_fixed_output("audio_out", 0)
            self.current_audio_input = None
            logger.info(f"{self.name} set to silence via fixed output")

        logger.info(f"=== {self.name} _update_audio_processing() end ===")

    def process(self):
        """
        モジュールのメイン処理。毎フレーム呼び出されることを想定しています。
        """
        self._update_audio_processing()

    # --- パラメータ設定用メソッド ---

    def set_gain(self, gain: float):
        gain = self._clip_value(gain, *self.GAIN_RANGE)
        self.set_parameter("gain", gain)

    def set_cv_amount(self, amount: float):
        amount = self._clip_value(amount, *self.CV_AMOUNT_RANGE)
        self.set_parameter("cv_amount", amount)

    def set_offset(self, offset: float):
        offset = self._clip_value(offset, *self.OFFSET_RANGE)
        self.set_parameter("offset", offset)

    def set_control_curve(self, curve: str):
        if curve in self.CONTROL_CURVES:
            self.set_parameter("control_curve", curve)
        else:
            logger.warning(f"Unknown control curve '{curve}', using 'exponential'")
            self.set_parameter("control_curve", "exponential")

    def set_max_gain(self, max_gain: float):
        max_gain = self._clip_value(max_gain, *self.MAX_GAIN_RANGE)
        self.set_parameter("max_gain", max_gain)

    def set_smoothing_time(self, time: float):
        time = self._clip_value(time, *self.SMOOTHING_TIME_RANGE)
        self.set_parameter("smoothing_time", time)
        if self.gain_smoother:
            self.gain_smoother.setRiseTime(time)
            self.gain_smoother.setFallTime(time)

    # --- ユーティリティメソッド ---

    def _clip_value(self, value: float, min_val: float, max_val: float) -> float:
        """指定された範囲内に値をクリップします。"""
        return max(min_val, min(max_val, value))

    def out_to_channel(self, channel: int):
        """指定されたチャンネルに音声を出力します。"""
        logger.info(f"=== {self.name} out_to_channel({channel}) called ===")
        if self.outputs.get("audio_out"):
            logger.info(f"{self.name} sending audio output to channel {channel}: {self.outputs['audio_out']}")
            self.outputs["audio_out"].out(chnl=channel)
            logger.info(f"{self.name} audio output sent to channel {channel}")
        else:
            logger.warning(f"{self.name} has no audio output to play.")

    def stop_output(self):
        """音声出力を停止します。"""
        if self.outputs.get("audio_out"):
            self.outputs["audio_out"].stop()

    def randomize_parameters(self):
        """モジュールのパラメータをランダムな値に設定します。"""
        self.set_gain(random.uniform(*self.GAIN_RANGE))
        self.set_cv_amount(random.uniform(*self.CV_AMOUNT_RANGE))
        self.set_offset(random.uniform(*self.OFFSET_RANGE))
        self.set_control_curve(random.choice(list(self.CONTROL_CURVES.keys())))
        self.set_smoothing_time(random.uniform(0.005, 0.05))
        logger.info(f"{self.name} parameters randomized.")

    def get_available_curves(self) -> List[str]:
        """利用可能な制御曲線のリストを返します。"""
        return list(self.CONTROL_CURVES.keys())

    def _cleanup(self):
        """モジュール停止時のクリーンアップ処理。"""
        super()._cleanup()
        self.current_audio_input = None
