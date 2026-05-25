<font style="color:rgb(15, 17, 21);">基于 PySide6 和 PostgreSQL 的桌面端亲子音乐管理平台，通过创新的</font>**<font style="color:rgb(15, 17, 21);">角色-共享-监测</font>**<font style="color:rgb(15, 17, 21);">三层权限模型，让孩子在安全、可控的环境中享受音乐，让家长随时掌握孩子的听歌行为。</font>

## <font style="color:rgb(15, 17, 21);">✨</font><font style="color:rgb(15, 17, 21);"> 项目亮点</font>
+ **<font style="color:rgb(15, 17, 21);">👪</font>****<font style="color:rgb(15, 17, 21);"> 亲子双角色体系</font>**<font style="color:rgb(15, 17, 21);">  
</font><font style="color:rgb(15, 17, 21);">严格区分家长（PARENT）和孩子（CHILD）两种角色，各自拥有独立的操作界面和数据视图。</font>
+ **<font style="color:rgb(15, 17, 21);">🔐</font>****<font style="color:rgb(15, 17, 21);"> 创新的共享权限模型</font>**<font style="color:rgb(15, 17, 21);">  
</font><font style="color:rgb(15, 17, 21);">家长拥有完整的音乐库管理权（上传、删除、修改），并可精准控制每一首音乐是否对孩子可见（</font>`<font style="color:rgb(15, 17, 21);background-color:rgb(235, 238, 242);">is_shared</font>`<font style="color:rgb(15, 17, 21);">）。</font><font style="color:rgb(15, 17, 21);">  
</font>**<font style="color:rgb(15, 17, 21);">孩子只能浏览和播放被家长标记为“共享”的音乐，无法接触其他资源。</font>**<font style="color:rgb(15, 17, 21);">  
</font><font style="color:rgb(15, 17, 21);">该模型既保障了内容安全，又给予了家长充分的过滤自由。</font>
+ **<font style="color:rgb(15, 17, 21);">📊</font>****<font style="color:rgb(15, 17, 21);"> 听歌行为可视化监测</font>**<font style="color:rgb(15, 17, 21);">  
</font><font style="color:rgb(15, 17, 21);">系统自动记录孩子每一次播放的时长和时间，家长可通过</font>**<font style="color:rgb(15, 17, 21);">折线图</font>**<font style="color:rgb(15, 17, 21);">直观查看孩子每日/每周听歌时长变化趋势，实现健康监督。</font>
+ **<font style="color:rgb(15, 17, 21);">❤️</font>****<font style="color:rgb(15, 17, 21);"> 孩子的专属交互</font>**<font style="color:rgb(15, 17, 21);">  
</font><font style="color:rgb(15, 17, 21);">孩子可收藏喜欢的共享音乐，查看最近播放记录，在受限环境中拥有个性化体验。</font>
+ **<font style="color:rgb(15, 17, 21);">🗂️</font>****<font style="color:rgb(15, 17, 21);"> 清晰的分层架构</font>**<font style="color:rgb(15, 17, 21);">  
</font><font style="color:rgb(15, 17, 21);">采用表示层（PySide6 UI）→ 业务控制层（Service Layer）→ 数据访问层（SQLAlchemy ORM）的三层架构，职责明确，易于扩展和维护。</font>

## <font style="color:rgb(15, 17, 21);">🧱</font><font style="color:rgb(15, 17, 21);"> 技术栈</font>
| <font style="color:rgb(15, 17, 21);">层级</font> | <font style="color:rgb(15, 17, 21);">技术</font> |
| --- | --- |
| <font style="color:rgb(15, 17, 21);">前端/桌面端</font> | <font style="color:rgb(15, 17, 21);">PySide6 (Qt for Python)</font> |
| <font style="color:rgb(15, 17, 21);">业务逻辑</font> | <font style="color:rgb(15, 17, 21);">Python 3.x</font> |
| <font style="color:rgb(15, 17, 21);">数据库</font> | <font style="color:rgb(15, 17, 21);">PostgreSQL 17</font> |
| <font style="color:rgb(15, 17, 21);">ORM</font> | <font style="color:rgb(15, 17, 21);">SQLAlchemy</font> |
| <font style="color:rgb(15, 17, 21);">可视化</font> | <font style="color:rgb(15, 17, 21);">PySide6 图表组件 / Matplotlib</font> |
| <font style="color:rgb(15, 17, 21);">音频播放</font> | <font style="color:rgb(15, 17, 21);">PySide6 Multimedia / PyAudio / VLC 等</font> |


## <font style="color:rgb(15, 17, 21);">📂</font><font style="color:rgb(15, 17, 21);"> 数据库核心模型</font>
+ **<font style="color:rgb(15, 17, 21);">实体</font>**<font style="color:rgb(15, 17, 21);">：用户（User）、音乐（Music）、播放日志（PlayLog）</font>
+ **<font style="color:rgb(15, 17, 21);">关系</font>**<font style="color:rgb(15, 17, 21);">：收藏（Favorites）、最近播放（Recent Plays）——通过多对多关联表实现</font>
+ <font style="color:rgb(15, 17, 21);">详细 ER 图与建表语句见</font><font style="color:rgb(15, 17, 21);"> </font>`<font style="color:rgb(15, 17, 21);background-color:rgb(235, 238, 242);">/docs/database.md</font>`<font style="color:rgb(15, 17, 21);">（或仓库内对应路径）</font>

## <font style="color:rgb(15, 17, 21);">🚀</font><font style="color:rgb(15, 17, 21);"> 功能模块一览</font>
| <font style="color:rgb(15, 17, 21);">模块</font> | <font style="color:rgb(15, 17, 21);">家长</font> | <font style="color:rgb(15, 17, 21);">孩子</font> |
| --- | --- | --- |
| <font style="color:rgb(15, 17, 21);">音乐增删改查</font> | <font style="color:rgb(15, 17, 21);">✔️</font> | <font style="color:rgb(15, 17, 21);">❌</font> |
| <font style="color:rgb(15, 17, 21);">设置音乐共享状态</font> | <font style="color:rgb(15, 17, 21);">✔️</font> | <font style="color:rgb(15, 17, 21);">❌</font> |
| <font style="color:rgb(15, 17, 21);">注册孩子账号</font> | <font style="color:rgb(15, 17, 21);">✔️</font> | <font style="color:rgb(15, 17, 21);">❌</font> |
| <font style="color:rgb(15, 17, 21);">查看孩子听歌时长图表</font> | <font style="color:rgb(15, 17, 21);">✔️</font> | <font style="color:rgb(15, 17, 21);">❌</font> |
| <font style="color:rgb(15, 17, 21);">浏览共享音乐库</font> | <font style="color:rgb(15, 17, 21);">✔️</font> | <font style="color:rgb(15, 17, 21);">✔️</font> |
| <font style="color:rgb(15, 17, 21);">音乐播放控制</font> | <font style="color:rgb(15, 17, 21);">✔️</font> | <font style="color:rgb(15, 17, 21);">✔️</font> |
| <font style="color:rgb(15, 17, 21);">收藏/喜欢音乐</font> | <font style="color:rgb(15, 17, 21);">✔️</font> | <font style="color:rgb(15, 17, 21);">✔️</font> |
| <font style="color:rgb(15, 17, 21);">查看最近播放</font> | <font style="color:rgb(15, 17, 21);">✔️</font> | <font style="color:rgb(15, 17, 21);">✔️</font> |
| <font style="color:rgb(15, 17, 21);">听歌行为自动记录</font> | <font style="color:rgb(15, 17, 21);">✔️</font> | <font style="color:rgb(15, 17, 21);">✔️</font> |


## <font style="color:rgb(15, 17, 21);">🧪</font><font style="color:rgb(15, 17, 21);"> 核心创新：亲子共享与监控一体化</font>
<font style="color:rgb(15, 17, 21);">传统音乐播放器要么全开放，要么强控制。本系统提出了</font><font style="color:rgb(15, 17, 21);"> </font>**<font style="color:rgb(15, 17, 21);">“家长主动共享 + 孩子受限访问 + 行为可追溯”</font>**<font style="color:rgb(15, 17, 21);"> </font><font style="color:rgb(15, 17, 21);">的亲子权限环：</font>

1. **<font style="color:rgb(15, 17, 21);">内容播种</font>**<font style="color:rgb(15, 17, 21);">：家长通过</font><font style="color:rgb(15, 17, 21);"> </font>`<font style="color:rgb(15, 17, 21);background-color:rgb(235, 238, 242);">is_shared</font>`<font style="color:rgb(15, 17, 21);"> </font><font style="color:rgb(15, 17, 21);">字段为每首音乐设定可见性，形成一个动态的“安全曲库”。</font>
2. **<font style="color:rgb(15, 17, 21);">安全围栏</font>**<font style="color:rgb(15, 17, 21);">：孩子端所有查询接口仅返回共享音乐，从数据库查询层即开始拦截，杜绝越权。</font>
3. **<font style="color:rgb(15, 17, 21);">行为日志</font>**<font style="color:rgb(15, 17, 21);">：每一次播放都被记录（</font>`<font style="color:rgb(15, 17, 21);background-color:rgb(235, 238, 242);">child_play_logs</font>`<font style="color:rgb(15, 17, 21);">），不依赖客户端缓存，数据真实可靠。</font>
4. **<font style="color:rgb(15, 17, 21);">洞察反馈</font>**<font style="color:rgb(15, 17, 21);">：基于日志生成时长趋势图，为家长提供科学育儿的数据参考。</font>

<font style="color:rgb(15, 17, 21);">这一模式可复用到任何需要“监护方控制资源+被监护方受限使用”的场景（如电子书阅读、教学视频等）。</font>

## <font style="color:rgb(15, 17, 21);">📦</font><font style="color:rgb(15, 17, 21);"> 快速开始</font>
<font style="color:rgb(15, 17, 21);">bash</font>

```plain
git clone https://github.com/C/ParentChildMusicPlayer.git
cd ParentChildMusicPlayer
pip install -r requirements.txt
# 请先创建 PostgreSQL 数据库并运行 database.sql 初始化表
python main.py
```

---

**<font style="color:rgb(15, 17, 21);">如果你觉得这个项目有帮助，欢迎 Star </font>****<font style="color:rgb(15, 17, 21);">⭐</font>****<font style="color:rgb(15, 17, 21);"> 和 Fork！</font>**<font style="color:rgb(15, 17, 21);">  
</font><font style="color:rgb(15, 17, 21);">任何问题或建议，请提交 Issue 或 Pull Request。</font>

  
 

