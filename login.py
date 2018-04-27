from bilibili import bilibili
from configloader import ConfigLoader
import rsa
import base64
from urllib import parse
import time

    
def calc_name_passw(key, Hash, username, password):
    pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(key.encode())
    password = base64.b64encode(rsa.encrypt((Hash + password).encode('utf-8'), pubkey))
    password = parse.quote_plus(password)
    username = parse.quote_plus(username)
    return username, password


def LoginWithPwd():
    username = ConfigLoader().dic_bilibili['account']['username']
    password = ConfigLoader().dic_bilibili['account']['password']
    response = bilibili().request_getkey()
    value = response.json()['data']
    key = value['key']
    Hash = str(value['hash'])
    username, password = calc_name_passw(key, Hash, username, password)
    
    response = bilibili().normal_login(username, password)
    while response.json()['code'] == -105:
        response = bilibili().login_with_captcha(username, password)
    try:
        # print(response.json())
        data = response.json()['data']
        access_key = data['token_info']['access_token']
        refresh_token = data['token_info']['refresh_token']
        cookie = data['cookie_info']['cookies']
        generator_cookie = (f'{i["name"]}={i["value"]}' for i in cookie)
        cookie_format = ';'.join(generator_cookie)
        dic_saved_session = {
            'csrf': cookie[0]['value'],
            'access_key': access_key,
            'refresh_token': refresh_token,
            'cookie': cookie_format,
            'uid': cookie[1]['value']
            }
        # print(dic_saved_session)
        bilibili().load_session(dic_saved_session)
        if ConfigLoader().dic_user['other_control']['keep-login']:
            ConfigLoader().write2bilibili(dic_saved_session)
        print("[{}] {}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), '密码登陆成功'))
        return True
        
    except:
        print("[{}] 登录失败,错误信息为:{}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())), response.json()['message']))
        return False

def login():    
    if ConfigLoader().dic_bilibili['saved-session']['cookie']:
        bilibili().load_session(ConfigLoader().dic_bilibili['saved-session'])
        return HandleExpire()
    else:
        return LoginWithPwd()
            

def logout():
    response = bilibili().request_logout()
    if response.text.find('成功退出登录') == -1:
        print('登出失败', response)
    else:
        print('成功退出登陆')

                
def check_token():
    response = bilibili().request_check_token()
    json_response = response.json()
    if not json_response['code'] and json_response['data'].get('mid', ''):
        print('token有效期检查: 仍有效')
        # print(json_response)
        return True
    print('token可能过期')
    return False

        
def RefreshToken():
    # return
    response = bilibili().request_refresh_token()
    json_response = response.json()
    # print(json_response)
    if not json_response['code'] and json_response['data'].get('mid', ''):
        print('token刷新成功')
        dic_saved_session = {
                'access_key': json_response['data']['access_token'],
                'refresh_token': json_response['data']['refresh_token']
                }
        bilibili().load_session(dic_saved_session)
        if ConfigLoader().dic_user['other_control']['keep-login']:
            ConfigLoader().write2bilibili(dic_saved_session)
        # 更新token信息
        return True
    print('联系作者(token刷新失败，cookie过期)', json_response)
    return False
    
def HandleExpire():
    if not check_token():
        if not RefreshToken():
            return LoginWithPwd()
    return True
    
            

        
        

    
