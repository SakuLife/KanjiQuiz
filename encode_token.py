#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
token.pickleをBase64エンコードしてGitHub Secrets用の値を生成するスクリプト
"""
import base64
import os
from pathlib import Path

def encode_token_pickle():
    """token.pickleをBase64エンコードして表示"""
    # スクリプトのディレクトリを取得
    script_dir = Path(__file__).parent
    token_file = script_dir / "token.pickle"

    if not token_file.exists():
        print(f"❌ エラー: {token_file} が見つかりません")
        print(f"   ファイルパス: {token_file.absolute()}")
        return

    try:
        # ファイルを読み込んでBase64エンコード
        with open(token_file, "rb") as f:
            token_data = f.read()
            encoded = base64.b64encode(token_data).decode('utf-8')

        print("=" * 70)
        print("✅ token.pickleのBase64エンコード完了")
        print("=" * 70)
        print("\n以下の文字列をコピーして、GitHub Secretsの YOUTUBE_TOKEN_PICKLE に貼り付けてください:\n")
        print("-" * 70)
        print(encoded)
        print("-" * 70)
        print(f"\n📊 ファイルサイズ: {len(token_data)} bytes")
        print(f"📊 エンコード後サイズ: {len(encoded)} 文字")
        print("\n💡 ヒント: 文字列全体をコピーしてください（改行を含まない1つの長い文字列です）")

    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    encode_token_pickle()
