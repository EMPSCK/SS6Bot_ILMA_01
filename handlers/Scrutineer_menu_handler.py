from aiogram import Router, F
from aiogram import types

import config
from keyboards import scrutineer_kb
from queries import get_user_status_query
from queries import scrutineer_queries
from queries import chairman_queries
from queries import general_queries
from aiogram.filters import Command
from handlers import start_stage_handler
router = Router()
confirm_tour_id_S = {}

#Вернуться в меню
@router.callback_query(F.data == 'back_to_scrutineer_menu')
async def cmd_start(call: types.CallbackQuery):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 2:
        active_comp = await general_queries.get_CompId(call.from_user.id)
        if await chairman_queries.del_unactive_comp(call.from_user.id, active_comp) == 1:
            active_comp = None
        info = await general_queries.CompId_to_name(active_comp)
        await call.message.edit_text(
            f"👋Добро пожаловать в scrutineer интерфейс бота SS6\n\n/help - список всех команд\nАктивное соревнование: {info}",
            reply_markup=scrutineer_kb.menu_kb)


#Выбрать активное соревнование
@router.callback_query(F.data == 'set_active_competition_for_S')
async def set_active_comp_S(call: types.CallbackQuery):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 2:
        active_comp = await general_queries.get_CompId(call.from_user.id)
        if await chairman_queries.del_unactive_comp(call.from_user.id, active_comp) == 1:
            active_comp = None
        markup = await scrutineer_kb.gen_list_comp(call.from_user.id)
        info = await general_queries.CompId_to_name(active_comp)
        await call.message.edit_text(
            f"👋Добро пожаловать в scrutineer интерфейс бота SS6\n\n/help - список всех команд\nАктивное соревнование: {info}",
            reply_markup=markup)


#Обработка после выбора активного соревнования
@router.callback_query(F.data.startswith('Scomp_'))
async def cmd_start(call: types.CallbackQuery):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 2:
        compId = int(call.data.replace('Scomp_', ''))
        confirm_tour_id_S[call.from_user.id] = compId
        info = await general_queries.CompId_to_name(compId)
        await call.message.edit_text(
            f"{info}\n\nПодтвердить выбор ?",
            reply_markup=scrutineer_kb.confirm_choice_kb_S)


@router.callback_query(F.data == 'confirm_choice_S')
async def cmd_start(call: types.CallbackQuery):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 2:
        try:
            await chairman_queries.set_active_comp_for_chairman(call.from_user.id, confirm_tour_id_S[call.from_user.id])
            active_comp = confirm_tour_id_S[call.from_user.id]
            info = await general_queries.CompId_to_name(active_comp)
            await call.message.edit_text(
                f"👋Добро пожаловать в scrutineer интерфейс бота SS6\n\n/help - список всех команд\nАктивное соревнование: {info}",
                reply_markup=scrutineer_kb.menu_kb)
        except:
            await call.message.answer('❌Ошибка. Попробуйте еще раз через /start')


@router.callback_query(F.data == 'confirm_choice_back_S')
async def cmd_start(call: types.CallbackQuery):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 2:
        active_comp = await general_queries.get_CompId(call.from_user.id)
        info = await general_queries.CompId_to_name(active_comp)
        markup = await scrutineer_kb.gen_list_comp(call.from_user.id)
        await call.message.edit_text(
            f"👋Добро пожаловать в scrutineer интерфейс бота SS6\n\n/help - список всех команд\nАктивное соревнование: {info}",
            reply_markup=markup)


@router.message(Command("delactive"))
async def cmd_start(message: types.Message):
    user_status = await get_user_status_query.get_user_status(message.from_user.id)
    if user_status == 2 or user_status == 3:
        status = await scrutineer_queries.set_active_0(message.from_user.id)
        if status == 1:
            msg = await message.answer('✅Судьи деактивированы')
            await message.delete()
            await start_stage_handler.del_message_after_time(msg, config.expirate_message_timer)
        else:
            await message.answer('❌Ошибка')
            await message.delete()


@router.message(Command("change_private_mode"))
async def cmd_start(message: types.Message):
    await message.delete()
    user_status = await get_user_status_query.get_user_status(message.from_user.id)
    if user_status == 2 or user_status == 3:
        status, mode = await scrutineer_queries.change_private_mode(message.from_user.id)
        if status == 1:
            if mode == 0:
                msg = await message.answer('🔽Режим конфиденциальности понижен')
            if mode == 1:
                msg = await message.answer('🔼Режим конфиденциальности повышен')
        elif status == -1:
            await message.answer('❌Ошибка')
    pass

@router.message(Command("change_generation_zgs_mode"))
async def cmd_start(message: types.Message):
    await message.delete()
    user_status = await get_user_status_query.get_user_status(message.from_user.id)
    if user_status == 2 or user_status == 3:
        status, mode = await scrutineer_queries.change_geneation_zgs_mode(message.from_user.id)
        if status == 1:
            if mode == 0:
                msg = await message.answer('🗓Режим генерации згс для спортивных категорий отключен')
                await start_stage_handler.del_message_after_time(msg, config.expirate_message_timer)
            if mode == 1:
                msg = await message.answer('🗓Режим генерации згс для спортивных категорий активирован')
                await start_stage_handler.del_message_after_time(msg, config.expirate_message_timer)
        elif status == -1:
            await message.answer('❌Ошибка')
    pass