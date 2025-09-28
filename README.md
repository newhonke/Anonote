# flask_bbs

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

### 4. 管理者アカウントの設定

PowerShellの場合（Windows）:
```powershell
notepad app.py
```
> Ctrl + S を押してからィンドウ右上の ×ボタン をクリックして終了

Linux/Macの場合:
```bash
nano app.py
```
> Ctrl + X を押してから Y を押して Enter キーを押して終了

```python
if not User.query.filter_by(username="admin").first():
        # 管理者を作成
        admin = User(
            username = "admin", #管理者アカウントのユーザーネームに変更
            password = generate_password_hash("password"), #管理者アカウントのパスワードに変更
            is_admin = True
        )
        db.session.add(admin)
        db.session.commit()
        print("管理者アカウントを作成しました")
    else:
        print("管理者アカウントは既に存在します")
```

- デフォルトのままにするとアプリケーション起動時に管理者アカウント（ユーザー名: `admin`, パスワード: `password`）が作成されます。  
**必ず自分しかしらないユーザーネーム、パスワードに変更してください！**

### 4. アプリケーションの起動

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

- 本番用デプロイを想定する場合は必ず`SECRET_KEY`と管理者アカウント情報を変更してください。
- IPブロックや削除機能は管理者のみ利用できます。