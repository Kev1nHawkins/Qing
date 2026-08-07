# 社区演示文化素材与许可清单

核验日期：2026-08-07。演示内容只使用列明来源的图片；文字均为本项目原创演示文案，
不把未经核实的具体历史断言当作事实发布。

| 素材 | 作者/来源 | 许可与用途 | 原始页面 |
|---|---|---|---|
| 广州大学大学城校区创新大楼 | Jasonjiang.1998 | CC BY-SA 4.0；已核验的后续素材候选 | https://commons.wikimedia.org/wiki/File:Innovation_Hub,_HEMC_Campus,_Guangzhou_University_20251018-A.jpg |
| 广州大学大学城校区德馨亭 | Jasonjiang.1998 | CC BY-SA 4.0；校园打卡封面；原图本地副本 | https://commons.wikimedia.org/wiki/File:Dexin_Pavilion,_HEMC_Campus,_Guangzhou_University_20251018-A.jpg |
| 广州大学大学城校区正门 | Jasonjiang.1998 | CC BY-SA 4.0；已核验的后续素材候选 | https://commons.wikimedia.org/wiki/File:Main_Gate_of_HEMC_Campus,_Guangzhou_University_20251018-A.jpg |
| 广州陵园西路木棉盛放 | jiang-wen-jie | CC BY-SA 3.0；木棉主题封面；原图本地副本 | https://commons.wikimedia.org/wiki/File:%E6%9C%A8%E6%A3%89%E7%9B%9B%E6%94%BE%E7%9A%84%E9%99%B5%E5%9B%AD%E8%A5%BF%E8%B7%AFScenery_in_Guangzhou,_China_-_panoramio.jpg |
| 广州青年粤剧团后台影像 | wingmelee | CC BY-SA 2.5；仅作许可核验参考，离线包改用 AI 原创插画 | https://commons.wikimedia.org/wiki/File:Guangzhou_Youth_Cantonese_Opera_Troupe_20130604-H.jpg |

## 统一文化分类封面

以下 7 张分类封面于 2026-08-07 使用 OpenAI 内置图像生成工具原创生成，不使用
真实人物肖像、学校标志、品牌商标或第三方作品作为画面素材。PNG 原稿保留在工具的
生成目录中，项目内导出为 1536×1024、质量 90 的 JPEG，并同时放入
`frontend-user/public/demo/culture-covers/` 与
`frontend-admin/public/demo/culture-covers/`。

| 文件 | 主题 | 使用分类 |
|---|---|---|
| `lingnan-overview.jpg` | 珠江、骑楼、木棉、戏曲衣袖、茶点与校园的综合意象 | 岭南概览 |
| `guangzhou-city.jpg` | 珠江港口、骑楼、城市天际线与花城花事 | 广州城市文化 |
| `intangible-arts.jpg` | 醒狮、广绣、广彩、广东音乐与玉雕 | 非遗艺术 |
| `architecture-gardens.jpg` | 骑楼、西关民居、园林水石与建筑装饰 | 建筑与园林 |
| `food-culture.jpg` | 茶点、时令食材、凉茶意象与月饼模 | 饮食文化 |
| `folk-festivals.jpg` | 龙舟、花市、庙会屋脊与手工波罗鸡意象 | 民俗节庆 |
| `campus-culture.jpg` | 三条校园路径、书本、湖亭、木棉与音乐意象 | 校园文化 |

### 生成提示词规范

母版提示词：`3:2 横幅文化知识卡封面；暖米色手工纸背景；现代中国编辑插画；
分层纸本拼贴、细墨线与丝网印刷色块；木棉红、岭南青绿、靛蓝和少量古金；
单一清晰视觉中心、适合卡片裁切；无文字、数字、标志、水印、商标和真实人物肖像。`

六张变体均以母版图片为风格参考，只替换分类主题。提示词统一要求：不冒充文物或
建筑实拍、不混入无关地域符号、不使用通用节庆海报套路、不模仿在世艺术家。

## 使用要求

- 本地文件 `frontend-*/public/demo/kapok.jpg` 来自上表木棉照片，保留原始
  CC BY-SA 许可与署名要求。
- 本地文件 `frontend-*/public/demo/dexin-pavilion.jpg` 来自上表德馨亭校园
  照片；离线演示中的校园场景帖子统一复用该图，不宣称为其他具体建筑。
- `frontend-*/public/demo/cantonese-opera-ai.png` 为本项目通过 OpenAI 图像工具
  生成的原创演示插画，不使用真实演员肖像，也不替代粤剧史料或授权照片。
- 文化列表与社区新演示数据统一使用 `culture-covers/` 下的 7 张分类封面；旧的
  木棉、德馨亭和粤剧素材仍保留给其他既有页面或历史演示使用，不删除、不覆盖。
- 其余上表链接保留为后续素材扩充候选；未成功下载或未核验到本地的图片不进入
  离线演示包。
- 页面或作品说明应保留作者、来源链接、许可证及是否修改的信息。
- 若下载、裁切、调色或把素材并入新作品，需遵守对应许可证的署名与相同方式共享要求。
- 广州大学官方标志只用于识别校园语境，不暗示本项目是学校官方网站。
- 比赛正式发布前，由内容负责人再次检查链接、许可状态和展示范围。
