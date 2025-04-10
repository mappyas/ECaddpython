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

### フロントエンド
```bash
cd frontend
npm install
npm run dev
```

### バックエンド
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## 開発環境
- Node.js 18+
- Python 3.8+
- PostgreSQL

## ライセンス
MIT 