# -*- coding: gbk -*-
import json
import psycopg2
import re
import time

# 隐藏db


con = psycopg2.connect(database=d['database'], user=d['user'], password=d['password'], host=d['host'], port=d['port'])
cur = con.cursor()


class Student:
    def __init__(self, name=None, cnname=None, grade=None, deptid=None, major=None):
        self.name = name
        self.cnname = cnname
        self.grade = parse_grade(grade) if grade is not None else None
        self.deptid = deptalias_to_deptid(deptid) if deptid is not None else None
        self.major = major

    def __str__(self):
        return f"{self.name}, {self.cnname}, {self.grade}, {self.deptid}, {self.major}"

    def having_name(self):
        cur.execute("SELECT 1 FROM student WHERE name = %s", (self.name, self.cnname))
        return bool(cur.fetchone())

    def check_name_cnname(self):
        cur.execute("SELECT 1 FROM student WHERE name = %s AND cnname = %s", (self.name, self.cnname))
        return bool(cur.fetchone())

    def check_name_grade(self):
        cur.execute("SELECT 1 FROM student WHERE name = %s AND grade = %s", (self.name, self.grade))
        return bool(cur.fetchone())

    def check_name_deptid(self):
        for d in self.deptid:
            cur.execute("SELECT 1 FROM student WHERE name = %s AND deptid = %s", (self.name, d))
            if cur.fetchone():
                return True
        return False

    def check_name_major(self):
        cur.execute("SELECT 1 FROM student WHERE name = %s AND major = %s", (self.name, self.major))
        return bool(cur.fetchone())

    def check_cnname_grade(self):
        cur.execute("SELECT 1 FROM student WHERE cnname = %s AND grade = %s", (self.cnname, self.grade))
        return bool(cur.fetchone())

    def check_cnname_deptid(self):
        for d in self.deptid:
            cur.execute("SELECT 1 FROM student WHERE cnname = %s AND deptid = %s", (self.cnname, d))
            if cur.fetchone():
                return True
        return False

    def check_cnname_major(self):
        cur.execute("SELECT 1 FROM student WHERE cnname = %s AND major = %s", (self.cnname, self.major))
        return bool(cur.fetchone())

    def get_name(self):
        name = []
        if self.deptid is not None:
            for d in self.deptid:
                cur.execute(f"SELECT name FROM student WHERE ({self.name is None} OR name = %s) AND ({self.cnname is None} OR cnname = %s) AND ({self.grade is None} OR grade = %s) AND ({d is None} OR deptid = %s) AND ({self.major is None} OR major = %s)", (self.name, self.cnname, self.grade, d, self.major))
                name += [c[0] for c in cur.fetchall()]
        else:
            cur.execute(f"SELECT name FROM student WHERE ({self.name is None} OR name = %s) AND ({self.cnname is None} OR cnname = %s) AND ({self.grade is None} OR grade = %s) AND ({self.major is None} OR major = %s)", (self.name, self.cnname, self.grade, self.major))
            name += [c[0] for c in cur.fetchall()]
        if len(name) == 1:
            return name[0]
        else:
            return None

    def search_by_name(self, arg):
        cur.execute(f"SELECT {arg} FROM student WHERE name = %s", (self.name,))
        return cur.fetchone()

class Config:
    def __init__(self, maingroup, enabled=False, admingroups=None, admins=None):
        self.maingroup = maingroup
        self.admingroups = admingroups
        self.enabled = enabled
        self.admins = admins

    def having(self):
        cur.execute("SELECT 1 FROM config WHERE maingroup = %s", (self.maingroup,))
        return bool(cur.fetchone())

    def upload(self):
        if not self.having():
            cur.execute("INSERT INTO config (maingroup, enabled, admingroups, admins) VALUES (%s, %s, %s, %s)", (self.maingroup, self.enabled, self.admingroups, self.admins))
            con.commit()
            return True
        else:
            return False

    def enable(self):
        if self.having():
            cur.execute("UPDATE config SET enabled = true WHERE maingroup = %s", (self.maingroup,))
            con.commit()
            return True
        else:
            return False

    def disable(self):
        if self.having():
            cur.execute("UPDATE config SET enabled = false WHERE maingroup = %s", (self.maingroup,))
            con.commit()
            return True
        else:
            return False

    def get_checks(self):
        cur.execute("SELECT checks FROM config WHERE maingroup = %s", (self.maingroup,))
        return cur.fetchone()[0]

    def get_admins(self):
        cur.execute("SELECT admins FROM config WHERE maingroup = %s", (self.maingroup,))
        data = cur.fetchone()
        if data:
            return data[0]
        else:
            return None

    def get_admingroups(self):
        cur.execute("SELECT admingroups FROM config WHERE maingroup = %s", (self.maingroup,))
        data = cur.fetchone()
        if data:
            return data[0]
        else:
            return None

"""    async def send_admin_msg(self, bot, msg):
        if self.get_admins():
            for admin in self.get_admins():
                await bot.send_private_message(user_id=int(admin), message=msg)
        if self.get_admingroups():
            for admingroup in self.get_admingroups():
                await bot.send_group_message(group_id=int(admingroup), message=msg)"""



def get_maingroup_info():
    cur.execute("SELECT maingroup, enabled FROM config")
    maingroup_info = cur.fetchall()
    if maingroup_info is not None:
        maingroup_info = {g[0]: g[1] for g in maingroup_info}
    else:
        maingroup_info = {}
    return maingroup_info

def upload_bug_log(groupid, userid, question, request, time):
    cur.execute("INSERT INTO bug_log (question, request, groupid, userid, time) VALUES (%s, %s, %s, %s, %s)", (question, request, groupid, userid, time))
    con.commit()
    return True

def upload_request_log(groupid, userid, request, checks, checked, time, name=None):
    cur.execute("SELECT 1 FROM request_log WHERE groupid = %s AND userid = %s AND request = %s AND checks = %s::varchar[] AND checked = %s", (groupid, userid, request, checks, checked))
    his_log = cur.fetchone()
    if his_log is None:
        cur.execute("INSERT INTO request_log (groupid, userid, request, checks, checked, time, name) VALUES (%s, %s, %s, %s, %s, %s, %s)", (groupid, userid, request, checks, checked, time, name))
        con.commit()
        return True
    else:
        return False

def get_request_count(groupid, userid, checks):
    cur.execute("SELECT 1 FROM request_log WHERE groupid = %s AND userid = %s AND checks = %s::varchar[]", (groupid, userid, checks))
    data = cur.fetchall()
    if data is not None:
        return len(data)
    return 0

def is_passed(groupid, name, checks):
    cur.execute("SELECT userid FROM request_log WHERE checked = TRUE AND groupid = %s AND name = %s AND checks = %s::varchar[]", (groupid, name, checks))
    userid = cur.fetchone()
    if userid is None:
        return None
    else:
        return userid[0]

def parse_grade(grade_str):
    # 匹配 "2023", "2023级", "23", "23级" 格式
    match = re.match(r"(\d{2,4})(级?)", grade_str)
    if match:
        year = match.group(1)
        # 如果是两位数，推断为2000年代的年份，比如 "23" => "2023"
        if len(year) == 2:
            return f"20{year}级"
        return year + '级'

    # 处理"大一"、"大二"、"大三"、"大四"、"大五"
    match = re.match(r"(大?)[一二三四五](年?)(级?)", grade_str)
    if match:
        if '一' in grade_str:
            return '2024级'
        elif '二' in grade_str:
            return '2023级'
        elif '三' in grade_str:
            return '2022级'
        elif '四' in grade_str:
            return '2021级'
        elif '五' in grade_str:
            return '2020级'
    return None

def deptalias_to_deptid(deptalias):
    with open('./src/plugins/group_request_auto_check/DeptAlias.json', 'r', encoding='gbk') as f:
        deptid = json.load(f)
    result = []
    for key, value in deptid.items():
        if key in deptalias:
            result.append(key)
        for v in value:
            if v in deptalias:
                result.append(key)
    return list(set(result))

c = Config(maingroup='894224667')
