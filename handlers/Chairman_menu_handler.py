import re
from aiogram import Router, F
from aiogram import types
from keyboards import chairmans_kb
from queries import chairman_queries
from queries import get_user_status_query
from queries import general_queries
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from chairman_moves import load_judges_list
from queries import scrutineer_queries
from handlers import start_stage_handler

import config
router = Router()
problemjudgesset = {}
current_problem_jud = {}
enter_mes = {}
confirm_tour_id = {}
last_added_judges = {}
judges_codes = {}
generation_results = {}
old_enter_pin_m = {}
generation_zgs_results = {}

class Load_list_judges(StatesGroup):
    next_step = State()

class Solve_judges_problem(StatesGroup):
    bookNumber = State()


#Вернуться в меню
@router.callback_query(F.data == 'back_to_chairman_menu')
async def cmd_start(call: types.CallbackQuery):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 3:
        active_comp = await general_queries.get_CompId(call.from_user.id)
        if await chairman_queries.del_unactive_comp(call.from_user.id, active_comp) == 1:
            active_comp = None
        info = await general_queries.CompId_to_name(active_comp)
        await call.message.edit_text(f"👋Добро пожаловать в chairman интерфейс бота SS6\n\n/help - список всех команд\nАктивное соревнование: {info}", reply_markup = chairmans_kb.menu_kb)


#Выбрать активное соревнование
@router.callback_query(F.data == 'set_active_competition')
async def set_active_comp(call: types.CallbackQuery):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 3:
        active_comp = await general_queries.get_CompId(call.from_user.id)
        if await chairman_queries.del_unactive_comp(call.from_user.id, active_comp) == 1:
            active_comp = None
        markup = await chairmans_kb.gen_list_comp(call.from_user.id)
        info = await general_queries.CompId_to_name(active_comp)
        await call.message.edit_text(
            f"👋Добро пожаловать в chairman интерфейс бота SS6\n\n/help - список всех команд\nАктивное соревнование: {info}",
            reply_markup=markup)


#Обработка после выбора активного соревнования
@router.callback_query(F.data.startswith('comp_'))
async def cmd_start(call: types.CallbackQuery):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 3:
        compId = int(call.data.replace('comp_', ''))
        confirm_tour_id[call.from_user.id] = compId
        info = await general_queries.CompId_to_name(compId)
        await call.message.edit_text(
            f"{info}\n\nПодтвердить выбор ?",
            reply_markup=chairmans_kb.confirm_choice_kb)



@router.callback_query(F.data == 'confirm_choice')
async def cmd_start(call: types.CallbackQuery):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 3:
        try:
            await chairman_queries.set_active_comp_for_chairman(call.from_user.id, confirm_tour_id[call.from_user.id])
            active_comp = await general_queries.get_CompId(call.from_user.id)
            info = await general_queries.CompId_to_name(active_comp)
            await call.message.edit_text(
                f"👋Добро пожаловать в chairman интерфейс бота SS6\n\n/help - список всех команд\nАктивное соревнование: {info}",
                reply_markup=chairmans_kb.menu_kb)
        except:
            await call.message.answer('❌Ошибка. Попробуйте еще раз через /start')


@router.callback_query(F.data == 'confirm_choice_back')
async def cmd_start(call: types.CallbackQuery):
    user_status = await get_user_status_query.get_user_status(call.from_user.id)
    if user_status == 3:
        active_comp = await general_queries.get_CompId(call.from_user.id)
        info = await general_queries.CompId_to_name(active_comp)
        markup = await chairmans_kb.gen_list_comp(call.from_user.id)
        await call.message.edit_text(
            f"👋Добро пожаловать в chairman интерфейс бота SS6\n\n/help - список всех команд\nАктивное соревнование: {info}", reply_markup=markup)



#Очистить список судей в турнире
@router.message(Command("clean"))
async def cmd_start(message: Message):
    user_status = await get_user_status_query.get_user_status(message.from_user.id)
    if user_status == 3 or user_status == 2:
        active_comp = await general_queries.get_CompId(message.from_user.id)
        active_or_not = await general_queries.active_or_not(active_comp)
        if active_or_not == 1:
            status = await chairman_queries.cancel_load(message.from_user.id)
            if status == 1:
                msg = await message.answer('✅Список очищен')
                await message.delete()
                await start_stage_handler.del_message_after_time(msg, config.expirate_message_timer)
            else:
                await message.answer('❌Ошибка')
        else:
            await message.answer('❌Ошибка. Выбранное соревнование неактивно')


#Показать свободных судей
@router.message(Command("free"))
async def cmd_start(message: Message):
    user_status = await get_user_status_query.get_user_status(message.from_user.id)
    if user_status == 3 or user_status == 2:
        active_comp = await general_queries.get_CompId(message.from_user.id)
        active_or_not = await general_queries.active_or_not(active_comp)
        if active_or_not == 1:
            status = await chairman_queries.for_free(message.from_user.id)
            if status == 0:
                await message.answer('❌Ошибка')
            else:
                if len(status) > 4096:
                    for x in range(0, len(status), 4096):
                        await message.answer(status[x:x + 4096])
                else:
                    await message.answer(status)
        else:
            await message.answer('❌Ошибка. Выбранное соревнование неактивно')


#Загрузка списка судей
@router.message(Command("judges"))
async def cmd_judes(message: Message, state:FSMContext):
    user_status = await get_user_status_query.get_user_status(message.from_user.id)
    if user_status == 3 or user_status == 2:
        judges_codes[message.from_user.id] = 0
        last_added_judges[message.from_user.id] = []
        try:
            await state.clear()
            enter_mes.pop(message.from_user.id, None)
            current_problem_jud.pop(message.from_user.id, None)
            problemjudgesset.pop(message.from_user.id, None)
        except:
            pass

        if await chairman_queries.check_have_tour_date(message.from_user.id) == 0:
            await message.answer('❌Ошибка. Установите активный турнир')
            return

        active_compId_chairman = await general_queries.get_CompId(message.from_user.id)
        if active_compId_chairman != 0:
            is_active = await general_queries.active_or_not(active_compId_chairman)
            if is_active == 1:
                await message.answer('Отправьте список в формате: Судья№1, Судья№2, ..., Судья№n.',
                                     reply_markup=chairmans_kb.load_judges_kb)
                await state.set_state(Load_list_judges.next_step)
            else:
                await message.answer('❌Ошибка\nВыбранное соревнование неактивно')
        else:
            await message.answer('❌Ошибка\nВыберите активное соревнование')


@router.message(Load_list_judges.next_step)
async def f2(message: Message, state: FSMContext):
    compid = await general_queries.get_CompId(message.from_user.id)
    code = judges_codes[message.from_user.id]
    status = await load_judges_list.load_list(message.from_user.id, message.text, compid, code)
    if status == 1:
        status1 = await chairman_queries.check_celebrate(message.from_user.id, last_added_judges[message.from_user.id])
        if status1 != 0:
            await message.answer(status1)
        await message.answer('Список загружен')

    elif type(status) == tuple:
        problem, names = status
        a = ', '.join([i for i in names])
        problemjudgesset[message.from_user.id] = problem
        await message.answer(f'🤔{a}: требуются редактирование', reply_markup=chairmans_kb.judges_problem_kb)
    else:
        await message.answer('При загрузке списка возникла ошибка, попробуйте еще раз через команду /judges')
    await state.clear()


@router.callback_query(F.data == 'cancel_load')
async def f4(callback: types.CallbackQuery, state: FSMContext):
    try:
        enter_mes.pop(callback.from_user.id, None)
        current_problem_jud.pop(callback.from_user.id, None)
        problemjudgesset.pop(callback.from_user.id, None)
    except:
        pass
    await state.clear()
    await callback.message.delete()
    await callback.message.answer('Загрузка завершена')


@router.callback_query(F.data == 'edit_problem_judges_info')
async def edit_problem_jud(callback: types.CallbackQuery, state: FSMContext, q=1):
    await state.clear()
    try:
        problemJudges = problemjudgesset[callback.from_user.id]
        if problemJudges == [] and current_problem_jud[callback.from_user.id] == 'end':
            status1 = await chairman_queries.check_celebrate(callback.from_user.id, last_added_judges[callback.from_user.id])
            if status1 != 0:
                await callback.message.answer(status1)
            await callback.message.answer('Загрузка завершена')
            await callback.message.delete()
            return

        if q == 1:
            current_problem_jud[callback.from_user.id] = problemJudges.pop(0)

        #Не обнаружена запись в бд или невозможно однозначно определить человека
        if current_problem_jud[callback.from_user.id][3] == 2:
            name = current_problem_jud[callback.from_user.id][0] + ' ' + current_problem_jud[callback.from_user.id][1]
            p = current_problem_jud[callback.from_user.id][2]
            await callback.message.edit_text(f"{name}\n{p}\n\nВыберите действие:", reply_markup=chairmans_kb.choose_problem_jud_action_kb)

        #На момент окончания турнира категория недействительна
        elif current_problem_jud[callback.from_user.id][3] == 1:
            name = current_problem_jud[callback.from_user.id][0] + ' ' + current_problem_jud[callback.from_user.id][1]
            p = current_problem_jud[callback.from_user.id][2]
            await callback.message.edit_text(f"{name}\n{p}\n\nВыберите действие:",reply_markup=chairmans_kb.choose_problem_jud_action_kb_1)

    except Exception as e:
        print(e)
        await callback.message.answer('При загрузке списка возникла ошибка, попробуйте еще раз через команду /judges')


async def edit_problem_jud_after_enter_booknum(message: Message, state: FSMContext, q=1):
    await state.clear()
    try:
        problemJudges = problemjudgesset[message.from_user.id]
        if problemJudges == [] and current_problem_jud[message.from_user.id] == 'end':
            status1 = await chairman_queries.check_celebrate(message.from_user.id, last_added_judges[message.from_user.id])
            if status1 != 0:
                await message.answer(status1)
            await message.answer('Загрузка завершена')
            return
        if q == 1:
            current_problem_jud[message.from_user.id] = problemJudges.pop(0)

        if current_problem_jud[message.from_user.id][3] == 2:
            name = current_problem_jud[message.from_user.id][0] + ' ' + current_problem_jud[message.from_user.id][1]
            p = current_problem_jud[message.from_user.id][2]
            await message.answer(f"{name}\n{p}\n\nВыберите действие:", reply_markup=chairmans_kb.choose_problem_jud_action_kb)
        elif current_problem_jud[message.from_user.id][3] == 1:
            name = current_problem_jud[message.from_user.id][0] + ' ' + current_problem_jud[message.from_user.id][1]
            p = current_problem_jud[message.from_user.id][2]
            await message.answer(f"{name}\n{p}\n\nВыберите действие:",reply_markup=chairmans_kb.choose_problem_jud_action_kb_1)

    except Exception as e:
        print(e)
        await message.answer('При загрузке списка возникла ошибка, попробуйте еще раз через команду /judges')


#Отправить как есть судью которого не смогли пробить по бд
@router.callback_query(F.data == 'take_as_is')
async def f4(callback: types.CallbackQuery, state: FSMContext):
    try:
        jud = current_problem_jud[callback.from_user.id]
        code = judges_codes[callback.from_user.id]
        await chairman_queries.set_problem_jud_as_is(callback.from_user.id, jud[0] + ' ' +jud[1], code)

        if problemjudgesset[callback.from_user.id] == []:
            current_problem_jud[callback.from_user.id] = 'end'

        await edit_problem_jud(callback, state, 1)
    except:
        await callback.message.answer('При загрузке списка возникла ошибка, попробуйте еще раз через команду /judges')

#Отправить как есть судью с проблемой по категории
@router.callback_query(F.data == 'take_as_is_1')
async def f4(callback: types.CallbackQuery, state: FSMContext):
    try:
        jud = current_problem_jud[callback.from_user.id]
        name = ''
        code = judges_codes[callback.from_user.id]
        if len(jud) > 4:
            name = jud[4]
        await chairman_queries.set_problem_jud_as_is_1(callback.from_user.id, jud[0] + ' ' +jud[1], code ,name)
        if problemjudgesset[callback.from_user.id] == []:
            current_problem_jud[callback.from_user.id] = 'end'

        await edit_problem_jud(callback, state, 1)
    except:
        await callback.message.answer('При загрузке списка возникла ошибка, попробуйте еще раз через команду /judges')


#Действующая категория
@router.callback_query(F.data == 'real_sport_category')
async def f4(callback: types.CallbackQuery, state: FSMContext):
    try:
        jud = current_problem_jud[callback.from_user.id]
        name = ''
        if len(jud) > 4:
            name = jud[4]
        code = judges_codes[callback.from_user.id]
        await chairman_queries.set_real_cetegory(callback.from_user.id, jud[0], jud[1], name, code)

        if problemjudgesset[callback.from_user.id] == []:
            current_problem_jud[callback.from_user.id] = 'end'

        await edit_problem_jud(callback, state, 1)
    except:
        await callback.message.answer('При загрузке списка возникла ошибка, попробуйте еще раз через команду /judges')


#Пропустить судью в загрузке списка
@router.callback_query(F.data == 'do_gap')
async def f4(callback: types.CallbackQuery, state: FSMContext):
    if problemjudgesset[callback.from_user.id] == []:
        current_problem_jud[callback.from_user.id] = 'end'
    await edit_problem_jud(callback, state, 1)

@router.callback_query(F.data == 'enter_book_number')
async def f4(callback: types.CallbackQuery, state: FSMContext):
    enter_mes[callback.from_user.id] = callback.message.message_id
    try:
        jud = current_problem_jud[callback.from_user.id]
        await callback.message.edit_text(f"{jud[0] + ' ' +jud[1]}\n\nВведите номер книжки:", reply_markup=chairmans_kb.book_number_kb)
        await state.set_state(Solve_judges_problem.bookNumber)
    except:
        await callback.message.answer('При загрузке списка возникла ошибка, попробуйте еще раз через команду /judges')


@router.message(Solve_judges_problem.bookNumber)
async def f2(message: Message, state: FSMContext):
    try:
        code = judges_codes[message.from_user.id]
        await message.bot.delete_message(chat_id=message.chat.id, message_id=enter_mes[message.from_user.id])
        await message.delete()
        booknumber = message.text
        jud = current_problem_jud[message.from_user.id]
        status = await chairman_queries.check_cat_for_enter_book_number(message.from_user.id, int(booknumber))
        if status == 1:
            await chairman_queries.set_problem_jud_as_is(message.from_user.id, jud[0] + ' ' +jud[1], code ,booknumber)
            if problemjudgesset[message.from_user.id] == []:
                current_problem_jud[message.from_user.id] = 'end'

            await edit_problem_jud_after_enter_booknum(message, state, 1)
            await state.clear()
        else:
            last, first = await chairman_queries.booknumber_to_name_1(int(booknumber))
            problemjudgesset[message.from_user.id].insert(0, [last, first, 'На момент окончания турнира категория недействительна', 1, jud[0] + ' ' + jud[1] + '|' + str(booknumber)])
            await edit_problem_jud_after_enter_booknum(message, state, 1)
            await state.clear()


    except Exception as e:
        await state.clear()
        print(e)
        await message.answer('При загрузке списка возникла ошибка, попробуйте еще раз через команду /judges')


@router.callback_query(F.data == 'search_for_db')
async def f2(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        jud = current_problem_jud[callback.from_user.id]
        mark = await chairmans_kb.gen_similar_judges(jud[0] + ' ' +jud[1])
        await callback.message.edit_text(f"{jud[0] + ' ' +jud[1]}\nВозможные варианты:",
                             reply_markup=mark)
    except Exception as e:
        await state.clear()
        print(e)
        await callback.message.answer('При загрузке списка возникла ошибка, попробуйте еще раз через команду /judges')



@router.callback_query(F.data == 'back_to_edit_jud')
async def f2(callback: types.CallbackQuery, state: FSMContext):
    await edit_problem_jud(callback, state, 0)


@router.callback_query(F.data.startswith('jud_'))
async def cmd_start(call: types.CallbackQuery, state: FSMContext):
    try:
        code = judges_codes[call.from_user.id]
        BookNumber = int(call.data.replace('jud_', ''))
        name = call.message.text.replace('Возможные варианты:', '').strip().strip('\n').strip() + f'|{BookNumber}'
        status = await chairman_queries.check_category_date_for_book_id(BookNumber, call.from_user.id)
        if status == 1:
            await chairman_queries.add_problemcorrect_jud(BookNumber, call.from_user.id, name.split('|')[0], code)

            if problemjudgesset[call.from_user.id] == []:
                current_problem_jud[call.from_user.id] = 'end'

            await edit_problem_jud(call, state)
        else:
            lastname, firstname = await chairman_queries.BookNumber_to_name(BookNumber)
            problemjudgesset[call.from_user.id].insert(0, [lastname, firstname, 'На момент окончания турнира категория недействительна', 1, name])
            await edit_problem_jud(call, state, 1)
    except:
        await state.clear()
        await call.message.answer('При загрузке списка возникла ошибка, попробуйте еще раз через команду /judges')


@router.message(Command("cleancounter"))
async def cmd_start(message: Message, state: FSMContext):
    user_status = await get_user_status_query.get_user_status(message.from_user.id)
    if user_status == 3 or user_status == 2:
        r = await chairman_queries.clean_group_counter(message.from_user.id)
        if r == 1:
            msg = await message.answer("✅Действие обработано")
            await message.delete()
            await start_stage_handler.del_message_after_time(msg, config.expirate_message_timer)
        else:
            await message.answer("❌Ошибка")


@router.message(Command("change_generation_mode"))
async def cmd_start(message: Message, state: FSMContext):
    user_status = await get_user_status_query.get_user_status(message.from_user.id)
    if user_status == 3 or user_status == 2:
        msg = await chairman_queries.change_generation_mode(message.from_user.id)
        if msg != -1:
            await message.delete()
            msg = await message.answer(msg)
            await start_stage_handler.del_message_after_time(msg, config.expirate_message_timer)
        else:
            await message.answer("❌Ошибка")

class Enter_chairman_pin(StatesGroup):
    firstState = State()


@router.callback_query(F.data == 'enter_pin_on_menu')
async def cmd_start(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    old_enter_pin_m[call.from_user.id] = call.message
    await call.message.edit_text('Введите код: ', reply_markup=chairmans_kb.back_kb)
    await state.set_state(Enter_chairman_pin.firstState)


@router.message(Enter_chairman_pin.firstState)
async def f2(message: Message, state: FSMContext):
    oldmessage = old_enter_pin_m[message.from_user.id]
    try:
        pin = message.text
        if pin.isdigit():
            status = await scrutineer_queries.check_chairman_pin(message.from_user.id, int(pin), 1)
            if status == -1:
                await message.delete()
                await oldmessage.edit_text('❌Ошибка', reply_markup=chairmans_kb.back_kb)
                await state.clear()

            if status == 1:
                text, userstatus = await get_mes_menu(message)
                await message.delete()
                if userstatus == 3:
                    await oldmessage.edit_text(text, reply_markup=chairmans_kb.menu_kb)
                    await state.clear()

            if status == 0:
                await message.delete()
                await oldmessage.edit_text('❌Ошибка. Пинкод не найден.', reply_markup=chairmans_kb.back_kb)
                await state.clear()

        else:
            await message.delete()
            await oldmessage.edit_text('❌Ошибка. Неправильный формат пинкода.', reply_markup=chairmans_kb.back_kb)
            await state.clear()
    except Exception as e:
        await state.clear()


async def get_mes_menu(message: Message):
    user_status = await get_user_status_query.get_user_status(message.from_user.id)
    #Админ
    if user_status == 1:
        return '👋Добро пожаловать в admin интерфейс бота SS6', user_status

    #scrutinner
    if user_status == 2:
        active_comp = await general_queries.get_CompId(message.from_user.id)
        if await chairman_queries.del_unactive_comp(message.from_user.id, active_comp) == 1:
            active_comp = None
        info = await general_queries.CompId_to_name(active_comp)
        return f"👋Добро пожаловать в scrutineer интерфейс бота SS6\n\n/help - список всех команд\nАктивное соревнование: {info}", user_status
    #chairman
    if user_status == 3:
        active_comp = await general_queries.get_CompId(message.from_user.id)
        if await chairman_queries.del_unactive_comp(message.from_user.id, active_comp) == 1:
            active_comp = None
        info = await general_queries.CompId_to_name(active_comp)
        return f"👋Добро пожаловать в chairman интерфейс бота SS6\n\n/judges - отправить список судей\n/help - список всех команд\nАктивное соревнование: {info}", 3
    if user_status == 0:
        return "👋Добро пожаловать в интерфейс бота SS6\n\nДля начала работы необходимо пройти регистрацию в системе\nВыберите роль:", 0


class Gen_zgs_states(StatesGroup):
    firstState = State()

from chairman_moves import generation_logic
@router.message(Command("gen_zgs"))
async def cmd_start(message: Message, state: FSMContext):
    user_status = await get_user_status_query.get_user_status(message.from_user.id)
    if user_status == 2 or user_status == 3:
        active_comp = await general_queries.get_CompId(message.from_user.id)
        if active_comp == 0:
            await message.delete()
            return await message.answer('❌Ошибка. Необходимо задать активное соревнование.')

        active_or_not = await general_queries.active_or_not(active_comp)
        if active_or_not == 0:
            return await message.answer('❌Ошибка. Соревнование неактивно.')

        await chairman_queries.clear_zgs(active_comp)
        msg = await message.answer('Введите количество:')
        generation_zgs_results[message.from_user.id] = {'en_msg': msg}
        await state.set_state(Gen_zgs_states.firstState)


@router.message(Gen_zgs_states.firstState)
async def f2(message: Message, state: FSMContext):
    try:
        num = message.text
        if num.isdigit():
            active_comp = await general_queries.get_CompId(message.from_user.id)
            json = await generation_logic.generate_zgs(active_comp, int(num))
            await message.delete()
            await generation_zgs_results[message.from_user.id]['en_msg'].delete()
            msg = await message.answer(json['msg'], reply_markup=chairmans_kb.generation_zgs_kb)
            generation_zgs_results[message.from_user.id] = {'json': json, 'num': num, 'compId': active_comp}
            await state.clear()
        else:
            await state.clear()
            return await message.answer('❌Ошибка. Неверный формат данных.')
    except:
        return await message.answer('❌Ошибка')


@router.callback_query(F.data == 'regenerate_zgs')
async def cmd_start(call: types.CallbackQuery, state: FSMContext):
    try:
        num = generation_zgs_results[call.from_user.id]['num']
        active_comp = await general_queries.get_CompId(call.from_user.id)
        json = await generation_logic.generate_zgs(active_comp, int(num))
        msg = await call.message.edit_text(json['msg'], reply_markup=chairmans_kb.generation_zgs_kb)
        generation_zgs_results[call.from_user.id] = {'json': json, 'num': num, 'compId': active_comp}
        await state.clear()
    except:
        return await call.message.answer('❌Ошибка')


@router.callback_query(F.data == 'save_zgs_result')
async def cmd_start(call: types.CallbackQuery):
    try:
        r = await chairman_queries.create_zgs(generation_zgs_results[call.from_user.id]['json'])
        if r == 1:
            await call.message.delete_reply_markup()
            await call.message.answer('✅Результат сохранен.')
        elif r == -1:
            await call.message.delete_reply_markup()
            await call.message.answer('❌Ошибка')
    except:
        return await call.message.answer('❌Ошибка')


@router.callback_query(F.data == 'end_zgs_generation_proces')
async def cmd_start(call: types.CallbackQuery):
    await call.message.delete_reply_markup()
    await call.message.answer('Генерация завершена')


@router.callback_query(F.data == 'back_to_zgs_generation')
async def cmd_start(call: types.CallbackQuery):
    try:
        text = generation_zgs_results[call.from_user.id]['json']['msg']
        await call.message.edit_text(text, reply_markup=chairmans_kb.generation_zgs_kb)
    except:
        pass


@router.callback_query(F.data == 'edit_zgs')
async def cmd_start(call: types.CallbackQuery):
    try:
        markup = await chairmans_kb.get_gen_zgs_edit_markup_01(generation_zgs_results[call.from_user.id]['json'])
        await call.message.edit_reply_markup(reply_markup=markup)
    except:
        return await call.message.answer('❌Ошибка')


@router.callback_query(F.data.startswith('zgs_generation_'))
async def cmd_start(call: types.CallbackQuery):
    try:
        judgeId = int(call.data.replace('zgs_generation_', ''))
        generation_zgs_results[call.from_user.id]['current'] = judgeId
        markup = await chairmans_kb.get_gen_zgs_edit_markup_02(generation_zgs_results[call.from_user.id]['json'],
                                                               generation_zgs_results[call.from_user.id]['compId'])
        await call.message.edit_reply_markup(reply_markup=markup)
    except:
        return await call.message.answer('❌Ошибка')

@router.callback_query(F.data.startswith('zgs_02_generation_'))
async def cmd_start(call: types.CallbackQuery):
    try:
        judgeId = int(call.data.replace('zgs_02_generation_', ''))
        old = generation_zgs_results[call.from_user.id]['current']
        compId = generation_zgs_results[call.from_user.id]['compId']
        n = await chairman_queries.ids_to_names([judgeId], compId)
        i = n.split()
        if len(i) == 2:
            lastname, firstname = i
        else:
            lastname = i[0]
            firstname = ' '.join(i[1::])

        oldf, oldl = generation_zgs_results[call.from_user.id]['json']['judges'][old]['firstName'], \
                     generation_zgs_results[call.from_user.id]['json']['judges'][old]['lastName']
        generation_zgs_results[call.from_user.id]['json']['msg'] = generation_zgs_results[call.from_user.id]['json'][
            'msg'].replace(oldl + ' ' + oldf, lastname + ' ' + firstname)
        generation_zgs_results[call.from_user.id]['json']['judges'][judgeId] = \
        generation_zgs_results[call.from_user.id]['json']['judges'][old]
        generation_zgs_results[call.from_user.id]['json']['judges'].pop(old, None)
        await call.message.edit_text(generation_zgs_results[call.from_user.id]['json']['msg'],
                                     reply_markup=chairmans_kb.generation_zgs_kb)
    except:
        return await call.message.answer('❌Ошибка')