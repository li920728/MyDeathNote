'''
变量 MT_BBS 
值   账号&密码#账号&密码【都是英文符号】
cron:  0 8 * * *
new Env('MT论坛签到
'''
import requests
import re
import os
from notify import send

proxies = {
    "http": "http://180.101.50.208:443",
    "https": "http://180.101.50.208:443",
}

bbs_url = "https://bbs.binmt.cc/member.php"
credit_url = "https://bbs.binmt.cc/home.php?mod=spacecp&ac=credit"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.50'
}
credit_headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; U; Android 14; zh-cn; 22127RK46C Build/UKQ1.230804.001) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/109.0.5414.118 Mobile Safari/537.36 XiaoMi/MiuiBrowser/18.2.150419',
}

def getLoginHashes(session):
    params = {
        'mod': 'logging',
        'action': 'login'
    }
    login_res = session.get(url=bbs_url, headers=headers, params=params, proxies=proxies)
    try:
        loginhash = re.search(r'loginhash=(.+?)"', login_res.text).group(1)
    except:
        print("登录loginhash查找失败，退出")
        return False
    try:
        formhash = re.search(r'name="formhash" value="(.+?)"', login_res.text).group(1)
    except:
        print("登录formhash查找失败，退出")
        return False
    return loginhash, formhash

def login(session, loginhash, formhash, u, p, loginfield="username"):
    params = {
        'mod': 'logging',
        'action': 'login',
        'loginsubmit': 'yes',
        'loginhash': loginhash,
        'inajax': '1'
    }
    data = {
        'formhash': formhash,
        'loginfield': loginfield,
        'username': u,
        'password': p,
        'questionid': '0',
        'answer': ''
    }
    res = session.post(url=bbs_url, headers=headers, params=params, data=data, proxies=proxies)
    if '欢迎您回来' in res.text:
        return True
    elif "手机号登录成功" in res.text:
        return True
    else:
        print("登录失败\n", res.text)
        return False

def checkin(session):
    checkin_res = session.get(url='https://bbs.binmt.cc/k_misign-sign.html', headers=headers, proxies=proxies)
    try:
        checkin_formhash = re.search('name="formhash" value="(.+?)"', checkin_res.text).group(1)
    except:
        return "签到formhash查找失败，退出"
    res = session.get(f'https://bbs.binmt.cc/plugin.php?id=k_misign%3Asign&operation=qiandao&format=empty&formhash={checkin_formhash}', headers=headers, proxies=proxies)
    if "![CDATA[]]" in res.text:
        return '🎉签到成功'
    elif "今日已签" in res.text:
        return '【签到状态】已完成'
    else:
        print(res.text)
        return '签到失败'

def checkinfo(session):
    res = session.get(url='https://bbs.binmt.cc/k_misign-sign.html', headers=headers, proxies=proxies)
    user = re.search('class="author">(.+?)</a>', res.text).group(1)
    lxdays = re.search('id="lxdays" value="(.+?)"', res.text).group(1)
    lxlevel = re.search('id="lxlevel" value="(.+?)"', res.text).group(1)
    lxreward = re.search('id="lxreward" value="(.+?)"', res.text).group(1)
    lxtdays = re.search('id="lxtdays" value="(.+?)"', res.text).group(1)
    paiming = re.search('您的签到排名：(.+?)<', res.text).group(1)
    msg = f'【MT论坛账号】{user}\n【连续签到】{lxdays}\n【签到等级】Lv.{lxlevel}\n【积分奖励】{lxreward}\n【签到天数】{lxtdays}\n【签到排名】{paiming}\n'
    return msg

def getCredits(session):
    res = session.get(url=credit_url, headers=credit_headers, proxies=proxies)
    try:
        points = re.search(r'积分: <span>(\d+)</span>', res.text).group(1)
    except:
        points = "查找失败"
    try:
        coins = re.search(r'金币: </span>(\d+)\s*&nbsp;', res.text).group(1)
    except:
        coins = "查找失败"
    try:
        praise = re.search(r'好评: </span>(\d+)', res.text).group(1)
    except:
        praise = "查找失败"
    try:
        reputation = re.search(r'信誉: </span>(\d+)', res.text).group(1)
    except:
        reputation = "查找失败"

    msg = f'【总积分】{points}\n【总金币】{coins}\n【好评】{praise}\n【账号信誉】{reputation}\n'
    return msg

def process_accounts(accounts_env):
    accounts = accounts_env.split('#')
    all_msgs = []
    for account in accounts:
        if not account.strip():
            continue
        try:
            config = account.split('&')
            if len(config) != 2:
                print(f"账号配置不完整: {account}")
                continue
            username = config[0]
            password = config[1]
            session = requests.session()
            hashes = getLoginHashes(session)
            if hashes is False:
                msg = f'【{username}】hash获取失败'
            else:
                if "@" in username:
                    loginfield = "email"
                else:
                    loginfield = "username"
                if login(session, hashes[0], hashes[1], username, password, loginfield) is False:
                    msg = f'【{username}】账号登录失败'
                else:
                    login_msg = f'{username}: 登录成功'
                    c = checkin(session)
                    info = checkinfo(session)
                    credits = getCredits(session)
                    msg = f"{login_msg}\n{info}{c}\n{credits}"
            all_msgs.append(msg)
        except Exception as e:
            print(f"处理账号 {account} 时出错: {e}")
            all_msgs.append(f"处理账号 {account} 时出错: {e}")
    return all_msgs

if __name__ == "__main__":
    if 'MT_BBS' in os.environ:
        mt_bbs_value = os.environ['MT_BBS']
        print("###MT论坛签到###")
        result = process_accounts(mt_bbs_value)
        if result:
            # 青龙通知推送
            send('MT论坛签到', '\n————————————\n'.join(result))
        else:
            print('未添加MT_BBS相关变量，退出')
    else:
        print('未找到MT_BBS环境变量，退出')
