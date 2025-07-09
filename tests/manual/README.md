# 手動テストスイート

このディレクトリには、モジュラーシンセサイザーの手動テストファイルが含まれています。

## テストファイル

### test_utils.py
テスト用の共通ユーティリティモジュール：
- `audio_server()`: Pyoサーバーのコンテキストマネージャー
- `TestModuleFactory`: 標準的なモジュールを作成するファクトリー
- `TestRunner`: テスト実行とモジュール管理のヘルパー

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

## 実行方法

各テストファイルを直接実行：

```bash
# VCO->VCA接続テスト
python tests/manual/test_vco_vca_connection.py

# 高度なモジュールテスト
python tests/manual/test_vcf_lfo_env.py
```

## 注意事項

- テストは手動実行用で、音声を実際に再生します
- 各テストの間でユーザーの入力待機があります
- 音量に注意してください（初期設定は控えめですが、スピーカー・ヘッドフォンの音量を確認してください）
- pyoサーバーは自動的に開始・停止されます

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