import random
import logging
from typing import Dict, List, Tuple
from pyo import Biquad, Sig, PyoObject
from .base_module import BaseModule

logger = logging.getLogger(__name__)


class VCF(BaseModule):
    """
    VCF (Voltage Controlled Filter)
    電圧制御フィルター - 音色を変化させます。
    オーディオ信号にフィルターをかけ、カットオフ周波数やレゾナンスを制御します。
    """

    # --- 定数の定義 ---
    FILTER_TYPES: Dict[int, str] = {
        0: "lowpass",
        1: "highpass",
        2: "bandpass",
        3: "bandreject",
        4: "allpass",
    }

    # パラメータのデフォルト範囲
    FREQ_RANGE: Tuple[float, float] = (20.0, 20000.0)
    Q_RANGE: Tuple[float, float] = (0.1, 100.0)
    GAIN_RANGE: Tuple[float, float] = (0.0, 2.0)
    CV_DEPTH_RANGE: Tuple[float, float] = (0.0, 10000.0)

    def __init__(self, name: str = "VCF", initial_freq: float = 1000.0, initial_q: float = 1.0):
        super().__init__(name)

        # --- パラメータの初期化 ---
        self.set_parameter("freq", initial_freq)
        self.set_parameter("q", initial_q)
        self.set_parameter("gain", 1.0)
        self.set_parameter("filter_type", 0)  # 0: lowpass
        self.set_parameter("freq_cv_depth", 2000.0)

        # --- 入出力ポートの定義 ---
        self.add_input("audio_in", 0)
        self.add_input("freq_cv", 0)

        self.add_output("audio_out")

        # --- pyoオブジェクトと内部状態の初期化 ---
        self.filter: Biquad | None = None
        self.initial_output: Sig | None = None
        self.current_audio_input: PyoObject | None = None

    def _initialize(self):
        """
        初期化処理 - pyoオブジェクトを作成し、参照を保持します。
        """
        self.initial_output = Sig(0)
        self.filter = Biquad(
            input=self.initial_output,
            freq=self.get_parameter("freq"),
            q=self.get_parameter("q"),
            type=self.get_parameter("filter_type"),
        )

        # ガベージコレクションを防ぐために参照を保持
        self.pyo_objects = [self.filter, self.initial_output]

        # 初期出力を設定
        self.outputs["audio_out"] = self.filter

    def _update_filter_params(self):
        """
        各種パラメータと入力値から、最終的なフィルター設定を計算し、適用します。
        """
        if not self.filter:
            return

        # --- 周波数の計算 ---
        base_freq = self.get_parameter("freq")
        cv_depth = self.get_parameter("freq_cv_depth")
        freq_cv = self.get_input_value("freq_cv", 0)

        cv_offset = 0
        if isinstance(freq_cv, (int, float)):
            cv_offset = freq_cv * cv_depth

        final_freq = base_freq + cv_offset
        final_freq = self._clip_value(final_freq, *self.FREQ_RANGE)

        # --- パラメータをpyoオブジェクトに適用 ---
        self.filter.setFreq(final_freq)
        self.filter.setQ(self.get_parameter("q"))
        self.filter.setMul(self.get_parameter("gain"))
        self.filter.setType(self.get_parameter("filter_type"))

    def _update_audio_routing(self):
        """
        オーディオ信号のルーティングを更新します。
        入力の接続状態を監視し、pyoオブジェクトの接続を管理します。
        """
        if not self.filter:
            return

        audio_input = self.get_input_value("audio_in")
        is_valid_input = isinstance(audio_input, PyoObject)

        if is_valid_input:
            # 新しい入力が接続された場合、または切断された後に再接続された場合
            if self.current_audio_input != audio_input:
                self.current_audio_input = audio_input
                self.filter.setInput(self.current_audio_input)
        else:
            # 入力が切断された場合、無音信号に接続
            if self.current_audio_input is not None:
                self.current_audio_input = None
                if self.initial_output:
                    self.filter.setInput(self.initial_output)

    def process(self):
        """
        モジュールのメイン処理。毎フレーム呼び出されることを想定しています。
        """
        self._update_audio_routing()
        self._update_filter_params()

    # --- パラメータ設定用メソッド ---

    def set_frequency(self, freq: float):
        freq = self._clip_value(freq, *self.FREQ_RANGE)
        self.set_parameter("freq", freq)

    def set_q(self, q: float):
        q = self._clip_value(q, *self.Q_RANGE)
        self.set_parameter("q", q)

    def set_gain(self, gain: float):
        gain = self._clip_value(gain, *self.GAIN_RANGE)
        self.set_parameter("gain", gain)

    def set_filter_type(self, type_name: str):
        type_id = -1
        for i, name in self.FILTER_TYPES.items():
            if name == type_name:
                type_id = i
                break

        if type_id != -1:
            self.set_parameter("filter_type", type_id)
        else:
            logger.warning(f"Unknown filter type '{type_name}', using 'lowpass'")
            self.set_parameter("filter_type", 0)

    # --- ユーティリティメソッド ---

    def _clip_value(self, value: float, min_val: float, max_val: float) -> float:
        """指定された範囲内に値をクリップします。"""
        return max(min_val, min(max_val, value))

    def randomize_parameters(self):
        """モジュールのパラメータをランダムな値に設定します。"""
        self.set_frequency(random.uniform(100, 5000))
        self.set_q(random.uniform(0.5, 10))
        self.set_gain(random.uniform(0.8, 1.2))
        logger.info(f"{self.name} parameters randomized.")

    def get_available_filter_types(self) -> List[str]:
        """利用可能なフィルタータイプのリストを返します。"""
        return list(self.FILTER_TYPES.values())

    def _cleanup(self):
        """モジュール停止時のクリーンアップ処理。"""
        super()._cleanup()
        self.current_audio_input = None
