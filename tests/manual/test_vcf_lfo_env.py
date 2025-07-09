#!/usr/bin/env python3
"""
VCF, LFO, ENV モジュールテスト (リファクタリング版)
"""

from test_utils import audio_server, TestModuleFactory, TestRunner, run_test, prompt_user, SignalType


def test_vcf_manual():
    """VCF手動テスト: VCO -> VCF -> VCA"""
    with audio_server() as s:
        runner = TestRunner("VCF Manual")

        # モジュール作成
        vco = runner.add_module("vco", TestModuleFactory.create_vco(freq=220, waveform="saw"))
        vcf = runner.add_module("vcf", TestModuleFactory.create_vcf(freq=2000, q=5))
        vca = runner.add_module("vca", TestModuleFactory.create_vca())

        # 接続
        runner.connect("vco", "audio_out", "vcf", "audio_in")
        runner.connect("vcf", "audio_out", "vca", "audio_in")
        runner.process_chain("vcf", "vca")

        # 音声出力とパラメータ変更テスト
        runner.output_audio("vca", 0)

        print("  初期設定 (カットオフ2000Hz, Q=5)")
        runner.play_for(3)

        print("  カットオフを500Hzに変更")
        vcf.set_frequency(500)
        vcf.process()
        runner.play_for(3)

        print("  カットオフを3000Hzに変更")
        vcf.set_frequency(3000)
        vcf.process()
        runner.play_for(3)

        print("  Q値を20に変更 (レゾナンス強化)")
        vcf.set_q(20)
        vcf.process()
        runner.play_for(3)

        runner.cleanup()
        return True


def test_lfo_to_vcf():
    """LFO->VCF テスト (ワウ効果)"""
    with audio_server() as s:
        runner = TestRunner("LFO->VCF")

        # モジュール作成
        vco = runner.add_module("vco", TestModuleFactory.create_vco(freq=110, waveform="saw"))
        lfo = runner.add_module("lfo", TestModuleFactory.create_lfo(freq=1, amplitude=300))
        vcf = runner.add_module("vcf", TestModuleFactory.create_vcf(freq=400, q=10))
        vca = runner.add_module("vca", TestModuleFactory.create_vca(gain=0.6))

        # 接続
        runner.connect("vco", "audio_out", "vcf", "audio_in")
        runner.connect("vcf", "audio_out", "vca", "audio_in")
        runner.connect("lfo", "cv_out", "vcf", "freq_cv", SignalType.CV)
        runner.process_chain("vcf", "vca")

        # ワウ効果テスト
        runner.output_audio("vca", 0)
        print("  ワウ効果 (LFO 1Hz, ±300Hz変調)")
        runner.play_for(8)

        runner.cleanup()
        return True


def test_lfo_to_vco():
    """LFO->VCO テスト (ビブラート効果)"""
    with audio_server() as s:
        runner = TestRunner("LFO->VCO")

        # モジュール作成
        vco = runner.add_module("vco", TestModuleFactory.create_vco(freq=440, waveform="sine"))
        lfo = runner.add_module("lfo", TestModuleFactory.create_lfo(freq=5, amplitude=20))
        vca = runner.add_module("vca", TestModuleFactory.create_vca())

        # 接続
        runner.connect("vco", "audio_out", "vca", "audio_in")
        runner.connect("lfo", "cv_out", "vco", "freq_cv", SignalType.CV)
        runner.process_chain("vco", "vca")

        # ビブラート効果テスト
        runner.output_audio("vca", 0)
        print("  ビブラート効果 (LFO 5Hz, ±20Hz変調)")
        runner.play_for(6)

        runner.cleanup()
        return True


def test_env_to_vca():
    """ENV->VCA テスト (ADSRエンベロープ)"""
    with audio_server() as s:
        runner = TestRunner("ENV->VCA")

        # モジュール作成
        vco = runner.add_module("vco", TestModuleFactory.create_vco(freq=330, waveform="square"))
        env = runner.add_module("env", TestModuleFactory.create_env())
        vca = runner.add_module("vca", TestModuleFactory.create_vca(gain=0))  # 初期音量0

        # 接続
        runner.connect("vco", "audio_out", "vca", "audio_in")
        runner.connect("env", "cv_out", "vca", "gain_cv", SignalType.CV)
        runner.process_chain("vca")

        # ENVのprocess()でADSRパラメータを反映
        env.process()

        # ADSRエンベロープテスト
        runner.output_audio("vca", 0)

        for i in range(3):
            print(f"  エンベロープ {i+1}/3 をトリガー")

            # エンベロープトリガー
            env.play()
            runner.play_for(1)  # Attack + Decay + Sustain

            # リリース
            if hasattr(env, "envelope") and env.envelope:
                env.envelope.stop()
            runner.play_for(1.5)  # Release

        runner.cleanup()
        return True


def test_complex_patch():
    """複雑なパッチテスト: VCO -> VCF -> VCA + LFO + ENV"""
    with audio_server() as s:
        runner = TestRunner("Complex Patch")

        # モジュール作成
        vco = runner.add_module("vco", TestModuleFactory.create_vco(freq=220, waveform="saw"))
        vcf = runner.add_module("vcf", TestModuleFactory.create_vcf(freq=600, q=8))
        vca = runner.add_module("vca", TestModuleFactory.create_vca(gain=0))
        lfo = runner.add_module("lfo", TestModuleFactory.create_lfo(freq=2, amplitude=200))
        env = runner.add_module("env", TestModuleFactory.create_env())

        # 接続
        runner.connect("vco", "audio_out", "vcf", "audio_in")
        runner.connect("vcf", "audio_out", "vca", "audio_in")
        runner.connect("lfo", "cv_out", "vcf", "freq_cv", SignalType.CV)
        runner.connect("env", "cv_out", "vca", "gain_cv", SignalType.CV)
        runner.process_chain("vcf", "vca")

        env.process()

        # 複雑なパッチテスト
        runner.output_audio("vca", 0)

        print("  複雑なパッチ: VCO->VCF->VCA + LFO(フィルター変調) + ENV(音量制御)")
        for i in range(2):
            print(f"    エンベロープ {i+1}/2 をトリガー")
            env.play()
            runner.play_for(2)

            if hasattr(env, "envelope") and env.envelope:
                env.envelope.stop()
            runner.play_for(1)

        runner.cleanup()
        return True


def main():
    """メイン実行関数"""
    print("VCF, LFO, ENV モジュールテストスイート")
    print("=" * 50)

    tests = [
        ("VCF手動テスト", test_vcf_manual),
        ("LFO->VCF (ワウ効果)", test_lfo_to_vcf),
        ("LFO->VCO (ビブラート効果)", test_lfo_to_vco),
        ("ENV->VCA (ADSRエンベロープ)", test_env_to_vca),
        ("複雑なパッチテスト", test_complex_patch),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        prompt_user(f"{test_name}を実行します")
        if run_test(test_name, test_func):
            passed += 1

    print(f"\n結果: {passed}/{total} テスト成功")
    return passed == total


if __name__ == "__main__":
    main()
