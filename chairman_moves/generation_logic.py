import random
import json
import config
import pymysql


async def get_ans(data):
    json_end = dict()
    json_export = dict()
    group_list = []

    group_list_raw = data['groupList']
    for group_id_inp in group_list_raw:
        r = await get_group_params(data['compId'], group_id_inp)

        #Не нашли группу
        if r == "undefinedGroup":
            json_end['group_number'] = group_id_inp
            json_end['status'] = "fail"
            json_end['msg'] = 'группа не была обнаружена'
            json_end['judge_id'] = []
            json_export[group_id_inp] = json_end
        else:
            group_list.append(r)

    #Все группы не пробились
    if group_list == []:
        ans = await json_to_message(json_export, data)
        return ans, json_export

    judge_counter_list = await get_future_tables()
    relatives_list = await get_relative_list(data['compId'])
    black_list = await get_black_list(data['compId'])


    comp_region_id = data['regionId']
    relatives_dict = await relatives_list_change(relatives_list)

    # 1. сортировка входящего списка групп в зависимости от требуемой для судейства категории

    group_list.sort(key=lambda x: x[2] * -1)

    # 2. запрашиваем и обрабатываем список судей
    ans = await get_all_judges_yana(data['compId'])
    #print(relatives_list)
    #print(black_list)
    #print()
    #for i in ans:
    #    print(i)

    all_judges_list = {}  # преобразуем словарь для более удобной работы, создаем общий список доступных для выбора судей с параметрами

    for i in ans:
        i['SPORT_Category_decoded'] = i['DSFARR_Category_Id'] #await decode_category(i['SPORT_Category'])
        all_judges_list[i['id']] = i

    all_judges_list = dict(sorted(all_judges_list.items(), key=lambda item: item[1]['group_counter']))
    all_zgs_list = await judges_zgs_filter(all_judges_list)  # доступные згс из базы



    #ГЕНЕРАЦИЯ ЗГС

    all_groups_finish_jud = []
    sucess_result_zgs = 0
    sucess_result = 0
    final_status = 0

    for i in group_list:
        group_number = i[0]
        json_end = dict()

        if final_status == 1:
            group_all_judges_list = all_judges_list.copy()
            for j in group_finish_judges_list:
                all_groups_finish_jud.append(j)
            for x in zgs_end_list:
                all_groups_finish_jud.append(x)
                zgs_list_generation.pop(x, None)
            for jj in all_groups_finish_jud:
                group_all_judges_list.pop(jj, None)
            group_finish_judges_list = []
            zgs_end_list = []
            regions = {}
        else:
            group_all_judges_list = all_judges_list.copy()  # общий список судей из которого будем случайно выбирать
            group_finish_judges_list = []  # список, в котором финально будем передавать судей, оценивающих категорию
            regions = {}  # счетчик судейств по регионам
            zgs_end_list = []  # список згс которых набрали
            zgs_list_generation = all_zgs_list.copy()  # динамический список для генерации

        zgs_number_to_have = int(i[4]) #сколко нужно набратғ ЗГС в группу

        black_list_cat = await black_list_convert(group_number,
                                                  black_list)  # 5. определяем судей с запретом на судейство в конкретной категории
        zgs_list_generation = await judges_black_list_filter(zgs_list_generation,
                                                      black_list_cat)  # 6. удаляем таких судей из категории



        if len(zgs_list_generation) >= zgs_number_to_have:
            while len(zgs_end_list) < zgs_number_to_have:
                if len(zgs_list_generation) > 0:
                    zgs_random_choice = await get_random_judge(zgs_list_generation)
                    zgs_end_list.append(zgs_random_choice['id'])

                    if zgs_random_choice['id'] in relatives_dict:
                        for l in relatives_dict[zgs_random_choice['id']]:
                            zgs_list_generation.pop(l, None)

                    zgs_list_generation = await delete_club_from_judges(zgs_list_generation, zgs_random_choice['Club'])

                else:
                    sucess_result_zgs = 0
                    json_end['group_number'] = group_number
                    json_end['status'] = "fail"
                    json_end['judge_id'] = []
                    json_end['zgs_id'] = []
                    json_end['msg'] = 'Не удалось сформировать бригаду с учетом заданных условий. Попробуйте уменьшить количество ЗГС'
                    break
            else:
                json_end['group_number'] = group_number
                if len(zgs_end_list) == zgs_number_to_have: sucess_result_zgs = 1
                json_end['status'] = "success"
                json_end['judge_id'] = list()
                json_end['zgs_id'] = list()
                for d in zgs_end_list:
                    json_end['judge_id'].append(all_zgs_list[d]['id'])
                    json_end['zgs_id'].append(all_zgs_list[d]['id'])

        else:
            #if zgs_number_to_have == 0:
             #   sucess_result_zgs = 1
              #  json_end['zgs_id'] = []
               # json_end['judge_id'] = []
            #else:
                sucess_result_zgs = 0
                json_end['group_number'] = group_number
                json_end['status'] = "fail"
                json_end['judge_id'] = []
                json_end['zgs_id'] = []
                json_end['msg'] = 'Не удалось сформировать бригаду с учетом заданных условий. Попробуйте уменьшить количество ЗГС'

    # 3. начинаем работать с каждой группой из переданного списка

        """
        Если нам передали несколько групп, то есть мы должны генерить в параллель
        и если это уже не первая группа и предыдущая была сгенерена успешно
        тогда из общего списка судей выкидываем всех кого нагенерили в панельки ранее
        """

        # определяем параметры группы
        n_judges, min_category = i[1], i[2]
        if min_category is None:
            min_category = 0
        #otd_num = group_list[i]['otd_num']

        n_judges_category = 0

        # определяем условия на регионы судей
        if i[3] == 0: # если группа не спортивная, проверяем регионы
            n_jud_comp_region, n_jud_other_region = await rc_a_region_rules(comp_region_id, n_judges)
        else:
            if i[3] == 1: #если группа спортивная, то ограничения на регионы нет, но надо проверить категории
                n_jud_comp_region, n_jud_other_region = 10000, 10000
                group_all_judges_list = await judges_category_date_filter(group_all_judges_list, data['compId'])
            else: #для РС В вообще пофиг
                n_jud_comp_region, n_jud_other_region = 10000, 10000

        group_all_judges_list = await judges_category_filter(group_all_judges_list,
                                                       min_category)  # 4. удаляем судей с неподходящей категорией

        black_list_cat = await black_list_convert(group_number,
                                            black_list)  # 5. определяем судей с запретом на судейство в конкретной категории
        group_all_judges_list = await judges_black_list_filter(group_all_judges_list,
                                                         black_list_cat)  # 6. удаляем таких судей из категории


        #Удаляем из пула згс ребят
        group_all_judges_list = await judges_black_list_filter(group_all_judges_list,
                                                       zgs_end_list)


        if len(group_all_judges_list) >= n_judges:
            while n_judges_category < n_judges:
                if len(group_all_judges_list) > 0:
                    # после чисток выбираем рандомного судью из списка
                    try_judge_data = await get_random_judge(group_all_judges_list)

                    # обновляем данные о судейском составе текущей группы
                    group_finish_judges_list.append(try_judge_data['id'])  # добавили судью в список выбранных
                    n_judges_category += 1  # количество набранных судей в категорию увеличилось на 1

                    # добавили информацию о регионе судьи в словарь по регионам
                    if try_judge_data['RegionId'] in regions:
                        regions[try_judge_data['RegionId']] += 1
                        if try_judge_data['RegionId'] == comp_region_id and regions[try_judge_data[
                            'RegionId']] == n_jud_comp_region:  # если судья из "домашнего" региона и при его добавлении лимит для региона исчерпан
                            # ФУНКЦИЯ удаляем всех судей с таким же регионом
                            group_all_judges_list = await delete_region_from_judges(group_all_judges_list,
                                                                              try_judge_data['RegionId'])
                        elif try_judge_data['RegionId'] != comp_region_id and regions[
                            try_judge_data['RegionId']] == n_jud_other_region:
                            # ФУНКЦИЯ удаляем всех судей с таким же регионом
                            group_all_judges_list = await delete_region_from_judges(group_all_judges_list,
                                                                              try_judge_data['RegionId'])
                    else:
                        regions[try_judge_data['RegionId']] = 1

                    # удалили всех с таким же клубом
                    group_all_judges_list = await delete_club_from_judges(group_all_judges_list, try_judge_data['Club'])

                    # обновляем данные о судях, доступных для выбора
                    group_all_judges_list.pop(try_judge_data['id'],
                                              None)  # судью которого мы выбрали второй раз выбрать нельзя
                    # если у судьи есть родственники, то применяем функцию для удаления родственников
                    if try_judge_data['id'] in relatives_dict:
                        for i in relatives_dict[try_judge_data['id']]:
                            group_all_judges_list.pop(i, None)

                    if n_judges_category == n_judges:  # если набрали необходимое количество судей, то успех
                        sucess_result = 1
                else:
                    sucess_result = 0
                    json_end['group_number'] = group_number
                    json_end['status'] = "fail"
                    json_end['judge_id'] = []
                    json_end['msg'] = 'Не удалось сформировать бригаду с учетом заданных условий. Попробуйте сгенерирвать еще раз или уменьшить количество судей в бригаде.'
                    break
            else:
                json_end['group_number'] = group_number
                json_end['status'] = "success"
                #json_end['judge_id'] = list()
                json_end['lin_id'] = list()
                for i in group_finish_judges_list:
                    json_end['judge_id'].append(all_judges_list[i]['id'])
                    json_end['lin_id'].append(all_judges_list[i]['id'])
        else:
            sucess_result = 0
            json_end['group_number'] = group_number
            json_end['status'] = "fail"
            json_end['judge_id'] = []
            json_end['msg'] = 'Не удалось сформировать бригаду с учетом заданных условий. Попробуйте сгенерирвать еще раз или уменьшить количество судей в бригаде'

        final_status = sucess_result
        if final_status > sucess_result_zgs: final_status = sucess_result_zgs
        result_dict = {0: "fail", 1: "success"}
        json_end['status'] = result_dict[final_status]
        json_export[group_number] = json_end


    #json.loads(json.dumps(json_export))
    ans = await json_to_message(json_export, data)
    return ans, json_export


#получить параметр групп по турниру и номеру
async def get_group_params(comp_id, group_id):
    try:
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
            cur.execute(
                f'''SELECT groupNumber,judges, minCategoryId, sport, zgsNumber
                 from competition_group
                 WHERE compId = {comp_id} and groupNumber = {group_id}
                                        ''')
            data = cur.fetchone()
            if data is None:
                return "undefinedGroup"
            else:
                if data['judges'] is None:
                    data['judges'] = 0
                if data['minCategoryId'] is None:
                    data['minCategoryId'] = 0

                return data['groupNumber'], data['judges'], data['minCategoryId'], data['sport'], data['zgsNumber']
    except Exception as e:
        print(e)
        return 0


#функция для ограничения на регионы
async def rc_a_region_rules(comp_region_id, n_judges):
  if n_judges == 7:
    return(3, 2)
  elif n_judges == 9:
    return(4, 2)
  elif n_judges == 11:
    return(5, 3)
  elif n_judges == 13:
    return(6, 3)


#костыль пока не таблиц в БД
async def get_future_tables():
    #group_list = {
        #21: {'name': 'Мужчины и женщины латиноамериканская программа', 'min_category': 8, 'otd_num': 11,
    #     'n_judges': 11},
        #22: {'name': 'Мужчины и женщины европейская программа', 'min_category': 7, 'otd_num': 11, 'n_judges': 9},
        # 23: {'name': 'Мужчины и женщины двоеборье', 'min_category': 5, 'otd_num' : 11, 'n_judges': 9},
        # 24: {'name': 'Мужчины и женщины сальса', 'min_category': 7, 'otd_num' : 11, 'n_judges': 9}
    #}

    '''
    relatives_list = [
        {'id': 1,
         'relative_id': 3},
        {'id': 3,
         'relative_id': 1}
    ]
    '''
    '''
    black_list = [
        {'group_number': 21,
         'id': 1},
        {'group_number': 21,
         'id': 5},
        {'group_number': 21,
         'id': 67}
    ]
    '''

    judge_counter_list = [{'otd_num': 11, 'id': i, 'jud_entries': 0} for i in range(1, 101)]
    return judge_counter_list


async def get_relative_list(compId):
    try:
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
            ans = []
            cur.execute(f"select firstId, secondId from judges_relatives where compId = {compId}")
            data = cur.fetchall()
            for connect in data:
                ans.append({'id': connect["firstId"], 'relative_id': connect["secondId"]})

            return ans

    except Exception as e:
        print(e, 'get_relative_list')


async def get_black_list(compId):
    try:
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
            ans = []
            cur.execute(f"select judgeId, groupNumber from competition_group_interdiction where compId = {compId}")
            data = cur.fetchall()
            for interdiction in data:
                ans.append({'group_number': interdiction['groupNumber'], 'id': interdiction['judgeId']})

            return ans

    except Exception as e:
        print(e, 'get_black_list')

async def get_all_judges_yana(compId):
    try:
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
            cur.execute(
               f"SELECT id, lastName, firstName, SPORT_Category, RegionId, Club, bookNumber, group_counter, DSFARR_Category_Id, workCode FROM competition_judges WHERE compId = {compId} and active = 1 and workCode <= 1")  # выбираем только активных на данный момент судей
            data = cur.fetchall()
            return data

    except Exception as e:
        print(e)
        return 0

#преобразование категории судьи
async def decode_category(category_name):


    judge_category = {
        'Всероссийская' :6,
        'Первая' : 5,
        'Вторая' : 4,
        'Третья' : 3,
        'Четвертая': 2
    }

    try:
        category_num = judge_category[category_name]
    except KeyError:
        return 10
    return category_num


#функция удаляет судей с категорией ниже минимальной для группы
async def judges_category_filter(all_judges_list, min_category):
    all_judges_list_1 = all_judges_list.copy()
    for i in all_judges_list:
        if all_judges_list_1[i]['SPORT_Category_decoded'] is None:
            all_judges_list_1[i]['SPORT_Category_decoded'] = 9
        if all_judges_list_1[i]['SPORT_Category_decoded'] < min_category:
            all_judges_list_1.pop(i, None)
    return all_judges_list_1

async def judges_zgs_filter(all_judges_list):
    all_judges_list_1 = all_judges_list.copy()
    for i in all_judges_list:
        if all_judges_list_1[i]['workCode'] != 1:
            all_judges_list_1.pop(i, None)
    return all_judges_list_1


async def judges_category_date_filter(all_judges_list, compId):
    bad_category_judges = await check_category_date(all_judges_list, compId)
    all_judges_list_1 = all_judges_list.copy()
    for i in all_judges_list:
        if i in bad_category_judges:
            all_judges_list_1.pop(i, None)
    return all_judges_list_1


#функция предварительной обработки блэклиста - по номеру категории определяем судей с запретом, на выход - айдишники судей
async def black_list_convert(category_number, black_list):
  category_black_list = []
  for i in black_list:
    if i['group_number'] == category_number:
      category_black_list.append(i['id'])
  return category_black_list

#функция удаляет судей с запретом на судейство в категории
async def judges_black_list_filter(all_judges_list, category_black_list):
  all_judges_list_1 = all_judges_list.copy()
  for i in all_judges_list:
    if i in category_black_list:
      all_judges_list_1.pop(i, None)
  return all_judges_list_1

#функция генерирует случайного судью
async def get_random_judge(group_all_judges_list):
    """
    random_number = random.randint(0, len(group_all_judges_list.keys()) - 1) #генерация случайного индекса

    return group_all_judges_list[list(group_all_judges_list.keys())[random_number]] #достаем из общего списка судей параметры по судье исходя из случайного индекса
    """
    min_counter = 10 ** 6
    for i in group_all_judges_list:
        a = group_all_judges_list[i]['group_counter']
        if a < min_counter:
            min_counter = a

    new_dict = group_all_judges_list.copy()
    for j in group_all_judges_list:
        if group_all_judges_list[j]['group_counter'] > min_counter:
            new_dict.pop(j, None)

    random_number = random.randint(0, len(new_dict.keys()) - 1)
    return new_dict[list(new_dict.keys())[random_number]]


#функция удаляет всех судей с таким же клубом
async def delete_club_from_judges(list_of_judges, club_name):
  dict_for_pop = list_of_judges.copy()
  for i in list(list_of_judges.values()):
    if i['Club'] == club_name:
      dict_for_pop.pop(i['id'], None)
  return dict_for_pop


#функция удаляет всех судей с таким же регионом
async def delete_region_from_judges(list_of_judges, region_id):

  dict_for_pop = list_of_judges.copy()
  for i in list(list_of_judges.values()):
    if i['RegionId'] == region_id:
      dict_for_pop.pop(i['id'], None)
  return dict_for_pop


# преобразование списка родственников после загрузки
async def relatives_list_change(relatives_list):

    relatives_dict = {}
    for i in relatives_list:
        if i['id'] in relatives_dict:
            relatives_dict[i['id']].append(i['relative_id'])
        else:
            relatives_dict[i['id']] = list()
            relatives_dict[i['id']].append(i['relative_id'])

    return relatives_dict


async def ids_to_names(judges, active_comp):
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
        r = []
        for judid in judges:
            cur.execute(f"select lastName, firstName from competition_judges where compId = {active_comp} and id = {judid} and active = 1")
            ans = cur.fetchone()
            r.append(f'{ans["lastName"]} {ans["firstName"]}')
        return ', '.join(r)


async def json_to_message(json_export, data):
    r = []
    for key in json_export:
        group_name = await get_group_name(data['compId'], key)
        if json_export[key]['status'] == 'success':
            peoples = await ids_to_names(json_export[key]['lin_id'], data['compId'])
            zgs = await ids_to_names(json_export[key]['zgs_id'], data['compId'])
            text = f'{key}. {group_name}\nЗгс. {zgs}.\nЛинейные судьи: {peoples}.'
            if len(zgs) == 0:
                text = f'{key}. {group_name}\nЛинейные судьи: {peoples}.'
            else:
                text = f'{key}. {group_name}\nЗгс. {zgs}.\nЛинейные судьи: {peoples}.'

            r.append(text)

        if json_export[key]['status'] == 'fail':
            text = f'{key}. {group_name}\n{json_export[key]["msg"]}'
            r.append(text)
    return '\n\n'.join(r)


async def get_group_name(compId, groupNumber):
    try:
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
            cur.execute(f"select groupName from competition_group where compId = {compId} and groupNumber = {groupNumber}")
            ans = cur.fetchone()
            if ans is None:
                return ''

            return ans['groupName']
    except Exception as e:
        print(e)
        return -1


async def check_category_date(judges, compId):
    try:
        problem =[]
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
            cur.execute(f"SELECT date1, date2 FROM competition WHERE compId = {compId}")
            dates = cur.fetchone()
            date1, date2 = dates['date1'], dates['date2']

            for key in judges:
                jud = judges[key]
                id = jud['id']
                cur.execute(f"SELECT SPORT_Category, SPORT_CategoryDate, SPORT_CategoryDateConfirm, DSFARR_Category_Id FROM competition_judges WHERE compId = {compId} AND id = {id}")
                info = cur.fetchone()
                category = info['SPORT_Category']
                SPORT_CategoryDate = info['SPORT_CategoryDate']
                SPORT_CategoryDateConfirm = info['SPORT_CategoryDateConfirm']
                code = info['DSFARR_Category_Id']
                if code is None:
                    code = 9

                if category == None or SPORT_CategoryDate == None or SPORT_CategoryDateConfirm == None:
                    continue

                if type(SPORT_CategoryDateConfirm) == str and type(SPORT_CategoryDate) == str:
                    problem.append(id)
                    continue
                elif type(SPORT_CategoryDateConfirm) == str and type(SPORT_CategoryDate) != str:
                    CategoryDate = SPORT_CategoryDate
                elif type(SPORT_CategoryDateConfirm) != str and type(SPORT_CategoryDate) == str:
                    CategoryDate = SPORT_CategoryDateConfirm
                else:
                    CategoryDate = max(SPORT_CategoryDateConfirm, SPORT_CategoryDate)

                a = date2 - CategoryDate
                a = a.days
                if code == 5 or code == 4:
                    if a - 365*2 > 0:
                        problem.append(id)

                elif code == 3:
                    if a - 365 > 0:
                        problem.append(id)

                elif code == 6:
                    if a - 365*4 > 0:
                        problem.append(id)

            return problem
    except Exception as e:
        print(e, 1)
        return -1


async def agregate_generation_lin_zgs_judges(json):
    lin = []
    zgs = []
    for key in json:

        if json[key]['status'] == 'success':
            lin += json[key]['lin_id']
            zgs += json[key]['zgs_id']

    return lin, zgs


async def unpac_json(json):
    ans = {}
    for key in json:
        if json[key]['status'] == 'success':
            for i in json[key]['judge_id']:
                ans[i] = json[key]['group_number']
    return ans


async def get_judges_list(json):
    ans = {}
    for key in json:
        if json[key]['status'] == 'success':
            for i in json[key]['lin_id']:
                ans[i] = [key, 'l', json[key]['lin_id']]

            for i in json[key]['zgs_id']:
                ans[i] = [key, 'z', json[key]['zgs_id']]

    return ans


async def same_judges_filter(all_judges, judges):
    all_judges_01 = all_judges.copy()
    for i in range(len(judges)):
        for j in all_judges:
            if j['id'] == judges[i]:
                all_judges_01.remove(j)

    return all_judges_01


async def distinct_clubs_filter(clubs_list, all_judges):
    all_judges_01 = all_judges.copy()
    try:
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
            for i in all_judges:
                cur.execute(f'select City, Club from competition_judges where id = {i["id"]}')
                req = cur.fetchone()
                if req['City'] is not None and req['Club'] is not None:
                    if f"{req['City']}, {req['Club']}" in clubs_list:
                        all_judges_01.remove(i)
        return all_judges_01
    except Exception as e:
        return -1

async def category_filter(all_judges, minCategoryId, compId, groupType, judgeType):
    all_judges_01 = all_judges.copy()
    try:
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
            cur.execute(f"select date2 from competition where compId = {compId}")
            date2 = cur.fetchone()
            date2 = date2['date2']

            for jud in all_judges:
                category = jud['SPORT_Category']
                SPORT_CategoryDate = jud['SPORT_CategoryDate']
                SPORT_CategoryDateConfirm = jud['SPORT_CategoryDateConfirm']
                code = jud['DSFARR_Category_Id']

                if code is None:
                    code = 9

                if judgeType == 'l':
                    if code < minCategoryId:
                        all_judges_01.remove(jud)
                        continue

                    if category == None or SPORT_CategoryDate == None or SPORT_CategoryDateConfirm == None:
                        continue

                    if type(SPORT_CategoryDateConfirm) == str and type(SPORT_CategoryDate) == str:
                        all_judges_01.remove(jud)
                        continue

                    elif type(SPORT_CategoryDateConfirm) == str and type(SPORT_CategoryDate) != str:
                        CategoryDate = SPORT_CategoryDate

                    elif type(SPORT_CategoryDateConfirm) != str and type(SPORT_CategoryDate) == str:
                        CategoryDate = SPORT_CategoryDateConfirm

                    else:
                        CategoryDate = max(SPORT_CategoryDateConfirm, SPORT_CategoryDate)

                    if groupType == 1:
                        a = date2 - CategoryDate
                        a = a.days
                        if code == 5 or code == 4:
                            if a - 365 * 2 > 0:
                                all_judges_01.remove(jud)

                        elif code == 3:
                            if a - 365 > 0:
                                all_judges_01.remove(jud)

                        elif code == 6:
                            if a - 365 * 4 > 0:
                                all_judges_01.remove(jud)
                if judgeType == 'z':
                    if groupType == 1:
                        if category == None or SPORT_CategoryDate == None or SPORT_CategoryDateConfirm == None:
                            continue

                        if type(SPORT_CategoryDateConfirm) == str and type(SPORT_CategoryDate) == str:
                            all_judges_01.remove(jud)
                            continue

                        elif type(SPORT_CategoryDateConfirm) == str and type(SPORT_CategoryDate) != str:
                            CategoryDate = SPORT_CategoryDate

                        elif type(SPORT_CategoryDateConfirm) != str and type(SPORT_CategoryDate) == str:
                            CategoryDate = SPORT_CategoryDateConfirm

                        else:
                            CategoryDate = max(SPORT_CategoryDateConfirm, SPORT_CategoryDate)

                        if groupType == 1:
                            a = date2 - CategoryDate
                            a = a.days
                            if code == 5 or code == 4:
                                if a - 365 * 2 > 0:
                                    all_judges_01.remove(jud)

                            elif code == 3:
                                if a - 365 > 0:
                                    all_judges_01.remove(jud)

                            elif code == 6:
                                if a - 365 * 4 > 0:
                                    all_judges_01.remove(jud)
        return all_judges_01
    except Exception as e:
        return -1



async def interdiction_filter(compId, groupNumber, all_judges):
    try:
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
            cur.execute(f"select judgeId from competition_group_interdiction where compId = {compId} and groupNumber = {groupNumber}")
            interdiction_list = cur.fetchall()
            interdiction_list = set([i['judgeId'] for i in interdiction_list])
            all_judges_01 = all_judges.copy()

            for jud in all_judges:
                if jud['id'] in interdiction_list:
                    all_judges_01.remove(jud)
        return all_judges_01
    except:
        return 0


async def relatives_filter(compId, all_judges, pull):
    try:
        all_judges_01 = all_judges.copy()
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
            cur.execute(f"select firstId, secondId from judges_relatives where compId = {compId}")
            relatives = cur.fetchall()
            relatives_list = []
            for rel in relatives:
                if rel['firstId'] in pull:
                    relatives_list.append(rel['secondId'])
            for jud in all_judges:
                if jud['id'] in relatives_list:
                    all_judges_01.remove(jud)

        return all_judges_01
    except Exception as e:
        print(e)
        return 0


async def generate_zgs(compId, n):
    try:
        names = {}
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
            cur.execute(f"select compId, firstName, lastName, id, DSFARR_Category_Id, SPORT_CategoryDate, SPORT_CategoryDateConfirm, SPORT_Category from competition_judges where compId = {compId} and active = 1 and workCode = 0")
            judges_all = cur.fetchall()

            cur.execute(f"select generation_zgs_mode from competition where compId = {compId}")
            generation_zgs_mode = cur.fetchone()
            generation_zgs_mode = generation_zgs_mode['generation_zgs_mode']


            if len(judges_all) < n:
                return {'msg': "Значение введеного параметра превышает количесво активных судей", 'judges': [], 'status': 'fail'}
            i = 0

            if generation_zgs_mode == 1:
                judges_all = await generation_zgs_cat_filter(judges_all, compId)
            while i != n:
                jud = judges_all.pop(random.randint(0, len(judges_all) - 1))
                names[jud['id']] = jud
                i += 1
            text = await generate_zgs_to_message(names)
            json_export = {'msg': text, 'status': 'succsess', 'judges': names}
        return json_export
    except Exception as e:
        print(e)
        pass


async def generate_zgs_to_message(names):
    text = []
    for judId in names:
        name = names[judId]["lastName"] + ' ' + names[judId]["firstName"]
        text.append(name)
    text = f"Згс. {', '.join(text)}"
    return text


async def generation_zgs_cat_filter(all_judges, compId):
    all_judges_01 = all_judges.copy()
    try:
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
            cur.execute(f"select date2 from competition where compId = {compId}")
            date2 = cur.fetchone()
            date2 = date2['date2']

            for jud in all_judges:
                category = jud['SPORT_Category']
                SPORT_CategoryDate = jud['SPORT_CategoryDate']
                SPORT_CategoryDateConfirm = jud['SPORT_CategoryDateConfirm']
                code = jud['DSFARR_Category_Id']

                if category == None or SPORT_CategoryDate == None or SPORT_CategoryDateConfirm == None:
                    continue

                if type(SPORT_CategoryDateConfirm) == str and type(SPORT_CategoryDate) == str:
                    all_judges_01.remove(jud)
                    continue

                elif type(SPORT_CategoryDateConfirm) == str and type(SPORT_CategoryDate) != str:
                    CategoryDate = SPORT_CategoryDate

                elif type(SPORT_CategoryDateConfirm) != str and type(SPORT_CategoryDate) == str:
                    CategoryDate = SPORT_CategoryDateConfirm

                else:
                    CategoryDate = max(SPORT_CategoryDateConfirm, SPORT_CategoryDate)

                a = date2 - CategoryDate
                a = a.days
                if code == 5 or code == 4:
                    if a - 365 * 2 > 0:
                        all_judges_01.remove(jud)

                elif code == 3:
                    if a - 365 > 0:
                        all_judges_01.remove(jud)

                elif code == 6:
                    if a - 365 * 4 > 0:
                        all_judges_01.remove(jud)
        return all_judges_01
    except Exception as e:
        return -1

async def regions_change_filter(all_judges, info, regions, compRegion):
    all_judges_01 = all_judges.copy()
    home, neibor = info
    for jud in all_judges:
        jud_region = jud['RegionId']
        if jud_region in regions:
            if jud_region == compRegion:
                if regions[jud_region] >= home:
                    all_judges_01.remove(jud)
            else:
                if regions[jud_region] >= neibor:
                    all_judges_01.remove(jud)
    return all_judges_01
