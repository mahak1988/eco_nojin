# مستندات API ماژول‌های جدید

## Marketplace

- `GET /api/v1/marketplace/health` - بررسی سلامت
- `GET /api/v1/marketplace/info` - اطلاعات سرویس
- `POST /api/v1/marketplace/products` - ثبت محصول
- `POST /api/v1/marketplace/orders` - ایجاد سفارش

## Tourism

- `GET /api/v1/tourism/health` - بررسی سلامت
- `GET /api/v1/tourism/info` - اطلاعات سرویس

## Landscape

- `GET /api/v1/landscape/health` - بررسی سلامت
- `GET /api/v1/landscape/info` - اطلاعات سرویس

## گام‌های بعدی

1. `alembic upgrade head`
2. `pytest services/*/tests/ -v`
3. مطالعه `NEW_MODULES_README.md`
