# モジュラーシンセサイザー接続ガイド

このガイドでは、Pythonモジュラーシンセサイザーの「**作法**」について詳しく説明します。実際のハードウェアモジュラーシンセとの対比を通じて、このシステムの使い方を理解しましょう。

## 🎛️ 基本的な考え方

### 実際のモジュラーシンセ vs Pythonモジュラーシンセ

| 実際のハードウェア | Pythonでの対応 |
|---|---|
| 🔌 パッチケーブルを挿す | `cm.connect()` |
| 🎛️ ノブを回す | `module.set_parameter()` |
| 🔄 設定を反映させる | `module.process()` |
| 🔊 音を出す | `module.out_to_channel()` |
| ⚡ 電源を入れる | `module.start()` |

### 重要な原則

**「物理的な変更には物理的な反映が必要」**

- パッチケーブルを挿したら → `process()` で反映
- ノブを回したら → `process()` で反映
- スイッチを切り替えたら → `process()` で反映

## 🔧 基本的な作法

### 1. モジュールの起動（電源を入れる）

```python
from pyo import Server
from src.connection import ConnectionManager, SignalType
from src.modules.vco import VCO
from src.modules.vca import VCA

# 1. Pyoサーバーを起動（ラックの電源を入れる）
s = Server(nchnls=2, buffersize=512, duplex=0).boot().start()

# 2. ConnectionManagerを作成（パッチベイを準備）
cm = ConnectionManager()

# 3. モジュールを作成（モジュールを選ぶ）
vco = VCO(name="my_osc", base_freq=440)
vca = VCA(name="my_amp", initial_gain=0.8)

# 4. モジュールを登録（ラックに装着）
cm.register_module("my_osc", vco)
cm.register_module("my_amp", vca)

# 5. モジュールを起動（各モジュールの電源を入れる）
vco.start()
vca.start()
```

### 2. パッチケーブルで接続

```python
# パッチケーブルを挿す
cm.connect("my_osc", "audio_out", "my_amp", "audio_in", SignalType.AUDIO)

# 🚨 重要：接続を物理的に反映させる
vca.process()  # VCAにパッチケーブルが「物理的に」挿された状態にする
```

### 3. 音を出す

```python
# スピーカーに接続（実際のモジュラーでは最終出力モジュールに接続）
vca.out_to_channel(0)  # 左チャンネル

# 音を聞く
time.sleep(5)  # 5秒間再生
```

### 4. 終了処理

```python
# モジュールを停止（電源を切る）
vco.stop()
vca.stop()

# サーバーを停止（ラック全体の電源を切る）
s.stop()
s.shutdown()
```

## 🎵 実践的なパッチング例

### 基本パッチ：VCO → VCA

```python
def basic_patch():
    s = Server(nchnls=2, buffersize=512, duplex=0).boot().start()

    try:
        cm = ConnectionManager()

        # モジュール作成・登録・起動
        vco = VCO(name="osc1", base_freq=440, waveform="sine")
        vca = VCA(name="amp1", initial_gain=0.7)

        cm.register_module("osc1", vco)
        cm.register_module("amp1", vca)

        vco.start()
        vca.start()

        # 接続 + 反映
        cm.connect("osc1", "audio_out", "amp1", "audio_in", SignalType.AUDIO)
        vca.process()  # パッチケーブルを物理的に挿す

        # 音を出す
        vca.out_to_channel(0)
        time.sleep(3)

    finally:
        s.stop()
        s.shutdown()
```

### フィルター付きパッチ：VCO → VCF → VCA

```python
def filter_patch():
    s = Server(nchnls=2, buffersize=512, duplex=0).boot().start()

    try:
        cm = ConnectionManager()

        # モジュール作成・登録・起動
        vco = VCO(name="osc1", base_freq=220, waveform="saw")
        vcf = VCF(name="filter1", initial_freq=1000, initial_q=5)
        vca = VCA(name="amp1", initial_gain=0.8)

        cm.register_module("osc1", vco)
        cm.register_module("filter1", vcf)
        cm.register_module("amp1", vca)

        vco.start()
        vcf.start()
        vca.start()

        # 接続 + 反映（信号の流れ順に）
        cm.connect("osc1", "audio_out", "filter1", "audio_in", SignalType.AUDIO)
        cm.connect("filter1", "audio_out", "amp1", "audio_in", SignalType.AUDIO)

        vcf.process()  # VCFにパッチケーブルを挿す
        vca.process()  # VCAにパッチケーブルを挿す

        # 音を出す
        vca.out_to_channel(0)
        time.sleep(3)

    finally:
        s.stop()
        s.shutdown()
```

### CV制御パッチ：LFO → VCF → VCA

```python
def cv_control_patch():
    s = Server(nchnls=2, buffersize=512, duplex=0).boot().start()

    try:
        cm = ConnectionManager()

        # モジュール作成・登録・起動
        vco = VCO(name="osc1", base_freq=110, waveform="saw")
        lfo = LFO(name="lfo1", initial_freq=1, waveform="sine")
        vcf = VCF(name="filter1", initial_freq=400, initial_q=10)
        vca = VCA(name="amp1", initial_gain=0.6)

        cm.register_module("osc1", vco)
        cm.register_module("lfo1", lfo)
        cm.register_module("filter1", vcf)
        cm.register_module("amp1", vca)

        vco.start()
        lfo.start()
        vcf.start()
        vca.start()

        # LFOの設定
        lfo.set_amplitude(300)  # ±300Hzの変調

        # 接続 + 反映
        cm.connect("osc1", "audio_out", "filter1", "audio_in", SignalType.AUDIO)
        cm.connect("filter1", "audio_out", "amp1", "audio_in", SignalType.AUDIO)
        cm.connect("lfo1", "cv_out", "filter1", "freq_cv", SignalType.CV)  # CV制御

        vcf.process()  # VCFに音声とCV両方のケーブルを挿す
        vca.process()  # VCAにパッチケーブルを挿す

        # ワウ効果を5秒間
        vca.out_to_channel(0)
        time.sleep(5)

    finally:
        s.stop()
        s.shutdown()
```

## 🎛️ パラメータ変更の作法

### リアルタイム変更

```python
def realtime_parameter_change():
    s = Server(nchnls=2, buffersize=512, duplex=0).boot().start()

    try:
        # ... 初期セットアップ ...

        # 音を出しながらパラメータを変更
        vca.out_to_channel(0)

        print("初期設定で3秒...")
        time.sleep(3)

        print("カットオフを500Hzに変更...")
        vcf.set_frequency(500)
        vcf.process()  # 🚨 重要：ノブを回したら必ず反映
        time.sleep(3)

        print("カットオフを3000Hzに変更...")
        vcf.set_frequency(3000)
        vcf.process()  # 🚨 重要：ノブを回したら必ず反映
        time.sleep(3)

        print("レゾナンスを20に変更...")
        vcf.set_q(20)
        vcf.process()  # 🚨 重要：ノブを回したら必ず反映
        time.sleep(3)

    finally:
        s.stop()
        s.shutdown()
```

### ENVモジュール（エンベロープ）の特別な作法

```python
def envelope_patch():
    s = Server(nchnls=2, buffersize=512, duplex=0).boot().start()

    try:
        cm = ConnectionManager()

        # モジュール作成・登録・起動
        vco = VCO(name="osc1", base_freq=330, waveform="square")
        env = ENV(name="env1")
        vca = VCA(name="amp1", initial_gain=0)  # 初期音量は0

        cm.register_module("osc1", vco)
        cm.register_module("env1", env)
        cm.register_module("amp1", vca)

        vco.start()
        env.start()
        vca.start()

        # 1. ADSRパラメータを設定
        env.set_attack(0.05)
        env.set_decay(0.3)
        env.set_sustain(0.4)
        env.set_release(1.5)
        env.process()  # 🚨 重要：ADSR設定を反映

        # 2. 音声接続
        cm.connect("osc1", "audio_out", "amp1", "audio_in", SignalType.AUDIO)
        cm.connect("env1", "cv_out", "amp1", "gain_cv", SignalType.CV)
        vca.process()  # VCAの接続を反映（PyoObject CV制御を含む）

        # 3. エンベロープを手動でトリガー
        vca.out_to_channel(0)

        for i in range(3):
            print(f"エンベロープ {i+1}/3 をトリガー")
            env.play()  # エンベロープを直接トリガー
            time.sleep(1.5)  # Attack + Decay + Sustain
            if hasattr(env, 'envelope') and env.envelope:
                env.envelope.stop()  # リリースを開始
            time.sleep(1.5)  # Release

    finally:
        s.stop()
        s.shutdown()
```

## ❌ よくある間違い

### 1. process()を呼び忘れる

```python
# ❌ 間違い：音が出ない
cm.connect("osc1", "audio_out", "amp1", "audio_in", SignalType.AUDIO)
vca.out_to_channel(0)  # 接続が反映されていない

# ✅ 正しい：音が出る
cm.connect("osc1", "audio_out", "amp1", "audio_in", SignalType.AUDIO)
vca.process()  # 接続を反映
vca.out_to_channel(0)
```

### 2. パラメータ変更後にprocess()を呼び忘れる

```python
# ❌ 間違い：音が変わらない
vcf.set_frequency(500)
time.sleep(3)  # パラメータ変更が反映されていない

# ✅ 正しい：音が変わる
vcf.set_frequency(500)
vcf.process()  # パラメータ変更を反映
time.sleep(3)
```

### 3. 信号の流れ順でprocess()を呼ばない

```python
# ❌ 間違い：途中で音が途切れる可能性
vca.process()  # VCAを先に処理
vcf.process()  # VCFを後で処理

# ✅ 正しい：信号の流れ順
vcf.process()  # 入力側から
vca.process()  # 出力側へ
```

## 🔄 process()メソッドの役割

各モジュールの`process()`メソッドが実行する内容：

### VCO（オシレーター）
- 周波数制御（CV）の反映
- 波形パラメータの更新
- FM変調の処理

### VCF（フィルター）
- 音声入力の接続更新
- カットオフ周波数の計算（CV制御含む）
- Q値やフィルタータイプの反映

### VCA（アンプ）
- 音声入力の接続更新
- ゲイン制御（数値・PyoObject CV制御の自動判別）
- 制御曲線の適用
- ENVモジュールのADSRエンベロープによる直接制御

### LFO（低周波オシレーター）
- 周波数パラメータの更新
- 波形設定の反映
- 出力レベルの計算

### ENV（エンベロープ）
- ADSRパラメータの反映
- ゲート信号の接続更新
- エンベロープ状態の管理

## 🔧 高度なモジュール

### Multiple（分岐）モジュール

```python
def multiple_stereo_effect():
    """ステレオ効果: 同じ音源を左右で異なるフィルター処理"""
    s = Server(nchnls=2, buffersize=512, duplex=0).boot().start()

    try:
        cm = ConnectionManager()

        # モジュール作成
        vco = VCO(name="source", base_freq=440, waveform="sine")
        mult = Multiple(name="splitter", outputs=2)
        vcf_left = VCF(name="filter_left", initial_freq=1000)
        vcf_right = VCF(name="filter_right", initial_freq=2000)
        vca_left = VCA(name="amp_left", initial_gain=0.3)
        vca_right = VCA(name="amp_right", initial_gain=0.3)

        # 登録・起動
        for module in [vco, mult, vcf_left, vcf_right, vca_left, vca_right]:
            cm.register_module(module.name, module)
            module.start()

        # 接続: VCO -> Multiple -> 2つのVCF -> 2つのVCA
        cm.connect("source", "audio_out", "splitter", "input", SignalType.AUDIO)
        cm.connect("splitter", "output0", "filter_left", "audio_in", SignalType.AUDIO)
        cm.connect("splitter", "output1", "filter_right", "audio_in", SignalType.AUDIO)
        cm.connect("filter_left", "audio_out", "amp_left", "audio_in", SignalType.AUDIO)
        cm.connect("filter_right", "audio_out", "amp_right", "audio_in", SignalType.AUDIO)

        # 処理
        mult.process()
        vcf_left.process()
        vcf_right.process()
        vca_left.process()
        vca_right.process()

        # ステレオ出力
        vca_left.out_to_channel(0)   # 左チャンネル
        vca_right.out_to_channel(1)  # 右チャンネル

        time.sleep(5)

    finally:
        s.stop()
        s.shutdown()
```

### Mixer（ミキシング）モジュール

```python
def mixer_chord():
    """和音生成: 複数のVCOをミキシング"""
    s = Server(nchnls=2, buffersize=512, duplex=0).boot().start()

    try:
        cm = ConnectionManager()

        # A major triad (A-C#-E)
        vco1 = VCO(name="note_a", base_freq=220)   # A3
        vco2 = VCO(name="note_cs", base_freq=277)  # C#4
        vco3 = VCO(name="note_e", base_freq=330)   # E4
        mixer = Mixer(name="chord_mixer", inputs=3)
        vca = VCA(name="chord_amp")

        # 登録・起動
        for module in [vco1, vco2, vco3, mixer, vca]:
            cm.register_module(module.name, module)
            module.start()

        # 接続
        cm.connect("note_a", "audio_out", "chord_mixer", "input0", SignalType.AUDIO)
        cm.connect("note_cs", "audio_out", "chord_mixer", "input1", SignalType.AUDIO)
        cm.connect("note_e", "audio_out", "chord_mixer", "input2", SignalType.AUDIO)
        cm.connect("chord_mixer", "output", "chord_amp", "audio_in", SignalType.AUDIO)

        # ミキサーレベル設定
        mixer.set_input_level(0, 0.4)  # A
        mixer.set_input_level(1, 0.3)  # C#
        mixer.set_input_level(2, 0.3)  # E
        mixer.set_master_level(0.6)

        # 処理
        mixer.process()
        vca.process()

        # 音声出力
        vca.out_to_channel(0)
        time.sleep(5)

    finally:
        s.stop()
        s.shutdown()
```

### CVMath（CV演算）モジュール

```python
def cvmath_complex_modulation():
    """複雑なCV制御: LFO + エンベロープでVCO制御"""
    s = Server(nchnls=2, buffersize=512, duplex=0).boot().start()

    try:
        cm = ConnectionManager()

        # モジュール作成
        lfo = LFO(name="vibrato", initial_freq=5)
        env = ENV(name="pitch_env")
        cv_add = CVMath(name="pitch_sum", operation="add")
        vco = VCO(name="voice", base_freq=440)
        vca = VCA(name="amp")

        # 登録・起動
        for module in [lfo, env, cv_add, vco, vca]:
            cm.register_module(module.name, module)
            module.start()

        # エンベロープ設定
        env.set_attack(0.3)
        env.set_decay(0.2)
        env.set_sustain(0.8)
        env.set_release(0.8)
        env.process()

        # CV演算設定
        cv_add.set_scale(0.5)
        cv_add.set_offset(0.1)

        # 接続: LFO + ENV → CVMath → VCO
        cm.connect("vibrato", "cv_out", "pitch_sum", "input_a", SignalType.CV)
        cm.connect("pitch_env", "cv_out", "pitch_sum", "input_b", SignalType.CV)
        cm.connect("pitch_sum", "output", "voice", "freq_cv", SignalType.CV)
        cm.connect("voice", "audio_out", "amp", "audio_in", SignalType.AUDIO)

        # 処理
        cv_add.process()
        vco.process()
        vca.process()

        # エンベロープトリガー
        env.trigger()
        env.process()

        # 音声出力
        vca.out_to_channel(0)
        time.sleep(5)

    finally:
        s.stop()
        s.shutdown()
```

## 🎯 まとめ

このPythonモジュラーシンセサイザーは、実際のハードウェアの体験を忠実に再現しています：

1. **物理的な操作** = コードでの操作
2. **物理的な反映** = `process()`の呼び出し
3. **音の変化** = パラメータ変更 + `process()`
4. **CV制御** = 数値・PyoObject両方に対応（VCAで自動判別）
5. **高度な機能** = Multiple・Mixer・CVMathで複雑なパッチが可能
    - **信号分岐**: 1つの音源を複数のエフェクトに分岐
    - **和音生成**: 複数のVCOを混合して和音作成
    - **複雑なCV制御**: 複数のCV信号を演算で組み合わせ
    - **ステレオ効果**: 左右で異なる処理を適用
    - **マルチバンド処理**: 周波数帯域別の処理

この作法を守ることで、本格的なモジュラーシンセサイザーの世界を楽しめます！

Happy patching! 🎵