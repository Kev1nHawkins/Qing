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

    location_specs = [
        ("广州大学正门", "大学城外环西路入口", "校园轴线起点", "23.0391000", "113.3683000"),
        ("广州大学图书馆", "广州大学图书馆", "知识与校园文化交汇点", "23.0387000", "113.3702000"),
        ("红棉广场", "校园中心广场", "木棉主题图片任务点", "23.0379000", "113.3714000"),
        ("校史展示点", "校园文化展示区", "校史与城市记忆打卡点", "23.0371000", "113.3699000"),
        ("生活区文化墙", "学生生活区", "青年文化表达拍照点", "23.0359000", "113.3689000"),
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
                ("广州大学正门", "正门启程", "观察校园轴线与入口景观，拍摄正门或校园轴线照片。", TaskType.CHECK_IN, "请上传正门或校园轴线现场照片", None, None, 10, 120),
                ("广州大学图书馆", "求知寻花", "阅读文化提示，回答广州城市文化问题。", TaskType.QUIZ, "广州的市花是什么？", ["木棉", "紫荆", "桂花"], "木棉", 15, 100),
                ("红棉广场", "红棉扫码", "扫描广场任务牌上的二维码，验证红棉文化地标。", TaskType.QR_CODE, "请扫描红棉广场任务二维码", None, "LINGCHAO-KAPOK-03", 15, 100),
                ("校史展示点", "文脉定位", "到达校史展示点附近，使用浏览器位置服务完成打卡。", TaskType.SIMULATED_LOCATION, "请在校史展示点 100 米范围内完成位置打卡", None, None, 20, 100),
                ("生活区文化墙", "青年文化记录", "拍摄一张校园文化图片，记录你发现的岭南元素。", TaskType.CHECK_IN, "请上传现场照片完成图片打卡", None, None, 15, 100),
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
