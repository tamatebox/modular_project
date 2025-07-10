#!/usr/bin/env python3
"""
Multiple（分岐）モジュールテスト
"""

import logging
from test_utils import audio_server, TestModuleFactory, TestRunner, run_test, prompt_user, SignalType

# デバッグ用にログレベルを設定
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def test_multiple_basic():
    """基本的な分岐テスト: VCO -> Multiple -> 2つのVCF"""
    with audio_server() as s:
        runner = TestRunner("Multiple Basic")

        # モジュール作成
        vco = runner.add_module("vco", TestModuleFactory.create_vco(freq=440, waveform="sine"))
        mult = runner.add_module("mult", TestModuleFactory.create_multiple(outputs=2))
        vcf1 = runner.add_module("vcf1", TestModuleFactory.create_vcf(freq=1000, q=5))
        vcf2 = runner.add_module("vcf2", TestModuleFactory.create_vcf(freq=2000, q=5))
        mixer = runner.add_module("mixer", TestModuleFactory.create_mixer(inputs=2))
        vca = runner.add_module("vca", TestModuleFactory.create_vca(gain=0.4))

        # 接続: VCO -> Multiple -> 2つのVCF -> Mixer -> VCA
        runner.connect("vco", "audio_out", "mult", "input")
        runner.connect("mult", "output0", "vcf1", "audio_in")
        runner.connect("mult", "output1", "vcf2", "audio_in")
        runner.connect("vcf1", "audio_out", "mixer", "input0")
        runner.connect("vcf2", "audio_out", "mixer", "input1")
        runner.connect("mixer", "output", "vca", "audio_in")

        # ミキサーレベル設定（ステレオ効果のため異なるレベル）
        mixer.set_input_level(0, 0.6)  # VCF1(1000Hz)を強調
        mixer.set_input_level(1, 0.4)  # VCF2(2000Hz)を弱く

        # 信号フロー順に処理：Multiple → 接続更新 → VCF × 2 → Mixer → VCA
        runner.process_chain("mult")  # 信号分岐を適用
        
        # Multipleの新しい出力をVCFに反映するため接続を更新
        runner.cm.update_all_connections()
        
        runner.process_chain("vcf1", "vcf2")  # VCFで信号を受信・処理
        runner.process_chain("mixer", "vca")  # Mixerから後を処理

        # デバッグ: Multipleの出力状態をチェック
        print(f"  DEBUG: Multiple outputs: {mult.outputs}")
        print(f"  DEBUG: Mixer inputs: {mixer.inputs}")
        print(f"  DEBUG: VCA inputs: {vca.inputs}")

        # モノラル出力（Mixerで既にブレンドされている）
        runner.output_audio("vca", 0)

        print("  分岐したオーディオ出力中（ミックス）")
        print("  VCO -> Multiple -> VCF1(1000Hz 60%) + VCF2(2000Hz 40%) -> Mixer")
        runner.play_for(3)

        print("  フィルター周波数を動的に変更")
        vcf1.set_frequency(500)
        vcf2.set_frequency(3000)
        runner.process_chain("vcf1", "vcf2", "mixer")
        runner.play_for(3)

        runner.cleanup()
        return True


def test_multiple_cv_split():
    """CV分岐テスト: LFO -> Multiple -> 2つのVCO"""
    with audio_server() as s:
        runner = TestRunner("Multiple CV Split")

        # モジュール作成
        lfo = runner.add_module("lfo", TestModuleFactory.create_lfo(freq=2, amplitude=100))
        mult = runner.add_module("mult", TestModuleFactory.create_multiple(outputs=2))
        vco1 = runner.add_module("vco1", TestModuleFactory.create_vco(freq=220, waveform="sine"))
        vco2 = runner.add_module("vco2", TestModuleFactory.create_vco(freq=330, waveform="sine"))
        mixer = runner.add_module("mixer", TestModuleFactory.create_mixer(inputs=2))
        vca = runner.add_module("vca", TestModuleFactory.create_vca(gain=0.4))

        # 接続: LFO -> Multiple -> 2つのVCO -> Mixer -> VCA
        runner.connect("lfo", "cv_out", "mult", "input", SignalType.CV)
        runner.connect("mult", "output0", "vco1", "freq_cv", SignalType.CV)
        runner.connect("mult", "output1", "vco2", "freq_cv", SignalType.CV)
        runner.connect("vco1", "audio_out", "mixer", "input0")
        runner.connect("vco2", "audio_out", "mixer", "input1")
        runner.connect("mixer", "output", "vca", "audio_in")

        # ミキサーレベル設定
        mixer.set_input_level(0, 0.5)
        mixer.set_input_level(1, 0.5)

        runner.process_chain("mult", "vco1", "vco2", "mixer", "vca")

        # 音声出力
        runner.output_audio("vca", 0)

        print("  LFO -> Multiple -> 2つのVCO周波数制御")
        print("  同じLFOで2つのVCOが同期して変調")
        runner.play_for(5)

        runner.cleanup()
        return True


def test_multiple_fan_out():
    """ファンアウトテスト: 1つのVCO -> Multiple -> 4つの異なる処理"""
    with audio_server() as s:
        runner = TestRunner("Multiple Fan Out")

        # モジュール作成
        vco = runner.add_module("vco", TestModuleFactory.create_vco(freq=220, waveform="saw"))
        mult = runner.add_module("mult", TestModuleFactory.create_multiple(outputs=4))

        # 4つの異なる処理
        vcf1 = runner.add_module("vcf1", TestModuleFactory.create_vcf(freq=500, q=5))  # 低域通過
        vcf2 = runner.add_module("vcf2", TestModuleFactory.create_vcf(freq=1500, q=5))  # 中域通過
        vcf3 = runner.add_module("vcf3", TestModuleFactory.create_vcf(freq=3000, q=5))  # 高域通過
        vca_direct = runner.add_module("vca_direct", TestModuleFactory.create_vca(gain=0.2))  # 直接

        mixer = runner.add_module("mixer", TestModuleFactory.create_mixer(inputs=4))
        vca_out = runner.add_module("vca_out", TestModuleFactory.create_vca(gain=0.6))

        # 接続: VCO -> Multiple -> 4つの処理 -> Mixer -> VCA
        runner.connect("vco", "audio_out", "mult", "input")
        runner.connect("mult", "output0", "vcf1", "audio_in")
        runner.connect("mult", "output1", "vcf2", "audio_in")
        runner.connect("mult", "output2", "vcf3", "audio_in")
        runner.connect("mult", "output3", "vca_direct", "audio_in")

        runner.connect("vcf1", "audio_out", "mixer", "input0")
        runner.connect("vcf2", "audio_out", "mixer", "input1")
        runner.connect("vcf3", "audio_out", "mixer", "input2")
        runner.connect("vca_direct", "audio_out", "mixer", "input3")
        runner.connect("mixer", "output", "vca_out", "audio_in")

        # ミキサーレベル設定
        mixer.set_input_level(0, 0.3)  # 低域
        mixer.set_input_level(1, 0.3)  # 中域
        mixer.set_input_level(2, 0.2)  # 高域
        mixer.set_input_level(3, 0.2)  # 直接

        # 信号フロー順に処理：Multiple → 接続更新 → VCF × 3 + VCA → Mixer → VCA
        runner.process_chain("mult")  # 信号分岐を適用
        
        # Multipleの新しい出力を中間モジュールに反映するため接続を更新
        runner.cm.update_all_connections()
        
        runner.process_chain("vcf1", "vcf2", "vcf3", "vca_direct")  # 中間処理
        runner.process_chain("mixer", "vca_out")  # Mixerから後を処理

        # デバッグ: Multipleの出力状態をチェック
        print(f"  DEBUG: Multiple outputs: {mult.outputs}")
        print(f"  DEBUG: VCO output: {vco.outputs}")
        print(f"  DEBUG: Mixer inputs: {mixer.inputs}")

        # 音声出力
        runner.output_audio("vca_out", 0)

        print("  1つのVCO -> 4つの異なる処理")
        print("  低域(500Hz) + 中域(1500Hz) + 高域(3000Hz) + 直接")
        runner.play_for(4)

        print("  ミキサーレベルを動的に変更")
        mixer.set_input_level(0, 0.6)  # 低域を強調
        mixer.set_input_level(1, 0.1)
        mixer.set_input_level(2, 0.1)
        mixer.set_input_level(3, 0.2)
        mixer.process()
        runner.play_for(3)

        runner.cleanup()
        return True


def main():
    """メイン実行関数"""
    print("Multiple（分岐）モジュールテストを開始します")

    tests = [
        ("基本的な分岐テスト", test_multiple_basic),
        ("CV分岐テスト", test_multiple_cv_split),
        ("ファンアウトテスト", test_multiple_fan_out),
    ]

    results = []
    for test_name, test_func in tests:
        prompt_user(f"{test_name}を実行します")
        result = run_test(test_name, test_func)
        results.append((test_name, result))

    print(f"\n{'='*60}")
    print("Multiple モジュールテスト結果:")
    for test_name, result in results:
        status = "✓ 成功" if result else "✗ 失敗"
        print(f"  {test_name}: {status}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
