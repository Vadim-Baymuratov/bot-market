from aiogram.dispatcher import FSMContext

from filters import IsUser
from aiogram.types import Message, CallbackQuery
from keyboards.inline.categories import categories_markup, category_cb
from .cart import process_cart
from .menu import catalog
from loader import dp, db, bot
from aiogram.types.chat import ChatActions
from keyboards.inline.products_from_catalog import product_cb, product_markup


@dp.message_handler(IsUser(), text=catalog)
async def process_catalog(message: Message):
    await message.answer('Выберите раздел, чтобы вывести список товаров:',
                         reply_markup=categories_markup())


# обработчик перехода к выводу всех товаров категории
@dp.callback_query_handler(IsUser(), category_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict):
    products = db.fetchall('''SELECT * FROM products product
        WHERE product.tag = (SELECT title FROM categories WHERE idx=?) 
            AND product.idx NOT IN (SELECT idx FROM cart WHERE cid = ?)''',
                           (callback_data['id'], query.message.chat.id))

    await query.answer('Все доступные товары.')
    await show_products(query.message, products)

# ниже сам обработчик отображения списка товаров.


async def show_products(m, products):

    if len(products) == 0:
        await m.answer('Здесь ничего нет 😢')
    else:
        await bot.send_chat_action(m.chat.id, ChatActions.TYPING)
        #Включаем имитацию печати человеком
        for idx, title, body, image, price, _ in products:
            #Для каждого товара получаем идентификатор категории, название товара, описание, фото, цену
            markup = product_markup(idx, price)
            text = f'<b>{title}</b>\n\n{body}'

            #  Формируем разметку кнопки добавления товара в корзину.
            await m.answer_photo(photo=image,
                                 caption=text,
                                 reply_markup=markup)
            #Выводим карточку товара с фото, названием и кнопкой добавления.


@dp.callback_query_handler(IsUser(), product_cb.filter(action='add'))
async def add_product_callback_handler(query: CallbackQuery,
                                       callback_data: dict):
    db.query('INSERT INTO cart VALUES (?, ?, 1)',
             (query.message.chat.id, callback_data['id']))
    await query.answer('Товар добавлен в корзину!')
    await query.message.delete()

