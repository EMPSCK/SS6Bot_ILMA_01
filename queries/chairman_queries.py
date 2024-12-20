import pymysql
import config
from queries import general_queries
from chairman_moves import check_list_judges
import re
import datetime
from datetime import date


async def set_active_comp_for_chairman(tg_id, id):
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
            cur.execute(f"UPDATE skatebotusers SET id_active_comp = {id} WHERE tg_id = {tg_id}")
            conn.commit()
            cur.close()
            return 1
    except:
        print('Ошибка выполнения запроса на установку соревнований')
        return 0


async def get_Scrutineer(tg_id):
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
            active_comp_id = await general_queries.get_CompId(tg_id)
            cur.execute(f"SELECT scrutineerId FROM competition WHERE compId = {active_comp_id}")
            scrutinner_id = cur.fetchone()
            cur.close()
            return scrutinner_id['scrutineerId']
    except:
        print('Ошибка выполнения запроса поиск scrutinner для chairman')
        return 0


async def get_list_comp(tg_id):
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
            cur.execute(f"SELECT compName, compId, city, date1, date2 FROM competition WHERE chairman_id = {tg_id} and isActive = 1")
            competitions = cur.fetchall()
            cur.close()
            ans = []
            now = date.today()
            for comp in competitions:
                a = now - comp['date2']
                if a.days <= 0:
                    ans.append(comp)
            return ans
    except:
        print('Ошибка выполнения запроса на поиск соревнований для chairman1')
        return 0

async def set_free_judges(user_id):
    try:
        active_comp = await general_queries.get_CompId(user_id)
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
            for i in config.judges_index[user_id]:
                cur.execute(f"UPDATE competition_judges SET is_use = 1 WHERE lastName = '{i[0]}' AND firstName = '{i[1]}' AND bookNumber = {i[2]} AND compId = {active_comp} and active = 1")
                conn.commit()

            cur.close()
            return 1
    except:
        print('Ошибка выполнения запроса на установку свободных судей')
        return 0

async def get_free_judges(user_id):
    try:
        active_comp = await general_queries.get_CompId(user_id)
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
            judges_use = config.judges_index[user_id]
            cur.execute(f"SELECT * FROM competition_judges WHERE compId = {active_comp} AND is_use = 0 AND active = 1 ORDER BY lastName")
            judgesComp = cur.fetchall()
            cur.close()

            #Если судьи не загружены на турнир
            if judgesComp == ():
                return 'свободных судей нет'
            judges_free = judgesComp.copy()
            for jud in judgesComp:
                for jud1 in judges_use:
                    if jud['firstName'] == jud1[1] and jud['lastName'] == jud1[0]:
                        judges_free.remove(jud)
            if judges_free == []:
                return 'свободных судей нет'

            judges_free = ', '.join([i['lastName'] + ' ' + i['firstName'] for i in judges_free])

            return judges_free

    except Exception as e:
        print(e)
        print('Ошибка выполнения запроса на установку свободных судей')
        return 0

from handlers import Chairman_menu_handler
async def set_problem_jud_as_is(user_id, jud, code ,booknumber=-1):
    try:
        active_comp = await general_queries.get_CompId(user_id)
        jud = jud.split()
        if len(jud) == 2:
            firstname = jud[1]
            lastname = jud[0]
        else:
            lastname = jud[0]
            firstname = ' '.join(jud[1::])

        Chairman_menu_handler.last_added_judges[user_id].append([lastname, firstname])
        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        notjud = re.match(r'^[a-zA-Z]+\Z', firstname.replace(' ', '')) is not None
        with conn:
            cur = conn.cursor()
            # Если судья уже есть в таблице competition_judges
            cur.execute(
                f"DELETE FROM competition_judges WHERE ((firstName = '{firstname}' AND lastName = '{lastname}') OR (firstName2 = '{firstname}' AND lastName2 = '{lastname}')) AND compId = {active_comp}")
            conn.commit()

            person = None
            if booknumber != -1:
                cur.execute(f"SELECT * FROM judges WHERE BookNumber = {booknumber}")
                person = cur.fetchone()
            if person is not None:
                lastname1 = person['LastName']
                firstname1 = person['FirstName']
                BookNumber = person['BookNumber']
                SecondName = person['SecondName']
                Birth = person['Birth']
                DSFARR_Category = person['DSFARR_Category']
                DSFARR_CategoryDate = person['DSFARR_CategoryDate']
                WDSF_CategoryDate = person['WDSF_CategoryDate']
                RegionId = person['RegionId']
                City = person['City']
                Club = person['Club']
                Translit = person['Translit']
                Archive = person['Archive']
                SPORT_Category = person['SPORT_Category']
                SPORT_CategoryDate = person['SPORT_CategoryDate']
                SPORT_CategoryDateConfirm = person['SPORT_CategoryDateConfirm']
                DSFARR_Category_Id = person['DSFARR_Category_Id']
                federation = person['federation']
                sql = "INSERT INTO competition_judges (`compId`, `lastName`, `firstName`, `SecondName`, `Birth`, `DSFARR_Category`, `DSFARR_CategoryDate`, `WDSF_CategoryDate`, `RegionId`, `City`, `Club`, `Translit`, `SPORT_Category`, `SPORT_CategoryDate`, `SPORT_CategoryDateConfirm`, `federation`, `Archive`, `bookNumber`, `notJudges`, `is_use`, `lastName2`, `firstName2`, `DSFARR_Category_Id`, `active`, `workCode`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cur.execute(sql, (
                    active_comp, lastname1, firstname1, SecondName, Birth, DSFARR_Category, DSFARR_CategoryDate,
                    WDSF_CategoryDate,
                    RegionId, City, Club, Translit, SPORT_Category, SPORT_CategoryDate, SPORT_CategoryDateConfirm,
                    federation, Archive, BookNumber, notjud, 0, lastname, firstname, DSFARR_Category_Id, 1, code))
                conn.commit()
            else:
                booknumber = await create_new_booknum(active_comp)
                sql = "INSERT INTO competition_judges (`compId`, `lastName`, `firstName`, `notJudges`, `is_use`, `bookNumber`, `lastName2`, `firstName2`, `active`, `workCode`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cur.execute(sql, (active_comp, lastname, firstname, notjud, 0, booknumber, lastname, firstname, 1, code))
                conn.commit()
        cur.close()
        return 1
    except Exception as e:
        print(e)
        print('Ошибка выполнения запроса на установку проблемных судей')
        return 0

from handlers import Chairman_menu_handler
async def set_problem_jud_as_is_1(user_id, jud, code ,name=''):
    try:
        bn = 0
        firstname2 = 'Artem'
        lastname2 = 'Bulatov'
        if name != '':
            i, bn = name.split('|')
            i = i.split()
            bn = int(bn)
            if len(i) == 2:
                lastname2 = i[0]
                firstname2 = i[1]
            else:
                lastname2 = i[0]
                firstname2 = ' '.join(i[1::])

        active_comp = await general_queries.get_CompId(user_id)
        jud = jud.split()
        if len(jud) == 2:
            firstname = jud[1]
            lastname = jud[0]
        else:
            lastname = jud[0]
            firstname = ' '.join(jud[1::])
        Chairman_menu_handler.last_added_judges[user_id].append([lastname, firstname])
        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        notjud = re.match(r'^[a-zA-Z]+\Z', firstname.replace(' ', '')) is not None
        with conn:
            cur = conn.cursor()
            if bn != 0:
                cur.execute(f"SELECT * FROM judges WHERE BookNumber = {bn}")
            else:
                cur.execute(
                    f"SELECT * FROM judges WHERE FirstName = '{firstname}' AND LastName = '{lastname}'")
            person = cur.fetchone()
            BookNumber = person['BookNumber']
            SecondName = person['SecondName']
            Birth = person['Birth']
            DSFARR_Category = person['DSFARR_Category']
            DSFARR_CategoryDate = person['DSFARR_CategoryDate']
            WDSF_CategoryDate = person['WDSF_CategoryDate']
            RegionId = person['RegionId']
            City = person['City']
            Club = person['Club']
            Translit = person['Translit']
            Archive = person['Archive']
            SPORT_Category = person['SPORT_Category']
            SPORT_CategoryDate = person['SPORT_CategoryDate']
            SPORT_CategoryDateConfirm = person['SPORT_CategoryDateConfirm']
            federation = person['federation']
            DSFARR_Category_Id = person['DSFARR_Category_Id']
            # Если судья уже есть в таблице competition_judges
            cur.execute(
                f"DELETE FROM competition_judges  WHERE (((firstName2 = '{firstname}' AND lastName2 = '{lastname}') OR (firstName = '{firstname}' AND lastName = '{lastname}')) OR ((firstName2 = '{firstname2}' AND lastName2 = '{lastname2}') OR (firstName = '{firstname2}' AND lastName = '{lastname2}'))) AND compId = {active_comp}")
            conn.commit()

            if name != '':
                sql = "INSERT INTO competition_judges (`compId`, `lastName`, `firstName`, `SecondName`, `Birth`, `DSFARR_Category`, `DSFARR_CategoryDate`, `WDSF_CategoryDate`, `RegionId`, `City`, `Club`, `Translit`, `SPORT_Category`, `SPORT_CategoryDate`, `SPORT_CategoryDateConfirm`, `federation`, `Archive`, `bookNumber`, `notJudges`, `is_use`, `firstName2`, `lastName2`, `DSFARR_Category_Id`, `active`, `workCode`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cur.execute(sql, (
                    active_comp, lastname, firstname, SecondName, Birth, DSFARR_Category, DSFARR_CategoryDate,
                    WDSF_CategoryDate,
                    RegionId, City, Club, Translit, SPORT_Category, SPORT_CategoryDate, SPORT_CategoryDateConfirm,
                    federation, Archive, BookNumber, notjud, 0, firstname2, lastname2, DSFARR_Category_Id, 1, code))
                conn.commit()
            else:
                sql = "INSERT INTO competition_judges (`compId`, `lastName`, `firstName`, `SecondName`, `Birth`, `DSFARR_Category`, `DSFARR_CategoryDate`, `WDSF_CategoryDate`, `RegionId`, `City`, `Club`, `Translit`, `SPORT_Category`, `SPORT_CategoryDate`, `SPORT_CategoryDateConfirm`, `federation`, `Archive`, `bookNumber`, `notJudges`, `is_use`, `DSFARR_Category_Id`, `active`, `workCode`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cur.execute(sql, (
                    active_comp, lastname, firstname, SecondName, Birth, DSFARR_Category, DSFARR_CategoryDate,
                    WDSF_CategoryDate,
                    RegionId, City, Club, Translit, SPORT_Category, SPORT_CategoryDate, SPORT_CategoryDateConfirm,
                    federation, Archive, BookNumber, notjud, 0, DSFARR_Category_Id, 1, code))
                conn.commit()
            cur.close()
            return 1
    except Exception as e:
        print(e)
        print('Ошибка выполнения запроса на установку проблемных судей')
        return 0


async def cancel_load(user_id):
    try:
        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        active_comp = await general_queries.get_CompId(user_id)
        with conn:
            cur = conn.cursor()
            cur.execute(f"DELETE FROM competition_judges WHERE compId = {active_comp}")
            conn.commit()
        return 1
    except:
        return 0


async def get_similar_judges(jud):
    try:
        similar_judges = []
        jud = jud.split()
        if len(jud) == 2:
            firstname = set(jud[1])
            lastname = set(jud[0])
        else:
            lastname = set(jud[0])
            firstname = set(' '.join(jud[1::]))

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
            cur.execute(f"SELECT * FROM judges")
            judges = cur.fetchall()
            for el in judges:
                elfirstname = el['FirstName']
                ellastname = el['LastName']
                elbboknumber = el['BookNumber']
                if len(set(firstname).symmetric_difference(set(elfirstname))) + len(set(lastname).symmetric_difference(set(ellastname))) <= 4:
                    similar_judges.append(el)
            cur.close()
            return similar_judges
    except:
        return 0

async def add_problemcorrect_jud(booknumber, user_id, name2, code):
    try:
        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        i = name2.split()
        if len(i) == 2:
            lastname2, firstname2 = i[0], i[1]
        else:
            lastname2 = i[0]
            firstname2 = ' '.join(i[1::])

        active_comp = await general_queries.get_CompId(user_id)
        with conn:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM judges WHERE BookNumber = {booknumber}")
            person = cur.fetchall()
            last_name = person[0]['LastName']
            name = person[0]['FirstName']
            SecondName = person[0]['SecondName']
            Birth = person[0]['Birth']
            DSFARR_Category = person[0]['DSFARR_Category']
            DSFARR_CategoryDate = person[0]['DSFARR_CategoryDate']
            WDSF_CategoryDate = person[0]['WDSF_CategoryDate']
            RegionId = person[0]['RegionId']
            City = person[0]['City']
            Club = person[0]['Club']
            Translit = person[0]['Translit']
            Archive = person[0]['Archive']
            SPORT_Category = person[0]['SPORT_Category']
            SPORT_CategoryDate = person[0]['SPORT_CategoryDate']
            SPORT_CategoryDateConfirm = person[0]['SPORT_CategoryDateConfirm']
            federation = person[0]['federation']
            notjud = re.match(r'^[a-zA-Z]+\Z', name.replace(' ', '')) is not None
            DSFARR_Category_Id = person[0]['DSFARR_Category_Id']
            Chairman_menu_handler.last_added_judges[user_id].append([last_name, name])

            # Если судья уже есть в таблице competition_judges
            cur.execute(
                f"DELETE FROM competition_judges WHERE firstName2 = '{firstname2}' AND lastName2 = '{lastname2}' AND compId = {active_comp}")
            conn.commit()

            sql = "INSERT INTO competition_judges (`compId`, `lastName`, `firstName`, `SecondName`, `Birth`, `DSFARR_Category`, `DSFARR_CategoryDate`, `WDSF_CategoryDate`, `RegionId`, `City`, `Club`, `Translit`, `SPORT_Category`, `SPORT_CategoryDate`, `SPORT_CategoryDateConfirm`, `federation`, `Archive`, `bookNumber`, `notJudges`, `is_use`, `firstName2`, `lastName2`, `DSFARR_Category_Id`, `active`, `workCode`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cur.execute(sql, (
                active_comp, last_name, name, SecondName, Birth, DSFARR_Category, DSFARR_CategoryDate,
                WDSF_CategoryDate,
                RegionId, City, Club, Translit, SPORT_Category, SPORT_CategoryDate, SPORT_CategoryDateConfirm,
                federation, Archive, booknumber, notjud, 0, firstname2, lastname2, DSFARR_Category_Id, 1, code))
            conn.commit()
    except Exception as e:
        print(e)
        return 0

async def for_free(user_id):
    try:
        active_comp = await general_queries.get_CompId(user_id)
        name = await general_queries.CompId_to_name(active_comp)
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
            cur.execute(f"SELECT * FROM competition_judges WHERE compId = {active_comp} AND is_use = 0 AND active = 1 ORDER BY lastName")
            judgesComp = cur.fetchall()
            cur.close()

            #Если судьи не загружены на турнир
            if judgesComp == ():
                return 'Свободных судей нет'
            #judges_free = name + '\n\n' +'\n'.join([i['lastName'] + ' ' + i['firstName'] + ', ' + str(i['City']) for i in judgesComp])
            n = len(judgesComp)
            judges_free = name + '\n' + f'Общее число: {n}' + '\n\n'
            for i in judgesComp:
                city = i['City']
                if city is None:
                    city = 'не определено'
                judges_free += i['lastName'] + ' ' + i['firstName'] + ', ' + city + '\n'
            return judges_free

    except Exception as e:
        print(e)
        print('Ошибка выполнения запроса for_free')
        return 0


async def get_similar_lin_judges(jud, user_id):
    try:
        similar_judges = []
        lastname, firstname = jud
        active_comp = await general_queries.get_CompId(user_id)

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
            cur.execute(f"SELECT * FROM competition_judges WHERE compId = {active_comp} AND active = 1")
            judges = cur.fetchall()
            for el in judges:
                elfirstname = el['firstName']
                ellastname = el['lastName']
                elbboknumber = el['bookNumber']
                if len(set(firstname).symmetric_difference(set(elfirstname))) + len(set(lastname).symmetric_difference(set(ellastname))) <= 4:
                    similar_judges.append(el)
            cur.close()
            return similar_judges
    except Exception as e:
        print(e)
        return 0


async def booknumber_to_name(booknumber):
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
            cur.execute(f"SELECT lastName, firstName FROM competition_judges WHERE bookNumber = {booknumber}")
            jud = cur.fetchone()
            return jud['lastName'] + ' ' +jud['firstName']

    except:
        return 0

async def booknumber_to_name_1(booknumber):
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
            cur.execute(f"SELECT lastName, firstName FROM judges WHERE bookNumber = {booknumber}")
            jud = cur.fetchone()
            return jud['lastName'], jud['firstName']

    except:
        return 0, 0

async def check_clubs_match(list):
    try:
        clubs = {}
        ans = ''
        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn:
            for jud in list:
                if len(jud.split()) == 2:
                    k = jud.split()
                    firstname = k[1]
                    lastname = k[0]
                else:
                    k = jud.split()
                    firstname = ' '.join(k[1::])
                    lastname = k[0]

                cur = conn.cursor()
                cur.execute(f"SELECT Club, City FROM competition_judges WHERE firstName = '{firstname}' AND lastName = '{lastname}'")
                info = cur.fetchone()
                club, city = info['Club'], info['City']

                if club != None and city != None:
                    name = club + ', ' + city
                    if name not in clubs:
                        clubs[name] = [jud]
                    else:
                        clubs[name].append(jud)
            for club in clubs:
                if len(clubs[club]) > 1:
                    ans = club + ': ' + ', '.join(clubs[club]) + '\n'
            if ans == '':
                return 0
            else:
                return ans

    except Exception as e:
        print(e, 1)
        return 0


async def check_have_tour_date(user_id):
    try:
        active_comp = await general_queries.get_CompId(user_id)
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
            return cur.execute(f"SELECT date1, date2 FROM competition WHERE compId = {active_comp}")
    except Exception as e:
        print(e)
        return 0




async def check_category_date(list, user_id):
    try:
        active_comp = await general_queries.get_CompId(user_id)
        ans = ''
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
            cur.execute(f"SELECT date1, date2 FROM competition WHERE compId = {active_comp}")
            dates = cur.fetchone()
            date1, date2 = dates['date1'], dates['date2']

            for jud in list:
                if len(jud.split()) == 2:
                    k = jud.split()
                    firstname = k[1]
                    lastname = k[0]
                else:
                    k = jud.split()
                    firstname = ' '.join(k[1::])
                    lastname = k[0]

                cur.execute(f"SELECT SPORT_Category, SPORT_CategoryDate, SPORT_CategoryDateConfirm, DSFARR_Category_Id FROM competition_judges WHERE compId = {active_comp} AND firstName = '{firstname}' AND lastName = '{lastname}'")
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
                    problem.append(jud)
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
                        problem.append(jud)

                elif code == 3:
                    if a - 365 > 0:
                        problem.append(jud)

                elif code == 6:
                    if a - 365*4 > 0:
                        problem.append(jud)

            if len(problem) == 0:
                return 0
            else:
                return f"{', '.join(problem)}: на момент окончания турнира категория недействительна"

    except Exception as e:
        print(e)
        return 0



async def check_category_date_for_book_id(book_id, user_id):
    try:
        active_comp = await general_queries.get_CompId(user_id)
        ans = ''
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
            cur.execute(f"SELECT date1, date2 FROM competition WHERE compId = {active_comp}")
            dates = cur.fetchone()
            date1, date2 = dates['date1'], dates['date2']
            cur.execute(f"SELECT SPORT_Category, SPORT_CategoryDate, SPORT_CategoryDateConfirm, DSFARR_Category_Id FROM judges WHERE BookNumber = {book_id}")
            info = cur.fetchone()
            category = info['SPORT_Category']
            SPORT_CategoryDate = info['SPORT_CategoryDate']
            SPORT_CategoryDateConfirm = info['SPORT_CategoryDateConfirm']
            code = info['DSFARR_Category_Id']
            if code is None:
                code = 9
            if category == None or SPORT_CategoryDate == None or SPORT_CategoryDateConfirm == None:
                return 0

            if type(SPORT_CategoryDateConfirm) == str and type(SPORT_CategoryDate) == str:
                return 0
            elif type(SPORT_CategoryDateConfirm) == str and type(SPORT_CategoryDate) != str:
                CategoryDate = SPORT_CategoryDate
            elif type(SPORT_CategoryDateConfirm) != str and type(SPORT_CategoryDate) == str:
                CategoryDate = SPORT_CategoryDateConfirm
            else:
                CategoryDate = max(SPORT_CategoryDateConfirm, SPORT_CategoryDate)

            a = date2 - CategoryDate
            a = a.days
            if code == 4 or code == 5:
                if a - 365 * 2 > 0:
                    return 0

            elif code == 3:
                if a - 365 > 0:
                    return 0

            elif code == 6:
                if a - 365 * 4 > 0:
                    return 0
        return 1
    except Exception as e:
        print(e)
        return 0

async def get_tournament_date(user_id):
    try:
        active_comp = await general_queries.get_CompId(user_id)
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
            cur.execute(f"SELECT date2 FROM competition WHERE compId = {active_comp}")
            ans = cur.fetchone()
            return ans['date2']
    except:
        return 0


async def BookNumber_to_name(book_id):
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
            cur.execute(f"SELECT FirstName, LastName FROM judges WHERE BookNumber = {book_id}")
            ans = cur.fetchone()
            return ans['LastName'], ans['FirstName']
    except:
        return 0

async def get_free_judges_for_wrong(user_id, text):
    try:
        ans = []
        active_comp = await general_queries.get_CompId(user_id)
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
            judges_lst = await check_list_judges.get_all_judges(text)
            cur.execute(f"SELECT * FROM competition_judges WHERE compId = {active_comp} and active = 1")
            free = cur.fetchall()
            if len(free) == 0:
                return 'свободных судей нет'

            free1 = free.copy()
            for jud in free:
                flag = 0
                for jud1 in judges_lst:
                    index = jud1.split()
                    if len(index) == 2:
                        last_name, name = index
                    else:
                        last_name = index[0]
                        name = ' '.join(index[1::])

                    if (jud['firstName'] == name and jud['lastName'] == last_name) or (jud['firstName2'] == name and jud['lastName2'] == last_name):
                        flag = 1

                if flag == 0:
                    ans.append(jud)

            return ans
    except:
        return 0



async def check_cat_for_enter_book_number(user_id, book_id):
    try:
        active_comp = await general_queries.get_CompId(user_id)
        book_id = int(book_id)
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
            cur.execute(f"SELECT date1, date2 FROM competition WHERE compId = {active_comp}")
            dates = cur.fetchone()
            date1, date2 = dates['date1'], dates['date2']

            cur.execute(
                f"SELECT SPORT_Category, SPORT_CategoryDate, SPORT_CategoryDateConfirm, DSFARR_Category_Id FROM judges WHERE bookNumber = {book_id}")
            info = cur.fetchone()
            if info is None:
                return 1

            category = info['SPORT_Category']
            SPORT_CategoryDate = info['SPORT_CategoryDate']
            SPORT_CategoryDateConfirm = info['SPORT_CategoryDateConfirm']
            code =['DSFARR_Category_Id']
            if code is None:
                code = 9
            if category == None or SPORT_CategoryDate == None or SPORT_CategoryDateConfirm == None:
                return 0

            if type(SPORT_CategoryDateConfirm) == str and type(SPORT_CategoryDate) == str:
                return 0
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
                    return 0

            elif code == 3:
                if a - 365 > 0:
                    return 0

            elif code == 6:
                if a - 365 * 4 > 0:
                    return 0
            return 1

    except Exception as e:
        print(e)
        return 0

def sort_key(list):
    return list[0], list[1]

async def check_celebrate(user_id, jl):
    try:
        msg = '🥳Дни рождения:\n\n'
        flag = 0
        active_comp = await general_queries.get_CompId(user_id)
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
            cur.execute(f"SELECT date1, date2 FROM competition WHERE compId = {active_comp}")
            ans = cur.fetchone()
            date1, date2 = ans['date1'], ans['date2']
            date1 = datetime.datetime.now().date()
            date2 = str(date2).split('-')
            jl.sort(key= lambda x: x[0])
            for judL in jl:
                lastname, firstname = judL
                cur.execute(f"SELECT lastName, firstName, Birth, City FROM competition_judges WHERE compId = {active_comp} AND Birth IS NOT NULL AND active = 1 AND ((firstName = '{firstname}'AND lastName = '{lastname}') OR (firstName2 = '{firstname}'AND lastName2 = '{lastname}'))")
                jud = cur.fetchone()
                if jud is None:
                    continue

                if type(jud['Birth']) != str:
                    judBirth = str(jud['Birth']).split('-')
                    judBirth[0] = date2[0]
                    judBirth = datetime.datetime.strptime('-'.join(judBirth), '%Y-%m-%d').date()
                    if date1 <= judBirth <= datetime.datetime.strptime('-'.join(date2), '%Y-%m-%d').date():
                        flag = 1
                        msg += f"{jud['lastName']} {jud['firstName']}, {jud['City']}, {jud['Birth']}\n"

            if flag == 1:
                return msg
            else:
                return 0

    except Exception as e:
        print(e)
        return 0


async def set_is_use_0(user_id):
    try:
        active_comp = await general_queries.get_CompId(user_id)
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
            cur.execute(f"update competition_judges set is_use = 0 where compId = {active_comp} and active = 1")
            conn.commit()
    except Exception as e:
        print(e)
        return 0


async def get_comment(user_id):
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
            cur.execute(f"SELECT сomment FROM skatebotusers WHERE tg_id = {user_id}")
            ans = cur.fetchone()
            cur.close()
            if ans['сomment'] is None:
                return 'chairman'
            return ans['сomment']
    except Exception as e:
        print(e)
        return 0




async def del_unactive_comp(tg_id, active_comp):
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
            cur.execute(f"SELECT date2 FROM competition WHERE compId = {active_comp}")
            ans = cur.fetchone()
            now = date.today()
            a = now - ans['date2']
            if a.days > 0:
                cur.execute(f"UPDATE skatebotusers set id_active_comp = NULL WHERE tg_id = {tg_id}")
                conn.commit()
                return 1
            cur.close()
            return 2
    except Exception as e:
        return 0


async def group_id_to_lin_const(compId, group_num):
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
            cur.execute(f"SELECT judges FROM competition_group WHERE compId = {compId} AND groupNumber = {group_num}")
            ans = cur.fetchone()
            cur.close()
            if ans is None:
                return 0

            if ans['judges'] is None:
                return 0

            return ans['judges']
    except Exception as e:
        print(e)
        return 0


async def check_min_category(judgesO, jundesL, group_num, compId, area):
    try:
        ans = []
        ans1 = []
        msg = ''
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
                f"SELECT minCategoryId FROM competition_group WHERE compId = {compId} AND groupNumber = {group_num}")
            mincat = cur.fetchone()
            cur.execute(f"SELECT judgeId, comment FROM competition_group_interdiction WHERE compId = {compId} AND groupNumber = {group_num}")
            black_list = cur.fetchall()
            if black_list == ():
                black_list = []
            else:
                black_list = [i['judgeId'] for i in black_list]


            if mincat is None:
                mincat = 0
            else:
                mincat = mincat['minCategoryId']
                if mincat is None:
                    mincat = 0

            #Проверка остальных на запреты
            for i in judgesO:
                if len(i.split()) == 2:
                    k = i.split()
                    firstname = k[1]
                    lastname = k[0]
                else:
                    k = i.split()
                    firstname = ' '.join(k[1::])
                    lastname = k[0]

                cur.execute(f"SELECT id FROM competition_judges WHERE compId = {compId} AND lastName = '{lastname}' AND firstName = '{firstname}'")
                jud_id = cur.fetchone()
                jud_id = jud_id['id']
                if jud_id in black_list:
                    ans1 += [i]


            #Проверка линейных на запреты/минимальную категорию
            for i in jundesL:
                if len(i.split()) == 2:
                    k = i.split()
                    firstname = k[1]
                    lastname = k[0]
                else:
                    k = i.split()
                    firstname = ' '.join(k[1::])
                    lastname = k[0]
                cur.execute(f"SELECT id FROM competition_judges WHERE compId = {compId} AND lastName = '{lastname}' AND firstName = '{firstname}'")
                jud_id = cur.fetchone()
                jud_id = jud_id['id']
                if jud_id in black_list:
                    ans1 += [i]

                cur.execute(
                    f"SELECT DSFARR_Category_Id FROM competition_judges WHERE compId = {compId} AND firstName = '{firstname}' and lastName = '{lastname}'")

                jud_cat = cur.fetchone()
                jud_cat = jud_cat['DSFARR_Category_Id']
                if jud_cat is None:
                    continue

                if jud_cat < mincat:
                    cur.execute(f"SELECT categoryName from judges_category WHERE categoryId = {jud_cat}")
                    s = cur.fetchone()
                    ans.append(i + f': {s["categoryName"]}\n')


            if len(ans) == 0:
                if len(ans1) == 0:
                    return 1
                else:
                    msg += f'❌Ошибка: {area}: {", ".join(ans1)} - запрещено работать в данной группе\n\n'
                    return msg
            else:
                if len(ans1) == 0:
                    cur.execute(f"SELECT categoryName from judges_category WHERE categoryId = {mincat}")
                    s = cur.fetchone()
                    s = s["categoryName"]
                    q = ''.join(ans)
                    msg = f'❌Ошибка: {area}: Минимальная категория для работы в группе: {s}\n{q}'
                    cur.close()
                    return msg + '\n'
                else:
                    cur.execute(f"SELECT categoryName from judges_category WHERE categoryId = {mincat}")
                    s = cur.fetchone()
                    s = s["categoryName"]
                    q = ''.join(ans)
                    msg = '' + f'❌Ошибка: {area}: Минимальная категория для работы в группе: {s}\n{q}\n'
                    msg += f'❌Ошибка: {area}: {", ".join(ans1)} - запрещено работать в данной группе\n\n'
                    cur.close()
                    return msg

    except Exception as e:
        print(e)
        return 1


async def add_name2(lastname2, firstname2, lastname, firstname, active_comp):
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
            print(firstname, lastname, firstname2, lastname2)
            print()
            cur.execute(f"UPDATE competition_judges set lastName2 = '{lastname2}', firstName2 = '{firstname2}' WHERE compId = {active_comp} and active = 1 and ((firstName = '{firstname}' AND lastName = '{lastname}') OR (firstName2 = '{firstname}' AND lastName2 = '{lastname}'))")
            conn.commit()
            cur.close()
    except Exception as e:
        return 0


async def create_new_booknum(compid):
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
        cur.execute(f"select bookNumber from competition_judges where compId = {compid}")
        a = cur.fetchall()
        a = [i['bookNumber'] for i in a if i['bookNumber'] is not None]
        if len(a) == 0:
            return -1

        if min(a) > 0:
            return -1
        else:
            return min(a) - 1


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
            cur.execute(f"select lastName, firstName from competition_judges where compId = {active_comp} and id = {judid}")
            ans = cur.fetchone()
            r.append(f'{ans["lastName"]} {ans["firstName"]}')
        return ', '.join(r)


async def set_group_counter(data, compId):
    conn = pymysql.connect(
        host=config.host,
        port=3306,
        user=config.user,
        password=config.password,
        database=config.db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    #print(data, "Проставляем счетчики")
    with conn:
        cur = conn.cursor()
        for judge_id in data:
            cur.execute(f"update competition_judges set group_counter = group_counter + 1 WHERE CompId = {compId} and id = {judge_id}")
            conn.commit()
    return 1


async def clean_group_counter(user_id):
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
            active_comp = await general_queries.get_CompId(user_id)
            cur.execute(f"update competition_judges set group_counter = 0 where compId = {active_comp} and active = 1")
            conn.commit()
            return 1
    except:
        return 0


async def get_regionId(active_comp):
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
            cur.execute(f"select regionId from competition where compId = {active_comp}")
            ans = cur.fetchone()
            return ans['regionId']
    except Exception as e:
        print(e)
        return -1


async def set_real_cetegory(user_id, lastname, firstname, name, code):
    try:
        bn = 0
        firstname2 = 'Artem'
        lastname2 = 'Bulatov'
        if name != '':
            i, bn = name.split('|')
            i = i.split()
            bn = int(bn)
            if len(i) == 2:
                lastname2 = i[0]
                firstname2 = i[1]
            else:
                lastname2 = i[0]
                firstname2 = ' '.join(i[1::])

        active_comp = await general_queries.get_CompId(user_id)
        Chairman_menu_handler.last_added_judges[user_id].append([lastname, firstname])
        conn = pymysql.connect(
            host=config.host,
            port=3306,
            user=config.user,
            password=config.password,
            database=config.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )

        notjud = re.match(r'^[a-zA-Z]+\Z', firstname.replace(' ', '')) is not None
        with conn:
            cur = conn.cursor()
            if bn != 0:
                cur.execute(f"SELECT * FROM judges WHERE BookNumber = {bn}")
            else:
                cur.execute(
                    f"SELECT * FROM judges WHERE FirstName = '{firstname}' AND LastName = '{lastname}'")
            person = cur.fetchone()
            BookNumber = person['BookNumber']
            SecondName = person['SecondName']
            Birth = person['Birth']
            DSFARR_Category = person['DSFARR_Category']
            DSFARR_CategoryDate = person['DSFARR_CategoryDate']
            WDSF_CategoryDate = person['WDSF_CategoryDate']
            RegionId = person['RegionId']
            City = person['City']
            Club = person['Club']
            Translit = person['Translit']
            Archive = person['Archive']
            SPORT_Category = person['SPORT_Category']
            SPORT_CategoryDate = person['SPORT_CategoryDate']
            SPORT_CategoryDateConfirm = person['SPORT_CategoryDateConfirm']
            federation = person['federation']
            DSFARR_Category_Id = person['DSFARR_Category_Id']

            cur.execute(f"select date2 from competition where compId = {active_comp}")
            date2 = cur.fetchone()
            date2 = date2['date2']

            date2 = date2 + datetime.timedelta(days=10)
            SPORT_CategoryDate, SPORT_CategoryDateConfirm = date2, date2


            # Если судья уже есть в таблице competition_judges
            cur.execute(
                f"DELETE FROM competition_judges  WHERE (((firstName2 = '{firstname}' AND lastName2 = '{lastname}') OR (firstName = '{firstname}' AND lastName = '{lastname}')) OR ((firstName2 = '{firstname2}' AND lastName2 = '{lastname2}') OR (firstName = '{firstname2}' AND lastName = '{lastname2}'))) AND compId = {active_comp}")
            conn.commit()

            if name != '':
                sql = "INSERT INTO competition_judges (`compId`, `lastName`, `firstName`, `SecondName`, `Birth`, `DSFARR_Category`, `DSFARR_CategoryDate`, `WDSF_CategoryDate`, `RegionId`, `City`, `Club`, `Translit`, `SPORT_Category`, `SPORT_CategoryDate`, `SPORT_CategoryDateConfirm`, `federation`, `Archive`, `bookNumber`, `notJudges`, `is_use`, `firstName2`, `lastName2`, `DSFARR_Category_Id`, `active`, `workCode`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cur.execute(sql, (
                    active_comp, lastname, firstname, SecondName, Birth, DSFARR_Category, DSFARR_CategoryDate,
                    WDSF_CategoryDate,
                    RegionId, City, Club, Translit, SPORT_Category, SPORT_CategoryDate, SPORT_CategoryDateConfirm,
                    federation, Archive, BookNumber, notjud, 0, firstname2, lastname2, DSFARR_Category_Id, 1, code))
                conn.commit()
            else:
                sql = "INSERT INTO competition_judges (`compId`, `lastName`, `firstName`, `SecondName`, `Birth`, `DSFARR_Category`, `DSFARR_CategoryDate`, `WDSF_CategoryDate`, `RegionId`, `City`, `Club`, `Translit`, `SPORT_Category`, `SPORT_CategoryDate`, `SPORT_CategoryDateConfirm`, `federation`, `Archive`, `bookNumber`, `notJudges`, `is_use`, `DSFARR_Category_Id`, `active`, `workCode`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cur.execute(sql, (
                    active_comp, lastname, firstname, SecondName, Birth, DSFARR_Category, DSFARR_CategoryDate,
                    WDSF_CategoryDate,
                    RegionId, City, Club, Translit, SPORT_Category, SPORT_CategoryDate, SPORT_CategoryDateConfirm,
                    federation, Archive, BookNumber, notjud, 0, DSFARR_Category_Id, 1, code))
                conn.commit()
            cur.close()
            return 1
    except Exception as e:
        print(e)
        print('Ошибка выполнения запроса на установку проблемных судей')
        return 0


async def change_generation_mode(user_id):
    try:
        active_comp = await general_queries.get_CompId(user_id)
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
            cur.execute(f"SELECT generation_mode from competition where compId = {active_comp}")
            mode = cur.fetchone()
            mode = mode['generation_mode']
            print(mode, active_comp)
            if mode == 1:
                cur.execute(f"UPDATE competition SET generation_mode = 0 where compId = {active_comp}")
                conn.commit()
                return '💻Режим генерации списков для отпраки информации РСК активирован'
            else:
                cur.execute(f"UPDATE competition SET generation_mode = 1 where compId = {active_comp}")
                conn.commit()
                return '💻Режим генерации списков для гс активирован'
    except Exception as e:
        print(e)
        return -1

async def get_generation_mode(active_comp):
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
            cur.execute(f"SELECT generation_mode from competition where compId = {active_comp}")
            mode = cur.fetchone()
            mode = mode['generation_mode']
            return mode
    except Exception as e:
        print(e)
        return -1


async def get_group_type(compId, groupNumber):
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
            cur.execute(f"SELECT sport from competition_group where compId = {compId} and groupNumber = {groupNumber}")
            mode = cur.fetchone()
            mode = mode['sport']
            return mode
    except Exception as e:
        print(e)
        return -1


async def get_lin_neibors_clubs(a):
    try:
        clubs_list = set()
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
            for i in range(len(a)):
                cur.execute(f'select City, Club from competition_judges where id = {a[i]}')
                req = cur.fetchone()
                if req['City'] is not None and req['Club'] is not None:
                    clubs_list.add(f"{req['City']}, {req['Club']}")

            return clubs_list
    except Exception as e:
        return -1


async def get_min_catId(compId, groupNumber):
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
            cur.execute(f"select minCategoryId from competition_group where compId = {compId} and groupNumber = {groupNumber}")
            ans = cur.fetchone()
            if ans['minCategoryId'] is None:
                return 0
            else:
                return ans['minCategoryId']
    except Exception as e:
        return -1


async def create_zgs(json):
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
            judges = json['judges']
            for jud in judges:
                cur.execute(f"update competition_judges set workCode = 1 where id = {jud}")
                conn.commit()
            return 1
    except Exception as e:
        print(e)
        return -1

async def clear_zgs(compId):
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
            cur.execute(f"update competition_judges set workCode = 0 where workCode = 1")
            conn.commit()
    except Exception as e:
        return -1


async def get_judges_regions(judges, compRegion):
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
            regions = {compRegion: 0}
            for judgeId in judges:
                cur.execute(f"select RegionId from competition_judges where id = {judgeId}")
                region = cur.fetchone()
                if region is None:
                    region = 0
                    continue

                region = region['RegionId']
                if region in regions:
                    regions[region] += 1
                else:
                    regions[region] = 1
            return regions, 1
    except Exception as e:
        return -1, -1

async def get_region_id(compId):
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
            cur.execute(f"select RegionId from competition where compId = {compId}")
            ans = cur.fetchone()
            return ans['RegionId']
    except:
        return -1


from chairman_moves import generation_logic
async def check_rc_a_regions_VE(linjuds, compId, group_num):
    try:
        info = await generation_logic.rc_a_region_rules(0, len(linjuds))
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
            cur.execute(f"select RegionId from competition where compId = {compId}")
            compRegion = cur.fetchone()
            compRegion = compRegion['RegionId']
            all_judges = []

            if compRegion == 0 or compRegion is None:
                return 0

            for jud in linjuds:
                i = jud.split()
                if len(i) == 2:
                    lastname, firstname = i
                else:
                    lastname = i[0]
                    firstname = ' '.join(i[1::])

                cur.execute(f"select id, lastName, firstName, RegionId from competition_judges where compId = {compId} and ((lastName = '{lastname}' and firstName = '{firstname}') or (lastName2 = '{lastname}' and firstName2 = '{firstname}'))")
                jud_bd = cur.fetchall()
                if len(jud_bd) != 1:
                    return 0
                jud_bd = jud_bd[0]
                all_judges.append(jud_bd)
        home, other = info
        regions = {}
        regions_result = 0
        j_r_list = []
        bad_list = set()
        for jud in all_judges:
            jud_region = jud['RegionId']
            j_r_list.append((jud_region, jud['lastName'], jud['firstName']))
            if jud_region in regions:
                regions[jud_region] += 1
            else:
                regions[jud_region] = 1
        for reg in regions:
            if reg == compRegion and regions[reg] > home:
                regions_result += 1
                bad_list.add(reg)
            else:
                if reg != compRegion and regions[reg] > other:
                    regions_result += 1
                    bad_list.add(reg)
        if regions_result == 0:
            return '', 0
        else:
            msg = {}
            for bad_reg in bad_list:
                msg[bad_reg] = []
                for j_r in j_r_list:
                    if j_r[0] == bad_reg:
                        msg[bad_reg].append((j_r[1], j_r[2]))

            return f"Распределение регионов судей не соответствует правилам РС А: {msg}", 1

    except Exception as e:
        return 0


async def is_rc_a(group_num, compId):
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
            cur.execute(f"select sport from competition_group where compId = {compId} and groupNumber = {group_num}")
            ans = cur.fetchone()
            if ans is None:
                return -1
            return ans['sport']
    except:
        return -1

async def update_zgs(compId):
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
            cur.execute(f"update competition_judges set workCode = 0 where workCode = 1")
            conn.commit()
            return 1
    except:
        return -1

async def set_category(compId, groupNumber, code):
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
            cur.execute(f"update competition_group set minCategoryId = {code} where compId = {compId} and groupNumber = {groupNumber}")
            conn.commit()
            return 1
    except:
        return -1

async def set_num_of_judges(compId, groupNumber, code, mode):
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
            if mode == 'l':
                cur.execute(
                    f"update competition_group set judges = {code} where compId = {compId} and groupNumber = {groupNumber}")
                conn.commit()
                return 1
            if mode == 'z':
                cur.execute(
                    f"update competition_group set zgsNumber = {code} where compId = {compId} and groupNumber = {groupNumber}")
                conn.commit()
                return 1
    except:
        return -1


async def set_type_of_group(compId, groupNumber, code):
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
            cur.execute(f"update competition_group set sport = {code} where compId = {compId} and groupNumber = {groupNumber}")
            conn.commit()
            return 1
    except:
        return -1