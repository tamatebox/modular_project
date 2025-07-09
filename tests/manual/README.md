# 手動テストスイート

このディレクトリには、モジュラーシンセサイザーの手動テストファイルが含まれています。

## テストファイル

### test_utils.py
テスト用の共通ユーティリティモジュール：
- `audio_server()`: Pyoサーバーのコンテキストマネージャー
- `TestModuleFactory`: 標準的なモジュールを作成するファクトリー
- `TestRunner`: テスト実行とモジュール管理のヘルパー

### 基本モジュールテスト

### test_vco_vca_connection.py
VCO->VCA接続の基本テスト：
- 基本的なVCO->VCA接続テスト
- VCOの各波形テスト (sine, saw, square, triangle, noise)
- VCAゲイン制御テスト
- マルチチャンネル出力テスト

### test_vcf_lfo_env.py
高度なモジュールテスト：
- VCF手動テスト (カットオフ・Q値変更)
- LFO->VCF (ワウ効果)
- LFO->VCO (ビブラート効果)
- ENV->VCA (ADSRエンベロープ)
- 複雑なパッチテスト (全モジュール組み合わせ)

### 高度なモジュールテスト

### test_multiple.py
Multiple（分岐）モジュールテスト：
- 基本的な分岐テスト: VCO -> Multiple -> 2つのVCF
- CV分岐テスト: LFO -> Multiple -> 2つのVCO
- ファンアウトテスト: 1つのVCO -> Multiple -> 4つの異なる処理

### test_mixer.py
Mixer（ミキシング）モジュールテスト：
- 基本的な和音テスト: 3つのVCO -> Mixer -> VCA
- 和音進行テスト: 動的に和音を変更
- リズミカルなパターンテスト: 複数の音源をリズミカルに混合
- ステレオスプレッドテスト: 左右で異なるミキシング

### test_cvmath.py
CVMath（CV演算）モジュールテスト：
- 基本的な演算テスト: 四則演算の確認
- 複雑なCV制御テスト: LFO + エンベロープでVCO制御
- フィルター制御テスト: 複数のCV信号でVCFを制御
- デュアルVCO制御テスト: 1つのCV信号で2つのVCOを異なる方法で制御
- エンベロープシェイピングテスト: エンベロープを数学的に変形

### test_advanced_modules.py
高度なモジュール統合テスト：
- 複雑なステレオパッチテスト: Multiple + Mixer + CVMath統合
- マルチバンドフィルターシステムテスト: 周波数帯域別処理
- 4つのオシレーターアンサンブルテスト: 複雑な音響合成
- リズミカルなCVパターンテスト: 複数CV信号の組み合わせ

## 実行方法

各テストファイルを直接実行：

```bash
# 基本モジュールテスト
python tests/manual/test_vco_vca_connection.py
python tests/manual/test_vcf_lfo_env.py

# 高度なモジュールテスト
python tests/manual/test_multiple.py
python tests/manual/test_mixer.py
python tests/manual/test_cvmath.py
python tests/manual/test_advanced_modules.py
```

## 注意事項

- **テストは手動実行用で、音声を実際に再生します**
- **各テストの間でユーザーの入力待機があります**
- **音量に注意してください**（初期設定は控えめですが、スピーカー・ヘッドフォンの音量を確認してください）
- **pyoサーバーは自動的に開始・停止されます**
- **テストの実行はユーザーが行う必要があります**（音声の確認が必要なため）

## 重要：テストの実行について

これらのテストは**実際に音声を再生**するため、以下の点にご注意ください：

1. **必ずユーザーが実行**してください（AIアシスタントは音声を聞くことができません）
2. **適切な音量設定**を確認してから実行してください
3. **ヘッドフォンまたはスピーカー**が正しく接続されていることを確認してください
4. **macOSの場合**：システム環境設定でマイク・オーディオのアクセス許可を確認してください
5. **テストが成功**したかどうかは、実際に音が出ているかで判断してください

## 開発時の使用方法

新しいモジュールを追加した場合：

1. `test_utils.py`の`TestModuleFactory`に新しいモジュール作成メソッドを追加
2. 適切なテストファイルに新しいテスト関数を追加
3. `main()`関数のテストリストに追加

テストの構造：
```python
def test_something():
    \"\"\"テストの説明\"\"\"
    with audio_server() as s:
        runner = TestRunner("Test Name")
        
        # モジュール作成
        module = runner.add_module("name", TestModuleFactory.create_module())
        
        # 接続
        runner.connect("source", "out", "target", "in")
        runner.process_chain("target")
        
        # 実行
        runner.output_audio("target", 0)
        runner.play_for(3)
        
        runner.cleanup()
        return True
```