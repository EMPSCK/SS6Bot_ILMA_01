from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
from queries import chairman_queries
import pymysql
import config
from chairman_moves import generation_logic

async def gen_list_comp(tg_id):
    list_comp_buttons = []

    competitions = await chairman_queries.get_list_comp(tg_id)
    for comp in competitions:
        b = InlineKeyboardButton(text=comp['compName'], callback_data=f"comp_{comp['compId']}")
        list_comp_buttons.append([b])
    list_comp_buttons.append([InlineKeyboardButton(text='Вернуться к меню', callback_data='back_to_chairman_menu')])

    return InlineKeyboardMarkup(inline_keyboard=list_comp_buttons)

confirm_choice_button = InlineKeyboardButton(text='Да', callback_data=f"confirm_choice")
confirm_choice_button1 = InlineKeyboardButton(text='Нет', callback_data=f"confirm_choice_back")
confirm_choice_kb = load_judges_kb = InlineKeyboardMarkup(inline_keyboard=[[confirm_choice_button, confirm_choice_button1]])

cancel_button = [InlineKeyboardButton(text="Завершить загрузку списка", callback_data='cancel_load')]
load_judges_kb = InlineKeyboardMarkup(inline_keyboard=[cancel_button])

edit_problem_judges_info = [InlineKeyboardButton(text="Редактировать информацию", callback_data='edit_problem_judges_info')]
judges_problem_kb = InlineKeyboardMarkup(inline_keyboard=[cancel_button, edit_problem_judges_info])

take_as_is = [InlineKeyboardButton(text="Отправить как есть", callback_data='take_as_is')]
enter_book_number = [InlineKeyboardButton(text="Ввести номер книжки", callback_data='enter_book_number')]
search_for_db = [InlineKeyboardButton(text="Поиск по общей бд", callback_data='search_for_db')]
do_gap = [InlineKeyboardButton(text="Удалить", callback_data='do_gap')]
choose_problem_jud_action_kb  = InlineKeyboardMarkup(inline_keyboard=[take_as_is, enter_book_number, search_for_db, do_gap, cancel_button])

take_as_is_1 = [InlineKeyboardButton(text="Отправить как есть", callback_data='take_as_is_1')]
take_as_is_2 = [InlineKeyboardButton(text="Действующая спорт категория", callback_data='real_sport_category')]
choose_problem_jud_action_kb_1 = InlineKeyboardMarkup(inline_keyboard=[take_as_is_2, take_as_is_1,do_gap ,cancel_button])

async def gen_similar_judges(jud):
    list_comp_buttons = []

    judges = await chairman_queries.get_similar_judges(jud)
    for jud in judges:
        list_comp_buttons.append([InlineKeyboardButton(text=jud['LastName'] + ' ' +  jud['FirstName'] + ' | ' + jud['City'], callback_data=f"jud_{jud['BookNumber']}")])
    list_comp_buttons.append([InlineKeyboardButton(text='Назад', callback_data='back_to_edit_jud')])
    return InlineKeyboardMarkup(inline_keyboard=list_comp_buttons)

book_number_button = [InlineKeyboardButton(text='Назад', callback_data='back_to_edit_jud')]
book_number_kb = InlineKeyboardMarkup(inline_keyboard=[book_number_button])


menu_button = [InlineKeyboardButton(text='Задать активное соревнование', callback_data='set_active_competition')]
menu_button_01 = [InlineKeyboardButton(text='Ввести код', callback_data='enter_chairaman_pin')]
menu_button_02 = [InlineKeyboardButton(text='Редактировать параметры групп', callback_data='group_edit')]
menu_kb = InlineKeyboardMarkup(inline_keyboard=[menu_button, menu_button_02, menu_button_01])

back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Вернуться к меню', callback_data='back_b')]])

list_jud_send_b1 = [InlineKeyboardButton(text='Подтвердить отправку', callback_data='send_list_anyway')]
list_jud_send_b2 = [InlineKeyboardButton(text='показать свободных судей', callback_data='show_free_judges')]
list_jud_send_kb = InlineKeyboardMarkup(inline_keyboard=[list_jud_send_b1, list_jud_send_b2])


to_edit_linlist = [InlineKeyboardButton(text="Редактировать по элементам", callback_data='to_edit_linlist')]
send_with_replace = [InlineKeyboardButton(text="Заменить", callback_data='send_with_replace')]
solve_problem_linjudges_kb = InlineKeyboardMarkup(inline_keyboard=[to_edit_linlist, send_with_replace])


send_id_to_admin_b = [InlineKeyboardButton(text="Отправить данные администратору", callback_data='send_id_to_admin')]
send_id_to_admin_kb = InlineKeyboardMarkup(inline_keyboard=[send_id_to_admin_b])

update_status_b = [InlineKeyboardButton(text="Обновить статус", callback_data='update_status')]
update_status_b_1 = [InlineKeyboardButton(text="Написать администратору", url='https://t.me/mitkrivich')]
update_status_kb = InlineKeyboardMarkup(inline_keyboard=[update_status_b, update_status_b_1])

edit_02_b = [InlineKeyboardButton(text="Редактировать", callback_data='edit_02')]
edit_02_kb = InlineKeyboardMarkup(inline_keyboard=[edit_02_b])


async def get_markup_EV(user_id, text):

    judges_replace = await chairman_queries.get_free_judges_for_wrong(user_id, text)
    if judges_replace == 'свободных судей нет':
        return 0

    sim_jud_buttons = []
    sjb5 = []
    for jud_rep in range(len(judges_replace)):
        i = jud_rep
        jud_rep = judges_replace[jud_rep]
        if jud_rep['City'] is None:
            k = 'не установлено'
        else:
            k = jud_rep['City']

        sjb5.append(InlineKeyboardButton(
            text=jud_rep['lastName'] + ' ' + jud_rep['firstName'] + ' | ' + k,
            callback_data=f"01jud_rep_{jud_rep['bookNumber']}_{jud_rep['lastName']}_{jud_rep['firstName']}"))

        if len(sjb5) % 2 == 0 or i == len(judges_replace) - 1:
            sim_jud_buttons.append(sjb5)
            sjb5 = []

    sim_jud_buttons.append(
        [InlineKeyboardButton(text='Завершить и отменить редактирование', callback_data='end_edit_02')])
    return sim_jud_buttons


generation_button_01 = InlineKeyboardButton(text="Отправить РСК", callback_data='send_generate_rsk')
generation_button_02 = InlineKeyboardButton(text="Перегенерировать", callback_data='regenerate_list')
generation_button_03 = [InlineKeyboardButton(text="Выйти из режима генерации", callback_data='end_generation_proces')]
generation_kb = InlineKeyboardMarkup(inline_keyboard=[[generation_button_01, generation_button_02], generation_button_03])

async def get_generation_kb(active_comp):
    mode = await chairman_queries.get_generation_mode(active_comp)
    if mode == 0:
        generation_button_01 = InlineKeyboardButton(text="Отправить РСК", callback_data='send_generate_rsk')
        generation_button_02 = InlineKeyboardButton(text="Перегенерировать", callback_data='regenerate_list')
        generation_button_03 = InlineKeyboardButton(text="Выйти из режима генерации", callback_data='end_generation_proces')
        generation_button_04 = InlineKeyboardButton(text="Редактировать", callback_data='edit_generation_result')
        generation_kb = InlineKeyboardMarkup(inline_keyboard=[[generation_button_01, generation_button_02], [generation_button_04, generation_button_03]])
        return generation_kb
    elif mode == 1:
        generation_button_01 = InlineKeyboardButton(text="Сохранить результат", callback_data='save_result')
        generation_button_02 = InlineKeyboardButton(text="Перегенерировать", callback_data='regenerate_list')
        generation_button_03 = InlineKeyboardButton(text="Выйти из режима генерации", callback_data='end_generation_proces')
        generation_button_04 = InlineKeyboardButton(text="Редактировать", callback_data='edit_generation_result')
        generation_kb = InlineKeyboardMarkup(inline_keyboard=[[generation_button_01, generation_button_02], [generation_button_04, generation_button_03]])
        return generation_kb

    elif mode == -1:
        return -1

async def get_gen_edit_markup(json):
    try:
        judges = json['judges']
        compid = json['compId']
        buttons = []
        but2 = []

        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn:
            cur = conn.cursor()
            for i in judges:
                cur.execute(f"SELECT firstName, lastName FROM competition_judges WHERE compId = {compid} and id = {i}")
                ans = cur.fetchone()


                group = judges[i][0]
                but2.append(InlineKeyboardButton(text=ans['lastName'] + ' ' + ans['firstName'], callback_data=f"gen_choise_jud_01_{judges[i][1]}_{group}_{i}"))
                if len(but2) == 2:
                    buttons.append(but2)
                    but2 = []



        if len(but2) == 0:
            b = [InlineKeyboardButton(text='Назад', callback_data=f"back_to_generation")]
            buttons.append(b)
        else:
            but2.append(InlineKeyboardButton(text='Назад', callback_data=f"back_to_generation"))
            buttons.append(but2)

        return InlineKeyboardMarkup(inline_keyboard=buttons)
    except Exception as e:
        print(e)

from chairman_moves import generation_logic
async def edit_gen_judegs_markup(groupType, judgeId, judges, compId, json):
    try:
        buttons = []
        but2 = []
        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn:
            cur = conn.cursor()
            if judges[judgeId][1] == 'l':
                cur.execute(f"SELECT firstName, lastName, id, DSFARR_Category_Id, SPORT_CategoryDate, SPORT_CategoryDateConfirm, SPORT_Category, RegionId, workCode from competition_judges WHERE compId = {compId} and active = 1 and workCode <> 3 ")
                all_judges = cur.fetchall()
                if len(all_judges) == 0:
                    but2.append(InlineKeyboardButton(text='Назад', callback_data=f"back_to_generation"))
                    buttons.append(but2)
                    return InlineKeyboardMarkup(inline_keyboard=buttons)

                all_judges = await generation_logic.same_judges_filter(all_judges, list(judges.keys()))
                all_judges = await generation_logic.interdiction_filter(compId, judges[judgeId][0], all_judges)

                pull = json[judges[judgeId][0]]['lin_id'] + json[judges[judgeId][0]]['zgs_id']

                pull.remove(judgeId)
                all_judges = await generation_logic.relatives_filter(compId, all_judges, pull)

                minCategoryId = await chairman_queries.get_min_catId(compId, judges[judgeId][0])
                all_judges = await generation_logic.category_filter(all_judges, minCategoryId, compId, groupType, 'l')


                lin_neibors_list = judges[judgeId][2].copy()
                lin_neibors_list.remove(judgeId)
                lin_neibors_clubs_list = await chairman_queries.get_lin_neibors_clubs(lin_neibors_list)
                all_judges = await generation_logic.distinct_clubs_filter(lin_neibors_clubs_list, all_judges)
                all_judges = await generation_logic.interdiction_filter(compId, judges[judgeId][0], all_judges)


                if groupType == 0:
                    pull = judges[judgeId][2]
                    pull.remove(judgeId)
                    info = await generation_logic.rc_a_region_rules(0, len(pull) + 1)
                    compRegionId = await chairman_queries.get_region_id(compId)
                    if compRegionId != 0:
                        regions, code = await chairman_queries.get_judges_regions(pull, compRegionId)
                        if code == 1:
                            all_judges = await generation_logic.regions_change_filter(all_judges, info, regions, compRegionId)





            if judges[judgeId][1] == 'z':
                cur.execute(f"SELECT firstName, lastName, id, DSFARR_Category_Id, SPORT_CategoryDate, SPORT_CategoryDateConfirm, SPORT_Category, workCode from competition_judges WHERE compId = {compId} and active = 1 and workCode = 1")
                all_judges = cur.fetchall()
                if len(all_judges) == 0:
                    but2.append(InlineKeyboardButton(text='Назад', callback_data=f"back_to_generation"))
                    buttons.append(but2)
                    return InlineKeyboardMarkup(inline_keyboard=buttons)

                all_judges = await generation_logic.same_judges_filter(all_judges, list(judges.keys()))
                all_judges = await generation_logic.interdiction_filter(compId, judges[judgeId][0], all_judges)
                zgs_neibors_list = judges[judgeId][2].copy()
                zgs_neibors_list.remove(judgeId)
                zgs_neibors_clubs_list = await chairman_queries.get_lin_neibors_clubs(zgs_neibors_list)

                all_judges = await generation_logic.distinct_clubs_filter(zgs_neibors_clubs_list, all_judges)

                minCategoryId = await chairman_queries.get_min_catId(compId, judges[judgeId][0])
                all_judges = await generation_logic.category_filter(all_judges, minCategoryId, compId, groupType, 'z')


                pull = json[judges[judgeId][0]]['lin_id'] + json[judges[judgeId][0]]['zgs_id']
                pull.remove(judgeId)
                all_judges = await generation_logic.relatives_filter(compId, all_judges, pull)


            for j in range(len(all_judges)):
                if all_judges[j]["workCode"] == 1:
                    lastName = all_judges[j]["lastName"]
                    firstName = all_judges[j]["firstName"] + ' (Згс)'
                elif all_judges[j]["workCode"] == 2:
                    lastName = all_judges[j]["lastName"]
                    firstName = all_judges[j]["firstName"] + ' (Гс)'
                else:
                    lastName = all_judges[j]["lastName"]
                    firstName = all_judges[j]["firstName"]

                but2.append(InlineKeyboardButton(text=f'{lastName} {firstName}',
                                                 callback_data=f'gen_choise_jud_02_{all_judges[j]["id"]}'))
                if j % 2 != 0:
                    buttons.append(but2)
                    but2 = []

            if len(but2) == 0:
                b = [InlineKeyboardButton(text='Назад', callback_data=f"back_to_generation")]
                buttons.append(b)
            else:
                but2.append(InlineKeyboardButton(text='Назад', callback_data=f"back_to_generation"))
                buttons.append(but2)

        return InlineKeyboardMarkup(inline_keyboard=buttons)
    except Exception as e:
        print(e)


async def edit_gen_judegs_markup_01(groupType, judgeId, judges, compId, json):
    try:
        buttons = []
        but2 = []
        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn:
            cur = conn.cursor()
            if judges[judgeId][1] == 'l':
                cur.execute(f"SELECT firstName, lastName, id, DSFARR_Category_Id, SPORT_CategoryDate, SPORT_CategoryDateConfirm, SPORT_Category from competition_judges WHERE compId = {compId} and active = 1 and workCode = 0")
                all_judges = cur.fetchall()
                if len(all_judges) == 0:
                    but2.append(InlineKeyboardButton(text='Назад', callback_data=f"back_to_generation"))
                    buttons.append(but2)
                    return InlineKeyboardMarkup(inline_keyboard=buttons)

                all_judges = await generation_logic.same_judges_filter(all_judges, list(judges.keys()))
                all_judges = await generation_logic.interdiction_filter(compId, judges[judgeId][0], all_judges)
                pull = json[judges[judgeId][0]]['lin_id'] + json[judges[judgeId][0]]['zgs_id']
                pull.remove(judgeId)
                all_judges = await generation_logic.relatives_filter(compId, all_judges, pull)


                minCategoryId = await chairman_queries.get_min_catId(compId, judges[judgeId][0])
                all_judges = await generation_logic.category_filter(all_judges, minCategoryId, compId, groupType, 'l')


                lin_neibors_list = judges[judgeId][2].copy()
                lin_neibors_list.remove(judgeId)
                lin_neibors_clubs_list = await chairman_queries.get_lin_neibors_clubs(lin_neibors_list)
                all_judges = await generation_logic.distinct_clubs_filter(lin_neibors_clubs_list, all_judges)
                all_judges = await generation_logic.interdiction_filter(compId, judges[judgeId][0], all_judges)


            if judges[judgeId][1] == 'z':
                cur.execute(f"SELECT firstName, lastName, id, DSFARR_Category_Id, SPORT_CategoryDate, SPORT_CategoryDateConfirm, SPORT_Category from competition_judges WHERE compId = {compId} and active = 1 and workCode = 1")
                all_judges = cur.fetchall()
                if len(all_judges) == 0:
                    but2.append(InlineKeyboardButton(text='Назад', callback_data=f"back_to_generation"))
                    buttons.append(but2)
                    return InlineKeyboardMarkup(inline_keyboard=buttons)

                all_judges = await generation_logic.same_judges_filter(all_judges, list(judges.keys()))
                all_judges = await generation_logic.interdiction_filter(compId, judges[judgeId][0], all_judges)
                zgs_neibors_list = judges[judgeId][2].copy()
                zgs_neibors_list.remove(judgeId)
                zgs_neibors_clubs_list = await chairman_queries.get_lin_neibors_clubs(zgs_neibors_list)

                all_judges = await generation_logic.distinct_clubs_filter(zgs_neibors_clubs_list, all_judges)

                minCategoryId = await chairman_queries.get_min_catId(compId, judges[judgeId][0])
                all_judges = await generation_logic.category_filter(all_judges, minCategoryId, compId, groupType, 'z')


                pull = json[judges[judgeId][0]]['lin_id'] + json[judges[judgeId][0]]['zgs_id']
                pull.remove(judgeId)
                all_judges = await generation_logic.relatives_filter(compId, all_judges, pull)


            for j in range(len(all_judges)):
                but2.append(InlineKeyboardButton(text=f'{all_judges[j]["lastName"]} {all_judges[j]["firstName"]}',
                                                 callback_data=f'gen_choise_jud_02_{all_judges[j]["id"]}'))
                if j % 2 != 0:
                    buttons.append(but2)
                    but2 = []

            if len(but2) == 0:
                b = [InlineKeyboardButton(text='Назад', callback_data=f"back_to_generation")]
                buttons.append(b)
            else:
                but2.append(InlineKeyboardButton(text='Назад', callback_data=f"back_to_generation"))
                buttons.append(but2)

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    except Exception as e:
        print(e)


generation_zgs_button_01 = InlineKeyboardButton(text="Сохранить", callback_data='save_zgs_result')
generation_zgs_button_02 = InlineKeyboardButton(text="Перегенерировать", callback_data='regenerate_zgs')
generation_zgs_button_03 = InlineKeyboardButton(text="Редактировать", callback_data='edit_zgs')
generation_zgs_button_04 = InlineKeyboardButton(text="Выйти из режима генерации", callback_data='end_zgs_generation_proces')
generation_zgs_kb = InlineKeyboardMarkup(inline_keyboard=[[generation_zgs_button_01, generation_zgs_button_02], [generation_zgs_button_03, generation_zgs_button_04]])


async def get_gen_zgs_edit_markup_01(json):
    try:
        judges = json['judges']
        buttons = []
        but2 = []

        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn:
            cur = conn.cursor()
            for ans in judges:
                but2.append(InlineKeyboardButton(text=judges[ans]['lastName'] + ' ' + judges[ans]['firstName'], callback_data=f"zgs_generation_{ans}"))
                if len(but2) == 2:
                    buttons.append(but2)
                    but2 = []


        if len(but2) == 0:
            b = [InlineKeyboardButton(text='Назад', callback_data=f"back_to_zgs_generation")]
            buttons.append(b)
        else:
            but2.append(InlineKeyboardButton(text='Назад', callback_data=f"back_to_zgs_generation"))
            buttons.append(but2)

        return InlineKeyboardMarkup(inline_keyboard=buttons)
    except Exception as e:
        print(e)

from chairman_moves import  generation_logic
async def get_gen_zgs_edit_markup_02(json, compId):
    try:
        buttons = []
        but2 = []
        judges = json['judges']
        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )


        with conn:
            cur = conn.cursor()
            cur.execute(f"SELECT firstName, lastName, id, DSFARR_Category_Id, SPORT_CategoryDate, SPORT_CategoryDateConfirm, SPORT_Category from competition_judges WHERE compId = {compId} and active = 1 and workCode = 0")
            all_judges = cur.fetchall()
            all_judges = await same_zgs_fiter(all_judges, judges)
            cur.execute(f"select generation_zgs_mode from competition where compId = {compId}")
            generation_zgs_mode = cur.fetchone()
            generation_zgs_mode = generation_zgs_mode['generation_zgs_mode']

            if generation_zgs_mode == 1:
                all_judges = await generation_logic.generation_zgs_cat_filter(all_judges, compId)

            for j in range(len(all_judges)):
                but2.append(InlineKeyboardButton(text=f'{all_judges[j]["lastName"]} {all_judges[j]["firstName"]}',
                                                 callback_data=f'zgs_02_generation_{all_judges[j]["id"]}'))
                if j % 2 != 0:
                    buttons.append(but2)
                    but2 = []

            if len(but2) == 0:
                b = [InlineKeyboardButton(text='Назад', callback_data=f"back_to_zgs_generation")]
                buttons.append(b)
            else:
                but2.append(InlineKeyboardButton(text='Назад', callback_data=f"back_to_zgs_generation"))
                buttons.append(but2)

        return InlineKeyboardMarkup(inline_keyboard=buttons)



    except Exception as e:
        print(e)


async def same_zgs_fiter(all_judges, judges):
    all_judges_01 = all_judges.copy()
    for i in all_judges:
        if i['id'] in judges:
            all_judges_01.remove(i)
    return all_judges_01


async def get_edit_group_kb(user_id, compId):
    try:
        buttons = []
        but2 = []
        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn:
            cur = conn.cursor()
            cur.execute(f"select groupNumber, groupName from competition_group where compId = {compId}")
            group_list = cur.fetchall()
            for j in range(len(group_list)):
                but2.append(InlineKeyboardButton(text=f'{group_list[j]["groupNumber"]}. {group_list[j]["groupName"]}',
                                                 callback_data=f'group_edit_01_{compId}_{group_list[j]["groupNumber"]}'))
                if j % 2 != 0:
                    buttons.append(but2)
                    but2 = []

            if len(but2) == 0:
                b = [InlineKeyboardButton(text='Назад', callback_data=f"back_b")]
                buttons.append(b)
            else:
                but2.append(InlineKeyboardButton(text='Назад', callback_data=f"back_b "))
                buttons.append(but2)

            return InlineKeyboardMarkup(inline_keyboard=buttons)
    except Exception as e:
        print(e)


edit_group_b1 = InlineKeyboardButton(text="Минимальная категория", callback_data='min_group_cat')
edit_group_b2 = InlineKeyboardButton(text="Число линейных", callback_data='num_of_lin')
edit_group_b3 = InlineKeyboardButton(text="Число згс", callback_data='num_of_zgs')
edit_group_b4 = InlineKeyboardButton(text="Тип группы", callback_data='type_of_group')
edit_group_b5 = InlineKeyboardButton(text="Назад", callback_data='back_b')
edit_group_kb = InlineKeyboardMarkup(inline_keyboard=[[edit_group_b1, edit_group_b4], [edit_group_b2, edit_group_b3], [edit_group_b5]])
