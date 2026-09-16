# ممیزی امنیتی قراردادهای هوشمند بازارگاه (pre-mainnet)

> تاریخ: ۲۰۲۶-۰۹-۱۵ · محدوده: `contracts/src/{IdentitySBT, EscrowWithDispute, MarketplaceLiability, BrandLicense, PaymentSplitter}.sol` (solc 0.8.26 هدف، OZ 5.x) · روش: بازبینی خط‌به‌خط دستی + ۱۷ تست Hardhat سبز. **این ممیزی داخلی جایگزین ممیزی مستقل (Slither/Echidna + شرکت ثالث) نیست.**

## ۱. ماتریس کنترل دسترسی

| تابع | چه کسی | محافظت |
|---|---|---|
| IdentitySBT.authorizeMarketplace / revoke | فقط owner (پلتفرم) | Ownable |
| IdentitySBT.issueIdentity | فقط بازارچههای مجازشده | mapping check |
| Escrow.createOrder/markAsShipped/confirmDelivery/openDispute | خریدار/فروشنده/خریدار | بررسی msg.sender |
| Escrow.sellerRespond / marketplaceResolve | فروشنده / بازارچه سفارش + مهلت | stage+deadline |
| Escrow.platformArbitrate | فقط owner، فقط پس از انقضای مهلت بازارچه | onlyOwner + DeadlineNotPassed |
| Liability.useInsuranceFund / updateScore / suspend | فقط owner (پلتفرم) | onlyPlatform + nonReentrant |
| BrandLicense.issue/revoke | فقط owner | Ownable |
| Splitter.release | هر payee برای سهم خودش | nonReentrant + محاسبه due |

## ۲. یافتهها

| # | شدت | یافته | وضعیت |
|---|---|---|---|
| 1 | کم | `EscrowWithDispute.sellerRespondToDispute` در مسیر پذیرش بازپرداخت `nonReentrant` ندارد (call به EOA خریدار) | توصیه: افزودن modifier در نسخه بعد |
| 2 | کم | `PaymentSplitter.addPayee` پس از واریز وجه، سهم قبلیها را رقیق میکند | توصیه: قفل افزودن پس از اولین واریز |
| 3 | اطلاعاتی | گردگیری سهم در Splitter ممکن است چند wei گرد به آخرین payee بگذارد | استاندارد صنعت، قابل قبول |
| 4 | اطلاعاتی | `identityInfo` پس از revoke باقی میماند (حسابرسی) ولی ownerOf خطا میدهد | رفتار آگاهانه SBT |
| 5 | اطلاعاتی | جریمه بازارچه در `_penalizeMarketplace` ساکتاً نادیده گرفته میشود اگر صندوق کافی نباشد | رویداد emitted؛ قابل پایش |
| 6 | متوسط (فرایندی) | آدرس `platform` = ownerdeployer؛ برای mainnet باید Multisig (Gnosis Safe) شود | **لازم پیش از mainnet** |
| 7 | کم | deadlineها بر اساس block.timestamp — ریسک ماینرمانیپولیشن جزئی؛ در L2 عملاً ناچیز | قابل قبول |

## ۳. چکلیست پیش از mainnet

- [x] تست واحد ۱۷/۱۷ سبز (مسیرهای خوشحال + خطا + مهلتها)
- [ ] اجرای Slither/Aderyn روی ریپو + رفع هشدارهای متوسط به بالا
- [ ] Fuzz/Invariant (Echidna یا Foundry invariant) برای escrow: «جمع موجودی همیشه = سفارشهای در جریان»
- [ ] انتقال ownership به Multisig پس از استقرار
- [ ] استقرار روی Amoy + سوسایک آزمایشی + تأیید آدرسها در `.env`
- [ ] ممیزی مستقل ثالث (حداقل یک دور) پیش از انتقال وجه واقعی

## ۴. یادداشت استقرار تستنت

`hardhat.config.js` شبکه `amoy` (chainId 80002) اضافه شده است. برای استقرار واقعی:
1. یک کیف پول تست با فاست Amoy شارژ کنید و کلید خصوصی را در `contracts/.env` بگذارید (`PRIVATE_KEY=0x...`).
2. `npx hardhat run scripts/deploy.js --network amoy`
3. آدرسهای خروجی را در `.env` ریشه پروژه (کلیدهای `*_ADDRESS` بخش Bazargah smart contracts) ثبت کنید.
> در این اجرا، deploy.js روی شبکهٔ محلی hardhat با موفقیت اجرا و هر ۵ قرارداد مستقر شد (dry-run معتبر)؛ استقرار Amoy نیازمند کلید تأمینشده است.