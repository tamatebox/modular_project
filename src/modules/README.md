# Synth Modules

このディレクトリには、Pythonモジュラーシンセサイザーの心臓部となる各音声処理モジュールが含まれています。

## 基本設計

すべてのモジュールは `src/modules/base_module.py` に定義されている `BaseModule` クラスを継承しています。これにより、すべてのモジュールは一貫したインターフェースを持ちます。

- **パラメータ (`parameters`)**: 各モジュールの設定値（周波数、ゲインなど）。
- **入力ポート (`inputs`)**: 他のモジュールから音声信号や制御信号（CV）を受け取るための端子。
- **出力ポート (`outputs`)**: 他のモジュールへ信号を送るための端子。
- **ライフサイクル**:
    - `__init__()`: モジュールの初期化。
    - `start()`: `pyo`オブジェクトを生成し、音声処理を開始する。
    - `stop()`: 音声処理を停止する。
    - `process()`: パラメータや入力の変更を`pyo`オブジェクトに反映させるためのメインループ。
- **固定出力アーキテクチャ**: `process()`実行後も出力オブジェクトが自動的に維持され、現実のハードウェアモジュラーシンセと同様の動作を実現。

## ロギング

各モジュールは、Pythonの標準`logging`モジュールを使用して、動作状況や警告を出力します。`print()`は使用されていません。

これにより、アプリケーション全体でログの表示レベルやフォーマット、出力先（コンソール、ファイルなど）を柔軟に制御できます。

モジュールからのログを有効にするには、アプリケーションのエントリーポイント（例: `main.py`）で以下のように基本的な設定を行う必要があります。

```python
import logging

logging.basicConfig(
    level=logging.INFO, # INFOレベル以上のログを表示
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```
- `level`: 表示するログの最低レベルを指定します (`DEBUG`, `INFO`, `WARNING`, `ERROR`)。
- `format`: ログの出力形式を定義します。`%(name)s` には `src.modules.vco` のようにモジュール名が入ります。

## モジュール一覧

### 基本モジュール

- ### `base_module.py`
  - すべてのモジュールの基底クラス。上記で説明した共通の機能を提供します。

- ### `vco.py` (Voltage Controlled Oscillator)
  - **役割**: 電圧制御オシレーター。音の源となる基本波形（サイン波、ノコギリ波、矩形波など）を生成します。
  - **主なパラメータ**: `base_freq`（基本周波数）、`waveform`（波形）、`amplitude`（振幅）。
  - **主な入出力**: `freq_cv`（周波数制御）、`audio_out`（音声出力）。

- ### `vcf.py` (Voltage Controlled Filter)
  - **役割**: 電圧制御フィルター。入力された音声信号の周波数成分を削ることで音色を変化させます。
  - **主なパラメータ**: `freq`（カットオフ周波数）、`q`（レゾナンス）。
  - **主な入出力**: `audio_in`（音声入力）、`freq_cv`（周波数制御）、`audio_out`（音声出力）。

- ### `lfo.py` (Low Frequency Oscillator)
  - **役割**: 低周波オシレーター。他のモジュールのパラメータ（VCOの周波数、VCFのカットオフなど）を周期的に変化させるための制御信号（CV）を生成します。
  - **主なパラメータ**: `freq`（周波数）、`waveform`（波形）、`amplitude`（振幅）。
  - **主な入出力**: `freq_cv`（周波数制御）、`cv_out`（制御信号出力）。

- ### `env.py` (Envelope Generator)
  - **役割**: エンベロープジェネレーター。ゲート信号をトリガーにして、時間的な変化の形状（ADSR）を持つ制御信号を生成します。主にVCAの音量制御に使用されます。
  - **主なパラメータ**: `attack`, `decay`, `sustain`, `release`。
  - **主な入出力**: `gate_in`（トリガー入力）、`cv_out`（制御信号出力）。

- ### `vca.py` (Voltage Controlled Amplifier)
  - **役割**: 電圧制御アンプ。入力された音声信号の音量を制御します。
  - **主なパラメータ**: `gain`（基本ゲイン）。
  - **主な入出力**: `audio_in`（音声入力）、`gain_cv`（ゲイン制御）、`audio_out`（音声出力）。

### 高度なモジュール

- ### `multiple.py` (Multiple/Signal Splitter)
  - **役割**: 信号分岐モジュール。1つの入力信号を複数の出力に分岐します。
  - **主なパラメータ**: `outputs`（出力数、デフォルト4）。
  - **主な入出力**: `input`（入力）、`output0`〜`outputN`（複数出力）。
  - **用途**: 同じ信号を複数のモジュールに送る、ステレオ効果、パラレル処理。

- ### `mixer.py` (Mixer)
  - **役割**: 信号ミキシングモジュール。複数の入力信号を重み付けして1つの出力に混合します。
  - **主なパラメータ**: `inputs`（入力数、デフォルト4）、`level0`〜`levelN`（各入力レベル）、`master_level`（マスターレベル）。
  - **主な入出力**: `input0`〜`inputN`（複数入力）、`output`（混合出力）。
  - **用途**: 和音生成、複数音源の混合、レベル調整。

- ### `cvmath.py` (CV Math)
  - **役割**: CV演算モジュール。2つのCV信号を数学的に演算します。
  - **主なパラメータ**: `operation`（演算タイプ: add, subtract, multiply, divide）、`scale`（スケール）、`offset`（オフセット）。
  - **主な入出力**: `input_a`, `input_b`（CV入力）、`output`（演算結果出力）。
  - **用途**: 複雑なCV制御、信号の組み合わせ、エンベロープシェイピング。

## 基本的な使い方

各モジュールは、`src/connection.py` の `ConnectionManager` を通じて接続することが推奨されます。

```python
from pyo import Server
from src.connection import ConnectionManager, SignalType
from src.modules.vco import VCO
from src.modules.vca import VCA

# 1. Pyoサーバーを起動
s = Server().boot().start()

# 2. ConnectionManagerとモジュールを作成
cm = ConnectionManager()
vco = VCO(name="my_osc")
vca = VCA(name="my_amp")

# 3. モジュールを登録して開始
cm.register_module("my_osc", vco)
cm.register_module("my_amp", vca)
vco.start()
vca.start()

# 4. モジュール間を接続
cm.connect("my_osc", "audio_out", "my_amp", "audio_in", SignalType.AUDIO)

# 5. VCAのprocessを呼び出して接続を反映
vca.process()

# 6. VCAから音声を出力
vca.out_to_channel(0)

# (適宜 time.sleep() などで待機)

# 7. 終了処理
s.stop()
s.shutdown()
```

## 🚨 重要な作法

### 1. モジュール接続後は必ず `process()` を呼ぶ

```python
# モジュールを接続した後は、受信側モジュールの process() を呼び出す
cm.connect("vco", "audio_out", "vcf", "audio_in", SignalType.AUDIO)
vcf.process()  # VCFに接続を反映

cm.connect("vcf", "audio_out", "vca", "audio_in", SignalType.AUDIO)
vca.process()  # VCAに接続を反映
```

### 2. パラメータ変更後は必ず `process()` を呼ぶ

```python
# パラメータを変更した後は、そのモジュールの process() を呼び出す
vcf.set_frequency(1000)
vcf.process()  # パラメータ変更を反映

vca.set_gain(0.8)
vca.process()  # パラメータ変更を反映
```

### 3. PyoObject CV制御への対応

特にVCAモジュールでは、ENVモジュールのPyoObject出力を適切に処理できます：

```python
# ENVモジュールのADSRエンベロープでVCAを制御
env = ENV(name="env1")
env.set_attack(0.05)
env.set_decay(0.3)
env.set_sustain(0.4)
env.set_release(1.5)
env.process()  # ADSRパラメータを反映

# ENVからVCAへのCV制御接続
cm.connect("env1", "cv_out", "vca1", "gain_cv", SignalType.CV)
vca.process()  # PyoObject CV制御を反映
```

詳細な使い方については、[`doc/MODULAR_GUIDE.md`](../../doc/MODULAR_GUIDE.md) を参照してください。
