# 🎛 制約付きランダム・モジュラーサウンドインスタレーション 制作手順書

## 🎯 プロジェクト概要

モジュラーシンセ風の音響構成を **制約付きランダム** に生成し、
**4ch出力**（内蔵 + USBオーディオIF）で再生するサウンドインスタレーションを Python で構築する。

-----

## 🧰 使用環境

  - **言語**: Python 3.8〜3.11
  - **ライブラリ**:
      - [`pyo`](https://www.google.com/search?q=%5Bhttps://ajaxsoundstudio.com/software/pyo/%5D\(https://ajaxsoundstudio.com/software/pyo/\))：音響合成向け
      - `numpy`, `sounddevice`：軽量テスト用
  - **プラットフォーム**: macOS
  - **出力構成**: 2ch → 4ch（macOSの「Aggregate Device」を利用）

-----

## ✅ ステップ別手順

### 🧩 ステップ0：環境準備

```bash
pip install numpy sounddevice pyo
```

1.  Audio MIDI設定.app で「Aggregate Device」を作成（内蔵+USB）
2.  Python からオーディオデバイスにアクセスできることを確認

-----

### 🔊 ステップ1：2ch音出力テスト

#### 方法A：sounddevice + numpy

```python
import numpy as np
import sounddevice as sd

fs = 44100
duration = 3
t = np.linspace(0, duration, int(fs * duration), endpoint=False)

left = 0.2 * np.sin(2 * np.pi * 440 * t)
right = 0.2 * np.sin(2 * np.pi * 660 * t)
stereo = np.stack([left, right], axis=1)

sd.play(stereo, samplerate=fs)
sd.wait()
```

#### 方法B：pyo

```python
from pyo import *

s = Server(nchnls=2).boot()
s.start()

Sine(freq=440, mul=0.2).out(chnl=0)
Sine(freq=660, mul=0.2).out(chnl=1)

s.gui(locals())
```

-----

### 🧱 ステップ2：モジュール構成の設計

#### モジュール例：

| モジュール | 説明                   |
| :--------- | :--------------------- |
| VCO        | 波形生成（Sine, Square, Saw） |
| VCF        | フィルター処理（ローパスなど） |
| LFO        | モジュレーション信号生成   |
| ENV        | エンベロープ（ADSR）   |
| VCA        | 音量制御               |

#### 制約ルール例：

  * 各パッチに最低1つのVCO、最大2つ
  * LFOは最大1つ、接続先はVCO.freqかVCF.freq
  * VCFは0〜1個、任意
  * VCAは出力直前に必須
  * ENVは任意

-----

### 🔁 ステップ3：制約付きランダム構成生成

  * 各モジュールの接続先を制約に従ってランダムに決定
  * 1チャンネルから開始し、4チャンネルまで展開可能
  * 出力は `.out(chnl=N)` で各チャンネルへ

-----

### 🕰 ステップ4：時間的変化

  * 一定時間ごとに再構成
  * 例：
      * 毎30秒に1モジュールを差し替え
      * 毎5分に全構成をリセット

-----

### 🤖 ステップ5（発展）：LLMによる構成生成

  * 制約やテーマを自然言語で指定して、LLMから構成を取得
  * 構成テキストをパースしてPythonオブジェクトに変換
  * インタラクティブ／ストーリー性のある音響環境を構築可能

-----

### 🗂 ディレクトリ構成案

```
modular_project/
├── modules/           # モジュールクラス（VCO, VCF, etc）
├── generator.py       # 制約付きランダム構成生成
├── main.py            # 実行スクリプト
├── llm_interface.py   # LLMとの連携（発展）
└── README.md
```

-----

### 📌 優先実装タスク

| 優先度 | 内容                                  |
| :----- | :------------------------------------ |
| ★      | 2ch音出力の確認（音が出るか試す）       |
| ★      | モジュールクラスの作成（VCO, LFO, VCFなど） |
| ★      | 制約付きランダム構成の生成（1chベース）   |
| ☆      | 4chへの拡張（Aggregate Device利用）   |
| ☆      | LLMを活用した構成案の生成（テキスト→パッチ） |

-----

### 📎 備考

  * `sounddevice.query_devices()` でデバイスIDを確認
  * pyoでは `Server(nchnls=4)` でチャンネル数指定
  * LLM活用時はプロンプト例の管理や文解析の設計が鍵になる

