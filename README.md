#Typing Shooter English
Typing Shooter English 是一个基于 pygame 的单词记忆与拼写练习游戏，帮助你通过趣味闯关和练习模式高效背单词。
安装与运行
环境依赖  Python 3.x；pygame      
安装依赖  pip install pygame      
准备词库  vocabulary.js      
（如果是自己准备英语词库，需要将英语词库重命名为vocabulary.js，数据结构与本仓库文件一致即可，并于py程序打包在一起即可）  
打包：pyinstaller -F -w --add-data "vocabulary.js;." Memorize_the_words.py
启动游戏  python Memorize_the_words.py

