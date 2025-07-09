import random
from typing import Dict, List, Tuple
from pyo import Sine, LFO, Noise, Sig, PyoObject
from .base_module import BaseModule


class VCO(BaseModule):
    """
    VCO (Voltage Controlled Oscillator)
    電圧制御オシレーター - 音の基本波形を生成します。
    周波数、波形、振幅をパラメータやCV入力で制御できます。
    """

    # --- 定数の定義 ---
    WAVEFORMS: List[str] = ["sine", "saw", "square", "triangle", "noise"]

    # パラメータのデフォルト範囲
    OCTAVE_RANGE: Tuple[int, int] = (-2, 2)
    FINE_TUNE_RANGE: Tuple[float, float] = (-100.0, 100.0)  # in cents
    AMPLITUDE_RANGE: Tuple[float, float] = (0.0, 1.0)
    FREQ_RANGE: Tuple[float, float] = (20.0, 20000.0)

    def __init__(self, name: str = "VCO", base_freq: float = 440.0, waveform: str = "sine"):
        super().__init__(name)

        # --- パラメータの初期化 ---
        self.set_parameter("base_freq", base_freq)
        self.set_parameter("waveform", waveform if waveform in self.WAVEFORMS else "sine")
        self.set_parameter("amplitude", 0.5)
        self.set_parameter("octave", 0)
        self.set_parameter("fine_tune", 0.0)
        self.set_parameter("fm_depth", 100.0)

        # --- 入出力ポートの定義 ---
        self.add_input("freq_cv", 0)
        self.add_input("fm_input", 0)
        self.add_input("pwm_input", 0)
        self.add_input("sync_input", 0)
        self.add_input("reset_input", 0)

        self.add_output("audio_out")
        self.add_output("sync_out")

        # --- pyoオブジェクトと内部状態の初期化 ---
        self.current_freq: float = base_freq
        self.last_waveform: str = self.get_parameter("waveform")

        self.amp_signal: Sig | None = None
        self.oscillator: PyoObject | None = None
        self.oscillators: Dict[str, PyoObject] = {}

    def _initialize(self):
        """
        初期化処理 - pyoオブジェクトを作成し、参照を保持します。
        """
        self.amp_signal = Sig(self.get_parameter("amplitude"))
        self._create_oscillators()
        self._set_waveform(self.get_parameter("waveform"))

        # ガベージコレクションを防ぐために参照を保持
        self.pyo_objects = [self.amp_signal] + list(self.oscillators.values())

    def _create_oscillators(self):
        """
        利用可能なすべての波形のpyoオブジェクトを生成し、辞書に格納します。
        """
        freq = self.get_parameter("base_freq")
        amp = self.amp_signal

        self.oscillators = {
            "sine": Sine(freq=freq, mul=amp),
            "saw": LFO(freq=freq, sharp=1.0, type=0, mul=amp),
            "square": LFO(freq=freq, sharp=0.5, type=2, mul=amp),
            "triangle": LFO(freq=freq, sharp=0.5, type=3, mul=amp),
            "noise": Noise(mul=amp * 0.1),  # ノイズは他より音量が大きいため調整
        }

    def _set_waveform(self, waveform: str):
        """
        出力する波形を、生成済みのオシレーターから選択します。
        """
        self.oscillator = self.oscillators.get(waveform, self.oscillators["sine"])
        self.outputs["audio_out"] = self.oscillator
        self.outputs["sync_out"] = self.oscillator  # 同期出力も同じ信号
        self.last_waveform = waveform

    def _update_frequency(self):
        """
        各種パラメータと入力値から、最終的な周波数を計算し、全オシレーターに適用します。
        """
        # パラメータを取得
        base_freq = self.get_parameter("base_freq")
        octave = self.get_parameter("octave")
        fine_tune = self.get_parameter("fine_tune")
        fm_depth = self.get_parameter("fm_depth")

        # オクターブとファインチューンを適用
        freq = base_freq * (2**octave) * (2 ** (fine_tune / 1200.0))

        # CV入力 (1V/Oct) を適用
        freq_cv = self.get_input_value("freq_cv", 0)
        if isinstance(freq_cv, (int, float)):
            freq *= 2**freq_cv

        # FM入力を適用
        fm_input = self.get_input_value("fm_input", 0)
        if isinstance(fm_input, (int, float)):
            freq += fm_input * fm_depth

        # 周波数をクリッピングして適用
        self.current_freq = self._clip_value(freq, *self.FREQ_RANGE)
        for osc in self.oscillators.values():
            if hasattr(osc, "setFreq"):
                osc.setFreq(self.current_freq)

    def _update_amplitude(self):
        """
        振幅パラメータの変更をamp_signalに反映します。
        """
        if self.amp_signal:
            self.amp_signal.setValue(self.get_parameter("amplitude"))

    def process(self):
        """
        モジュールのメイン処理。毎フレーム呼び出されることを想定しています。
        """
        self._update_frequency()
        self._update_amplitude()

        # 波形の変更をチェック
        current_waveform = self.get_parameter("waveform")
        if current_waveform != self.last_waveform:
            self._set_waveform(current_waveform)

        # 同期/リセット入力の処理
        sync_input = self.get_input_value("sync_input", 0)
        if sync_input and hasattr(self.oscillator, "reset"):
            self.oscillator.reset()

        reset_input = self.get_input_value("reset_input", 0)
        if reset_input and hasattr(self.oscillator, "reset"):
            self.oscillator.reset()

    # --- パラメータ設定用メソッド ---

    def set_frequency(self, freq: float):
        self.set_parameter("base_freq", freq)
        self._update_frequency()

    def set_waveform(self, waveform: str):
        if waveform in self.WAVEFORMS:
            self.set_parameter("waveform", waveform)
        else:
            print(f"Warning: Unknown waveform '{waveform}', using 'sine'")
            self.set_parameter("waveform", "sine")

    def set_octave(self, octave: int):
        octave = int(self._clip_value(octave, *self.OCTAVE_RANGE))
        self.set_parameter("octave", octave)
        self._update_frequency()

    def set_fine_tune(self, cents: float):
        cents = self._clip_value(cents, *self.FINE_TUNE_RANGE)
        self.set_parameter("fine_tune", cents)
        self._update_frequency()

    def set_amplitude(self, amp: float):
        amp = self._clip_value(amp, *self.AMPLITUDE_RANGE)
        self.set_parameter("amplitude", amp)
        self._update_amplitude()

    # --- ユーティリティメソッド ---

    def _clip_value(self, value: float, min_val: float, max_val: float) -> float:
        """指定された範囲内に値をクリップします。"""
        return max(min_val, min(max_val, value))

    def randomize_parameters(self):
        """モジュールのパラメータをランダムな値に設定します。"""
        self.set_frequency(55 * (2 ** random.randint(0, 5)))  # A1-A6
        self.set_waveform(random.choice(self.WAVEFORMS))
        self.set_octave(random.randint(-1, 1))
        self.set_fine_tune(random.uniform(-50, 50))
        self.set_amplitude(random.uniform(0.3, 0.8))
        print(f"{self.name} parameters randomized.")

    def get_available_waveforms(self) -> List[str]:
        """利用可能な波形のリストを返します。"""
        return self.WAVEFORMS

    def _cleanup(self):
        """モジュール停止時のクリーンアップ処理。"""
        super()._cleanup()
        self.oscillator = None
        self.oscillators.clear()
