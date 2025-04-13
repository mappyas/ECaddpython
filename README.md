# EC Shop

モダンなECサイトのプロトタイプ。Next.js + TypeScript + Python (Django + FastAPI) で構築。

## プロジェクト構成

### フロントエンド (Next.js + TypeScript)
- 顧客向けインターフェース
- 商品閲覧・購入機能
- カート機能
- ユーザー認証

### バックエンド (Python)
- Django: 管理画面
- FastAPI: REST API
- 商品管理
- 注文管理
- ユーザー管理

## セットアップ

1. リポジトリをクローン
```bash
git clone [リポジトリURL]
cd ec-shop
```

2. 仮想環境の作成と有効化
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 依存パッケージのインストール
```bash
pip install -r requirements.txt
```

4. 設定ファイルの作成
```bash
cp backend/ec_shop/settings.py.template backend/ec_shop/settings.py
```

5. 設定ファイルの編集
- `backend/ec_shop/settings.py`を開き、必要に応じて設定を変更
- 特に以下の設定を確認・変更：
  - `SECRET_KEY`
  - `DEBUG`
  - `ALLOWED_HOSTS`
  - `DATABASES`

6. データベースのマイグレーション
```bash
python manage.py migrate
```

7. 開発サーバーの起動
```bash
python manage.py runserver
```

## 環境変数

重要な設定は環境変数として管理することを推奨します。`.env`ファイルを作成し、以下のような設定を追加します：

```bash
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

## プロジェクト構造

```
ec-shop/
├── backend/
│   ├── ec_shop/
│   │   ├── settings.py      # 本番環境用設定
│   │   ├── settings.py.template  # テンプレート
│   │   └── ...
│   ├── users/
│   └── products/
└── frontend/
```

## 注意事項

- `settings.py`は機密情報を含むため、Gitの追跡対象から除外されています
- 新しい環境でセットアップする際は、`settings.py.template`をコピーして`settings.py`を作成してください
- 本番環境では必ず`DEBUG=False`に設定してください

## 開発環境
- Node.js 18+
- Python 3.8+
- PostgreSQL

## ライセンス
MIT 