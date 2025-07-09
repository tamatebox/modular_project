import random
from pyo import Sine, LFO, Noise
from .base_module import BaseModule


class VCO(BaseModule):
    """
    VCO (Voltage Controlled Oscillator)
    電圧制御オシレーター - 音の基本波形を生成
    """

    # 利用可能な波形タイプ
    WAVEFORMS = {"sine": "sine", "saw": "saw", "square": "square", "triangle": "triangle", "noise": "noise"}

    def __init__(self, name: str = "VCO", base_freq: float = 440.0, waveform: str = "sine"):
        super().__init__(name)

        # 基本パラメータ
        self.set_parameter("base_freq", base_freq)
        self.set_parameter("waveform", waveform)
        self.set_parameter("amplitude", 0.5)
        self.set_parameter("octave", 0)  # オクターブ調整 (-2 ~ +2)
        self.set_parameter("fine_tune", 0)  # ファインチューニング (-100 ~ +100 cents)

        # 入力端子を定義
        self.add_input("freq_cv", 0)  # 周波数制御電圧
        self.add_input("fm_input", 0)  # FM変調入力
        self.add_input("pwm_input", 0)  # PWM入力（square波用）
        self.add_input("sync_input", 0)  # 同期入力
        self.add_input("reset_input", 0)  # リセット入力

        # 出力端子を定義
        self.add_output("audio_out")  # メイン音声出力
        self.add_output("sync_out")  # 同期出力

        # pyoオブジェクト
        self.oscillator = None
        self.freq_signal = None
        self.current_freq = base_freq

        # 波形生成オブジェクト
        self.sine_osc = None
        self.saw_osc = None
        self.square_osc = None
        self.triangle_osc = None
        self.noise_gen = None

        # 内部状態
        self.last_waveform = waveform
        self.phase = 0.0

    def _initialize(self):
        """
        初期化処理 - pyoオブジェクトを作成
        """
        # 基本周波数の計算
        self._update_frequency()

        # 波形オシレーターを作成
        self._create_oscillators()

        # 初期波形を設定
        self._set_waveform(self.get_parameter("waveform"))

        # 出力を設定
        self.outputs["audio_out"] = self.oscillator
        self.outputs["sync_out"] = self.oscillator  # 同期出力も同じ信号

    def _create_oscillators(self):
        """
        各波形のオシレーターを作成
        """
        freq = self.current_freq
        amp = self.get_parameter("amplitude")

        # 各波形のオシレーターを作成
        self.sine_osc = Sine(freq=freq, mul=amp)
        self.saw_osc = LFO(freq=freq, sharp=1.0, type=0, mul=amp)  # Saw up
        self.square_osc = LFO(freq=freq, sharp=0.5, type=2, mul=amp)  # Square
        self.triangle_osc = LFO(freq=freq, sharp=0.5, type=3, mul=amp)  # Triangle
        self.noise_gen = Noise(mul=amp * 0.1)  # ノイズは音量を下げる

        # pyoオブジェクトリストに追加
        self.pyo_objects = [self.sine_osc, self.saw_osc, self.square_osc, self.triangle_osc, self.noise_gen]

    def _set_waveform(self, waveform: str):
        """
        波形を設定

        Args:
            waveform: 波形の種類
        """
        if waveform not in self.WAVEFORMS:
            print(f"Warning: Unknown waveform '{waveform}', using 'sine'")
            waveform = "sine"

        # 現在のオシレーターを設定
        if waveform == "sine":
            self.oscillator = self.sine_osc
        elif waveform == "saw":
            self.oscillator = self.saw_osc
        elif waveform == "square":
            self.oscillator = self.square_osc
        elif waveform == "triangle":
            self.oscillator = self.triangle_osc
        elif waveform == "noise":
            self.oscillator = self.noise_gen

        # 出力を更新
        self.outputs["audio_out"] = self.oscillator
        self.outputs["sync_out"] = self.oscillator

        self.last_waveform = waveform

    def _update_frequency(self):
        """
        周波数を計算・更新
        """
        base_freq = self.get_parameter("base_freq")
        octave = self.get_parameter("octave")
        fine_tune = self.get_parameter("fine_tune")

        # オクターブ調整
        freq_with_octave = base_freq * (2**octave)

        # ファインチューニング（セント単位）
        freq_with_fine = freq_with_octave * (2 ** (fine_tune / 1200.0))

        # CV入力の処理（1V/Oct標準）
        freq_cv = self.get_input_value("freq_cv", 0)
        if isinstance(freq_cv, (int, float)):
            freq_with_cv = freq_with_fine * (2**freq_cv)
        else:
            freq_with_cv = freq_with_fine

        # FM入力の処理
        fm_input = self.get_input_value("fm_input", 0)
        if isinstance(fm_input, (int, float)):
            freq_with_fm = freq_with_cv + (fm_input * 100)  # FM深度
        else:
            freq_with_fm = freq_with_cv

        # 周波数の範囲制限
        self.current_freq = max(20, min(20000, freq_with_fm))

        # 全オシレーターの周波数を更新
        if self.is_active:
            self._update_all_oscillators()

    def _update_all_oscillators(self):
        """
        すべてのオシレーターの周波数を更新
        """
        freq = self.current_freq

        if self.sine_osc:
            self.sine_osc.setFreq(freq)
        if self.saw_osc:
            self.saw_osc.setFreq(freq)
        if self.square_osc:
            self.square_osc.setFreq(freq)
        if self.triangle_osc:
            self.triangle_osc.setFreq(freq)

    def _update_amplitude(self):
        """
        振幅を更新
        """
        amp = self.get_parameter("amplitude")

        if self.sine_osc:
            self.sine_osc.setMul(amp)
        if self.saw_osc:
            self.saw_osc.setMul(amp)
        if self.square_osc:
            self.square_osc.setMul(amp)
        if self.triangle_osc:
            self.triangle_osc.setMul(amp)
        if self.noise_gen:
            self.noise_gen.setMul(amp * 0.1)

    def process(self):
        """
        メイン処理 - 毎フレーム呼び出される
        """
        # 周波数の更新
        self._update_frequency()

        # 波形の変更チェック
        current_waveform = self.get_parameter("waveform")
        if current_waveform != self.last_waveform:
            self._set_waveform(current_waveform)

        # 振幅の更新
        self._update_amplitude()

        # 同期入力の処理
        sync_input = self.get_input_value("sync_input", 0)
        if sync_input and hasattr(self.oscillator, "reset"):
            self.oscillator.reset()

        # リセット入力の処理
        reset_input = self.get_input_value("reset_input", 0)
        if reset_input and hasattr(self.oscillator, "reset"):
            self.oscillator.reset()

    def set_frequency(self, freq: float):
        """
        基本周波数を設定

        Args:
            freq: 周波数（Hz）
        """
        self.set_parameter("base_freq", freq)
        self._update_frequency()

    def set_waveform(self, waveform: str):
        """
        波形を設定

        Args:
            waveform: 波形の種類
        """
        if waveform in self.WAVEFORMS:
            self.set_parameter("waveform", waveform)
            if self.is_active:
                self._set_waveform(waveform)

    def set_octave(self, octave: int):
        """
        オクターブを設定

        Args:
            octave: オクターブ（-2 ~ +2）
        """
        octave = max(-2, min(2, octave))
        self.set_parameter("octave", octave)
        self._update_frequency()

    def set_fine_tune(self, cents: float):
        """
        ファインチューニングを設定

        Args:
            cents: セント単位の調整値（-100 ~ +100）
        """
        cents = max(-100, min(100, cents))
        self.set_parameter("fine_tune", cents)
        self._update_frequency()

    def set_amplitude(self, amp: float):
        """
        振幅を設定

        Args:
            amp: 振幅（0.0 ~ 1.0）
        """
        amp = max(0.0, min(1.0, amp))
        self.set_parameter("amplitude", amp)
        self._update_amplitude()

    def randomize_parameters(self):
        """
        パラメータをランダムに設定
        """
        # ランダムな周波数（A1～A6）
        random_freq = 55 * (2 ** random.randint(0, 5))
        self.set_frequency(random_freq)

        # ランダムな波形
        random_waveform = random.choice(list(self.WAVEFORMS.keys()))
        self.set_waveform(random_waveform)

        # ランダムなオクターブ
        random_octave = random.randint(-1, 1)
        self.set_octave(random_octave)

        # ランダムなファインチューニング
        random_fine = random.uniform(-50, 50)
        self.set_fine_tune(random_fine)

        # ランダムな振幅
        random_amp = random.uniform(0.3, 0.8)
        self.set_amplitude(random_amp)

        print(
            f"{self.name}: Randomized to {random_freq}Hz, {random_waveform}, oct:{random_octave}, fine:{random_fine:.1f}, amp:{random_amp:.2f}"
        )

    def get_current_frequency(self) -> float:
        """
        現在の周波数を取得

        Returns:
            現在の周波数（Hz）
        """
        return self.current_freq

    def get_available_waveforms(self) -> list:
        """
        利用可能な波形のリストを取得

        Returns:
            波形名のリスト
        """
        return list(self.WAVEFORMS.keys())

    def _cleanup(self):
        """
        終了処理
        """
        super()._cleanup()

        # 追加の終了処理があればここに記述
        self.oscillator = None
        self.freq_signal = None
