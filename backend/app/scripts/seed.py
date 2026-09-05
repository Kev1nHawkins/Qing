import asyncio
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.creation import CreationTemplate
from app.models.culture import CultureItem, Location
from app.models.enums import BadgeRuleType, PublishStatus, TaskType
from app.models.points import Badge
from app.models.route import Route, RouteTask
from app.models.user import Role, User


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
    culture = await session.scalar(
        select(CultureItem).where(CultureItem.slug == "kapok-hero-flower")
    )
    if not culture:
        culture = CultureItem(
            title="木棉：广州的英雄花",
            slug="kapok-hero-flower",
            category="岭南文化",
            summary="从木棉的城市记忆出发，连接广州与广州大学校园文化。",
            content="木棉在岭南地区具有鲜明的地域文化意象。本条目为演示数据，正式内容须补充权威来源复核。",
            source_title="岭潮共创演示素材（待内容负责人复核）",
            source_url=None,
            status=PublishStatus.PUBLISHED.value,
            created_by_id=admin.id,
        )
        session.add(culture)
        await session.flush()

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
        ("广州大学正门", "大学城外环西路入口", "校园轴线起点", "23.0370990", "113.3706420"),
        ("广州大学图书馆", "广州大学图书馆", "知识与校园文化交汇点", "23.0404540", "113.3703990"),
        ("何世杰体育馆广场", "何世杰体育馆正门广场", "连接广州亚运会、全运会与校园体育精神的打卡点", "23.0436550", "113.3704310"),
        ("校史馆门口", "广州大学校史馆门口", "从校史出发认识广州十三行与海上商都记忆", "23.0399440", "113.3706840"),
        ("红色长廊", "广州大学红色文化长廊", "了解广州革命先烈与青年担当的文化打卡点", "23.0384840", "113.3687460"),
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
                ("校史馆门口", "海丝商都打卡", "从广州大学校史空间连接十三行、海上丝绸之路与广州商贸文化。", TaskType.CHECK_IN, "请上传包含校史馆门口或馆名标识的现场照片", None, None, 20, 100),
                ("何世杰体育馆广场", "活力羊城打卡", "在体育馆广场感受广州从亚运会到全运会延续的城市体育活力。", TaskType.CHECK_IN, "请上传包含何世杰体育馆或广场标识的现场照片", None, None, 15, 100),
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

    await ensure_creation_templates(session, culture.id)


async def ensure_creation_templates(
    session: AsyncSession,
    kapok_culture_id: int | None,
) -> None:
    template_specs = [
        {
            "name": "红棉国潮海报",
            "code": "kapok-poster",
            "description": "组合文化元素、校园地标与视觉风格，生成文化海报。",
            "prompt_template": "以{culture_element}和{campus_landmark}为主题，创作{style}风格文化海报。",
            "options_schema": {
                "culture_element": ["木棉", "醒狮", "广彩"],
                "campus_landmark": ["广州大学图书馆", "红棉广场"],
                "style": ["国潮", "剪纸", "现代插画"],
            },
            "preview_url": "/demo/kapok.jpg",
            "culture_item_id": kapok_culture_id,
        },
        {
            "name": "醒狮校园活力海报",
            "code": "lion-dance-poster",
            "description": "用醒狮形象、校园空间与青年潮流语言表达广府活力。",
            "prompt_template": "以{culture_element}为主视觉，在{campus_landmark}场景中创作{style}风格醒狮校园海报。",
            "options_schema": {
                "culture_element": ["醒狮", "南狮", "锣鼓纹样"],
                "campus_landmark": ["广州大学正门", "何世杰体育馆广场"],
                "style": ["国潮插画", "剪纸", "潮玩"],
            },
            "preview_url": None,
            "culture_item_id": None,
        },
        {
            "name": "广彩校园纹样海报",
            "code": "guangcai-poster",
            "description": "将广彩纹样转译为连接传统工艺与校园生活的视觉设计。",
            "prompt_template": "围绕{culture_element}纹样，在{campus_landmark}场景中设计{style}风格校园文化海报。",
            "options_schema": {
                "culture_element": ["广彩", "缠枝纹", "岭南花鸟"],
                "campus_landmark": ["广州大学图书馆", "德信亭", "教学楼中庭"],
                "style": ["现代插画", "典雅国风", "信息设计"],
            },
            "preview_url": None,
            "culture_item_id": None,
        },
    ]
    for spec in template_specs:
        template = await session.scalar(
            select(CreationTemplate).where(CreationTemplate.code == spec["code"])
        )
        if not template:
            session.add(
                CreationTemplate(
                    **spec,
                    status=PublishStatus.PUBLISHED.value,
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
