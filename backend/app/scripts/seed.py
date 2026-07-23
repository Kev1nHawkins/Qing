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
        if not await session.scalar(select(Badge).where(Badge.code == code)):
            session.add(
                Badge(
                    code=code,
                    name=name,
                    description=description,
                    rule_type=rule_type.value,
                    rule_value=rule_value,
                )
            )


async def ensure_demo_route(session, admin: User) -> None:
    if await session.scalar(select(Route).where(Route.slug == "kapok-trail")):
        return
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
        ("广州大学正门", "大学城外环西路入口", Decimal("23.0391000"), Decimal("113.3683000")),
        ("图书馆", "广州大学图书馆", Decimal("23.0387000"), Decimal("113.3702000")),
        ("红棉广场", "校园中心广场", Decimal("23.0379000"), Decimal("113.3714000")),
        ("校史展示点", "校园文化展示区", Decimal("23.0371000"), Decimal("113.3699000")),
        ("生活区文化墙", "学生生活区", Decimal("23.0359000"), Decimal("113.3689000")),
    ]
    locations = []
    for name, address, latitude, longitude in location_specs:
        location = Location(
            name=name,
            address=address,
            description=f"{name}红棉寻迹任务点",
            latitude=latitude,
            longitude=longitude,
            culture_item_id=culture.id,
        )
        session.add(location)
        locations.append(location)
    await session.flush()

    route = Route(
        title="红棉寻迹",
        slug="kapok-trail",
        summary="沿校园地标认识木棉与岭南文化的联系。",
        duration_minutes=60,
        distance_km=Decimal("2.30"),
        status=PublishStatus.PUBLISHED.value,
        created_by_id=admin.id,
    )
    session.add(route)
    await session.flush()

    task_specs = [
        ("领取红棉路线", TaskType.CHECK_IN, None, None),
        ("图书馆文化问答", TaskType.QUIZ, "广州的市花是什么？", "木棉"),
        ("红棉广场扫码", TaskType.QR_CODE, None, None),
        ("校史展示点打卡", TaskType.SIMULATED_LOCATION, None, None),
        ("完成文化宣言", TaskType.CHECK_IN, None, None),
    ]
    for index, (title, task_type, question, answer) in enumerate(task_specs, start=1):
        session.add(
            RouteTask(
                route_id=route.id,
                culture_item_id=culture.id,
                location_id=locations[index - 1].id,
                order_no=index,
                title=title,
                description=f"红棉寻迹第 {index} 站：{title}",
                task_type=task_type.value,
                question=question,
                options=["木棉", "紫荆", "桂花"] if question else None,
                correct_answer=answer,
                points=10,
                qr_code="LINGCHAO-KAPOK-03" if task_type == TaskType.QR_CODE else None,
                latitude=locations[index - 1].latitude,
                longitude=locations[index - 1].longitude,
                radius_meters=100,
            )
        )

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
        await ensure_demo_route(session, admin)
        await session.commit()
    print("Seed data is ready.")


if __name__ == "__main__":
    asyncio.run(main())
