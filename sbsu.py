import os, time
from selenium import webdriver
from retrying import retry
import requests

#from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

options = webdriver.FirefoxOptions()
options.add_argument("--headless") #设置火狐为headless无界面模式
options.add_argument("--disable-gpu")
options.add_argument('user-agent=Mozilla/5.0 (iPad; CPU OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1')
driver = webdriver.Firefox(executable_path=f"{os.environ['GITHUB_ACTION_PATH']}/eck new.exe", options=options)


print("初始化selenium driver完成")

ocr_token = os.environ['OCR_TOKEN']


# 失败后随机 1-3s 后重试，最多 10 次
@retry(wait_random_min=1000, wait_random_max=3000, stop_max_attempt_number=10)
def login():
    print("访问登录页面")
    driver.get("https://cas.sysu.edu.cn/cas/login")
    time.sleep(10)

    print("读取用户名密码")
    try:
        netid = os.environ['NETID']
        password = os.environ['PASSWORD']
    except:
        print("err 00")

    print("输入用户名密码")
    try:    
        driver.find_element_by_xpath('//*[@id="username"]').send_keys(netid)
    except:
        print("err 01")
    try: 
        driver.find_element_by_xpath('//*[@id="password"]').send_keys(password)
    except:
        print("err 02")

    print("识别验证码")
    code = get_img(driver, ocr_token)
    print("输入验证码")
    driver.find_element_by_xpath('//*[@id="captcha"]').send_keys(code)

    # 点击登录按钮
    print("登录信息门户")
    driver.find_element_by_xpath('//*[@id="fm1"]/section[2]/input[4]').click()
    try:
        print(driver.find_element_by_xpath('//*[@id="cas"]/div/div[1]/div/div/h2').text)
    except:
        print(driver.find_element_by_xpath('//*[@id="fm1"]/div[1]/span').text)
        raise Exception('登陆失败')

# 失败后随机 3-5s 后重试，最多 6 次
@retry(wait_random_min=3000, wait_random_max=5000, stop_max_attempt_number=6)
def jksb():
    print('访问健康申报页面')
    driver.get("http://jksb.sysu.edu.cn/infoplus/form/XNYQSB/start")
    time.sleep(20)
    try:
        number = driver.find_element_by_xpath('//*[@id="title_description"]').text
        print('打开健康申报成功')
    except:
        print('打开健康申报失败')
        raise Exception('打开健康申报失败')

    print("点击下一步")
    driver.find_element_by_xpath('//*[@id="form_command_bar"]/li[1]').click()
    time.sleep(20)

    print("提交健康申报")
    driver.find_element_by_xpath('//*[@id="form_command_bar"]/li[1]').click()
    time.sleep(20)
    result = driver.find_element_by_xpath('//div[8]/div/div[1]/div[2]').text
    print("完成健康申报")
    return f'{number}: {result}'

def get_img(driver, token):
    ''' 调用 http://fast.95man.com 在线识别验证码
    '''

    headers = {'Connection': 'Keep-Alive',
        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)'}
    cookies = driver.get_cookies()
    s = requests.Session()
    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])

    url = "https://cas.sysu.edu.cn/cas/captcha.jsp"
    res =  s.get(url)
    
    if token.startswith('RECURL'):
        files = {'img': ('captcha.jpg', res.content, 'image/jpeg')}
        r =  requests.post(token[6:], files = files)
        if len(r.text) == 4:
            capt = r.text
            print(f'验证码识别成功：{capt}')
            return capt
        else:
            print(f'识别失败：{r.text}，重试')
            raise Exception('验证码识别失败')
    else:
        files = {'imgfile': ('captcha.jpg', res.content)}
        r = requests.post(f'http://api.95man.com:8888/api/Http/Recog?Taken={token}&imgtype=1&len=4', 
            files=files, headers=headers)
        arrstr = r.text.split('|')
        # 返回格式：识别ID|识别结果|用户余额
        if(int(arrstr[0]) > 0):
            print(f'验证码识别成功：{arrstr[1]}')
            capt = arrstr[1]
            return capt
        else:
            print(f'识别失败：{arrstr[1]}，重试')
            raise Exception('验证码识别失败')


if __name__ == "__main__":
    login()
    time.sleep(4)
    try:
        result = jksb()
    except:
        result = '健康申报失败'
        print(result)
    driver.quit()

    # 判断是否发送通知

