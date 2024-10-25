from nonebot.plugin import on_command, on_request, on_notice
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import GroupRequestEvent, Bot, GroupDecreaseNoticeEvent
from .checker import *


# 入群申请事件判定
async def is_group_request(event: GroupRequestEvent):
    return isinstance(event, GroupRequestEvent) and event.sub_type == 'add'

group_join_request = on_request(rule=is_group_request, priority=1)


@group_join_request.handle()
async def handle_request(
    bot: Bot,
    event: GroupRequestEvent,
):
    # 获取入群申请事件
    logger.info('开始处理入群申请事件')
    join_request = json.loads(event.model_dump_json())
    userid = str(event.user_id)
    groupid = str(event.group_id)
    comment = event.comment
    flag = event.flag
    nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(join_request['time']))
    question = comment.split('答案：')[0]
    comment = comment.split('答案：')[1]
    logger.info(f'已获取({groupid})({userid})的入群申请事件')

    # 判断是否在处理范围内
    maingroup_info = get_maingroup_info()
    if str(groupid) not in maingroup_info.keys() or maingroup_info[str(groupid)] is False:
        logger.info(f'无权处理申请({groupid})({userid})')
        return

    # 进行事件处理
    config = Config(maingroup=str(groupid))
    checks = config.get_checks()
    checked = False

    name = ''

    # 年级、学院、姓名 三字段认证
    if set(checks) == {'grade', 'deptid', 'cnname'}:
        match = re.match(r"([\u4e00-\u9fa5a-zA-Z0-9]+)\s*[\+\^&*#@$% ]\s*([\u4e00-\u9fa5a-zA-Z0-9]+)\s*[\+\^&*#@$%]\s*([\u4e00-\u9fa5a-zA-Z0-9]+)", comment)
        if match:
            info = {checks[0]: match.group(1), checks[1]: match.group(2), checks[2]: match.group(3)}
            student = Student(grade=info['grade'], deptid=info['deptid'], cnname=info['cnname'])
            name = student.get_name()
            student.name = name
            if get_request_count(groupid, userid, checks) >= 3:
                msg = "该QQ号已达自动核验上限(3次)，请手动核验\n"
                msg += f"申请信息：{comment}\nQQ号：{userid}"
            elif student.check_cnname_grade() and student.check_cnname_deptid():
                if student.name and is_passed(groupid, student.get_name(), checks):
                    msg = f"该用户信息已被{is_passed(groupid, student.get_name(), checks)}使用，请手动确认\n"
                    msg += f"申请信息：{comment}\nQQ号：{userid}"
                else:
                    msg = "信息核验通过\n"
                    msg += f"申请信息：{comment}\nQQ号：{userid}"
                    # 通过入群申请
                    await bot.set_group_add_request(
                        flag=flag,
                        approve=True,
                        sub_type='add',
                    )
                    checked = True
            else:
                msg = "信息核验未通过，请手动核验\n"
                # 尝试查找信息
                if student.name:
                    sinfo = student.search_by_name('name, cnname, deptid')
                    msg += f'学号：{sinfo[0]}\n'
                    msg += f'姓名：{sinfo[1]}\n'
                    msg += f'学院：{sinfo[2]}\n'
                msg += f"申请信息：{comment}\nQQ号：{userid}"
                checked = False
        else:
            msg = f"正则匹配失败，请手动核验\n申请信息：{comment}\nQQ号：{userid}"
            upload_bug_log(question, comment, groupid, userid, nowtime)
    # (校区)、学院、学号 二字段认证
    elif set(checks) == {'deptid', 'name'}:
        for c in re.findall(r"\d+", comment):
            if 8 <= len(c) <= 14:
                name = c
        if name:
            student = Student(name=name, deptid=comment)
            if not student.search_by_name('name'):
                msg = f"学号不存在！\n申请信息：{comment}\nQQ号：{userid}"
            elif get_request_count(groupid, userid, checks) >= 3:
                msg = "该QQ号已达自动核验上限(3次)，请手动核验\n"
                msg += f"申请信息：{comment}\nQQ号：{userid}"
            elif student.check_name_deptid():
                if student.get_name() and is_passed(groupid, student.get_name(), checks):
                    msg = f"该用户信息已被{is_passed(groupid, student.get_name(), checks)}使用，请手动确认\n"
                    msg += f"申请信息：{comment}\nQQ号：{userid}"
                else:
                    msg = "信息核验通过\n"
                    msg += f"申请信息：{comment}\nQQ号：{userid}"
                    # 通过入群申请
                    await bot.set_group_add_request(
                        flag=flag,
                        approve=True,
                        sub_type='add',
                    )
                    checked = True
            else:
                msg = "信息核验未通过，请手动核验\n"
                # 尝试查找信息
                if student.name:
                    sinfo = student.search_by_name('name, cnname, deptid')
                    msg += f'学号：{sinfo[0]}\n'
                    msg += f'姓名：{sinfo[1]}\n'
                    msg += f'学院：{sinfo[2]}\n'
                msg += f"申请信息：{comment}\nQQ号：{userid}"
                checked = False
        else:
            msg = f"学号不存在！\n申请信息：{comment}\nQQ号：{userid}"
    else:
        msg = '出错辣'

    if upload_request_log(groupid, userid, comment, checks, checked, nowtime, name):
        if config.get_admins():
            for admin in config.get_admins():
                await bot.send_private_msg(user_id=int(admin), message=msg)
        if config.get_admingroups():
            for admingroup in config.get_admingroups():
                await bot.send_group_msg(group_id=int(admingroup), message=msg)
        logger.info(f'已发送msg({groupid})({userid})')
    return


# 退群事件判定
async def is_leave_group_notice(event: GroupDecreaseNoticeEvent):
    return isinstance(event, GroupDecreaseNoticeEvent)

leave_group_notice = on_notice(rule=is_leave_group_notice, priority=2)

@leave_group_notice.handle()
async def update_leave(
    event: GroupDecreaseNoticeEvent,
):
    logger.info('开始处理退群事件')
    userid = str(event.user_id)
    groupid = str(event.group_id)
    # 判断是否在处理范围内
    maingroup_info = get_maingroup_info()
    if str(groupid) not in maingroup_info.keys() or maingroup_info[str(groupid)] is False:
        logger.info(f'无权处理退群事件({groupid})({userid})')
        return

    cur.execute("UPDATE request_log SET checks = ARRAY['left'] WHERE groupid = %s AND userid = %s", (groupid, userid))
    con.commit()
    logger.info(f'已更新({groupid})({userid})的入群状态')