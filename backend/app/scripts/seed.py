import asyncio
from decimal import Decimal

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.creation import CreationTemplate
from app.models.culture import CultureItem, Location
from app.models.enums import BadgeRuleType, PublishStatus, TaskType
from app.models.points import Badge
from app.models.route import Route, RouteTask
from app.models.user import Role, User


CULTURE_SPECS = [
    {
        "title": "岭南文化概述",
        "slug": "lingnan-culture-overview",
        "category": "岭南概览",
        "summary": "从广府、客家、潮汕等文化分支出发，理解岭南在语言、艺术、建筑、饮食与商贸交流中形成的多元面貌，并认识它与当代青年生活的连接。",
        "content": "\n\n".join(
            [
                "岭南文化是五岭以南地区在长期历史发展中形成的区域文化体系，也是中华文明的重要组成部分。广东是其核心区域之一，但岭南文化不能简单等同于今天的广东省行政区划。",
                "广府、客家、潮汕等文化分支既共享区域历史背景，也保留各自的语言、艺术、建筑、饮食和民俗传统。人口迁徙、海洋交通、商贸往来与多族群互动，共同塑造了岭南文化开放、多元而持续变化的面貌。",
                "理解岭南文化，应避免把开放、务实等概括套用到每一个人，也不应把某一种地方传统当成岭南文化的全部。保护传统并不意味着停止变化，而是在尊重文化主体和历史依据的前提下延续与创新。",
            ]
        ),
        "cover_image_url": None,
        "source_title": "广东省人民政府文史研究馆：《正确理解岭南文化的突出特性与创新创造》",
        "source_url": "https://www.gdwsw.gov.cn/wsgdxxyt/content/post_34729.html",
        "status": PublishStatus.PUBLISHED.value,
    },
    {
        "title": "木棉：广州的英雄花",
        "slug": "kapok-hero-flower",
        "category": "广州城市文化",
        "summary": "从木棉的花期、形态与广州城市记忆出发，理解“英雄花”如何连接自然观察、红色历史与当代校园表达，以及文化符号如何被重新讲述。",
        "content": "\n\n".join(
            [
                "木棉是广州具有代表性的城市文化符号，也是广州市花。木棉树形高大，春季常先开花后长叶，鲜红或橙红的花朵在枝干上形成醒目的城市景观。",
                "广州公共文化传播常把木棉称为“红棉”“英雄花”或“英雄树”。这些称呼把木棉挺拔、热烈的形象与广州的英雄城市记忆连接起来，承载昂扬向上、奋勇争先等文化寓意。",
                "木棉既是自然植物，也是观察城市文化如何形成的入口。在校园共创中，应先核对植物与历史资料，再把花形、枝干和色彩转译为当代视觉语言，避免只把木棉当作一个红色装饰符号。",
            ]
        ),
        "cover_image_url": "/demo/kapok.jpg",
        "source_title": "广州市林业和园林局：《植物百科——木棉》",
        "source_url": "https://lyylj.gz.gov.cn/kpyd/dwbk/zw/content/post_3032236.html",
        "status": PublishStatus.PUBLISHED.value,
    },
    {
        "title": "粤剧文化",
        "slug": "cantonese-opera-culture",
        "category": "非遗艺术",
        "summary": "认识粤剧以粤语演唱、唱做念打结合的艺术特点，以及它在粤港澳和海外粤语社群中的活态传承，理解非遗保护为何离不开传承人和社群。",
        "content": "\n\n".join(
            [
                "粤剧是以粤语演唱、主要流行于粤语地区的传统戏剧。它在长期发展中吸收多种声腔、广东民间音乐与表演因素，形成唱、做、念、打结合的舞台艺术。",
                "粤剧于2006年列入第一批国家级非物质文化遗产名录，并于2009年列入联合国教科文组织人类非物质文化遗产代表作名录。保护对象不仅包括剧目，也包括表演实践、知识技能、传承人、社群和文化空间。",
                "粤剧的实践范围不只在广州，也包括广东、广西部分粤语地区、香港、澳门及海外粤语社群。进行视觉共创时，应尊重具体剧目和表演语境，避免混用不同戏曲的脸谱、服饰与动作元素。",
            ]
        ),
        "cover_image_url": "/demo/cantonese-opera-ai.png",
        "source_title": "中国非物质文化遗产网·中国非物质文化遗产数字博物馆：《粤剧》",
        "source_url": "https://www.ihchina.cn/yueju.html",
        "status": PublishStatus.PUBLISHED.value,
    },
    {
        "title": "岭南骑楼",
        "slug": "lingnan-arcades",
        "category": "建筑与园林",
        "summary": "从遮阳避雨、连续步行和沿街商业生活理解骑楼，观察岭南建筑如何回应气候并为城市公共交往留出空间，并思考这些空间经验如何进入当代校园设计。",
        "content": "\n\n".join(
            [
                "骑楼通常把建筑上层向街道伸出，在底层形成连续、有遮蔽的公共步行空间。它能够帮助行人遮阳避雨，也让商铺、街道与日常交往保持紧密联系。",
                "广州部分传统街区保留了骑楼与商业生活相互交织的城市肌理。骑楼并非单一、固定的样式，其形成和变化与岭南气候、近代商贸、建造技术及不同文化交流有关。",
                "观察骑楼时，不应只停留在立面装饰，还可以关注人在廊下怎样行走、停留和交谈，并思考这种灰空间对今天校园连廊和公共空间设计的启发。",
            ]
        ),
        "cover_image_url": None,
        "source_title": "广州市民政局：《广州市地名保护名录（第一批）》",
        "source_url": "https://mzj.gz.gov.cn/attachment/7/7537/7537434/8753411.pdf",
        "status": PublishStatus.PUBLISHED.value,
    },
    {
        "title": "西关大屋",
        "slug": "xiguan-mansions",
        "category": "建筑与园林",
        "summary": "通过门厅、天井、廊道和传统构件认识西关大屋，理解广府民居对家庭生活、街区关系与岭南气候的回应，以及传统建筑在今天保护与活化时面对的问题。",
        "content": "\n\n".join(
            [
                "西关大屋是广州西关传统民居的重要类型，常与西关历史街区、商贸发展和广府家庭生活相联系。其空间并不是孤立的建筑样式，而是特定时代社会生活的物质见证。",
                "传统西关大屋通过门厅、天井、厅堂和廊道组织居住空间，并使用趟栊门、满洲窗等具有地方特色的构件。通风、采光、遮阳和内外空间过渡体现了对岭南气候的适应。",
                "介绍西关大屋时，应区分历史原貌、后期修缮和当代活化利用，不把所有广州老建筑都称作西关大屋，也不以单一装饰元素代替完整的生活与街区语境。",
            ]
        ),
        "cover_image_url": None,
        "source_title": "广州市民政局：《广州市地名保护名录（第一批）》",
        "source_url": "https://mzj.gz.gov.cn/attachment/7/7537/7537434/8753411.pdf",
        "status": PublishStatus.PUBLISHED.value,
    },
    {
        "title": "岭南园林",
        "slug": "lingnan-gardens",
        "category": "建筑与园林",
        "summary": "从庭院、水石、植物与建筑的组合认识岭南园林，理解其因地制宜、求实兼蓄并持续吸收现代设计的特点，并把这种空间智慧带回校园景观观察。",
        "content": "\n\n".join(
            [
                "岭南园林是在岭南自然环境、社会生活和审美传统中发展起来的地域园林。庭院、水体、山石、植物和建筑共同组织空间，并通过通风、遮阳和灵活布局回应湿热气候。",
                "番禺余荫山房、佛山梁园、东莞可园和顺德清晖园常被合称为广东四大名园。它们各有历史与空间特点，不能用一种固定模板概括全部岭南园林。",
                "岭南园林的发展既延续传统造园艺术，也吸收现代材料、公共绿地功能和新的设计观念。校园景观观察可以从水体、植物、连廊和使用者活动出发，理解园林如何服务真实生活。",
            ]
        ),
        "cover_image_url": None,
        "source_title": "广州市林业和园林局：《岭南园林发展概况》",
        "source_url": "https://lyylj.gz.gov.cn/kpyd/zhzy/content/post_9223681.html",
        "status": PublishStatus.PUBLISHED.value,
    },
    {
        "title": "广州早茶文化",
        "slug": "guangzhou-morning-tea",
        "category": "饮食文化",
        "summary": "早茶不只是一顿早餐，也是一种围绕茶点、交谈和共享时间形成的广府生活方式与城市文化记忆，理解饮食传承为何同时关乎技艺、礼俗与社区生活。",
        "content": "\n\n".join(
            [
                "广州早茶是以饮茶、品尝点心和社交交往共同构成的生活文化。人们常用“饮茶”或“叹茶”描述这一活动，其中既有饮食选择，也包含与亲友相聚和维系日常关系的意义。",
                "“一盅两件”通常用来概括一盅茶配两件点心的传统消费方式，但今天的早茶品类和场景更加丰富。虾饺、烧卖等常见点心只是其中一部分，不能代表所有广州饮食。",
                "广州已通过专项规定推动早茶文化的传承保护。展示早茶时，应同时关注制作技艺、服务礼俗、老字号、社区生活和当代创新，避免把它简化成网红食品清单。",
            ]
        ),
        "cover_image_url": None,
        "source_title": "广州市文化广电旅游局：《广州出台全国首部早茶专项法规〈广州早茶传承保护规定〉》",
        "source_url": "https://wglj.gz.gov.cn/gzdt/zwxx/content/post_10755149.html",
        "status": PublishStatus.PUBLISHED.value,
    },
    {
        "title": "粤菜与广州饮食",
        "slug": "cantonese-cuisine-guangzhou",
        "category": "饮食文化",
        "summary": "从食材、技法、时令与城市交流理解粤菜，认识广州饮食如何在日常生活、商贸往来和持续创新中形成，并辨认个人口味、地方传统与权威知识之间的边界。",
        "content": "\n\n".join(
            [
                "粤菜是中国重要的地方菜系之一，广州饮食是观察其发展与传播的重要窗口。选材、刀工、火候、汤羹和点心共同构成丰富的技法体系，不能用“清淡”一个词概括。",
                "广州长期的商贸往来、人口流动与城市生活，使本地饮食不断吸收新的食材、制作方法和服务方式。老字号、街坊餐桌、专业餐饮和校园食堂都可以成为理解饮食记忆的不同入口。",
                "记录广州饮食时，应区分个人口味与可核验事实，尊重菜品的具体来源和制作传统。校园口味地图适合呈现同学的生活经验，但不应被包装成唯一或权威的粤菜排名。",
            ]
        ),
        "cover_image_url": None,
        "source_title": "广州市商务局：《广州市餐饮高质量发展规划》",
        "source_url": "https://sw.gz.gov.cn/attachment/7/7595/7595905/9621816.pdf",
        "status": PublishStatus.PUBLISHED.value,
    },
    {
        "title": "广州大学历史沿革",
        "slug": "guangzhou-university-history",
        "category": "校园文化",
        "summary": "从1927年的办学传统到2000年合并组建的新广州大学，认识学校历史如何与广州城市发展相互连接，并把宏大校史转换为师生能够感知的校园记忆。",
        "content": "\n\n".join(
            [
                "广州大学以国家重要中心城市广州命名，拥有可追溯至1927年的办学传统。学校历史由不同阶段、不同办学机构和一代代师生共同积累而成。",
                "2000年，广州师范学院、广州大学、广州高等师范专科学校、广州教育学院、华南建设学院（西院）等院校教育资源合并组建新的广州大学。理解校史时，应同时尊重各前身学校的历史贡献。",
                "今天的广州大学继续强调与广州和粤港澳大湾区发展相连接。校园文化展示既可以呈现重要时间节点，也应记录普通师生的学习、研究、服务与日常生活。",
            ]
        ),
        "cover_image_url": "/demo/dexin-pavilion.jpg",
        "source_title": "广州大学档案馆：《博学笃行九十一载：广州大学简史》",
        "source_url": "https://dag.gzhu.edu.cn/info/1041/1264.htm",
        "status": PublishStatus.PUBLISHED.value,
    },
    {
        "title": "广州大学校训",
        "slug": "guangzhou-university-motto",
        "category": "校园文化",
        "summary": "“博学笃行、与时俱进”把广博学习、踏实实践与面向时代的持续进步连接为广州大学的共同精神表达，认识校训如何落实在学习、实践、服务与文化共创之中。",
        "content": "\n\n".join(
            [
                "广州大学校训是“博学笃行、与时俱进”。它既强调广泛学习、深入理解，也强调把知识落实到行动，并在社会与时代变化中保持开放和进取。",
                "校训不是只用于典礼和标识的口号。课程学习、校园寻迹、社会服务和文化共创，都可以成为理解“博学”与“笃行”关系的具体实践。",
                "在校园传播中使用校训，应保持文字准确和语境庄重，不随意改写为商业宣传口号，也不把某一次活动等同于学校精神的全部。",
            ]
        ),
        "cover_image_url": "/demo/dexin-pavilion.jpg",
        "source_title": "广州大学：《校训校徽校歌》",
        "source_url": "https://www.gzhu.edu.cn/xxgk/xxxhxg.htm",
        "status": PublishStatus.PUBLISHED.value,
    },
    {
        "title": "广州大学校徽文化",
        "slug": "guangzhou-university-emblem",
        "category": "校园文化",
        "summary": "从“GU”“羊”、火炬与红棉花开的组合认识广州大学校徽，理解学校身份、广州城市意象与校园共同体的连接，同时明确学生项目使用官方标识时应遵守的边界。",
        "content": "\n\n".join(
            [
                "广州大学校徽志由“GU”“羊”字及英文校名组合而成。“GU”是Guangzhou University的英文缩写，“羊”代表广州，组合形态又呈现火炬与红棉花开的意象。",
                "校徽把学校名称、广州城市文化和积极向上的视觉象征连接在一起。它既是校园身份识别，也是师生共同体在正式场合使用的重要学校标识。",
                "本项目只在识别广州大学校园语境时使用官方标识，不改变校徽构图、颜色和文字，也不暗示学生项目是学校官方网站或官方发布平台。",
            ]
        ),
        "cover_image_url": "/demo/dexin-pavilion.jpg",
        "source_title": "广州大学：《校训校徽校歌》",
        "source_url": "https://www.gzhu.edu.cn/xxgk/xxxhxg.htm",
        "status": PublishStatus.PUBLISHED.value,
    },
    {
        "title": "一校三园与广州城市连接",
        "slug": "guangzhou-university-three-campuses",
        "category": "校园文化",
        "summary": "大学城、桂花岗和黄埔三个校区处在不同城市空间，共同构成广州大学连接教育、历史城区与创新发展的校园文化地图，并理解不同校区怎样共同参与广州的教育与城市发展。",
        "content": "\n\n".join(
            [
                "广州大学设有大学城、桂花岗和黄埔三个校区。三个校区拥有不同的空间环境和发展背景，共同组成学校的办学空间与校园文化网络。",
                "大学城校区连接广州大学城的学习与公共生活，桂花岗校区邻近中心城区历史文脉，黄埔校区位于中新广州知识城科教创新区。介绍各校区时，应以学校最新公开信息为准。",
                "当前“红棉寻迹”以大学城校区为演示场景，后续内容可以继续记录桂花岗的城市记忆与黄埔的创新实践，但不在本轮擅自扩展新的路线和任务逻辑。",
            ]
        ),
        "cover_image_url": "/demo/dexin-pavilion.jpg",
        "source_title": "广州大学：《广州大学章程（2023年核准稿）》",
        "source_url": "https://www.gzhu.edu.cn/info/1255/10225.htm",
        "status": PublishStatus.PUBLISHED.value,
    },
]


async def ensure_roles(session) -> dict[str, Role]:
    result: dict[str, Role] = {}
    for code, name in [("user", "普通用户"), ("admin", "管理员")]:
        role = await session.scalar(select(Role).where(Role.code == code))
        if not role:
            role = Role(code=code, name=name, description=f"{name}角色")
            session.add(role)
            await session.flush()
        result[code] = role
    return result


async def ensure_admin(session, role: Role) -> User:
    admin = await session.scalar(select(User).where(User.username == settings.admin_username))
    admin_email = "admin@lingchao.example.com"
    if not admin:
        admin = User(
            username=settings.admin_username,
            email=admin_email,
            password_hash=hash_password(settings.admin_password),
            nickname="岭潮管理员",
            role_id=role.id,
        )
        session.add(admin)
        await session.flush()
    elif admin.email != admin_email:
        admin.email = admin_email
        await session.flush()
    return admin


async def ensure_badges(session) -> None:
    badge_specs = [
        ("kapok-first", "红棉初见", "完成首个红棉寻迹任务", BadgeRuleType.TASK_COUNT, 1),
        ("culture-walker", "文化行者", "累计完成 3 个寻迹任务", BadgeRuleType.TASK_COUNT, 3),
        ("tide-creator", "岭潮共创者", "累计获得 50 积分", BadgeRuleType.POINT_TOTAL, 50),
    ]
    for code, name, description, rule_type, rule_value in badge_specs:
        badge = await session.scalar(select(Badge).where(Badge.code == code))
        if not badge:
            session.add(
                Badge(
                    code=code,
                    name=name,
                    description=description,
                    rule_type=rule_type.value,
                    rule_value=rule_value,
                )
            )
        else:
            badge.name = name
            badge.description = description
            badge.rule_type = rule_type.value
            badge.rule_value = rule_value
            badge.is_active = True


async def ensure_demo_routes(session, admin: User) -> None:
    cultures: dict[str, CultureItem] = {}
    for spec in CULTURE_SPECS:
        culture_item = await session.scalar(
            select(CultureItem).where(CultureItem.slug == spec["slug"])
        )
        if not culture_item:
            culture_item = CultureItem(**spec, created_by_id=admin.id)
            session.add(culture_item)
            await session.flush()
        else:
            for field, value in spec.items():
                setattr(culture_item, field, value)
            if culture_item.created_by_id is None:
                culture_item.created_by_id = admin.id
        cultures[culture_item.slug] = culture_item

    culture = cultures["kapok-hero-flower"]

    location_renames = {
        "红棉广场": "何世杰体育馆广场",
        "校史展示点": "校史馆门口",
        "生活区文化墙": "红色长廊",
    }
    for old_name, new_name in location_renames.items():
        existing_new = await session.scalar(
            select(Location).where(Location.name == new_name)
        )
        existing_old = await session.scalar(
            select(Location).where(Location.name == old_name)
        )
        if existing_old and not existing_new:
            existing_old.name = new_name

    location_specs = [
        ("广州大学正门", "大学城外环西路入口", "校园轴线起点", "23.0391000", "113.3683000"),
        ("广州大学图书馆", "广州大学图书馆", "知识与校园文化交汇点", "23.0387000", "113.3702000"),
        ("何世杰体育馆广场", "何世杰体育馆正门广场", "连接广州亚运会、全运会与校园体育精神的打卡点", "23.0379000", "113.3714000"),
        ("校史馆门口", "广州大学校史馆门口", "从校史出发认识广州十三行与海上商都记忆", "23.0371000", "113.3699000"),
        ("红色长廊", "广州大学红色文化长廊", "了解广州革命先烈与青年担当的文化打卡点", "23.0359000", "113.3689000"),
        ("岭南建筑连廊", "教学区连廊", "观察通风、遮阳与灰空间", "23.0382000", "113.3720000"),
        ("德信亭", "广州大学大学城校区", "传统亭廊与当代校园景观", "23.0369000", "113.3725000"),
        ("教学楼中庭", "教学区中庭", "岭南建筑气候适应任务点", "23.0363000", "113.3716000"),
        ("中心湖东岸", "广州大学中心湖东岸", "观察水体与校园生态", "23.0356000", "113.3708000"),
        ("湖畔栈道", "广州大学湖畔步道", "校园自然摄影任务点", "23.0349000", "113.3697000"),
        ("学生广场", "广州大学学生广场", "路线总结与文化问答点", "23.0354000", "113.3684000"),
    ]
    locations: dict[str, Location] = {}
    for name, address, description, latitude, longitude in location_specs:
        location = await session.scalar(select(Location).where(Location.name == name))
        if not location:
            location = Location(
                name=name,
                address=address,
                description=description,
                latitude=Decimal(latitude),
                longitude=Decimal(longitude),
                culture_item_id=culture.id,
            )
            session.add(location)
            await session.flush()
        else:
            location.address = address
            location.description = description
            location.latitude = Decimal(latitude)
            location.longitude = Decimal(longitude)
            location.culture_item_id = culture.id
        locations[name] = location

    route_specs = [
        {
            "title": "红棉寻迹",
            "slug": "kapok-trail",
            "summary": "沿校园文化地标寻找木棉印记，在行走、观察和问答中认识广州城市精神。",
            "duration": 55,
            "distance": "2.40",
            "tasks": [
                ("广州大学正门", "正门启程", "在大学正门开启岭潮路线，认识醒狮所代表的勇气、协作与广府精气神。", TaskType.CHECK_IN, "请上传包含广州大学正门或校名标识的现场照片", None, None, 10, 120),
                ("广州大学图书馆", "羊城求知闯关", "进入独立知识问答页，完成广州城市文化、非遗与建筑知识闯关。答完即可获得文化令牌。", TaskType.QUIZ, "完成广州文化五题知识闯关", ["木棉与羊城", "粤剧与非遗", "骑楼与十三行"], "完成广州文化知识闯关", 15, 100),
                ("何世杰体育馆广场", "活力羊城打卡", "在体育馆广场感受广州从亚运会到全运会延续的城市体育活力。", TaskType.CHECK_IN, "请上传包含何世杰体育馆或广场标识的现场照片", None, None, 15, 100),
                ("校史馆门口", "海丝商都打卡", "从广州大学校史空间连接十三行、海上丝绸之路与广州商贸文化。", TaskType.CHECK_IN, "请上传包含校史馆门口或馆名标识的现场照片", None, None, 20, 100),
                ("红色长廊", "英雄薪火打卡", "沿红色长廊认识广州革命先烈，把城市记忆转化为青年担当。", TaskType.CHECK_IN, "请上传包含红色长廊主题展板或标识的现场照片", None, None, 15, 100),
            ],
        },
        {
            "title": "建筑寻纹",
            "slug": "architecture-trail",
            "summary": "从门廊、窗格与庭院中寻找岭南建筑适应气候、连接生活的设计智慧。",
            "duration": 45,
            "distance": "1.80",
            "tasks": [
                ("岭南建筑连廊", "连廊观察", "观察校园连廊的遮阳设计并拍摄建筑细节。", TaskType.CHECK_IN, "请上传连廊遮阳或通风设计照片", None, None, 10, 100),
                ("德信亭", "亭廊问答", "辨认岭南建筑中连接室内外的过渡空间。", TaskType.QUIZ, "岭南建筑中兼具遮阳和交通功能的空间是什么？", ["骑楼或连廊", "封闭地下室", "玻璃幕墙"], "骑楼或连廊", 15, 100),
                ("教学楼中庭", "中庭光影", "观察中庭的采光、通风与公共活动空间。", TaskType.CHECK_IN, "请上传教学楼中庭现场照片", None, None, 20, 100),
            ],
        },
        {
            "title": "湖畔拾光",
            "slug": "lakeside-trail",
            "summary": "沿湖连接自然景观、校园记忆与公共生活，用照片记录一段可分享的广大时光。",
            "duration": 50,
            "distance": "2.10",
            "tasks": [
                ("中心湖东岸", "湖岸观察", "观察校园水体与公共空间并记录湖岸景观。", TaskType.CHECK_IN, "请上传中心湖东岸现场照片", None, None, 10, 120),
                ("湖畔栈道", "湖畔影像", "拍摄湖畔植物、步道或同学活动的现场照片。", TaskType.CHECK_IN, "请上传湖畔现场照片完成图片打卡", None, None, 15, 100),
                ("学生广场", "生态共生问答", "完成路线总结，选择校园景观设计应遵循的原则。", TaskType.QUIZ, "校园生态景观最应优先尊重什么？", ["自然与人的共生", "只追求装饰效果", "完全隔离公共活动"], "自然与人的共生", 15, 100),
            ],
        },
    ]

    for route_spec in route_specs:
        route = await session.scalar(
            select(Route).where(Route.slug == route_spec["slug"])
        )
        if not route:
            route = Route(
                title=route_spec["title"],
                slug=route_spec["slug"],
                summary=route_spec["summary"],
                duration_minutes=route_spec["duration"],
                distance_km=Decimal(route_spec["distance"]),
                status=PublishStatus.PUBLISHED.value,
                created_by_id=admin.id,
            )
            session.add(route)
            await session.flush()
        else:
            route.title = route_spec["title"]
            route.summary = route_spec["summary"]
            route.duration_minutes = route_spec["duration"]
            route.distance_km = Decimal(route_spec["distance"])
            route.status = PublishStatus.PUBLISHED.value

        for index, task_spec in enumerate(route_spec["tasks"], start=1):
            (
                location_name,
                title,
                description,
                task_type,
                question,
                options,
                answer_or_qr,
                points,
                radius,
            ) = task_spec
            location = locations[location_name]
            task = await session.scalar(
                select(RouteTask).where(
                    RouteTask.route_id == route.id,
                    RouteTask.order_no == index,
                )
            )
            values = {
                "culture_item_id": culture.id,
                "location_id": location.id,
                "title": title,
                "description": description,
                "task_type": task_type.value,
                "question": question,
                "options": options,
                "correct_answer": answer_or_qr if task_type == TaskType.QUIZ else None,
                "points": points,
                "qr_code": answer_or_qr if task_type == TaskType.QR_CODE else None,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "radius_meters": radius,
            }
            if task:
                for key, value in values.items():
                    setattr(task, key, value)
            else:
                session.add(
                    RouteTask(
                        route_id=route.id,
                        order_no=index,
                        **values,
                    )
                )

    template = await session.scalar(
        select(CreationTemplate).where(CreationTemplate.code == "kapok-poster")
    )
    if not template:
        session.add(
            CreationTemplate(
                name="红棉国潮海报",
                code="kapok-poster",
                description="组合文化元素、校园地标与视觉风格，生成文化海报。",
                prompt_template="以{culture_element}和{campus_landmark}为主题，创作{style}风格文化海报。",
                options_schema={
                    "culture_element": ["木棉", "醒狮", "广彩"],
                    "campus_landmark": ["广州大学图书馆", "红棉广场"],
                    "style": ["国潮", "剪纸", "现代插画"],
                },
                status=PublishStatus.PUBLISHED.value,
                culture_item_id=culture.id,
            )
        )


async def main() -> None:
    async with AsyncSessionLocal() as session:
        roles = await ensure_roles(session)
        admin = await ensure_admin(session, roles["admin"])
        await ensure_badges(session)
        await ensure_demo_routes(session, admin)
        await session.commit()
    print("Seed data is ready.")


if __name__ == "__main__":
    asyncio.run(main())
