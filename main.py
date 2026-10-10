

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.types import FSInputFile

# ========================= CONFIG =========================
BOT_TOKEN = os.getenv("BOT_TOKEN", " ")
IMAGES_DIR = Path(__file__).parent / "images"

# Map of region -> list of staff chat IDs (edit these!)
STAFF_BY_REGION: Dict[str, List[int]] = {
    # RU labels (they are used internally; UZ shown by translation)
    "Ташкент город": [888936051, 5579006763],
    "Ташкент": [888936051],
    "Андижан": [888936051],
    "Наманган": [888936051],
    "Фергана": [888936051],
    "Сырдарья": [888936051],
    "Джиззах": [888936051],
    "Самарканд": [888936051],
    "Бухара": [888936051],
    "Кашкадарья": [888936051],
    "Сурхандарья": [888936051],
    "Наваи": [888936051],
    "Хорезм": [888936051],
}

# Contacts (edit freely)
CONTACTS_RU = (
    "Телефон: +998 (71) 230-70-00 "
    "Email: support@seventech.uz"
)
CONTACTS_UZ = (
    "Telefon: +998 (71) 230-70-00 "
    "Email: support@seventech.uz"
)

# Product categories and links (keys are internal canonical names)
PRODUCT_LINKS = {
    "Кондиционеры": "https://seventech.uz/market?category=kondicionery",
    "Холодильники": "https://seventech.uz/market?category=xolodilniki",
    "Телевизоры": "https://seventech.uz/market?category=televizory",
    "Диспенсеры для воды": "https://seventech.uz/market?category=televizory",  # as requested
    "Мониторы": "https://seventech.uz/market?category=monitory",
    "Пылесосы": "https://seventech.uz/market?category=pylesosy",
    "Стиральные машины": "https://seventech.uz/market?category=ctiralnye-masiny",
    "Варочные панели": "https://seventech.uz/market?category=varocnye-paneli",
    "Духовые шкафы": "https://seventech.uz/market?category=duxovye-skafy",
    "Сушильные машины": "https://seventech.uz/market?category=susilnye-masiny",
    "Вытяжки": "https://seventech.uz/market?category=vytiazki",
    "Посудомоечные машины": "https://seventech.uz/market?category=posudomoecnye-masiny",
    "Микроволновые печи": "https://seventech.uz/market?category=mikrovolnovye-peci",
}

# Appliances list reused in Service flow
APPLIANCES = list(PRODUCT_LINKS.keys())

# Regions list reused in Service flow (internal RU labels)
REGIONS_RU = list(STAFF_BY_REGION.keys())

# ========================= I18N =========================
RU = {
    "lang_name": "Русский",
    "choose_language": "Выберите язык:",
    "brand_caption": (
        "7tech — бытовая техника нового уровня. Надёжность, качество и стиль для вашего дома. "
        "Мы заботимся о каждом клиенте. 😊"
    ),
    "menu_products": "Продукции",
    "menu_service": "Сервис",
    "menu_contacts": "Контакты",
    "menu_about": "О нас",
    "menu_back": "⬅️ Назад",
    "about_text": "Мы 7tech. Продаём самые лучшие и качественные бытовые техники ✨",
    "contacts_text": CONTACTS_RU,
    "products_title": "Выберите категорию продукции:",
    "service_warranty_caption": "Гарантийные условия. Пожалуйста, ознакомьтесь и подтвердите.",
    "agree": "Я соглашаюсь",
    "ask_appliance": "С какой техникой вам нужен сервис?",
    "ask_region": "Выберите ваш регион:",
    "ask_problem": "Опишите вашу проблему:",
    "ask_phone": "Укажите ваш номер телефона (введите текстом):",
    "ask_address": "Уточните ваш точный адрес:",
    "ticket_submitted": (
        "Спасибо! Ваша заявка передана сотрудникам, она будет рассмотрена в течение 5 рабочих дней. "
        "С вами свяжутся. 📩"
    ),
    "invalid_phone": "Похоже, номер некорректен. Введите, пожалуйста, снова (пример: +998901234567):",
    "products_sent": "Откройте ссылку на выбранную категорию:",
}

UZ = {
    "lang_name": "Oʻzbekcha",
    "choose_language": "Tilni tanlang:",
    "brand_caption": (
        "7tech — zamonaviy maishiy texnika. Ishonchlilik, sifat va uslub sizning uyingiz uchun. "
        "Har bir mijoz biz uchun muhim. 😊"
    ),
    "menu_products": "Mahsulotlar",
    "menu_service": "Servis",
    "menu_contacts": "Aloqa",
    "menu_about": "Biz haqimizda",
    "menu_back": "⬅️ Ortga",
    "about_text": "Biz 7tech. Eng zoʻr va sifatli maishiy texnikalarni sotamiz ✨",
    "contacts_text": CONTACTS_UZ,
    "products_title": "Mahsulot turini tanlang:",
    "service_warranty_caption": "Kafolat shartlari. Iltimos, tanishib chiqing va tasdiqlang.",
    "agree": "Roziman",
    "ask_appliance": "Qaysi texnika bo‘yicha servis kerak?",
    "ask_region": "Hududingizni tanlang:",
    "ask_problem": "Muammoni qisqacha yozing:",
    "ask_phone": "Telefon raqamingizni kiriting (matn bilan):",
    "ask_address": "Aniq manzilingizni yozing:",
    "ticket_submitted": (
        "Rahmat! So‘rovingiz xodimlarga yuborildi. 5 ish kuni ichida ko‘rib chiqiladi. "
        "Siz bilan bog‘lanishadi. 📩"
    ),
    "invalid_phone": "Raqam noto‘g‘ri ko‘rinadi. Iltimos, qayta kiriting (namuna: +998901234567):",
    "products_sent": "Tanlangan bo‘lim uchun havola:",
}

I18N = {"ru": RU, "uz": UZ}

# Translations for product and region visible labels in UZ
TRANSLATE_LABELS_UZ = {
    # Products
    "Продукции": "Mahsulotlar",
    "Сервис": "Servis",
    "Контакты": "Aloqa",
    "О нас": "Biz haqimizda",
    "⬅️ Назад": "⬅️ Ortga",
    # Appliances
    "Кондиционеры": "Konditsionerlar",
    "Холодильники": "Muzlatkichlar",
    "Телевизоры": "Televizorlar",
    "Диспенсеры для воды": "Suv dispenserlari",
    "Мониторы": "Monitorlar",
    "Пылесосы": "Changyutgichlar",
    "Стиральные машины": "Kir yuvish mashinalari",
    "Варочные панели": "Pishirish panellari",
    "Духовые шкафы": "Duxovkalar",
    "Сушильные машины": "Quritish mashinalari",
    "Вытяжки": "Moy tutgichlar",
    "Посудомоечные машины": "Idish yuvish mashinalari",
    "Микроволновые печи": "Mikroto‘lqinli pechlar",
    # Regions
    "Ташкент город": "Toshkent shahri",
    "Ташкентская область": "Toshkent viloyati",
    "Андижан": "Andijon",
    "Наманган": "Namangan",
    "Фергана": "Farg‘ona",
    "Сырдарья": "Sirdaryo",
    "Джиззах": "Jizzax",
    "Самарканд": "Samarqand",
    "Бухара": "Buxoro",
    "Кашкадарья": "Qashqadaryo",
    "Сурхандарья": "Surxondaryo",
    "Наваи": "Navoiy",
    "Хорезм": "Xorazm",
}

# Helper: display label for current language
def label(lang: str, ru_label: str) -> str:
    if lang == "uz":
        return TRANSLATE_LABELS_UZ.get(ru_label, ru_label)
    return ru_label

# ========================= STATES =========================
class ServiceForm(StatesGroup):
    waiting_agree = State()
    waiting_appliance = State()
    waiting_region = State()
    waiting_problem = State()
    waiting_phone = State()
    waiting_address = State()
    submitted = State()

# ========================= UTIL =========================
user_lang: Dict[int, str] = {}  # user_id -> 'ru'|'uz'


def t(user_id: int, key: str) -> str:
    lang = user_lang.get(user_id, "ru")
    return I18N[lang][key]


def main_menu_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=I18N[lang]["menu_products"]),
                KeyboardButton(text=I18N[lang]["menu_service"]),
            ],
            [
                KeyboardButton(text=I18N[lang]["menu_contacts"]),
                KeyboardButton(text=I18N[lang]["menu_about"]),
            ],
            [KeyboardButton(text=I18N[lang]["menu_back"])],
        ],
        resize_keyboard=True,
        input_field_placeholder=None,
        is_persistent=True,
    )


def language_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Русский"), KeyboardButton(text="Oʻzbekcha")]],
        resize_keyboard=True,
        is_persistent=True,
    )


def appliances_kb(lang: str) -> ReplyKeyboardMarkup:
    rows = []
    row: List[KeyboardButton] = []
    for idx, item in enumerate(APPLIANCES, start=1):
        row.append(KeyboardButton(text=label(lang, item)))
        if idx % 2 == 0:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton(text=I18N[lang]["menu_back"])])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def regions_kb(lang: str) -> ReplyKeyboardMarkup:
    rows = []
    row: List[KeyboardButton] = []
    for idx, reg in enumerate(REGIONS_RU, start=1):
        row.append(KeyboardButton(text=label(lang, reg)))
        if idx % 2 == 0:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([KeyboardButton(text=I18N[lang]["menu_back"])])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def products_inline_kb(lang: str) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for idx, name in enumerate(APPLIANCES, start=1):
        row.append(InlineKeyboardButton(text=label(lang, name), callback_data=f"prod:{name}"))
        if idx % 2 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    # Inline back to just delete message (user can use ReplyKeyboard Back too)
    buttons.append([InlineKeyboardButton(text=I18N[lang]["menu_back"], callback_data="prod_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def warranty_inline_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t(user_id, "agree"), callback_data="agree")]]
    )


# ========================= ROUTER =========================
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=language_kb())


@router.message(F.text.in_({"Русский", "Oʻzbekcha"}))
async def set_language(message: Message, state: FSMContext):
    lang = "ru" if message.text == "Русский" else "uz"
    user_lang[message.from_user.id] = lang

    # Send brand image + text
    img_name = "brand_ru.jpg" if lang == "ru" else "brand_uz.jpg"
    img_path = IMAGES_DIR / img_name
    caption = I18N[lang]["brand_caption"]

    if img_path.exists():
        try:
            await message.answer_photo(photo=FSInputFile(str(img_path)), caption=caption)
        except Exception as e:
            logging.exception("Failed to send brand image: %s", e)
            await message.answer(caption)
    else:
        await message.answer(caption)

    # Show main menu
    await message.answer("⁣", reply_markup=main_menu_kb(lang))  # invisible char to push keyboard


@router.message(F.text)
async def main_handler(message: Message, state: FSMContext):
    uid = message.from_user.id
    lang = user_lang.get(uid, "ru")
    text = message.text

    # Map Back
    if text == I18N[lang]["menu_back"]:
        await state.clear()
        await message.answer(t(uid, "choose_language"), reply_markup=language_kb())
        return

    # Main menu entries
    if text in (I18N[lang]["menu_products"],):
        # Show inline keyboard with a non-empty text to satisfy Telegram API
        await message.answer(t(uid, "products_title"), reply_markup=products_inline_kb(lang))
        return

    if text in (I18N[lang]["menu_contacts"],):
        await message.answer(t(uid, "contacts_text"), reply_markup=main_menu_kb(lang))
        return

    if text in (I18N[lang]["menu_about"],):
        await message.answer(t(uid, "about_text"), reply_markup=main_menu_kb(lang))
        return

    if text in (I18N[lang]["menu_service"],):
        await start_service_flow(message, state)
        return

    # During service flow, delegate to states
    current_state = await state.get_state()
    if current_state and current_state.startswith(ServiceForm.__name__):
        await service_flow_handler(message, state)
        return

    # Unknown input → remind menu
    await message.answer(t(uid, "choose_language"), reply_markup=language_kb())


@router.callback_query(F.data.startswith("prod:"))
async def product_click(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = user_lang.get(uid, "ru")
    name_ru = callback.data.split(":", 1)[1]
    link = PRODUCT_LINKS.get(name_ru)
    if link:
        await callback.answer()
        await callback.message.answer(f"{t(uid, 'products_sent')} {link}", reply_markup=main_menu_kb(lang))
    else:
        await callback.answer("Not found", show_alert=True)


@router.callback_query(F.data == "prod_back")
async def product_back(callback: CallbackQuery):
    await callback.answer()
    uid = callback.from_user.id
    lang = user_lang.get(uid, "ru")
    await callback.message.delete()
    await callback.message.answer("⁣", reply_markup=main_menu_kb(lang))


# ========================= SERVICE FLOW =========================
async def start_service_flow(message: Message, state: FSMContext):
    uid = message.from_user.id
    lang = user_lang.get(uid, "ru")

    # Send warranty image + agree button
    img_name = "warranty_ru.jpg" if lang == "ru" else "warranty_uz.jpg"
    img_path = IMAGES_DIR / img_name
    caption = t(uid, "service_warranty_caption")

    if img_path.exists():
        try:
            await message.answer_photo(photo=FSInputFile(str(img_path)), caption=caption, reply_markup=warranty_inline_kb(uid))
        except Exception as e:
            logging.exception("Failed to send warranty: %s", e)
            await message.answer(caption, reply_markup=warranty_inline_kb(uid))
    else:
        await message.answer(caption, reply_markup=warranty_inline_kb(uid))

    await state.set_state(ServiceForm.waiting_agree)


@router.callback_query(F.data == "agree")
async def agreed(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    lang = user_lang.get(uid, "ru")

    await callback.message.answer(t(uid, "ask_appliance"), reply_markup=appliances_kb(lang))
    await state.set_state(ServiceForm.waiting_appliance)


async def service_flow_handler(message: Message, state: FSMContext):
    uid = message.from_user.id
    lang = user_lang.get(uid, "ru")
    data = await state.get_data()
    current = await state.get_state()

    back = I18N[lang]["menu_back"]

    # waiting_appliance
    if current == ServiceForm.waiting_appliance.state:
        if message.text == back:
            await state.clear()
            await message.answer("⁣", reply_markup=main_menu_kb(lang))
            return
        # Normalize to RU internal name
        choice_ru = None
        for ru_name in APPLIANCES:
            if message.text in {ru_name, label(lang, ru_name)}:
                choice_ru = ru_name
                break
        if not choice_ru:
            await message.answer(t(uid, "ask_appliance"))
            return
        await state.update_data(appliance=choice_ru)
        await message.answer(t(uid, "ask_region"), reply_markup=regions_kb(lang))
        await state.set_state(ServiceForm.waiting_region)
        return

    # waiting_region
    if current == ServiceForm.waiting_region.state:
        if message.text == back:
            await message.answer(t(uid, "ask_appliance"), reply_markup=appliances_kb(lang))
            await state.set_state(ServiceForm.waiting_appliance)
            return
        # Normalize to RU internal region label
        region_ru = None
        for ru_reg in REGIONS_RU:
            if message.text in {ru_reg, label(lang, ru_reg)}:
                region_ru = ru_reg
                break
        if not region_ru:
            await message.answer(t(uid, "ask_region"))
            return
        await state.update_data(region=region_ru)
        await message.answer(t(uid, "ask_problem"), reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=back)]], resize_keyboard=True))
        await state.set_state(ServiceForm.waiting_problem)
        return

    # waiting_problem
    if current == ServiceForm.waiting_problem.state:
        if message.text == back:
            await message.answer(t(uid, "ask_region"), reply_markup=regions_kb(lang))
            await state.set_state(ServiceForm.waiting_region)
            return
        await state.update_data(problem=message.text)
        await message.answer(t(uid, "ask_phone"), reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=back)]], resize_keyboard=True))
        await state.set_state(ServiceForm.waiting_phone)
        return

    # waiting_phone
    if current == ServiceForm.waiting_phone.state:
        if message.text == back:
            await message.answer(t(uid, "ask_problem"), reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=back)]], resize_keyboard=True))
            await state.set_state(ServiceForm.waiting_problem)
            return
        phone = message.text.strip()
        if not is_valid_phone(phone):
            await message.answer(t(uid, "invalid_phone"))
            return
        await state.update_data(phone=phone)
        await message.answer(t(uid, "ask_address"), reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=back)]], resize_keyboard=True))
        await state.set_state(ServiceForm.waiting_address)
        return

    # waiting_address
    if current == ServiceForm.waiting_address.state:
        if message.text == back:
            await message.answer(t(uid, "ask_phone"), reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=back)]], resize_keyboard=True))
            await state.set_state(ServiceForm.waiting_phone)
            return
        await state.update_data(address=message.text)
        await submit_ticket(message, state)
        return


def is_valid_phone(s: str) -> bool:
    # very light check: must contain at least 9 digits; accepts + and spaces/dashes/() but we keep as-is
    digits = [ch for ch in s if ch.isdigit()]
    return len(digits) >= 9


async def submit_ticket(message: Message, state: FSMContext):
    uid = message.from_user.id
    lang = user_lang.get(uid, "ru")
    data = await state.get_data()

    # Guard against double submit
    if data.get("_submitted"):
        await message.answer(t(uid, "ticket_submitted"), reply_markup=main_menu_kb(lang))
        return

    appliance_ru = data.get("appliance", "-")
    region_ru = data.get("region", "-")
    problem = data.get("problem", "-")
    phone = data.get("phone", "-")
    address = data.get("address", "-")

    user = message.from_user
    username = f"@{user.username}" if user.username else "—"

    ticket_text = (
        "📨 Новая заявка на сервис"
        f"👤 Пользователь: {user.full_name} ({username}, id={user.id})"
        f"📦 Техника: {appliance_ru}"
        f"📍 Регион: {region_ru}"
        f"📝 Проблема: {problem}"
        f"📞 Телефон: {phone}"
        f"🏠 Адрес: {address}"
    )

    # Forward to staff of region
    staff_list = STAFF_BY_REGION.get(region_ru, [])
    for chat_id in staff_list:
        try:
            await message.bot.send_message(chat_id=chat_id, text=ticket_text)
        except Exception as e:
            logging.exception("Failed to send ticket to %s: %s", chat_id, e)

    await message.answer(t(uid, "ticket_submitted"), reply_markup=main_menu_kb(lang))
    await state.update_data(_submitted=True)
    await state.set_state(ServiceForm.submitted)


# ========================= BOOT =========================
async def on_startup(bot: Bot):
    me = await bot.get_me()
    logging.info("Bot started as @%s (%s)", me.username, me.id)


async def main():
    logging.basicConfig(level=logging.INFO)
    if not BOT_TOKEN or BOT_TOKEN == "PUT_YOUR_TOKEN_HERE":
        raise RuntimeError("Please set BOT_TOKEN env var or edit BOT_TOKEN in the script.")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await on_startup(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped")
