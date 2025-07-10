#!/usr/bin/env python3
"""
手動テスト用の共通ユーティリティ
"""

import sys
import os
import time
import logging
from contextlib import contextmanager
from pyo import Server

# srcディレクトリをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.connection import ConnectionManager, SignalType
from src.modules.vco import VCO
from src.modules.vca import VCA
from src.modules.vcf import VCF
from src.modules.lfo import LFO
from src.modules.env import ENV
from src.modules.multiple import Multiple
from src.modules.mixer import Mixer
from src.modules.cvmath import CVMath

# ログ設定
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


@contextmanager
def audio_server(channels=2, buffersize=512):
    """
    Pyoサーバーのコンテキストマネージャー
    """
    s = Server(nchnls=channels, buffersize=buffersize, duplex=0)
    s.boot()
    s.start()
    try:
        yield s
    finally:
        s.stop()
        s.shutdown()


class TestModuleFactory:
    """テスト用モジュールファクトリー"""

    @staticmethod
    def create_vco(name="test_vco", freq=440, waveform="sine", amplitude=0.5):
        """標準的なVCOを作成"""
        vco = VCO(name=name, base_freq=freq, waveform=waveform)
        vco.set_amplitude(amplitude)
        return vco

    @staticmethod
    def create_vca(name="test_vca", gain=0.7):
        """標準的なVCAを作成"""
        return VCA(name=name, initial_gain=gain)

    @staticmethod
    def create_vcf(name="test_vcf", freq=1000, q=5):
        """標準的なVCFを作成"""
        return VCF(name=name, initial_freq=freq, initial_q=q)

    @staticmethod
    def create_lfo(name="test_lfo", freq=1.0, waveform="sine", amplitude=100):
        """標準的なLFOを作成（float周波数対応）"""
        lfo = LFO(name=name, initial_freq=float(freq), waveform=waveform)
        lfo.set_amplitude(amplitude)
        return lfo

    @staticmethod
    def create_env(name="test_env", attack=0.05, decay=0.3, sustain=0.4, release=1.5):
        """標準的なENVを作成"""
        env = ENV(name=name)
        env.set_attack(attack)
        env.set_decay(decay)
        env.set_sustain(sustain)
        env.set_release(release)
        return env

    @staticmethod
    def create_multiple(name="test_multiple", outputs=4):
        """標準的なMultipleを作成"""
        return Multiple(name=name, outputs=outputs)

    @staticmethod
    def create_mixer(name="test_mixer", inputs=4):
        """標準的なMixerを作成"""
        return Mixer(name=name, inputs=inputs)

    @staticmethod
    def create_cvmath(name="test_cvmath", operation="add"):
        """標準的なCVMathを作成"""
        return CVMath(name=name, operation=operation)


class TestRunner:
    """テスト実行ヘルパー"""

    def __init__(self, name):
        self.name = name
        self.cm = ConnectionManager()
        self.modules = {}

    def add_module(self, name, module):
        """モジュールを追加して登録・開始"""
        self.modules[name] = module
        self.cm.register_module(name, module)
        module.start()
        return module

    def connect(self, source, source_port, target, target_port, signal_type=SignalType.AUDIO):
        """モジュールを接続"""
        self.cm.connect(source, source_port, target, target_port, signal_type)

    def process_chain(self, *module_names):
        """指定されたモジュールをチェーン順にprocess"""
        for name in module_names:
            if name in self.modules:
                self.modules[name].process()

    def output_audio(self, module_name, channel=0):
        """指定されたモジュールから音声を出力"""
        if module_name in self.modules:
            self.modules[module_name].out_to_channel(channel)

    def play_for(self, seconds):
        """指定された秒数だけ音声を再生"""
        print(f"  {seconds}秒間再生中...")
        time.sleep(seconds)

    def cleanup(self):
        """全モジュールを停止"""
        for module in self.modules.values():
            module.stop()


def run_test(test_name, test_func):
    """テストを実行してエラーハンドリング"""
    print(f"\n{'='*20} {test_name} {'='*20}")
    try:
        result = test_func()
        if result:
            print(f"✓ {test_name} 成功")
        else:
            print(f"✗ {test_name} 失敗")
        return result
    except Exception as e:
        print(f"✗ {test_name} エラー: {e}")
        logging.error(f"Test {test_name} failed: {e}")
        return False


def prompt_user(message):
    """ユーザーにプロンプトを表示"""
    input(f"\n{message} (Enter を押して続行...)")
