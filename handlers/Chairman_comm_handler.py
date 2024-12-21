import asyncio
import json
import re
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import chairman_moves.check_list_judges
from queries import get_user_status_query
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards import chairmans_kb
from queries import chairman_queries
from queries import scrutineer_queries
from queries import general_queries
from aiogram import types
from chairman_moves import check_list_judges
from handlers import Chairman_comm_handler_02
from aiogram.filters import Filter
from chairman_moves import generation_logic
router = Router()
linsets = {}
problemjudgesset_for_check_lin ={}
current_problem_jud_for_check_lin = {}
bank_for_edit_costyl = {}
chairmans_groups_lists = {}
generation_results = {}

#Обработка списка от CHAIRPERSON
@router.message(F.text.lower().contains('линейные судьи'))
async def f2(message: Message):
    user_status = await get_user_status_query.get_user_status(message.from_user.id)
    if user_status == 3 or user_status == 2:
        try:
            linsets.pop(message.from_user.id, None)
            problemjudgesset_for_check_lin.pop(message.from_user.id, None)
            current_problem_jud_for_check_lin.pop(message.from_user.id, None)
            Chairman_comm_handler_02.current_jud_point.pop(message.from_user.id, None)
            Chairman_comm_handler_02.jud_problem_list.pop(message.from_user.id, None)
            Chairman_comm_handler_02.to_index_future.pop(message.from_user.id, None)
            Chairman_comm_handler_02.markup_buttons.pop(message.from_user.id, None)
        except:
            pass

        if await chairman_queries.check_have_tour_date(message.from_user.id) == 0:
            await message.answer('❌Ошибка. Установите активный турнир')
            return

        #judges_problem - не получилось пробить по competition_judges (в двух полях с именами)
        #judges_problem_db - имя совпало со вторым вариантом, далее в сообщении меняем их имена на имена в judges
        await chairman_queries.set_is_use_0(message.from_user.id)
        linsets[message.from_user.id] = [message.text, [], [], []]
        judges_problem, judges_problem_db, text_edit = await check_list_judges.get_parse(message.text, message.from_user.id)
        linsets[message.from_user.id][1] = judges_problem
        text = await check_list_judges.transform_linlist(text_edit, judges_problem_db, message.from_user.id)
        linsets[message.from_user.id][0] = text
        #Все пробились в competition_judges
        if judges_problem == []:
            res, msg, list_counter = await check_list_judges.check_list(text, message.from_user.id)
            linsets[message.from_user.id][3] = msg
            linsets[message.from_user.id].append(list_counter)
            await chairman_queries.set_free_judges(message.from_user.id)
            if res == 1:
                # Перед отправкой сообщения проверяем, совпадает ли выбор турниров у пары и активно ли соревнование
                scrutineer_id = await chairman_queries.get_Scrutineer(message.from_user.id)
                if scrutineer_id == 0:
                    await message.answer('❌Ошибка')
                else:
                    active_compId_chairman = await general_queries.get_CompId(message.from_user.id)
                    active_compId_scrutineer = await general_queries.get_CompId(scrutineer_id)
                    is_active = await general_queries.active_or_not(active_compId_chairman)
                    if is_active == 0:
                        await message.answer('❌Ошибка\nВыбранное соревнование неактивно')
                    elif active_compId_scrutineer == active_compId_chairman:
                        try:
                            if message.from_user.username is None:
                                name = await chairman_queries.get_comment(message.from_user.id)
                            else:
                                name = f'@{message.from_user.username}'

                            await check_list_judges.set_group_counter_for_lin_list(list_counter, message.from_user.id)
                            await message.bot.send_message(scrutineer_id, f"Сообщение от пользователя {name}")
                            await message.bot.send_message(scrutineer_id, text)
                            await message.answer('✅Информация отправлена РСК')
                        except:
                            print('Бот в бане')
                    else:
                        await message.answer('❌Ошибка\nВыбор турниров не согласуется')
            elif res == 0:
                await chairman_queries.set_free_judges(message.from_user.id)
                await message.answer(text)
                await message.answer(msg, reply_markup=chairmans_kb.list_jud_send_kb)

            elif res == 2:
                await message.answer('❌Ошибка')
        else:
            #Находим замены на тех, кого не получилось пробить
            linsets[message.from_user.id][2] = [await chairman_queries.get_similar_lin_judges(i, message.from_user.id)
                                                for i in linsets[message.from_user.id][1]]


            #Никого и близко нет в бд
            if all(i == [] for i in linsets[message.from_user.id][2]):
                await message.answer(
                    f"🤔{', '.join([i[0] + ' ' + i[1] for i in linsets[message.from_user.id][1]])}: не обнаружены в бд. Пожалуйста загрузите дополнительных судей через /judges или отредактируйте сообщение",
                    reply_markup=chairmans_kb.edit_02_kb)
            else:
                bank_for_edit_costyl[message.from_user.id] = [linsets[message.from_user.id][1], linsets[message.from_user.id][2]]
                text = ''
                for i in range(len(linsets[message.from_user.id][1])):
                    if linsets[message.from_user.id][2][i] != []:
                        text += linsets[message.from_user.id][1][i][0] + ' ' + linsets[message.from_user.id][1][i][
                            1] + ' -> ' + linsets[message.from_user.id][2][i][0]['lastName'] + ' ' + \
                                linsets[message.from_user.id][2][i][0]['firstName'] + ' | ' + str(
                            linsets[message.from_user.id][2][i][0]['City']) + '\n'
                a1 = linsets[message.from_user.id][1]
                a2 = linsets[message.from_user.id][2]
                await message.answer(
                    f"🤔{', '.join([a1[i][0] +  ' ' + a1[i][1] for i in range(len(a1)) if a2[i] != []])}: не обнаружены в бд\n\nВариант замены:\n{text}",
                    reply_markup=chairmans_kb.solve_problem_linjudges_kb)


@router.callback_query(F.data == 'edit_02')
async def edit_linset(callback: types.CallbackQuery):
    await Chairman_comm_handler_02.edit_linlist(callback, callback.message.text)
    return


@router.callback_query(F.data == 'send_with_replace')
async def edit_linset(callback: types.CallbackQuery):
    try:
        text = linsets[callback.from_user.id][0]
        # Заменяем всех по шаблону
        active_comp = await general_queries.get_CompId(callback.from_user.id)
        for oldindex in range(len(linsets[callback.from_user.id][1])):
            if linsets[callback.from_user.id][2][oldindex] != []:
                '''
                text = text.replace(
                    linsets[callback.from_user.id][1][oldindex][0] + ' ' + linsets[callback.from_user.id][1][oldindex][
                        1],
                    linsets[callback.from_user.id][2][oldindex][0]['lastName'] + ' ' +
                    linsets[callback.from_user.id][2][oldindex][0]['firstName'])
                '''
                lastname2 = linsets[callback.from_user.id][1][oldindex][0]
                firstname2 = linsets[callback.from_user.id][1][oldindex][1]
                lastname = linsets[callback.from_user.id][2][oldindex][0]['lastName']
                firstname = linsets[callback.from_user.id][2][oldindex][0]['firstName']
                await chairman_queries.add_name2(lastname2, firstname2, lastname, firstname, active_comp)
                text = re.sub(fr'{linsets[callback.from_user.id][1][oldindex][0]}\s+{linsets[callback.from_user.id][1][oldindex][1]}', linsets[callback.from_user.id][2][oldindex][0]['lastName'] + ' ' + linsets[callback.from_user.id][2][oldindex][0]['firstName'] , text)


        linsets[callback.from_user.id][0] = text
        if any(i == [] for i in linsets[callback.from_user.id][2]):
            #problem = f"🤔{', '.join([i[0] + ' ' + i[1] for i in linsets[message.from_user.id][1]])}: не обнаружены в бд. Пожалуйста загрузите дополнительных судей через /judges или отредактируйте сообщение"
            a1 = linsets[callback.from_user.id][1]
            a2 = linsets[callback.from_user.id][2]
            problem = f"🤔{', '.join([a1[i][0] +  ' ' + a1[i][1] for i in range(len(a1)) if a2[i] == []])}: не обнаружены в бд. Пожалуйста загрузите дополнительных судей через /judges или отредактируйте сообщение"
            return await Chairman_comm_handler_02.edit_linlist(callback, problem)

        await callback.message.edit_text(text)
        res, msg, counter_list = await check_list_judges.check_list(text, callback.from_user.id)
        linsets[callback.from_user.id][3] = msg
        linsets[callback.from_user.id].append(counter_list)
        if res == 1:
            await chairman_queries.set_free_judges(callback.from_user.id)
            # Перед отправкой сообщения проверяем, совпадает ли выбор турниров у пары и активно ли соревнование
            scrutineer_id = await chairman_queries.get_Scrutineer(callback.from_user.id)
            if scrutineer_id == 0:
                await callback.message.answer('❌Ошибка')
            else:
                active_compId_chairman = await general_queries.get_CompId(callback.from_user.id)
                active_compId_scrutineer = await general_queries.get_CompId(scrutineer_id)
                is_active = await general_queries.active_or_not(active_compId_chairman)
                if is_active == 0:
                    await callback.message.answer('❌Ошибка\nВыбранное соревнование неактивно')
                elif active_compId_scrutineer == active_compId_chairman:
                    try:
                        #await chairman_queries.set_free_judges(callback.from_user.id)
                        if callback.from_user.username is None:
                            name = await chairman_queries.get_comment(callback.from_user.id)
                        else:
                            name = f'@{callback.from_user.username}'

                        await check_list_judges.set_group_counter_for_lin_list(counter_list, callback.from_user.id)
                        await callback.message.bot.send_message(scrutineer_id, f"Сообщение от пользователя {name}")
                        await callback.message.bot.send_message(scrutineer_id, text)
                        await callback.message.answer('✅Информация отправлена РСК')
                    except:
                        print('Бот в бане')
                else:
                    await callback.message.answer('❌Ошибка\nВыбор турниров не согласуется')
        elif res == 0:
            await chairman_queries.set_free_judges(callback.from_user.id)
            await callback.message.answer(msg, reply_markup=chairmans_kb.list_jud_send_kb)

        elif res == 2:
            await callback.message.answer('❌Ошибка')

    except Exception as e:
        print(e)
        await callback.message.answer('❌Ошибка. Пожалуйста отправьте список еще раз')


#Редактировать бригадный список
@router.callback_query(F.data == 'to_edit_linlist')
async def edit_linset(callback: types.CallbackQuery):
    try:
        problemJudges = []
        if [] in linsets[callback.from_user.id][2]:
            bank_for_edit_costyl[callback.from_user.id][0] = linsets[callback.from_user.id][1]
            bank_for_edit_costyl[callback.from_user.id][1] = linsets[callback.from_user.id][2]

        linsets[callback.from_user.id][1] = [linsets[callback.from_user.id][1][i] for i in range(len(linsets[callback.from_user.id][1])) if linsets[callback.from_user.id][2][i] != []]
        linsets[callback.from_user.id][2] = [i for i in linsets[callback.from_user.id][2] if i != []]
        problemJudges = linsets[callback.from_user.id][1]

        #Отредактировали тех, кого изначально не получилось пробить
        if problemJudges == []:
            linsets[callback.from_user.id][1] = bank_for_edit_costyl[callback.from_user.id][0]
            linsets[callback.from_user.id][2] = bank_for_edit_costyl[callback.from_user.id][1]
            if any(i == [] for i in linsets[callback.from_user.id][2]):
                # problem = f"🤔{', '.join([i[0] + ' ' + i[1] for i in linsets[message.from_user.id][1]])}: не обнаружены в бд. Пожалуйста загрузите дополнительных судей через /judges или отредактируйте сообщение"
                a1 = linsets[callback.from_user.id][1]
                a2 = linsets[callback.from_user.id][2]
                problem = f"🤔{', '.join([a1[i][0] + ' ' + a1[i][1] for i in range(len(a1)) if a2[i] == []])}: не обнаружены в бд. Пожалуйста загрузите дополнительных судей через /judges или отредактируйте сообщение"
                return await Chairman_comm_handler_02.edit_linlist(callback, problem)


            res, msg, counter_list = await check_list_judges.check_list(linsets[callback.from_user.id][0], callback.from_user.id)
            linsets[callback.from_user.id].append(counter_list)
            await chairman_queries.set_free_judges(callback.from_user.id)
            if res == 1:
                # Перед отправкой сообщения проверяем, совпадает ли выбор турниров у пары и активно ли соревнование
                scrutineer_id = await chairman_queries.get_Scrutineer(callback.from_user.id)
                if scrutineer_id == 0:
                    await callback.message.answer('❌Ошибка')
                else:
                    active_compId_chairman = await general_queries.get_CompId(callback.from_user.id)
                    active_compId_scrutineer = await general_queries.get_CompId(scrutineer_id)
                    is_active = await general_queries.active_or_not(active_compId_chairman)
                    if is_active == 0:
                        await callback.message.answer('❌Ошибка\nВыбранное соревнование неактивно')
                    elif active_compId_scrutineer == active_compId_chairman:
                        try:
                            #await chairman_queries.set_free_judges(callback.from_user.id)
                            if callback.from_user.username is None:
                                name = await chairman_queries.get_comment(callback.from_user.id)
                            else:
                                name = f'@{callback.from_user.username}'

                            await check_list_judges.set_group_counter_for_lin_list(linsets[callback.from_user.id][4], callback.from_user.id)
                            await callback.message.bot.send_message(scrutineer_id,
                                                           f"Сообщение от пользователя {name}")
                            await callback.message.bot.send_message(scrutineer_id, linsets[callback.from_user.id][0])
                            await callback.message.delete()
                            await callback.message.answer(linsets[callback.from_user.id][0])
                            await callback.message.answer('✅Информация отправлена РСК')
                        except:
                            print('Бот в бане')
                    else:
                        await callback.message.answer('❌Ошибка\nВыбор турниров не согласуется')
            elif res == 0:
                await callback.message.edit_text(linsets[callback.from_user.id][0])
                linsets[callback.from_user.id][3] = msg
                await callback.message.answer(msg, reply_markup=chairmans_kb.list_jud_send_kb)

            elif res == 2:
                await callback.message.answer('❌Ошибка')
            return

        #Остались проблемные друзья
        current_problem_jud_for_check_lin[callback.from_user.id] = linsets[callback.from_user.id][1].pop(0)
        replace = linsets[callback.from_user.id][2].pop(0)
        list_comp_buttons = []
        for jud in replace:
            list_comp_buttons.append([InlineKeyboardButton(text=jud['lastName'] + ' ' + jud['firstName'] + '|' + str(jud['City']),
                                                           callback_data=f"replin_{jud['bookNumber']}")])

        list_comp_buttons.append([InlineKeyboardButton(text='Отменить редактирование и отправку', callback_data='cancel_edit_linset')])
        markup = InlineKeyboardMarkup(inline_keyboard=list_comp_buttons)
        await callback.message.edit_text(f'{current_problem_jud_for_check_lin[callback.from_user.id][0]} {current_problem_jud_for_check_lin[callback.from_user.id][1]}\nВыберите замену:', reply_markup=markup)
    except Exception as e:
        print(e)
        await callback.message.answer('Во время редактирования возникла ошибка. Пожайлуста отправьте список еще раз')


@router.callback_query(F.data.startswith('replin_'))
async def cmd_start(call: types.CallbackQuery):
    try:
        BookNumber = int(call.data.replace('replin_', ''))
        name = await chairman_queries.booknumber_to_name(BookNumber)
        linsets[call.from_user.id][0] = re.sub(
            fr'{current_problem_jud_for_check_lin[call.from_user.id][0]}\s+{current_problem_jud_for_check_lin[call.from_user.id][1]}',
            name, linsets[call.from_user.id][0])

        if len(name.split()) == 2:
            lastname, firstname = name.split()
        else:
            k = name.split()
            lastname = k[0]
            firstname = ' '.join(k[1::])

        active_comp = await general_queries.get_CompId(call.from_user.id)
        lastname2 = current_problem_jud_for_check_lin[call.from_user.id][0]
        firstname2 = current_problem_jud_for_check_lin[call.from_user.id][1]
        await chairman_queries.add_name2(lastname2, firstname2, lastname, firstname, active_comp)
        #old = current_problem_jud_for_check_lin[call.from_user.id][0] + ' ' + current_problem_jud_for_check_lin[call.from_user.id][1]
        #linsets[call.from_user.id][0] = linsets[call.from_user.id][0].replace(old, name)
        await edit_linset(call)
    except:
        await call.message.answer('Во время редактирования возникла ошибка. Пожалуйста отправьте список еще раз')


@router.callback_query(F.data == 'cancel_edit_linset')
async def cmd_start(call: types.CallbackQuery):
    try:
        linsets.pop(call.from_user.id, None)
        problemjudgesset_for_check_lin.pop(call.from_user.id, None)
        current_problem_jud_for_check_lin.pop(call.from_user.id, None)
        Chairman_comm_handler_02.current_jud_point.pop(call.from_user.id, None)
        Chairman_comm_handler_02.jud_problem_list.pop(call.from_user.id, None)
        Chairman_comm_handler_02.to_index_future.pop(call.from_user.id, None)
        Chairman_comm_handler_02.markup_buttons.pop(call.from_user.id, None)
        bank_for_edit_costyl.pop(call.from_user.id, None)
    except:
        pass
    await call.message.delete()
    await call.message.answer('Действие обработано')


#Подтверждаем отправку списка линейных
@router.callback_query(F.data == 'send_list_anyway')
async def f4(callback: types.CallbackQuery):
    try:
        text = linsets[callback.from_user.id][0]
    except:
        text = 0

    if text != 0:
        scrutineer_id = await chairman_queries.get_Scrutineer(callback.from_user.id)
        if scrutineer_id == 0:
            await callback.message.answer('❌Ошибка')
        else:
            active_compId_chairman = await general_queries.get_CompId(callback.from_user.id)
            active_compId_scrutineer = await general_queries.get_CompId(scrutineer_id)
            is_active = await general_queries.active_or_not(active_compId_chairman)
            if is_active == 0:
                await callback.message.answer('❌Ошибка\nВыбранное соревнование неактивно')

            elif active_compId_scrutineer == active_compId_chairman:
                try:
                    #r = await chairman_queries.set_free_judges(callback.from_user.id)
                    r = 1
                    if r == 1:
                        if callback.from_user.username is None:
                            name = await chairman_queries.get_comment(callback.from_user.id)
                        else:
                            name = f'@{callback.from_user.username}'

                        await check_list_judges.set_group_counter_for_lin_list(linsets[callback.from_user.id][4], callback.from_user.id)
                        await callback.message.bot.send_message(scrutineer_id, f"Сообщение от пользователя {name}")
                        await callback.message.bot.send_message(scrutineer_id, text)
                        await callback.message.bot.send_message(scrutineer_id, linsets[callback.from_user.id][3])
                        await callback.message.delete()
                        await callback.message.answer('✅Информация отправлена РСК')
                    else:
                        await callback.message.answer('❌Ошибка. Пожалуйста отправьте список еще раз')
                except Exception as e:
                    print(e)
                    await callback.message.answer('❌Ошибка. Пожалуйста отправьте список еще раз')
            else:
                await callback.message.answer('❌Ошибка\nВыбор турниров не согласуется')

    else:
        await callback.message.answer('❌Ошибка, отправьте список еще раз')


#Показать свободных судей
@router.callback_query(F.data == 'show_free_judges')
async def f4(callback: types.CallbackQuery):
    try:
        a = await chairman_queries.get_free_judges(callback.from_user.id)
        if a == 0:
            await callback.message.answer('❌Ошибка, отправьте список еще раз')
        else:
            await callback.message.edit_text(callback.message.text + f'\n\n<b>Свободные судьи:</b> {a}', reply_markup=chairmans_kb.list_jud_send_kb, parse_mode='html')
    except Exception as e:
        print(e)
        await callback.message.answer('❌Ошибка, отправьте список еще раз')


#Формирования списка по номерам групп
class Is_Group_List(Filter):
    def __init__(self, my_text: str) -> None:
        self.my_text = my_text
    async def __call__(self, message: Message) -> bool:
        if message.text is None:
            return False
        text = message.text.split()
        text = [i.strip('\n').strip('.').isdigit() for i in text]
        return all(i == 1 for i in text)

from handlers import start_stage_handler
from keyboards import scrutineer_kb
@router.message(Is_Group_List(F.text))
async def handle_text_message(message: types.Message):
    try:
        group_list = [int(i.strip('\n').strip('.')) for i in message.text.split()]

        active_comp = await general_queries.get_CompId(message.from_user.id)
        regionId = await chairman_queries.get_regionId(active_comp)

        if active_comp is None:
            return await message.answer('❌Ошибка. Необходимо задать активный турнир')

        data = {'compId': active_comp, "regionId": regionId, "status": 12, "groupList": group_list}
        ans, json = await generation_logic.get_ans(data)

        id_to_group = await generation_logic.unpac_json(json)
        judges = await generation_logic.get_judges_list(json)
        #print(judges, "Генерация")
        #ans[i] = [key, 'l', json[key]['lin_id']]

        generation_results[message.from_user.id] = {'ans': ans, 'json': json, 'compId': active_comp, 'id_to_group': id_to_group, 'judges': judges}
        chairmans_groups_lists[message.from_user.id] = {'compId': active_comp, 'json': json, 'name': ''}

        markup = await chairmans_kb.get_generation_kb(active_comp)
        if markup == -1:
            return message.answer('❌Ошибка')

        #print(list(judges.keys()), "Генерация")
        #print(judges)
        #print()
        await message.answer(ans, reply_markup=markup, parse_mode='html')
    except Exception as e:
        print(e)
        await message.answer('❌Ошибка')


@router.callback_query(F.data == 'regenerate_list')
async def f4(callback: types.CallbackQuery):
    try:
        active_comp = chairmans_groups_lists[callback.from_user.id]['compId']
        group_list = chairmans_groups_lists[callback.from_user.id]['json'].keys()

        if active_comp is None:
            return await callback.answer('❌Ошибка. Необходимо задать активный турнир')

        data = {'compId': active_comp, "regionId": 78, "status": 12, "groupList": group_list}
        ans, json = await generation_logic.get_ans(data)
        id_to_group = await generation_logic.unpac_json(json)
        judges = await generation_logic.get_judges_list(json)

        generation_results[callback.from_user.id] = {'ans': ans, 'json': json, 'compId': active_comp, 'id_to_group': id_to_group, 'judges': judges}
        chairmans_groups_lists[callback.from_user.id] = {'compId': active_comp, 'json': json, 'name': '', 'groupNumber': -1}


        markup = await chairmans_kb.get_generation_kb(active_comp)
        if markup == -1:
            return callback.message.answer('❌Ошибка')

        await callback.message.edit_text(ans, reply_markup=markup, parse_mode='html')
    except Exception as e:
        print(e)
        await callback.answer('❌Изменения не обнаружены')


@router.callback_query(F.data == 'end_generation_proces')
async def f4(callback: types.CallbackQuery):
    await callback.message.delete_reply_markup()
    await callback.message.answer('Генерация завершена')


@router.callback_query(F.data == 'send_generate_rsk')
async def f4(callback: types.CallbackQuery):
    scrutineer_id = await chairman_queries.get_Scrutineer(callback.from_user.id)
    if scrutineer_id == 0:
        await callback.message.answer('❌Ошибка')
    else:
        active_compId_chairman = await general_queries.get_CompId(callback.from_user.id)
        active_compId_scrutineer = await general_queries.get_CompId(scrutineer_id)
        is_active = await general_queries.active_or_not(active_compId_chairman)
        if is_active == 0:
            await callback.message.answer('❌Ошибка\nВыбранное соревнование неактивно')

        elif active_compId_scrutineer == active_compId_chairman:
            try:
                r = 1
                if r == 1:
                    if callback.from_user.username is None:
                        name = await chairman_queries.get_comment(callback.from_user.id)
                    else:
                        name = f'@{callback.from_user.username}'

                    await callback.message.bot.send_message(scrutineer_id, f"Сообщение от пользователя {name}")
                    await callback.message.bot.send_message(scrutineer_id, f"<code>{callback.message.text}</code>", parse_mode='html')
                    await callback.message.delete_reply_markup()
                    await chairman_queries.set_group_counter(generation_results[callback.from_user.id]['judges'], generation_results[callback.from_user.id]['compId'])
                    await callback.message.answer('✅Информация отправлена РСК')
                else:
                    await callback.message.answer('❌Ошибка. Пожалуйста отправьте список еще раз')
            except Exception as e:
                print(e)
                await callback.message.answer('❌Ошибка. Пожалуйста отправьте список еще раз')
        else:
            await callback.message.answer('❌Ошибка\nВыбор турниров не согласуется')


@router.callback_query(F.data == 'save_result')
async def f4(callback: types.CallbackQuery):
    await callback.message.delete_reply_markup()
    await chairman_queries.set_group_counter(generation_results[callback.from_user.id]['judges'], generation_results[callback.from_user.id]['compId'])
    await callback.message.answer('Результат сохранен')


@router.callback_query(F.data == 'edit_generation_result')
async def f4(callback: types.CallbackQuery):
    markup = await chairmans_kb.get_gen_edit_markup(generation_results[callback.from_user.id])
    await callback.message.edit_reply_markup(reply_markup=markup)


@router.callback_query(F.data == 'back_to_generation')
async def f4(callback: types.CallbackQuery):
    compid = await general_queries.get_CompId(callback.from_user.id)
    markup = await chairmans_kb.get_generation_kb(compid)
    text = generation_results[callback.from_user.id]['ans']
    await callback.message.edit_text(text=text, reply_markup=markup, parse_mode='html')


@router.callback_query(F.data.startswith('gen_choise_jud_01_'))
async def cmd_start(call: types.CallbackQuery):
    judgeType, group, judgeId = call.data.replace('gen_choise_jud_01_', '').split('_')
    groupType = await chairman_queries.get_group_type(generation_results[call.from_user.id]['compId'], int(group))
    chairmans_groups_lists[call.from_user.id]['groupNumber'] = group

    n = await chairman_queries.ids_to_names([judgeId], generation_results[call.from_user.id]['compId'])
    i = n.split()
    if len(i) == 2:
        lastname, firstname = i
    else:
        lastname = i[0]
        firstname = ' '.join(i[1::])

    chairmans_groups_lists[call.from_user.id]['name'] = [lastname + ' ' + firstname, judgeId]
    judges = generation_results[call.from_user.id]['judges']
    compId = generation_results[call.from_user.id]['compId']
    json = generation_results[call.from_user.id]['json']

    markup = await chairmans_kb.edit_gen_judegs_markup(groupType, int(judgeId), judges, compId, json)
    await call.message.edit_text('👨‍⚖️' + lastname + ' ' + firstname + "\n" + "\n" + "Выберите судью для замены:",
                                 reply_markup=markup)


@router.callback_query(F.data.startswith('gen_choise_jud_02_'))
async def cmd_start(call: types.CallbackQuery):
    judgeid = call.data.replace('gen_choise_jud_02_', '')
    n = await chairman_queries.ids_to_names([judgeid], generation_results[call.from_user.id]['compId'])
    i = n.split()

    if len(i) == 2:
        lastname, firstname = i
    else:
        lastname = i[0]
        firstname = ' '.join(i[1::])

    text = generation_results[call.from_user.id]['ans'].replace(chairmans_groups_lists[call.from_user.id]['name'][0], lastname + ' ' + firstname)
    generation_results[call.from_user.id]['ans'] = text

    oldId = int(chairmans_groups_lists[call.from_user.id]['name'][1])
    oldJud = generation_results[call.from_user.id]['judges'][oldId]
    newId = int(judgeid)

    generation_results[call.from_user.id]['judges'][newId] = oldJud

    generation_results[call.from_user.id]['judges'][newId][2].remove(oldId)
    generation_results[call.from_user.id]['judges'][newId][2].append(newId)
    del generation_results[call.from_user.id]['judges'][oldId]

    #print(list(generation_results[call.from_user.id]['judges'].keys()), "После редактирования")
    #print(generation_results[call.from_user.id]['judges'])
    compid = generation_results[call.from_user.id]['compId']
    markup = await chairmans_kb.get_generation_kb(compid)


    await call.message.edit_text(text=text, reply_markup=markup, parse_mode='html')


#Обработка сообщений между scrutineer и chairman
@router.message()
async def f3(message: Message):
    user_status = await get_user_status_query.get_user_status(message.from_user.id)
    if user_status == 3:
        scrutineer_id = await chairman_queries.get_Scrutineer(message.from_user.id)
        if scrutineer_id == 0:
            await message.answer('❌Ошибка')
        else:
            active_compId_chairman = await general_queries.get_CompId(message.from_user.id)
            active_compId_scrutineer = await general_queries.get_CompId(scrutineer_id)
            is_active = await general_queries.active_or_not(active_compId_chairman)
            if is_active == 0:
                await message.answer('❌Ошибка\nВыбранное соревнование неактивно')
            elif active_compId_scrutineer == active_compId_chairman:
                try:
                    await message.bot.forward_message(scrutineer_id, message.chat.id, message.message_id)
                except:
                    print('Бот в бане')
            else:
                await message.answer('❌Ошибка\nВыбор турниров не согласуется')

    if user_status == 2:
        chairman_id = await scrutineer_queries.get_Chairman(message.from_user.id)
        if chairman_id == 0:
            await message.answer('❌Ошибка')
        else:
            active_compId_scrutineer = await general_queries.get_CompId(message.from_user.id)
            active_compId_chairman = await general_queries.get_CompId(chairman_id)
            is_active = await general_queries.active_or_not(active_compId_scrutineer)
            if is_active == 0:
                await message.answer('❌Ошибка\nВыбранное соревнование неактивно')
            elif active_compId_scrutineer == active_compId_chairman:
                try:
                    await message.bot.forward_message(chairman_id, message.chat.id, message.message_id)
                except:
                    print('Бот в бане')
            else:
                await message.answer('❌Ошибка\nВыбор турниров не согласуется')
