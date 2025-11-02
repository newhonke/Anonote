# Anonote

シンプルなFlask製BBS（掲示板）アプリケーション

## 概要

- ユーザー投稿機能（匿名投稿可）
- 投稿の自動全削除（1000件超過時）
- 管理者ページ（ログイン制）
- 投稿の削除（管理者のみ）
- IPアドレスによる投稿ブロック（管理者のみ）
- パスワードハッシュ化保存
- SQLAlchemyによるORM
- Flask-Loginによる認証

## 生い立ち


このアプリケーションは **Flask の学習の一環** として作成しました。  

学習の目的としては、以下のような点があります。  

- Python と Flask の基本的な使い方を身につける  
- データベース（SQLAlchemy）やユーザー認証（Flask-Login）の実装に慣れる  
- Webアプリに最低限必要な「投稿」「認証」「管理」の流れを一通り体験する  

---

また、元々私が **Misskey** という分散型ミニブログ用オープンソースソフトウェアに興味を持ち、 プログラミングを始めたという経緯もあります。  

そのため、この掲示板アプリには **Misskeyっぽい要素** がちょくちょくあるかもしれません。  
ぜひ探してみてください！

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/newhonke/flask_bbs.git
cd flask_bbs
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```
> `requirements.txt`がない場合は下記を参考にインストールしてください
> 
> ```
> pip install flask flask_sqlalchemy flask_login werkzeug
> ```

### 3. SECRET_KEYの設定（本番環境推奨）

PowerShellの場合（Windows）:
```powershell
setx SECRET_KEY "安全なランダム文字列"
```

Linux/Macの場合:
```bash
export SECRET_KEY="安全なランダム文字列"
```

> ローカル開発ではプロジェクト直下の `.env` ファイルに `SECRET_KEY` や `ADMIN_USERNAME` を記述しても読み込まれます（`python-dotenv` を使用）。本番では `.env` ではなく実際の環境変数を設定してください。

### 4. 管理者アカウントの設定

アプリケーションは **環境変数 `ADMIN_USERNAME` と `ADMIN_PASSWORD`** が設定されている場合に限り、初回起動時に管理者アカウントを自動作成します（ユーザー名は10文字以内）。

PowerShellの場合（Windows）:
```powershell
setx ADMIN_USERNAME "your-admin"
setx ADMIN_PASSWORD "very-strong-password"
```

Linux/Macの場合:
```bash
export ADMIN_USERNAME="your-admin"
export ADMIN_PASSWORD="very-strong-password"
```

> `ADMIN_PASSWORD` は平文のままプロセス環境に残るため、使用後は必ずシェル履歴から削除してください。

すでに管理者アカウントが存在する場合は再作成されません。別のアカウントを追加したい場合はアプリケーションにログインし、機能追加などで対応してください。

### 5. アプリケーションの起動

```bash
python app.py
```
- http://127.0.0.1:5000/ を開いて無事に起動できているか確認しましょう。

## 管理者機能

- `/login` で管理者ログイン
- `/admin` で投稿一覧・削除・IPブロックが可能

## データベース

- SQLite（`test.db`）を利用しています

## 注意事項

- 本番用デプロイを想定する場合は必ず `SECRET_KEY`・`ADMIN_USERNAME`・`ADMIN_PASSWORD` を安全に管理してください。
- ログアウトや管理操作はすべて POST + CSRF トークンで保護されています。テンプレートを変更する際はトークン入力を削除しないよう注意してください。
- 逆プロキシ配下で `X-Forwarded-For` を信頼したい場合は `TRUST_X_FORWARDED_FOR=true` を環境変数に設定してください（デフォルトは信頼しません）。
- 開発時のみ `FLASK_DEBUG=1` を設定すると Flask デバッガが有効になります。**本番でのデバッグモードは厳禁です。**
- IPブロックや削除機能は管理者のみ利用できます。
