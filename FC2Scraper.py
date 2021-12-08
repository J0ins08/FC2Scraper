# -*- encoding: utf-8 -*-
#@File      :   FC2Scraper.py
#@Time      :   2021/12/08 21:42:21
#@Author    :   J0ins08
#@Software  :   Visual Studio Code

import re 
import urllib 
import urllib.request
import urllib.parse
import os
import sys
import time
import tkinter.filedialog
import configparser
from bs4 import BeautifulSoup
import time
import platform
os.environ['TK_SILENCE_DEPRECATION'] = 1

def get_num(video_name):
    if re.compile('[0-9]+').findall(os.path.splitext(video_name)[0]) == []:
        return 'None'
    if len(re.search('\d+',video_name).group()) > 7 and len(re.search('\d+',video_name).group()) < 6:
        return 'None'
    else:
        video_num = re.search('\d{6,7}',video_name).group()
        print('%s匹配到番号%s。'%(warning,video_num))
        return video_num

def askURL(video_num):
    url = 'https://adult.contents.fc2.com/article/%s/'%video_num
    print('%s正在向%s请求数据……'%(warning,url))
    headers = {
    "Accept-Language": "zh-CN,zh;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36 Edg/96.0.1054.29"
}
    request = urllib.request.Request(url = url, headers = headers)
    response = urllib.request.urlopen(request)
    response = response.read().decode("utf-8")
    soup = BeautifulSoup(response,"html.parser")
    if soup.title.string == '没有发现您要找的商品':
        if soup.find('h3').string == '非常抱歉，此商品未在您的居住国家公开。':
            print('%s削刮失败。该影片卖家只对特定地区销售，请更换科学上网线路后重试。'%error)
            return 'error1'
        elif soup.find('h3').string == '非常抱歉，找不到您要的商品。':
            print('%s削刮失败。该影片已下架或文件名错误。'%error)
            return 'error2'
    else:
        nfo_dict = {'title':'','sorttitle':'','year':'','date':'','director':'','tag':[],'plot':'','post':'','rating':'','votes':'','id':''}
        nfo_dict['title'] = soup.find('meta',{'name':"twitter:title"})['content']
        nfo_dict['sorttitle'] = re.search('FC2-PPV-\d+',soup.find('meta',{'name':"keywords"})['content']).group()
        nfo_dict['year'] = soup.find(text=re.compile('\d{4}[-/]\d{2}[-/]\d{2}'))[-10:-6]
        nfo_dict['date'] = soup.find(text=re.compile('\d{4}[-/]\d{2}[-/]\d{2}'))[-10:]
        nfo_dict['director'] = soup.select("h4 > a")[0].get_text()
        for tag in soup.find_all('a',{'class':'tag tagTag'}):
            nfo_dict['tag'].append(tag.get_text())
        nfo_dict['plot'] = soup.find('meta',{'name':"description"})['content']
        nfo_dict['post'] = re.findall("\"image\":{\"url\":\"(.*?)\"",str(soup.find('script',{'type':"application/ld+json"})))[0].replace('\\','')
        nfo_dict['rating'] = re.findall("\"ratingValue\":(\d)",str(soup.find('script',{'type':"application/ld+json"})))[0]
        nfo_dict['votes'] = re.findall("\"reviewCount\":(\d+)",str(soup.find('script',{'type':"application/ld+json"})))[0]
        nfo_dict['id'] = re.findall("article:(\d+)",str(soup.find('script',{'type':"application/ld+json"})))[0]
        return nfo_dict

def rename(video_basename):
    dst_name = video_basename.replace(os.path.splitext(video_basename)[0],config.get('RENAME','name-format'))
    dst_name = dst_name.replace('{number}',video_num)
    return dst_name

def get_dstdir(video_dirname):
    for tag in re.findall('{.*?}',config.get('OUTPUT','output-format')):
        if 'director' in tag:
            video_dirname = os.path.join(video_dirname,nfo_dict['director'])
        elif 'year' in tag:
            video_dirname = os.path.join(video_dirname,nfo_dict['year'])
        elif 'number' in tag:
            video_dirname = os.path.join(video_dirname,video_num)
    return video_dirname

def write_nfo(nfo):
    nfo_contents = '''<?xml version="1.0" encoding="UTF-8"?>
    <movie>
        <title>%s</title>
            <sorttitle>%s</sorttitle>
        <rating name="FC2" max="5">
            <value>%s</value>
            <votes>%s</votes>
        </rating>
        <plot>%s</plot>
        <id>%s</id>
        <director>%s</director>
        <premiered>%s</premiered>
        <year>%s</year>'''
    print(nfo_contents%(nfo_dict['title'],nfo_dict['sorttitle'],nfo_dict['rating'],nfo_dict['votes'],nfo_dict['plot'],nfo_dict['id'],nfo_dict['director'],nfo_dict['date'],nfo_dict['year']),file=nfo)
    for tag in nfo_dict['tag']:
        print('\t\t<genre>%s</genre>'%tag,file=nfo)
    print('\t</movie>',file=nfo)
    
def check_rename():
    if config.get('RENAME','rename') == 'True':
        dst_name = rename(video_basename)
        dst_name_text = os.path.splitext(dst_name)[0]
        os.rename(video_name,os.path.join(dst_dir,dst_name))
        urllib.request.urlretrieve(nfo_dict['post'],'%s/%s.jpg'%(dst_dir,dst_name_text))
        with open('%s/%s.nfo'%(dst_dir,dst_name_text),'w+',encoding='utf-8') as nfo:
            write_nfo(nfo)
    else:
        os.rename(video_name,os.path.join(dst_dir,video_basename))
        urllib.request.urlretrieve(nfo_dict['post'],'%s/%s.jpg'%(dst_dir,video_basename_text))
        with open('%s/%s.nfo'%(dst_dir,video_basename_text),'w+',encoding='utf-8') as nfo:
            write_nfo(nfo)
            
def exit():
    for i in range(10,0,-1):
        print('\r''{}程序将在{}秒后退出。'.format(warning,i),end='',flush=True)
        time.sleep(1)
    sys.exit(0)

def check_config():
    if (config.get('RENAME','rename') != 'True' and config.get('RENAME','rename') != 'False') or (config.get('MOVE','move') != 'True' and config.get('MOVE','move') != 'False') or (config.get('OUTPUT','output') != 'True' and config.get('OUTPUT','output') != 'False'):
        print('%s初始化失败。rename、move、output选项只能设置为True或False。请检查后重试。'%error)
        exit()
    elif '{number}' not in config.get('RENAME','name-format'):
        print('%s初始化失败。name-format选项应包含{number}。'%error)
    elif platform.system() == 'Windows':
        chart_list = ['<','>','/','\\','|',':','"','*','?']
        for chart in chart_list:
            if chart in config.get('RENAME','name-format'):
                print('%s初始化失败。文件名不能包含%s字符，请修改name-format选项后重试。'%(error,chart))
                exit()
    elif platform.system() == 'Darwin':
        if config.get('RENAME','name-format').startswith('.') or ':' in config.get('RENAME','name-format'):
            print('%s初始化失败。文件名不能包含:字符，且不能以.开头。请修改name-format选项后重试。'%error)
    for tag in re.findall('{.*?}',config.get('OUTPUT','output-format')):
        if tag != '{director}' and tag != '{year}' and tag != '{number}':
            print('%s初始化失败。output-format选项中的标签只能是{director}、{year}、{number}中的一个或多个，请检查后重试。'%error)
            exit()

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
scraper_path = os.path.dirname(sys.argv[0])
error = "\033[1;31m[错误]\033[0m"
warning = "\033[1;33m[提示]\033[0m"

if __name__=='__main__':
    print(logo)
    print('%s程序初始化…'%warning)
    if os.path.exists('%s/config.ini'%scraper_path):
        config = configparser.ConfigParser()
        conf_file = '%s/config.ini'%scraper_path
        config.read(conf_file,encoding='utf-8')
        check_config()
        print('%s初始化完成。'%warning)
        print('%s正在查找当前程序所在文件夹内的影片…'%warning)
        file_list = os.listdir(scraper_path)
        video_list = []
        error_name_list = []
        not_sale_list = []
        sold_out_list = []
        for video in file_list:
            if video.endswith('mp4') or video.endswith('avi') or video.endswith('ts') or video.endswith('mkv') or video.endswith('mov'):
                video_list.append(video)
        if video_list == []:
            print('%s当前程序所在文件夹没有找到影片，请手动选择。'%warning)
            time.sleep(1)
            while True:
                video_name = tkinter.filedialog.askopenfilename(title='请选择需要削刮的影片：', filetypes=[('Video','*.mp4 *.ts *.avi *.mkv *.mov'), ('All Files', '*')])
                if video_name == '':
                    print('%s你已取消选择。'%error)
                    input('%s按回车继续选择或关闭程序。'%warning)
                    continue
                else:
                    video_dirname = os.path.dirname(video_name)
                    video_basename = os.path.basename(video_name)
                    video_basename_text = os.path.splitext(video_basename)[0]
                    video_num = get_num(video_basename)
                    if video_num != 'None':
                        nfo_dict = askURL(video_num)
                        if nfo_dict != 'error1' and nfo_dict != 'error2':
                            if config.get('MOVE','move') == 'False' and config.get('OUTPUT','output') == 'False':
                                dst_dir = video_dirname
                                check_rename()
                                print('%s削刮成功。'%warning)
                            elif config.get('MOVE','move') == 'False' and config.get('OUTPUT','output') == 'True':
                                dst_dir = get_dstdir(video_dirname)
                                try:
                                    os.makedirs(dst_dir)
                                except FileExistsError:
                                    print('%s文件夹：%s已存在，请检查后重试。'%(error,dst_dir))
                                    exit()
                                check_rename()
                                print('%s削刮成功。'%warning)
                            elif config.get('MOVE','move') == 'True' and config.get('OUTPUT','output') == 'False':
                                move_dir = config.get('MOVE','move-to')
                                dst_dir = move_dir
                                check_rename()
                                print('%s削刮成功。'%warning)
                            elif config.get('MOVE','move') == 'True' and config.get('OUTPUT','output') == 'True':
                                move_dir = config.get('MOVE','move-to')
                                video_dirname = move_dir
                                dst_dir = get_dstdir(video_dirname)
                                try:
                                    os.makedirs(dst_dir)
                                except FileExistsError:
                                    print('%s文件夹：%s已存在，请检查后重试。'%(error,dst_dir))
                                    exit()
                                check_rename()
                                print('%s削刮成功。'%warning)
                            note = input('%s按回车继续削刮或关闭程序。'%warning)
                        else:
                            exit()
                    else:
                        print('%s文件名错误!请检查文件名含番号，且番号前后不为数字后重试。'%error)
                        exit()
        else:
            for video_basename in video_list:
                video_num = get_num(video_basename)
                if video_num == 'None':
                    error_name_list.append(video_basename)
                    continue
                else:
                    video_dirname = scraper_path
                    video_name = os.path.join(video_dirname,video_basename)
                    video_basename_text = os.path.splitext(video_basename)[0]
                    nfo_dict = askURL(video_num)
                    if nfo_dict == 'error1':
                        not_sale_list.append(video_basename)
                        continue
                    elif nfo_dict == 'error2':
                        sold_out_list.append(video_basename)
                        continue
                    else:
                        if config.get('MOVE','move') == 'False' and config.get('OUTPUT','output') == 'False':
                            dst_dir = video_dirname
                            check_rename()
                            print('%s削刮成功。'%warning)
                        elif config.get('MOVE','move') == 'False' and config.get('OUTPUT','output') == 'True':
                            dst_dir = get_dstdir(video_dirname)
                            try:
                                os.makedirs(dst_dir)
                            except FileExistsError:
                                print('%s文件夹：%s已存在，请检查后重试。'%(error,dst_dir))
                                exit()
                            check_rename()
                            print('%s削刮成功。'%warning)
                        elif config.get('MOVE','move') == 'True' and config.get('OUTPUT','output') == 'False':
                            move_dir = config.get('MOVE','move-to')
                            dst_dir = move_dir
                            check_rename()
                            print('%s削刮成功。'%warning)
                        elif config.get('MOVE','move') == 'True' and config.get('OUTPUT','output') == 'True':
                            move_dir = config.get('MOVE','move-to')
                            video_dirname = move_dir
                            dst_dir = get_dstdir(video_dirname)
                            try:
                                os.makedirs(dst_dir)
                            except FileExistsError:
                                print('%s文件夹：%s已存在，请检查后重试。'%(error,dst_dir))
                                exit()
                            check_rename()
                            print('%s削刮成功。'%warning)
            
            if error_name_list != []:
                print(error,error_name_list,'文件名错误!请检查文件名含番号，且番号前后不为数字后重试。')
            if not_sale_list != []:
                print(error,not_sale_list,'削刮失败。这些影片卖家只对特定地区销售，请更换科学上网线路后重试。')
            if sold_out_list != []:
                print(error,sold_out_list,'削刮失败。这些影片已下架或文件名错误。')
            print('%s文件夹：%s 内所有影片削刮完毕。'%(warning,scraper_path))
            exit()
    else:
        print('%s初始化失败。未找到config.ini配置文件。'%error)
        exit()
        

