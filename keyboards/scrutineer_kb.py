from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from queries import scrutineer_queries

async def gen_list_comp(tg_id):
    list_comp_buttons = []

    competitions = await scrutineer_queries.get_list_comp(tg_id)
    for comp in competitions:
        list_comp_buttons.append([InlineKeyboardButton(text=comp['compName'], callback_data=f"Scomp_{comp['compId']}")])
    list_comp_buttons.append([InlineKeyboardButton(text='Вернуться к меню', callback_data='back_to_scrutineer_menu')])
    return InlineKeyboardMarkup(inline_keyboard=list_comp_buttons)

menu_button = [InlineKeyboardButton(text='Задать активное соревнование', callback_data='set_active_competition_for_S')]
menu_kb = InlineKeyboardMarkup(inline_keyboard=[menu_button])

confirm_choice_button_S = InlineKeyboardButton(text='Да', callback_data=f"confirm_choice_S")
confirm_choice_button1_S = InlineKeyboardButton(text='Нет', callback_data=f"confirm_choice_back_S")
confirm_choice_kb_S = load_judges_kb = InlineKeyboardMarkup(inline_keyboard=[[confirm_choice_button_S, confirm_choice_button1_S]])

chairman_b = InlineKeyboardButton(text='Chairman', callback_data=f"enter_chairaman_pin")
scrutiner_b = InlineKeyboardButton(text='Scrutineer', callback_data=f"scrutiner_role")
scrutiner_chairman_mark = InlineKeyboardMarkup(inline_keyboard=[[chairman_b, scrutiner_b]])

back_b = InlineKeyboardButton(text='Назад', callback_data=f"back_b")
back_mark = InlineKeyboardMarkup(inline_keyboard=[[back_b]])

pin_b = InlineKeyboardButton(text='Ввести код', callback_data=f"enter_chairaman_pin")
chairman_reg_mark = InlineKeyboardMarkup(inline_keyboard=[[pin_b, back_b]])

conf_data =InlineKeyboardButton(text='Подтвердить', callback_data=f"conf_chairman_data")
reject_data =InlineKeyboardButton(text='Отклонить', callback_data=f"back_b")
accept_gs_data_kb =InlineKeyboardMarkup(inline_keyboard=[[conf_data, reject_data]])

