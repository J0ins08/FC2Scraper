## FC2 Scraper
通过番号爬取FC2电子市场在售影片基本信息，生成海报及NFO文件。
### 功能
- 削刮完自动移动到指定文件夹。
- 手动选择和自动批量削刮两种模式。
- 自定义输出目录。
- 生成海报。
- 生成符合 [Kodi Movie](https://kodi.wiki/view/NFO_files/Movies#nfo_Tags)规范 NFO文件，理论上适配Infuse、Kodi、Emby等。
### 如何使用
首次运行需修改`config.ini`配置文件，配置文件应与程序在同一文件夹内。
- 自动模式
将程序及配置文件`config.ini`移到需要削刮的文件夹运行。
- 手动模式
在任意文件夹运行程序。程序会扫描当前程序所在文件夹内影片，找不到即弹出文件选择窗口，手动选择需要削刮影片即可。
### 文件名规范
影片名要符合一定规范才能削刮。文件名可以为任意合法文件名，但必须带番号，且番号前后不能是罗马数字。
✅ FC2-`1234567`
✅ 葫芦娃与`1234567`七个爷爷
❎ FC2`1234567`
❎ `1234567`1024
### Config配置
```
[RENAME]
#rename为Ture时削刮完自动重命名。默认为True。
rename=True
#重命名后的文件名应为合法的文件名。在Windows中，文件名不应超过255个字符，且不能带有< > / \ | : " * ?等字符。在Mac OS中， 文件名不能带有:字符，且文件名不能以.开头。
#name-format应包含{number}字样。范例：name-formate=FC2-PPV-{number}
name-format=FC2-PPV-{number}
[MOVE]
#move为Ture时削刮完自动移动到指定文件夹。默认为False。
move=False
#move-to路径应为绝对路径。范例：move-to=C:\your\path(Windows)或move-to=/Users/username/yourpath(Mac OS)
move-to=
<OUTPUT>
#output为Ture时削刮完自动创建文件夹，并将影片移到文件夹中。默认为True。
output=True
#output为Ture时，output-format应至少包含{director}、{<year}、{number}标签中的一个或多个。范例：move-to={director}
output-format={director}/{<year}/{number}
```
### F&Q

- Q：为什么我用了科学上网部分影片依然不能削刮？

- A： 部分卖家只对特定地区销售，请更换科学上网线路。
