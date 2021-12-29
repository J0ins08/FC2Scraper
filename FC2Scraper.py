# -*- encoding: utf-8 -*-
#@File      :   FC2Scraper.py
#@Time      :   2021/12/27 15:06:38
#@Author    :   J0ins08
#@Software  :   Visual Studio Code

import configparser
import os
import time
import traceback
import re
import platform
import tkinter.filedialog
import urllib.request
from bs4 import BeautifulSoup
from pathlib import Path
import sys
import datetime

def time_now():
    '''获取时间'''
    return str(datetime.datetime.now())[:-7]

def exit_after_5_seconds():
    '''5秒后退出程序'''
    for i in range(5,0,-1):
        print('\r' f'> 程序将在{i}秒后退出。', end='',flush=True)
        time.sleep(1)
    sys.exit()

def error_log(log):
    '''打印错误日志'''
    print(error_red + log)
    error_log_file = Path(scraper_path).joinpath('log.txt')
    with open(error_log_file, 'a', encoding='utf-8') as f:
        print(f'[{time_now()}] ' + log, file=f)

def check_config():
    '''检查config.ini配置文件'''
    config_file = Path(scraper_path).joinpath('config.ini')
    if Path(config_file).exists():
        config = configparser.ConfigParser()
        config.read(config_file,encoding='utf-8')

        global option_rename, option_move, option_output
        try:
            option_rename = config.getboolean('RENAME', 'rename')
            option_move = config.getboolean('MOVE', 'move')
            option_output = config.getboolean('OUTPUT', 'output')
        except ValueError as e:
            traceback_fromat = traceback.format_exc()
            e_reason = re.search('Not a boolean: (.+)',str(e)).group(1)
            result = re.search("config.getboolean[(]'(.+?)', '(.+?)'[)]", 
                               traceback_fromat)
            log = (f'初始化失败。[{result.group(1)}]模块中的{result.group(2)}'
                   f'选项应为True或False，不能为{e_reason}。')
            error_log(log)
            exit_after_5_seconds()

        global option_rename_format, option_move_to, option_output_format
        option_rename_format= config.get('RENAME', 'name-format')
        option_output_format = config.get('OUTPUT', 'output-format')
        option_move_to = config.get('MOVE','move-to')
        if '{number}' not in option_rename_format:
            log = ('初始化失败。[RENAME]模块中的name-format选项应包含{number}'
                   '(含花括号{})。')
            error_log(log)
            exit_after_5_seconds()
        if platform.system() == 'Windows':
            charts = ['<','>','/','\\','|',':','"','*','?']
            for chart in charts:
                if chart in option_rename_format:
                    log = ('初始化失败。[RENAME]模块中的name-format选项'
                           f'设置的文件名不能有{chart}字符。')
                    error_log(log)
                    exit_after_5_seconds()
        elif platform.system() == 'Darwin':
            if (option_rename_format.startswith('.') or 
                    ':' in option_rename_format):
                log = ('初始化失败。[RENAME]模块中的name-format选项'
                       '设置的文件名不能以.开头且不能有:字符。')
                error_log(log)
                exit_after_5_seconds()
        if option_output:
            keywords = re.findall('{.*?}',option_output_format)
            if keywords == []:
                log = (
                    '初始化失败。[OUTPUT]模块中的output-format选项应包含{year}、'
                    '{director}、{number}中的一个或多个(含花括号{})，'
                    '否则请将output选项设为False。')
                error_log(log)
                exit_after_5_seconds()
            else:
                for keyword in keywords:
                    if (keyword != '{director}' and keyword != '{year}' and 
                            keyword != '{number}'):
                        log = (
                            '初始化失败。[OUTPUT]模块中的output-format选项花括号{}'
                            f'内只能为director、year、number，不能为{keyword}。')
                        error_log(log)
                        exit_after_5_seconds()
    else:
        log = f'初始化失败。程序所在路径：{scraper_path}未找到config.ini配置文件。'
        error_log(log)
        exit_after_5_seconds()

def get_videos():
    '''获取程序所在目录内所有影片'''
    files = os.listdir(scraper_path)
    global videos
    videos = []
    for file in files:
        if (file.endswith('mp4') or file.endswith('avi') or file.endswith('ts') 
                or file.endswith('mkv') or file.endswith('mov')):
            videos.append(file)

def select_videos():
    '''手动选择影片'''
    root = tkinter.Tk()
    root.withdraw()
    root.focus_force()
    return tkinter.filedialog.askopenfilenames(
        title='请选择需要削刮的影片：', 
        filetypes=[('视频', '*.mp4 *.ts *.avi *.mkv *.mov'), ('All Files', '*')])

def get_video_num(video_basename_text):
    '''通过文件名匹配影片番号'''
    try:
        video_num = re.search('\d{6,}',video_basename_text).group()
        if len(video_num) > 8:
            log = f'{video_basename} 匹配不到番号。请检查文件名后重试。'
            error_log(log)
        elif len(video_num) == 8:
            if f'fc{video_num}' in video_basename_text.lower():
                video_num = video_num[1:]
            else:
                log = f'{video_basename} 匹配不到番号。请检查文件名后重试。'
                error_log(log)
        elif len(video_num) == 7:
            if f'fc{video_num}' in video_basename_text.lower():
                video_num = video_num[1:]
        return video_num
    except AttributeError:
        log = f'{video_basename} 匹配不到番号。请检查文件名后重试。'
        error_log(log)

def askURL(video_num):
    '''从FC2官网获取信息'''
    url = f'https://adult.contents.fc2.com/article/{video_num}/'
    headers = {
        "Accept-Language": "zh-CN,zh;q=0.9",
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/96.0.4664.45 Safari/537.36 Edg/96.0.1054.29")}
    print(f'尝试从{url}获取信息...')
    req = urllib.request.Request(url=url, headers=headers)
    response = urllib.request.urlopen(req).read().decode('utf-8')
    soup = BeautifulSoup(response,'html.parser')
    if soup.title.string == '没有发现您要找的商品':
        if soup.find('h3').string == '非常抱歉，此商品未在您的居住国家公开。':
            log = (f'{video_basename} 削刮失败。该影片卖家只对特定地区销售，'
                   '请更换科学上网线路后重试。')
            error_log(log)
        elif soup.find('h3').string == '非常抱歉，找不到您要的商品。':
            log = (f'{video_basename} 削刮失败。番号{video_num}不存在'
                   '或该影片已下架。')
            error_log(log)
    else:
        global nfo_items
        nfo_items = {}
        nfo_items['title'] = soup.find('meta',
                                       {'name':"twitter:title"})['content']
        nfo_items['sorttitle'] = re.search(
            'FC2-PPV-\d+', 
            soup.find('meta',{'name':"keywords"})['content']).group()
        nfo_items['date'] = soup.find(
            text=re.compile('\d{4}[-/]\d{2}[-/]\d{2}'))[-10:]
        nfo_items['year'] = nfo_items['date'][:4]
        nfo_items['director'] = soup.select("h4 > a")[0].get_text()
        nfo_items['tag'] = []
        for tag in soup.find_all('a',{'class':'tag tagTag'}):
            nfo_items['tag'].append(tag.get_text())
        nfo_items['plot'] = soup.find('meta',{'name':"description"})['content']
        result = str(soup.find('script', {'type':"application/ld+json"}))
        nfo_items['post'] = re.search("\"image\":{\"url\":\"(.*?)\"", 
                                      result).group(1).replace('\\','')
        nfo_items['rating'] = re.search("\"ratingValue\":(\d)", result).group(1)
        nfo_items['votes'] = re.search("\"reviewCount\":(\d+)", result).group(1)
        nfo_items['id'] = re.findall("article:(\d+)",result)[0]
    return nfo_items

def get_target_dir(target_dir):
    '''获取保存文件夹'''
    for keyword in re.findall('{.*?}', option_output_format):
        if 'director' in keyword:
            target_dir = Path(target_dir).joinpath(nfo_items['director'])
        elif 'year' in keyword:
            target_dir = Path(target_dir).joinpath(nfo_items['year'])
        elif 'number' in keyword:
            target_dir = Path(target_dir).joinpath(nfo_items['id'])
    return target_dir

def write2nfo(nfo_file):
    '''往NFO文件写入内容'''
    nfo_contents = f'''<?xml version="1.0" encoding="UTF-8"?>
    <movie>
        <title>{nfo_items['title']}</title>
            <sorttitle>{nfo_items['sorttitle']}</sorttitle>
        <rating name="FC2" max="5">
            <value>{nfo_items['rating']}</value>
            <votes>{nfo_items['votes']}</votes>
        </rating>
        <plot>{nfo_items['plot']}</plot>
        <id>{nfo_items['id']}</id>
        <director>{nfo_items['director']}</director>
        <premiered>{nfo_items['date']}</premiered>
        <year>{nfo_items['year']}</year>
'''
    with open(nfo_file, 'w', encoding='utf-8') as f:
        f.write(nfo_contents)
        for tag in nfo_items['tag']:
            f.write(f'\t\t<genre>{tag}</genre>\n')
        f.write('\t</movie>')

def save_data(target_video_name, target_video_name_text):
    '''下载封面，移动文件，保存nfo文件。'''
    os.rename(video, Path(target_dir).joinpath(target_video_name))
    urllib.request.urlretrieve(
        nfo_items['post'], 
        Path(target_dir).joinpath(f'{target_video_name_text}.jpg'))
    nfo_file = Path(target_dir).joinpath(f'{target_video_name_text}.nfo')
    write2nfo(nfo_file)
    print(f'> {video_basename} 削刮成功。')

def check_option_rename():
    '''检查是否需要重命名'''
    Path(target_dir).mkdir(parents=True, exist_ok=True)
    if option_rename:
        global target_video_name_text, target_video_name
        target_video_name_text = option_rename_format.replace('{number}', 
                                                              nfo_items['id'])
        target_video_name = video_basename.replace(video_basename_text, 
                                                   target_video_name_text)
        save_data(target_video_name, target_video_name_text)
    else:
        target_video_name = video_basename
        target_video_name_text = video_basename_text
        save_data(target_video_name, target_video_name_text)

def scrape_video():
    '''削刮影片'''
    global video_dirname, video_basename, video_basename_text, video, target_dir
    for video in videos:
        video_dirname = Path(video).parent
        video_basename = Path(video).name
        video_basename_text = Path(video_basename).stem
        video_num = get_video_num(video_basename_text)
        if video_num != None and len(video_num) < 8:
            print(f'> 从{video_basename}匹配到番号{video_num}。')
            try:
                nfo_items = askURL(video_num)
            except Exception:
                continue
            else:
                if not option_move and not option_output:
                    target_dir = video_dirname
                    check_option_rename()
                elif not option_move and option_output:
                    target_dir = get_target_dir(video_dirname)
                    check_option_rename()
                elif option_move and not option_output:
                    target_dir = option_move_to
                    check_option_rename()
                elif option_move and option_output:
                    target_dir = get_target_dir(option_move_to)
                    check_option_rename()
        else:
            continue

logo = '''
______ _____  _____   _____                                
|  ___/  __ \/ __  \ /  ___|                               
| |_  | /  \/`' / /' \ `--.  ___ _ __ __ _ _ __   ___ _ __ 
|  _| | |      / /    `--. \/ __| '__/ _` | '_ \ / _ \ '__|
| |   | \__/\./ /___ /\__/ / (__| | | (_| | |_) |  __/ |   
\_|    \____/\_____/ \____/ \___|_|  \__,_| .__/ \___|_|   
                                          | |              
                                          |_|              
'''
scraper_path = Path(sys.argv[0]).parent
error_red = "\033[1;31m[错误]\033[0m"

if __name__ == '__main__':
    print(logo)
    print('程序开始初始化...')
    check_config()
    print('> 初始化完成。')
    print(f'尝试在当前程序所在目录:{scraper_path}中查找影片...')
    get_videos()
    if videos:
        print(f'> 该目录内有{len(videos)}部影片。')
        for i in range(len(videos)):
            videos[i] = Path(scraper_path).joinpath(videos[i])
        print('开始削刮影片...')
        scrape_video()
        print('\n> 该文件夹内所有影片已削刮完毕。')
        exit_after_5_seconds()
    else:
        print('> 该目录内没有影片,请手动选择。')
        while True:
            videos = select_videos()
            if videos == '':
                print('> 你已取消选择。')
                answer = input('> 按Q(uit)退出程序或按回车键继续：')
                if answer.lower() == 'q':
                    sys.exit()
            else:
                print('开始削刮影片...')
                scrape_video()
            answer = input('> 按Q(uit)退出程序或按回车键继续：')
            if answer.lower() == 'q':
                sys.exit()
