#!/usr/bin/env python3
"""
Mixer（ミキシング）モジュールテスト
"""

from test_utils import audio_server, TestModuleFactory, TestRunner, run_test, prompt_user


def test_mixer_basic_chord():
    """基本的な和音テスト: 3つのVCO -> Mixer -> VCA"""
    with audio_server() as s:
        runner = TestRunner("Mixer Basic Chord")

        # モジュール作成（A major triad: A-C#-E）
        vco1 = runner.add_module("vco1", TestModuleFactory.create_vco(freq=220, waveform="sine"))  # A3
        vco2 = runner.add_module("vco2", TestModuleFactory.create_vco(freq=277, waveform="sine"))  # C#4
        vco3 = runner.add_module("vco3", TestModuleFactory.create_vco(freq=330, waveform="sine"))  # E4
        mixer = runner.add_module("mixer", TestModuleFactory.create_mixer(inputs=3))
        vca = runner.add_module("vca", TestModuleFactory.create_vca(gain=0.5))

        # 接続: 3つのVCO -> Mixer -> VCA
        runner.connect("vco1", "audio_out", "mixer", "input0")
        runner.connect("vco2", "audio_out", "mixer", "input1")
        runner.connect("vco3", "audio_out", "mixer", "input2")
        runner.connect("mixer", "output", "vca", "audio_in")

        # ミキサーレベル設定
        mixer.set_input_level(0, 0.4)  # A
        mixer.set_input_level(1, 0.3)  # C#
        mixer.set_input_level(2, 0.3)  # E
        mixer.set_master_level(0.6)

        print("  デバッグ: 各モジュールの状態を確認")
        print(f"  VCO1 出力: {vco1.outputs.get('audio_out')}")
        print(f"  VCO2 出力: {vco2.outputs.get('audio_out')}")
        print(f"  VCO3 出力: {vco3.outputs.get('audio_out')}")
        print(f"  Mixer 出力: {mixer.outputs.get('output')}")
        print(f"  VCA 出力: {vca.outputs.get('audio_out')}")

        runner.process_chain("mixer", "vca")

        # 重要：接続を再適用してMixerの新しい出力をVCAに渡す
        runner.cm.update_all_connections()
        vca.process()
        runner.output_audio("vca", 0)

        print("  process()後の状態:")
        print(f"  Mixer 出力: {mixer.outputs.get('output')}")
        print(f"  VCA 出力: {vca.outputs.get('audio_out')}")

        print("  A major triad (A-C#-E) 和音出力中")
        runner.play_for(3)

        print("  レベル調整: C#を強調")
        mixer.set_input_level(0, 0.2)  # A を小さく
        mixer.set_input_level(1, 0.5)  # C# を大きく
        mixer.set_input_level(2, 0.3)  # E はそのまま
        mixer.process()
        runner.play_for(3)

        runner.cleanup()
        return True


def test_mixer_chord_progression():
    """和音進行テスト: 動的に和音を変更"""
    with audio_server() as s:
        runner = TestRunner("Mixer Chord Progression")

        # モジュール作成
        vco1 = runner.add_module("vco1", TestModuleFactory.create_vco(freq=220, waveform="sine"))
        vco2 = runner.add_module("vco2", TestModuleFactory.create_vco(freq=277, waveform="sine"))
        vco3 = runner.add_module("vco3", TestModuleFactory.create_vco(freq=330, waveform="sine"))
        mixer = runner.add_module("mixer", TestModuleFactory.create_mixer(inputs=3))
        vcf = runner.add_module("vcf", TestModuleFactory.create_vcf(freq=2000, q=5))
        vca = runner.add_module("vca", TestModuleFactory.create_vca(gain=0.5))

        # 接続: 3つのVCO -> Mixer -> VCF -> VCA
        runner.connect("vco1", "audio_out", "mixer", "input0")
        runner.connect("vco2", "audio_out", "mixer", "input1")
        runner.connect("vco3", "audio_out", "mixer", "input2")
        runner.connect("mixer", "output", "vcf", "audio_in")
        runner.connect("vcf", "audio_out", "vca", "audio_in")

        # 初期レベル設定
        mixer.set_input_level(0, 0.4)
        mixer.set_input_level(1, 0.3)
        mixer.set_input_level(2, 0.3)
        mixer.set_master_level(0.6)

        runner.process_chain("mixer", "vcf", "vca")
        # 重要：接続を再適用してMixerの新しい出力をVCFに渡す
        runner.cm.update_all_connections()
        runner.process_chain("vcf", "vca")
        runner.output_audio("vca", 0)

        print("  A major (A-C#-E) 和音")
        runner.play_for(3)

        print("  D major (D-F#-A) に変更")
        vco1.set_frequency(147)  # D3
        vco2.set_frequency(185)  # F#3
        vco3.set_frequency(220)  # A3
        runner.process_chain("vco1", "vco2", "vco3")
        runner.play_for(3)

        print("  G major (G-B-D) に変更")
        vco1.set_frequency(196)  # G3
        vco2.set_frequency(247)  # B3
        vco3.set_frequency(294)  # D4
        runner.process_chain("vco1", "vco2", "vco3")
        runner.play_for(3)

        runner.cleanup()
        return True


def test_mixer_rhythmic_pattern():
    """リズミカルなパターンテスト: 複数の音源をリズミカルに混合"""
    with audio_server() as s:
        runner = TestRunner("Mixer Rhythmic Pattern")

        # モジュール作成
        vco_bass = runner.add_module("vco_bass", TestModuleFactory.create_vco(freq=110, waveform="square"))
        vco_lead = runner.add_module("vco_lead", TestModuleFactory.create_vco(freq=440, waveform="sine"))
        vco_noise = runner.add_module("vco_noise", TestModuleFactory.create_vco(freq=1000, waveform="noise"))

        mixer = runner.add_module("mixer", TestModuleFactory.create_mixer(inputs=3))
        vcf = runner.add_module("vcf", TestModuleFactory.create_vcf(freq=1500, q=8))
        vca = runner.add_module("vca", TestModuleFactory.create_vca(gain=0.6))

        # 接続
        runner.connect("vco_bass", "audio_out", "mixer", "input0")
        runner.connect("vco_lead", "audio_out", "mixer", "input1")
        runner.connect("vco_noise", "audio_out", "mixer", "input2")
        runner.connect("mixer", "output", "vcf", "audio_in")
        runner.connect("vcf", "audio_out", "vca", "audio_in")

        # 初期レベル設定
        mixer.set_input_level(0, 0.6)  # ベース
        mixer.set_input_level(1, 0.0)  # リード（最初は無音）
        mixer.set_input_level(2, 0.0)  # ノイズ（最初は無音）
        mixer.set_master_level(0.7)

        runner.process_chain("mixer", "vcf", "vca")
        # 重要：接続を再適用してMixerの新しい出力をVCFに渡す
        runner.cm.update_all_connections()
        runner.process_chain("vcf", "vca")
        runner.output_audio("vca", 0)

        print("  ベースのみ")
        runner.play_for(2)

        print("  リード追加")
        mixer.set_input_level(1, 0.4)
        mixer.process()
        runner.cm.update_all_connections()
        vcf.process()
        vca.process()
        # VCAの出力が新しいオブジェクトに変わるため、再度チャンネル出力を設定
        runner.output_audio("vca", 0)
        runner.play_for(2)

        print("  ノイズ追加（パーカッション風）")
        mixer.set_input_level(2, 0.2)
        mixer.process()
        runner.cm.update_all_connections()
        vcf.process()
        vca.process()
        runner.output_audio("vca", 0)
        runner.play_for(2)

        print("  ベースを減らしてリードを強調")
        mixer.set_input_level(0, 0.3)
        mixer.set_input_level(1, 0.6)
        mixer.set_input_level(2, 0.1)
        mixer.process()
        runner.cm.update_all_connections()
        vcf.process()
        vca.process()
        runner.output_audio("vca", 0)
        runner.play_for(2)

        runner.cleanup()
        return True


def test_mixer_stereo_spread():
    """ステレオスプレッドテスト: 左右で異なるミキシング"""
    with audio_server() as s:
        runner = TestRunner("Mixer Stereo Spread")

        # モジュール作成
        vco1 = runner.add_module("vco1", TestModuleFactory.create_vco(freq=220, waveform="sine"))
        vco2 = runner.add_module("vco2", TestModuleFactory.create_vco(freq=330, waveform="sine"))
        vco3 = runner.add_module("vco3", TestModuleFactory.create_vco(freq=440, waveform="sine"))

        mixer_left = runner.add_module("mixer_left", TestModuleFactory.create_mixer(inputs=3))
        mixer_right = runner.add_module("mixer_right", TestModuleFactory.create_mixer(inputs=3))

        vca_left = runner.add_module("vca_left", TestModuleFactory.create_vca(gain=0.5))
        vca_right = runner.add_module("vca_right", TestModuleFactory.create_vca(gain=0.5))

        # 接続: 3つのVCO -> 2つのMixer -> 2つのVCA
        for i, vco_name in enumerate(["vco1", "vco2", "vco3"]):
            runner.connect(vco_name, "audio_out", "mixer_left", f"input{i}")
            runner.connect(vco_name, "audio_out", "mixer_right", f"input{i}")

        runner.connect("mixer_left", "output", "vca_left", "audio_in")
        runner.connect("mixer_right", "output", "vca_right", "audio_in")

        # 左右で異なるミキシング
        # 左: 低音強調
        mixer_left.set_input_level(0, 0.6)  # 220Hz
        mixer_left.set_input_level(1, 0.3)  # 330Hz
        mixer_left.set_input_level(2, 0.1)  # 440Hz

        # 右: 高音強調
        mixer_right.set_input_level(0, 0.1)  # 220Hz
        mixer_right.set_input_level(1, 0.3)  # 330Hz
        mixer_right.set_input_level(2, 0.6)  # 440Hz

        runner.process_chain("mixer_left", "mixer_right", "vca_left", "vca_right")

        # 重要：接続を再適用してMixerの新しい出力をVCAに渡す
        runner.cm.update_all_connections()
        runner.process_chain("vca_left", "vca_right")

        # ステレオ出力を後に設定
        runner.output_audio("vca_left", 0)  # 左チャンネル
        runner.output_audio("vca_right", 1)  # 右チャンネル

        print("  ステレオスプレッド出力")
        print("  左: 低音強調, 右: 高音強調")
        runner.play_for(4)

        print("  左右のバランスを反転")
        # 左: 高音強調
        mixer_left.set_input_level(0, 0.1)
        mixer_left.set_input_level(1, 0.3)
        mixer_left.set_input_level(2, 0.6)

        # 右: 低音強調
        mixer_right.set_input_level(0, 0.6)
        mixer_right.set_input_level(1, 0.3)
        mixer_right.set_input_level(2, 0.1)

        runner.process_chain("mixer_left", "mixer_right")
        runner.play_for(4)

        runner.cleanup()
        return True


def main():
    """メイン実行関数"""
    print("Mixer（ミキシング）モジュールテストを開始します")

    tests = [
        ("基本的な和音テスト", test_mixer_basic_chord),
        ("和音進行テスト", test_mixer_chord_progression),
        ("リズミカルなパターンテスト", test_mixer_rhythmic_pattern),
        ("ステレオスプレッドテスト", test_mixer_stereo_spread),
    ]

    results = []
    for test_name, test_func in tests:
        prompt_user(f"{test_name}を実行します")
        result = run_test(test_name, test_func)
        results.append((test_name, result))

    print(f"\n{'='*60}")
    print("Mixer モジュールテスト結果:")
    for test_name, result in results:
        status = "✓ 成功" if result else "✗ 失敗"
        print(f"  {test_name}: {status}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
