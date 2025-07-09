#!/usr/bin/env python3
"""
VCO->VCA接続テスト (リファクタリング版)
"""

from test_utils import audio_server, TestModuleFactory, TestRunner, run_test, prompt_user, SignalType


def test_basic_vco_vca_connection():
    """基本的なVCO->VCA接続テスト"""
    with audio_server() as s:
        runner = TestRunner("Basic VCO->VCA")

        # モジュール作成
        vco = runner.add_module("vco", TestModuleFactory.create_vco())
        vca = runner.add_module("vca", TestModuleFactory.create_vca())

        # 接続とプロセス
        runner.connect("vco", "audio_out", "vca", "audio_in")
        runner.process_chain("vca")

        # 音声出力
        runner.output_audio("vca", 0)
        runner.play_for(3)

        runner.cleanup()
        return True


def test_vco_waveforms():
    """VCOの各波形テスト"""
    waveforms = ["sine", "saw", "square", "triangle", "noise"]

    with audio_server() as s:
        runner = TestRunner("VCO Waveforms")

        for waveform in waveforms:
            print(f"\n  テスト中: {waveform} 波形")

            # モジュール作成
            vco = runner.add_module("vco", TestModuleFactory.create_vco(waveform=waveform))
            vca = runner.add_module("vca", TestModuleFactory.create_vca())

            # 接続とプロセス
            runner.connect("vco", "audio_out", "vca", "audio_in")
            runner.process_chain("vca")

            # 音声出力
            runner.output_audio("vca", 0)
            runner.play_for(2)

            # モジュール停止
            vco.stop()
            vca.stop()

            # 新しいテストのために辞書をクリア
            runner.modules.clear()

        return True


def test_vca_gain_control():
    """VCAゲイン制御テスト"""
    gains = [0.1, 0.5, 1.0]

    with audio_server() as s:
        runner = TestRunner("VCA Gain Control")

        vco = runner.add_module("vco", TestModuleFactory.create_vco())
        vca = runner.add_module("vca", TestModuleFactory.create_vca())

        runner.connect("vco", "audio_out", "vca", "audio_in")
        runner.process_chain("vca")
        runner.output_audio("vca", 0)

        for gain in gains:
            print(f"\n  ゲイン設定: {gain}")
            vca.set_gain(gain)
            vca.process()
            runner.play_for(2)

        runner.cleanup()
        return True


def test_multichannel_output():
    """マルチチャンネル出力テスト"""
    with audio_server() as s:
        runner = TestRunner("Multichannel Output")

        # 4つのVCO-VCAペアを作成
        for i in range(4):
            freq = 220 * (2 ** (i * 0.25))  # 4分音階
            vco = runner.add_module(
                f"vco_{i}", TestModuleFactory.create_vco(name=f"vco_{i}", freq=freq, amplitude=0.3)
            )
            vca = runner.add_module(f"vca_{i}", TestModuleFactory.create_vca(name=f"vca_{i}", gain=0.6))

            runner.connect(f"vco_{i}", "audio_out", f"vca_{i}", "audio_in")
            runner.process_chain(f"vca_{i}")
            runner.output_audio(f"vca_{i}", i % 2)  # 0と1チャンネルに交互配置

        print("  4つの異なる音程を2チャンネルで再生")
        runner.play_for(5)

        runner.cleanup()
        return True


def main():
    """メイン実行関数"""
    print("VCO->VCA接続テストスイート")
    print("=" * 50)

    tests = [
        ("基本的なVCO->VCA接続", test_basic_vco_vca_connection),
        ("VCO波形テスト", test_vco_waveforms),
        ("VCAゲイン制御テスト", test_vca_gain_control),
        ("マルチチャンネル出力テスト", test_multichannel_output),
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
