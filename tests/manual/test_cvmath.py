#!/usr/bin/env python3
"""
CVMath（CV演算）モジュールテスト
"""

from test_utils import audio_server, TestModuleFactory, TestRunner, run_test, prompt_user, SignalType


def test_cvmath_basic_operations():
    """基本的な演算テスト: 四則演算の確認"""
    with audio_server() as s:
        runner = TestRunner("CVMath Basic Operations")

        # モジュール作成（大幅に異なるLFO設定で明確な違いを作る）
        lfo1 = runner.add_module("lfo1", TestModuleFactory.create_lfo(freq=0.2, amplitude=200))  # 非常にゆっくり
        lfo2 = runner.add_module("lfo2", TestModuleFactory.create_lfo(freq=3.0, amplitude=100))  # 速い変調
        cv_math = runner.add_module("cv_math", TestModuleFactory.create_cvmath(operation="add"))
        vco = runner.add_module("vco", TestModuleFactory.create_vco(freq=440, waveform="sine"))
        vca = runner.add_module("vca", TestModuleFactory.create_vca(gain=0.4))

        # 接続: 2つのLFO -> CVMath -> VCO -> VCA
        runner.connect("lfo1", "cv_out", "cv_math", "input_a", SignalType.CV)
        runner.connect("lfo2", "cv_out", "cv_math", "input_b", SignalType.CV)
        runner.connect("cv_math", "output", "vco", "freq_cv", SignalType.CV)
        runner.connect("vco", "audio_out", "vca", "audio_in")

        # 初期CV演算設定
        cv_math.set_scale(0.8)  # 適度なスケール
        cv_math.set_offset(0.1)

        runner.process_chain("cv_math", "vco", "vca")

        # CV値の数値監視機能を追加
        def print_cv_values_basic():
            try:
                # outputsディクショナリから正しくCV値を取得
                lfo1_cv = lfo1.outputs.get("cv_out")
                lfo2_cv = lfo2.outputs.get("cv_out")
                cv_result_obj = cv_math.outputs.get("output")
                
                # PyoObjectの値を安全に取得（単一値の場合とリストの場合に対応）
                def get_pyo_value(pyo_obj):
                    if not pyo_obj or not hasattr(pyo_obj, 'get'):
                        return "N/A"
                    try:
                        val = pyo_obj.get()
                        return val[0] if isinstance(val, (list, tuple)) and len(val) > 0 else val
                    except (IndexError, TypeError):
                        return "N/A"
                
                lfo1_val = get_pyo_value(lfo1_cv)
                lfo2_val = get_pyo_value(lfo2_cv)
                cv_result = get_pyo_value(cv_result_obj)
                # 数値フォーマット（N/Aの場合はそのまま表示）
                def format_val(val):
                    return f"{val:.3f}" if isinstance(val, (int, float)) else str(val)
                
                print(f"    数値監視 - LFO1: {format_val(lfo1_val)}, LFO2: {format_val(lfo2_val)}, CV演算結果: {format_val(cv_result)}")
            except Exception as e:
                print(f"    CV値監視エラー: {e}")

        # 音声出力
        runner.output_audio("vca", 0)

        print("  加算演算: LFO1(0.2Hz, 200) + LFO2(3Hz, 100)")
        print("    期待する音: ゆっくりとした大きな変化 + 細かい高速変化")
        
        # リアルタイム連続監視（0.5秒間隔で6秒間）
        import time
        print("    リアルタイム数値監視開始...")
        for i in range(12):  # 6秒間、0.5秒間隔
            print_cv_values_basic()
            time.sleep(0.5)
        print("    監視終了")

        print("  減算演算: LFO1 - LFO2 -> 異なる相互作用パターン")
        print("    期待する音: 加算とは明らかに異なる周波数パターン")
        cv_math.set_operation("subtract")
        cv_math.process()
        
        # 減算演算の短時間監視（2秒間）
        print("    減算演算の2秒間監視...")
        for i in range(4):  # 2秒間、0.5秒間隔
            print_cv_values_basic()
            time.sleep(0.5)
        print("    残り4秒間の音響効果確認中...")
        time.sleep(4)

        print("  乗算演算: LFO1 * LFO2 -> リングモジュレーション効果")
        print("    期待する音: より複雑で非線形な周波数変化")
        cv_math.set_operation("multiply")
        cv_math.set_scale(0.1)  # 乗算結果は大きくなりがちなので小さくする
        cv_math.process()
        print_cv_values_basic()
        runner.play_for(6)

        print("  極端なテスト: LFO1単体の効果確認")
        print("    LFO2を除外してLFO1のみの変調を聞く")
        cv_math.set_operation("add")
        cv_math.set_scale(1.0)  # LFO1 + 0 = LFO1
        cv_math.set_offset(0.0)
        # input_bの接続を維持したまま、LFO2を0に近い値に設定
        lfo2.set_amplitude(0.1)  # ほぼゼロ
        lfo2.process()
        cv_math.process()
        print_cv_values_basic()
        runner.play_for(4)

        runner.cleanup()
        return True


def test_cvmath_complex_modulation():
    """複雑なCV制御テスト: LFO + エンベロープでVCO制御"""
    with audio_server() as s:
        runner = TestRunner("CVMath Complex Modulation")

        # モジュール作成
        lfo = runner.add_module("lfo", TestModuleFactory.create_lfo(freq=5, amplitude=200))
        env = runner.add_module("env", TestModuleFactory.create_env(attack=0.3, decay=0.2, sustain=0.8, release=0.8))
        cv_add = runner.add_module("cv_add", TestModuleFactory.create_cvmath(operation="add"))
        vco = runner.add_module("vco", TestModuleFactory.create_vco(freq=440, waveform="sine"))
        vca = runner.add_module("vca", TestModuleFactory.create_vca(gain=0.4))

        # 接続: LFO + ENV -> CVMath -> VCO -> VCA
        runner.connect("lfo", "cv_out", "cv_add", "input_a", SignalType.CV)
        runner.connect("env", "cv_out", "cv_add", "input_b", SignalType.CV)
        runner.connect("cv_add", "output", "vco", "freq_cv", SignalType.CV)
        runner.connect("vco", "audio_out", "vca", "audio_in")

        # CV演算のスケール設定
        cv_add.set_scale(0.5)  # 結果を半分に
        cv_add.set_offset(0.1)  # 小さなオフセット

        runner.process_chain("cv_add", "vco", "vca")

        # 音声出力
        runner.output_audio("vca", 0)

        print("  エンベロープトリガー: LFO + ENV -> VCO周波数制御")
        env.play()
        env.process()
        runner.play_for(4)

        print("  演算タイプを乗算に変更")
        cv_add.set_operation("multiply")
        cv_add.set_scale(0.1)
        cv_add.process()

        env.play()
        env.process()
        runner.play_for(4)

        runner.cleanup()
        return True


def test_cvmath_filter_modulation():
    """フィルター制御テスト: 複数のCV信号でVCFを制御"""
    with audio_server() as s:
        runner = TestRunner("CVMath Filter Modulation")

        # モジュール作成
        vco = runner.add_module("vco", TestModuleFactory.create_vco(freq=220, waveform="saw"))
        lfo_slow = runner.add_module(
            "lfo_slow", TestModuleFactory.create_lfo(freq=0.5, amplitude=300)
        )  # ゆっくりなLFO
        lfo_fast = runner.add_module("lfo_fast", TestModuleFactory.create_lfo(freq=8, amplitude=150))
        cv_add = runner.add_module("cv_add", TestModuleFactory.create_cvmath(operation="add"))
        vcf = runner.add_module("vcf", TestModuleFactory.create_vcf(freq=1000, q=10))
        vca = runner.add_module("vca", TestModuleFactory.create_vca(gain=0.5))

        # 接続: VCO -> VCF -> VCA, 2つのLFO -> CVMath -> VCF制御
        runner.connect("vco", "audio_out", "vcf", "audio_in")
        runner.connect("vcf", "audio_out", "vca", "audio_in")
        runner.connect("lfo_slow", "cv_out", "cv_add", "input_a", SignalType.CV)
        runner.connect("lfo_fast", "cv_out", "cv_add", "input_b", SignalType.CV)
        runner.connect("cv_add", "output", "vcf", "freq_cv", SignalType.CV)

        # CV演算設定
        cv_add.set_scale(0.6)
        cv_add.set_offset(0.2)

        runner.process_chain("cv_add", "vcf", "vca")

        # 音声出力
        runner.output_audio("vca", 0)

        print("  フィルター制御: 低速LFO + 高速LFO -> VCF")
        runner.play_for(5)

        print("  演算を減算に変更")
        cv_add.set_operation("subtract")
        cv_add.process()
        runner.play_for(4)

        print("  フィルターQ値を変更")
        vcf.set_q(20)
        vcf.process()
        runner.play_for(3)

        runner.cleanup()
        return True


def test_cvmath_dual_vco_control():
    """デュアルVCO制御テスト: 1つのCV信号で2つのVCOを異なる方法で制御"""
    with audio_server() as s:
        runner = TestRunner("CVMath Dual VCO Control")

        # モジュール作成（問題修正: Mixerを使わずに個別テスト）
        lfo = runner.add_module("lfo", TestModuleFactory.create_lfo(freq=0.8, amplitude=100))  # 適度な変調強度
        cv_normal = runner.add_module("cv_normal", TestModuleFactory.create_cvmath(operation="add"))
        cv_inverted = runner.add_module("cv_inverted", TestModuleFactory.create_cvmath(operation="add"))
        vco1 = runner.add_module("vco1", TestModuleFactory.create_vco(freq=440, waveform="sine"))
        vco2 = runner.add_module("vco2", TestModuleFactory.create_vco(freq=550, waveform="sine"))
        vca1 = runner.add_module("vca1", TestModuleFactory.create_vca(gain=0.4))
        vca2 = runner.add_module("vca2", TestModuleFactory.create_vca(gain=0.4))

        # 接続: LFO -> 2つのCVMath -> 2つのVCO -> 2つのVCA (個別出力)
        runner.connect("lfo", "cv_out", "cv_normal", "input_a", SignalType.CV)
        runner.connect("lfo", "cv_out", "cv_inverted", "input_a", SignalType.CV)

        runner.connect("cv_normal", "output", "vco1", "freq_cv", SignalType.CV)
        runner.connect("cv_inverted", "output", "vco2", "freq_cv", SignalType.CV)
        runner.connect("vco1", "audio_out", "vca1", "audio_in")
        runner.connect("vco2", "audio_out", "vca2", "audio_in")

        # CV演算設定（修正: 明確な差を作る）
        cv_normal.set_operation("add")
        cv_normal.set_scale(1.0)  # 通常の変調（LFO + 0 = LFO）
        cv_normal.set_offset(0.0)

        cv_inverted.set_operation("add")  # 加算だが負のスケールで逆相
        cv_inverted.set_scale(-1.0)  # 逆方向の変調（-LFO + 0 = -LFO）
        cv_inverted.set_offset(0.0)

        runner.process_chain("cv_normal", "cv_inverted", "vco1", "vco2", "vca1", "vca2")

        # CV値の数値監視機能を追加
        def print_cv_values():
            try:
                # outputsディクショナリから正しくCV値を取得
                lfo_cv = lfo.outputs.get("cv_out")
                cv_normal_obj = cv_normal.outputs.get("output")
                cv_inverted_obj = cv_inverted.outputs.get("output")
                
                # PyoObjectの値を安全に取得（単一値の場合とリストの場合に対応）
                def get_pyo_value(pyo_obj):
                    if not pyo_obj or not hasattr(pyo_obj, 'get'):
                        return "N/A"
                    try:
                        val = pyo_obj.get()
                        return val[0] if isinstance(val, (list, tuple)) and len(val) > 0 else val
                    except (IndexError, TypeError):
                        return "N/A"
                
                # 数値フォーマット（N/Aの場合はそのまま表示）
                def format_val(val):
                    return f"{val:.3f}" if isinstance(val, (int, float)) else str(val)
                
                lfo_val = get_pyo_value(lfo_cv)
                cv_normal_val = get_pyo_value(cv_normal_obj)
                cv_inverted_val = get_pyo_value(cv_inverted_obj)
                print(f"    数値監視 - LFO: {format_val(lfo_val)}, CV_normal: {format_val(cv_normal_val)}, CV_inverted: {format_val(cv_inverted_val)}")
            except Exception as e:
                print(f"    CV値監視エラー: {e}")

        print("  VCO1のみ出力テスト (440Hz + LFO変調)")
        print_cv_values()
        runner.output_audio("vca1", 0)
        runner.play_for(3)

        print("  VCO2のみ出力テスト (550Hz - LFO変調)")
        # VCA1のゲインを0にして無音化（out_to_channel(-1)の代替）
        vca1.set_gain(0)
        vca1.process()
        print_cv_values()
        runner.output_audio("vca2", 0)
        runner.play_for(3)

        print("  変調強度を3倍に増加してテスト")
        cv_normal.set_scale(3.0)
        cv_inverted.set_scale(-3.0)
        runner.process_chain("cv_normal", "cv_inverted")
        print_cv_values()

        print("  VCO1 (3倍変調)")
        # VCA2のゲインを0、VCA1のゲインを復元
        vca1.set_gain(0.4)
        vca2.set_gain(0)
        runner.process_chain("vca1", "vca2")
        runner.output_audio("vca1", 0)
        runner.play_for(3)

        print("  VCO2 (3倍逆変調)")
        # VCA1のゲインを0、VCA2のゲインを復元
        vca1.set_gain(0)
        vca2.set_gain(0.4)
        runner.process_chain("vca1", "vca2")

        runner.output_audio("vca2", 0)
        runner.play_for(3)

        runner.cleanup()
        return True


def test_cvmath_envelope_shaping():
    """エンベロープシェイピングテスト: エンベロープを数学的に変形"""
    with audio_server() as s:
        runner = TestRunner("CVMath Envelope Shaping")

        # モジュール作成
        vco = runner.add_module("vco", TestModuleFactory.create_vco(freq=440, waveform="sine"))
        env = runner.add_module("env", TestModuleFactory.create_env(attack=0.2, decay=0.3, sustain=0.7, release=1.5))
        cv_shape = runner.add_module("cv_shape", TestModuleFactory.create_cvmath(operation="multiply"))
        vca = runner.add_module("vca", TestModuleFactory.create_vca(gain=0.1))  # 小さな基本ゲイン

        # 接続: VCO -> VCA, ENV -> CVMath -> VCA制御
        runner.connect("vco", "audio_out", "vca", "audio_in")
        runner.connect("env", "cv_out", "cv_shape", "input_a", SignalType.CV)
        # input_bは接続せずにデフォルト値を使用
        runner.connect("cv_shape", "output", "vca", "gain_cv", SignalType.CV)

        # CV演算設定（エンベロープを2乗して急峻にする）
        cv_shape.set_scale(1.0)
        cv_shape.set_offset(0.0)

        runner.process_chain("cv_shape", "vca")

        # 音声出力
        runner.output_audio("vca", 0)

        print("  元のエンベロープ（パススルー）")
        cv_shape.set_operation("add")  # input_b = 0でパススルー (ENV + 0 = ENV)
        cv_shape.process()
        print("    エンベロープをトリガー...")
        env.play()
        env.process()
        runner.play_for(4)  # 少し長めに

        print("  エンベロープを2乗（急峻化）")
        # input_bにもエンベロープを接続して自分自身を掛ける
        runner.connect("env", "cv_out", "cv_shape", "input_b", SignalType.CV)
        cv_shape.set_operation("multiply")  # ENV * ENV = ENV²
        cv_shape.process()
        print("    エンベロープをトリガー...")
        env.play()
        env.process()
        runner.play_for(4)

        print("  エンベロープをスケール（弱める）")
        cv_shape.set_operation("multiply")
        cv_shape.set_scale(0.3)  # より小さく
        cv_shape.process()
        print("    エンベロープをトリガー...")
        env.play()
        env.process()
        runner.play_for(4)

        runner.cleanup()
        return True


def main():
    """メイン実行関数"""
    print("CVMath（CV演算）モジュールテストを開始します")

    tests = [
        ("基本的な演算テスト", test_cvmath_basic_operations),
        ("複雑なCV制御テスト", test_cvmath_complex_modulation),
        ("フィルター制御テスト", test_cvmath_filter_modulation),
        ("デュアルVCO制御テスト", test_cvmath_dual_vco_control),
        ("エンベロープシェイピングテスト", test_cvmath_envelope_shaping),
    ]

    results = []
    for test_name, test_func in tests:
        prompt_user(f"{test_name}を実行します")
        result = run_test(test_name, test_func)
        results.append((test_name, result))

    print(f"\n{'='*60}")
    print("CVMath モジュールテスト結果:")
    for test_name, result in results:
        status = "✓ 成功" if result else "✗ 失敗"
        print(f"  {test_name}: {status}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
