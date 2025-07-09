import random
import logging
from typing import Tuple
from pyo import Adsr, Sig, PyoObject
from .base_module import BaseModule

logger = logging.getLogger(__name__)


class ENV(BaseModule):
    """
    ENV (Envelope Generator)
    エンベロープジェネレーター - 時間的な音量変化の形状を作ります。
    ADSR (Attack, Decay, Sustain, Release) パラメータに基づいて制御信号を生成します。
    """

    # パラメータのデフォルト範囲
    ATTACK_RANGE: Tuple[float, float] = (0.001, 5.0)
    DECAY_RANGE: Tuple[float, float] = (0.0, 5.0)
    SUSTAIN_RANGE: Tuple[float, float] = (0.0, 1.0)
    RELEASE_RANGE: Tuple[float, float] = (0.001, 10.0)
    DURATION_RANGE: Tuple[float, float] = (0.0, 20.0)

    def __init__(self, name: str = "ENV"):
        super().__init__(name)

        # --- パラメータの初期化 ---
        self.set_parameter("attack", 0.01)
        self.set_parameter("decay", 0.1)
        self.set_parameter("sustain", 0.5)
        self.set_parameter("release", 1.0)
        self.set_parameter("duration", 0)  # 0 for sustain-pedal mode

        # --- 入出力ポートの定義 ---
        self.add_input("gate_in", 0)

        self.add_output("cv_out")

        # --- pyoオブジェクトと内部状態の初期化 ---
        self.envelope: Adsr | None = None
        self.gate_signal: Sig | None = None

    def _initialize(self):
        """
        初期化処理 - pyoオブジェクトを作成し、参照を保持します。
        """
        self.gate_signal = Sig(0)
        self.envelope = Adsr(
            attack=self.get_parameter("attack"),
            decay=self.get_parameter("decay"),
            sustain=self.get_parameter("sustain"),
            release=self.get_parameter("release"),
            dur=self.get_parameter("duration"),
            mul=1.0,
        )
        # The gate signal will be connected in the process method

        self.pyo_objects = [self.envelope, self.gate_signal]
        self.outputs["cv_out"] = self.envelope

    def _update_envelope_params(self):
        """
        ADSRパラメータの変更をpyoオブジェクトに適用します。
        """
        if not self.envelope:
            return

        self.envelope.setAttack(self.get_parameter("attack"))
        self.envelope.setDecay(self.get_parameter("decay"))
        self.envelope.setSustain(self.get_parameter("sustain"))
        self.envelope.setRelease(self.get_parameter("release"))
        self.envelope.setDur(self.get_parameter("duration"))

    def _update_gate_routing(self):
        """
        ゲート入力のルーティングを管理します。
        """
        if not self.envelope:
            return

        gate_input = self.get_input_value("gate_in")

        if isinstance(gate_input, PyoObject):
            # 外部からのPyoObjectで直接ゲートを制御
            # pyoのAdsrは直接入力を受け取れないので、手動でトリガーを処理
            # この実装は簡略化されており、実際のゲート処理は呼び出し側で行う
            pass
        else:
            # 数値入力でゲートを制御
            # 1.0以上でplay()、0.0以下でstop()を呼び出す
            if isinstance(gate_input, (int, float)):
                if gate_input > 0.5:
                    self.envelope.play()
                else:
                    self.envelope.stop()

    def process(self):
        """
        モジュールのメイン処理。
        """
        self._update_gate_routing()
        self._update_envelope_params()

    def play(self):
        """
        エンベロープをトリガーします。
        gate_inが外部接続されていない場合に使用します。
        """
        if self.envelope:
            self.envelope.play()

    # --- パラメータ設定用メソッド ---

    def set_attack(self, time: float):
        time = self._clip_value(time, *self.ATTACK_RANGE)
        self.set_parameter("attack", time)

    def set_decay(self, time: float):
        time = self._clip_value(time, *self.DECAY_RANGE)
        self.set_parameter("decay", time)

    def set_sustain(self, level: float):
        level = self._clip_value(level, *self.SUSTAIN_RANGE)
        self.set_parameter("sustain", level)

    def set_release(self, time: float):
        time = self._clip_value(time, *self.RELEASE_RANGE)
        self.set_parameter("release", time)

    def set_duration(self, dur: float):
        dur = self._clip_value(dur, *self.DURATION_RANGE)
        self.set_parameter("duration", dur)

    # --- ユーティリティメソッド ---

    def _clip_value(self, value: float, min_val: float, max_val: float) -> float:
        """指定された範囲内に値をクリップします。"""
        return max(min_val, min(max_val, value))

    def randomize_parameters(self):
        """モジュールのパラメータをランダムな値に設定します。"""
        self.set_attack(random.uniform(0.01, 0.5))
        self.set_decay(random.uniform(0.1, 0.8))
        self.set_sustain(random.uniform(0.2, 0.8))
        self.set_release(random.uniform(0.5, 3.0))
        logger.info(f"{self.name} parameters randomized.")

    def _cleanup(self):
        """モジュール停止時のクリーンアップ処理。"""
        super()._cleanup()
