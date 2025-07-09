import random
import logging
from typing import List, Tuple
from pyo import LFO as pyoLFO
from .base_module import BaseModule

logger = logging.getLogger(__name__)


class LFO(BaseModule):
    """
    LFO (Low Frequency Oscillator)
    低周波オシレーター - モジュレーション信号を生成します。
    他のモジュールのパラメータ（VCOの周波数、VCFのカットオフなど）を周期的に変化させます。
    """

    # --- 定数の定義 ---
    WAVEFORMS: List[str] = ["sine", "saw_up", "saw_down", "square", "triangle", "pulse", "random"]

    # パラメータのデフォルト範囲
    FREQ_RANGE: Tuple[float, float] = (0.01, 100.0)
    AMP_RANGE: Tuple[float, float] = (0.0, 10.0)
    OFFSET_RANGE: Tuple[float, float] = (-5.0, 5.0)

    def __init__(self, name: str = "LFO", initial_freq: float = 1.0, waveform: str = "sine"):
        super().__init__(name)

        # --- パラメータの初期化 ---
        self.set_parameter("freq", initial_freq)
        self.set_parameter("waveform", waveform if waveform in self.WAVEFORMS else "sine")
        self.set_parameter("amplitude", 1.0)
        self.set_parameter("offset", 0.0)
        self.set_parameter("sharpness", 0.5)  # for square/pulse

        # --- 入出力ポートの定義 ---
        self.add_input("freq_cv", 0)
        self.add_input("reset_input", 0)

        self.add_output("cv_out")

        # --- pyoオブジェクトと内部状態の初期化 ---
        self.lfo: pyoLFO | None = None
        self.last_waveform: str = self.get_parameter("waveform")

    def _initialize(self):
        """
        初期化処理 - pyoオブジェクトを作成し、参照を保持します。
        """
        self._create_lfo()
        self.pyo_objects = [self.lfo]

    def _get_waveform_type(self, waveform_name: str) -> int:
        """波形名に対応するpyoのtype番号を返します。"""
        type_map = {
            "sine": 7,  # Sine
            "saw_up": 0,  # Sawtooth Up
            "saw_down": 1,  # Sawtooth Down
            "square": 2,  # Square
            "triangle": 3,  # Triangle
            "pulse": 4,  # Pulse
            "random": 6,  # Random
        }
        return type_map.get(waveform_name, 7)

    def _create_lfo(self):
        """
        LFOオブジェクトを生成または更新します。
        """
        waveform_str = self.get_parameter("waveform")
        waveform_type = self._get_waveform_type(waveform_str)

        self.lfo = pyoLFO(
            freq=self.get_parameter("freq"),
            sharp=self.get_parameter("sharpness"),
            type=waveform_type,
            mul=self.get_parameter("amplitude"),
            add=self.get_parameter("offset"),
        )
        self.outputs["cv_out"] = self.lfo
        self.last_waveform = waveform_str

    def _update_lfo_params(self):
        """
        各種パラメータと入力値から、最終的なLFO設定を計算し、適用します。
        """
        if not self.lfo:
            return

        # --- 周波数の計算 ---
        base_freq = self.get_parameter("freq")
        freq_cv = self.get_input_value("freq_cv", 0)
        cv_contribution = 0
        if isinstance(freq_cv, (int, float)):
            cv_contribution = freq_cv

        final_freq = base_freq + cv_contribution
        final_freq = self._clip_value(final_freq, *self.FREQ_RANGE)

        # --- パラメータをpyoオブジェクトに適用 ---
        self.lfo.setFreq(final_freq)
        self.lfo.setSharp(self.get_parameter("sharpness"))
        self.lfo.setMul(self.get_parameter("amplitude"))
        self.lfo.setAdd(self.get_parameter("offset"))

    def process(self):
        """
        モジュールのメイン処理。毎フレーム呼び出されることを想定しています。
        """
        # 波形の変更をチェック
        current_waveform = self.get_parameter("waveform")
        if current_waveform != self.last_waveform:
            # 波形が変わった場合はLFOを再生成
            if self.lfo:
                self.lfo.stop()
            self._create_lfo()
            if self.is_active:
                self.lfo.play()

        self._update_lfo_params()

        # リセット入力の処理
        reset_input = self.get_input_value("reset_input", 0)
        if reset_input and hasattr(self.lfo, "reset"):
            self.lfo.reset()

    # --- パラメータ設定用メソッド ---

    def set_frequency(self, freq: float):
        freq = self._clip_value(freq, *self.FREQ_RANGE)
        self.set_parameter("freq", freq)

    def set_waveform(self, waveform: str):
        if waveform in self.WAVEFORMS:
            self.set_parameter("waveform", waveform)
        else:
            logger.warning(f"Unknown waveform '{waveform}', using 'sine'")
            self.set_parameter("waveform", "sine")

    def set_amplitude(self, amp: float):
        amp = self._clip_value(amp, *self.AMP_RANGE)
        self.set_parameter("amplitude", amp)

    def set_offset(self, offset: float):
        offset = self._clip_value(offset, *self.OFFSET_RANGE)
        self.set_parameter("offset", offset)

    # --- ユーティリティメソッド ---

    def _clip_value(self, value: float, min_val: float, max_val: float) -> float:
        """指定された範囲内に値をクリップします。"""
        return max(min_val, min(max_val, value))

    def randomize_parameters(self):
        """モジュールのパラメータをランダムな値に設定します。"""
        self.set_frequency(random.uniform(0.1, 10))
        self.set_waveform(random.choice(self.WAVEFORMS))
        self.set_amplitude(random.uniform(0.5, 2.0))
        self.set_offset(random.uniform(-1.0, 1.0))
        logger.info(f"{self.name} parameters randomized.")

    def get_available_waveforms(self) -> List[str]:
        """利用可能な波形のリストを返します。"""
        return self.WAVEFORMS

    def _cleanup(self):
        """モジュール停止時のクリーンアップ処理。"""
        super()._cleanup()
