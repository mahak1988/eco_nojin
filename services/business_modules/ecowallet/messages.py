"""Educational Messages for ECO Wallet.

CRITICAL: All messages must be POSITIVE and EMPOWERING.
NO warnings, NO fear-inducing language, NO technical jargon.
"""


class EcoMessages:
    EARNING = {
        "tree_planting": {
            "en": "Congratulations! You earned {amount} ECO for planting trees!",
            "fa": "تبریک! شما {amount} امتیاز سبز برای کاشت درخت گرفتید!",
        },
        "training_completion": {
            "en": "Well done! You earned {amount} ECO for training!",
            "fa": "آفرین! شما {amount} امتیاز سبز برای آموزش گرفتید!",
        },
        "market_sale": {
            "en": "Great! You earned {amount} ECO from market sales!",
            "fa": "عالی! شما {amount} امتیاز سبز از فروش بازار گرفتید!",
        },
        "carbon_verification": {
            "en": "Excellent! Satellite verified your carbon work. +{amount} ECO!",
            "fa": "فوق‌العاده! ماهواره کار کربن شما را تأیید کرد. +{amount} امتیاز!",
        },
        "referral": {
            "en": "Thank you for referring! +{amount} ECO!",
            "fa": "از معرفی شما متشکریم! +{amount} امتیاز!",
        },
        "regenerative_farming": {
            "en": "Amazing! +{amount} ECO for regenerative farming!",
            "fa": "شگفت‌انگیز! +{amount} امتیاز برای کشاورزی احیاکننده!",
        },
        "soil_improvement": {
            "en": "Great job! +{amount} ECO for improving soil!",
            "fa": "عالی بود! +{amount} امتیاز برای بهبود خاک!",
        },
        "water_conservation": {
            "en": "Well done! +{amount} ECO for water conservation!",
            "fa": "آفرین! +{amount} امتیاز برای صرفه‌جویی در آب!",
        },
    }

    REDEMPTION = {
        "seed_purchase": {
            "en": "Seeds purchased! {remaining} ECO remaining.",
            "fa": "بذر خریداری شد! {remaining} امتیاز باقی مانده.",
        },
        "consultation": {
            "en": "Consultation booked! {remaining} ECO remaining.",
            "fa": "مشاوره رزرو شد! {remaining} امتیاز باقی مانده.",
        },
        "insurance_discount": {
            "en": "Insurance discount applied! {remaining} ECO remaining.",
            "fa": "تخفیف بیمه اعمال شد! {remaining} امتیاز باقی مانده.",
        },
        "market_access": {
            "en": "Market access unlocked! {remaining} ECO remaining.",
            "fa": "دسترسی بازار فعال شد! {remaining} امتیاز باقی مانده.",
        },
        "training_course": {
            "en": "Training course unlocked! {remaining} ECO remaining.",
            "fa": "دوره آموزشی فعال شد! {remaining} امتیاز باقی مانده.",
        },
        "equipment_rental": {
            "en": "Equipment booked! {remaining} ECO remaining.",
            "fa": "تجهیزات رزرو شد! {remaining} امتیاز باقی مانده.",
        },
        "veterinary_service": {
            "en": "Vet consultation booked! {remaining} ECO remaining.",
            "fa": "مشاوره دامپزشکی رزرو شد! {remaining} امتیاز باقی مانده.",
        },
    }

    BALANCE = {
        "en": "Your balance: {balance} ECO (worth {irr_value:,} IRR in services)",
        "fa": "موجودی شما: {balance} امتیاز سبز (معادل {irr_value:,} تومان خدمات)",
    }

    WELCOME = {
        "en": "Welcome! Your ECO wallet is ready. Start earning by planting trees and completing training!",
        "fa": "خوش آمدید! کیف پول امتیاز سبز شما آماده است. با کاشت درخت و آموزش شروع کنید!",
    }

    LOW_BALANCE = {
        "en": "You have {balance} ECO remaining. Plant more trees to earn more!",
        "fa": "{balance} امتیاز باقی مانده. درخت بیشتری بکارید تا امتیاز بیشتری بگیرید!",
    }

    @classmethod
    def earning(cls, category, amount, lang="en"):
        template = cls.EARNING.get(category, {}).get(
            lang, cls.EARNING.get(category, {}).get("en", "")
        )
        return template.format(amount=amount)

    @classmethod
    def redemption(cls, category, remaining, lang="en"):
        template = cls.REDEMPTION.get(category, {}).get(
            lang, cls.REDEMPTION.get(category, {}).get("en", "")
        )
        return template.format(remaining=remaining)

    @classmethod
    def balance(cls, balance, irr_value, lang="en"):
        template = cls.BALANCE.get(lang, cls.BALANCE["en"])
        return template.format(balance=balance, irr_value=int(irr_value))

    @classmethod
    def welcome(cls, lang="en"):
        return cls.WELCOME.get(lang, cls.WELCOME["en"])
