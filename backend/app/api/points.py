import hashlib
import hmac

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.dependencies import CurrentUser, DbSession
from app.api.helpers import paginated
from app.core.config import settings
from app.core.response import success
from app.models.enums import PointReason
from app.models.points import PointRecord
from app.models.user import User
from app.schemas.points import PointRead, PointRedeemRequest

router = APIRouter(prefix="/points", tags=["Points"])
REWARD_REDEEM_REASON = PointReason.REWARD_REDEEM.value

SHOP_PRODUCTS = [
    {
        "code": "kapok-wallpaper",
        "name": "木棉花期手机壁纸",
        "subtitle": "把木棉花期装进每一次亮屏",
        "description": "解锁广州木棉与广大四季主题高清壁纸，让完成寻迹后的文化记忆每天都与你见面。",
        "category": "DIGITAL",
        "categoryLabel": "数字藏品",
        "points": 10,
        "delivery": "即时解锁",
        "limit": "ONCE",
        "badge": "轻松入手",
        "symbol": "花",
        "accent": "#b9333d",
    },
    {
        "code": "xiaomian-stickers",
        "name": "小棉表情贴纸包",
        "subtitle": "让每次聊天都带一点岭潮表情",
        "description": "收下小棉的问候、打卡、加油与文化热梗表情，把你的校园探索分享给更多朋友。",
        "category": "DIGITAL",
        "categoryLabel": "数字藏品",
        "points": 20,
        "delivery": "即时解锁",
        "limit": "ONCE",
        "badge": "同学人气款",
        "symbol": "棉",
        "accent": "#df7b45",
    },
    {
        "code": "library-bookplate",
        "name": "图书馆电子藏书票",
        "subtitle": "生成只属于你的文化身份藏书票",
        "description": "将姓名、路线成就和木棉纹样组合成专属电子藏书票，收藏或分享你的岭潮文化身份。",
        "category": "DIGITAL",
        "categoryLabel": "数字藏品",
        "points": 35,
        "delivery": "即时解锁",
        "limit": "REPEATABLE",
        "badge": "专属定制",
        "symbol": "藏",
        "accent": "#315f77",
    },
    {
        "code": "kapok-icon-pack",
        "name": "红棉头像与图标包",
        "subtitle": "用六款岭南图案换上文化新身份",
        "description": "一次解锁木棉、醒狮、骑楼等主题头像与图标，让社交主页也成为你的文化展示角。",
        "category": "DIGITAL",
        "categoryLabel": "数字藏品",
        "points": 30,
        "delivery": "即时解锁",
        "limit": "ONCE",
        "badge": "焕新身份",
        "symbol": "像",
        "accent": "#a94352",
    },
    {
        "code": "xiaomian-audio",
        "name": "小棉语音导览包",
        "subtitle": "戴上耳机，让小棉陪你重走三条路线",
        "description": "解锁木棉、岭南建筑与校园湖畔主题语音，在行走中听见地标背后容易错过的故事。",
        "category": "GUIDE",
        "categoryLabel": "导览权益",
        "points": 50,
        "delivery": "即时解锁",
        "limit": "ONCE",
        "badge": "沉浸推荐",
        "symbol": "声",
        "accent": "#386b5a",
    },
    {
        "code": "architecture-guide-cards",
        "name": "岭南建筑导览卡",
        "subtitle": "一套卡片，教你看懂身边的岭南建筑",
        "description": "用骑楼、连廊、中庭与灰空间四组图文卡，把普通路过变成一场有发现的建筑观察。",
        "category": "GUIDE",
        "categoryLabel": "导览权益",
        "points": 40,
        "delivery": "即时解锁",
        "limit": "ONCE",
        "badge": "发现力加成",
        "symbol": "览",
        "accent": "#52745b",
    },
    {
        "code": "weekend-docent-pass",
        "name": "周末文化导赏名额",
        "subtitle": "和讲解员一起发现地图之外的校园故事",
        "description": "预约一次校内主题小组导赏，在真实场景中提问、交流，解锁自助路线没有讲完的文化细节。",
        "category": "GUIDE",
        "categoryLabel": "导览权益",
        "points": 90,
        "delivery": "人工确认",
        "limit": "REPEATABLE",
        "badge": "小组限定",
        "symbol": "游",
        "accent": "#326852",
    },
    {
        "code": "lingnan-bookmarks",
        "name": "岭南纹样书签套装",
        "subtitle": "把广彩、木棉与骑楼夹进下一本书",
        "description": "三枚岭南主题纸质书签，将路线里的色彩和纹样带回日常阅读，也适合作为文化心意相赠。",
        "category": "CULTURAL",
        "categoryLabel": "文化文创",
        "points": 60,
        "delivery": "服务台领取",
        "limit": "REPEATABLE",
        "badge": "三枚成套",
        "symbol": "书",
        "accent": "#8a552f",
    },
    {
        "code": "kapok-postcard",
        "name": "红棉种子纸明信片",
        "subtitle": "写下寻迹故事，再亲手种出一份期待",
        "description": "在环保种子纸上寄出你的校园发现，完成书写后还可尝试种植，让文化记忆继续生长。",
        "category": "CULTURAL",
        "categoryLabel": "文化文创",
        "points": 70,
        "delivery": "服务台领取",
        "limit": "REPEATABLE",
        "badge": "会生长的礼物",
        "symbol": "信",
        "accent": "#a73b43",
    },
    {
        "code": "lingnan-pattern-tape",
        "name": "岭南窗花纹样胶带",
        "subtitle": "把满洲窗与木棉色彩贴进你的手账",
        "description": "融合满洲窗、木棉和广彩配色，用一卷纹样胶带装饰笔记、照片与寻迹收藏页。",
        "category": "CULTURAL",
        "categoryLabel": "文化文创",
        "points": 45,
        "delivery": "服务台领取",
        "limit": "REPEATABLE",
        "badge": "纹样收藏",
        "symbol": "纹",
        "accent": "#9b6640",
    },
    {
        "code": "campus-map-foldout",
        "name": "广大文化地图折页",
        "subtitle": "展开一张地图，收藏三校区文化坐标",
        "description": "收录大学城、桂花岗与黄埔校区代表性地标，既是下一次探索指南，也是可带走的校园文化图鉴。",
        "category": "CAMPUS",
        "categoryLabel": "校园限定",
        "points": 80,
        "delivery": "服务台领取",
        "limit": "REPEATABLE",
        "badge": "三校区收藏",
        "symbol": "图",
        "accent": "#346455",
    },
    {
        "code": "kapok-pin",
        "name": "岭潮木棉珐琅徽章",
        "subtitle": "把完成寻迹的高光时刻佩在身上",
        "description": "以木棉花和广州大学校园轮廓打造的珐琅纪念章，用一枚实体徽章证明你真正走过这段路线。",
        "category": "CAMPUS",
        "categoryLabel": "校园限定",
        "points": 100,
        "delivery": "服务台领取",
        "limit": "ONCE",
        "badge": "纪念限定",
        "symbol": "徽",
        "accent": "#9e3138",
    },
    {
        "code": "route-passport",
        "name": "校园寻迹盖章护照",
        "subtitle": "一本可以越走越丰富的实体探索护照",
        "description": "带上岭潮文化探索手册前往路线服务点盖章，让每次到达都留下看得见、摸得到的收藏印记。",
        "category": "CAMPUS",
        "categoryLabel": "校园限定",
        "points": 55,
        "delivery": "服务台领取",
        "limit": "ONCE",
        "badge": "探索者必备",
        "symbol": "章",
        "accent": "#3f735e",
    },
    {
        "code": "poster-hd-export",
        "name": "AI 海报高清导出券",
        "subtitle": "让你的文化创意以高清作品正式亮相",
        "description": "为一次岭潮共创作品解锁无水印高清导出，适合打印、参展或分享，让灵感不止停留在屏幕预览。",
        "category": "CREATION",
        "categoryLabel": "共创权益",
        "points": 120,
        "delivery": "即时到账",
        "limit": "REPEATABLE",
        "badge": "作品升级",
        "symbol": "创",
        "accent": "#72547c",
    },
    {
        "code": "co-create-template-pack",
        "name": "岭潮共创模板扩展包",
        "subtitle": "解锁三款限定版式，让下一张海报更出彩",
        "description": "获得广彩、醒狮和岭南窗花主题共创模板，用更丰富的构图快速完成具有个人风格的文化表达。",
        "category": "CREATION",
        "categoryLabel": "共创权益",
        "points": 80,
        "delivery": "即时到账",
        "limit": "ONCE",
        "badge": "限定模板",
        "symbol": "绘",
        "accent": "#765889",
    },
    {
        "code": "culture-workshop",
        "name": "岭南手作工坊预约",
        "subtitle": "亲手完成一件可以带走的岭南作品",
        "description": "优先预约广彩或醒狮主题校内手作体验，在老师带领下从认识技艺到完成自己的文化小作品。",
        "category": "EXPERIENCE",
        "categoryLabel": "文化体验",
        "points": 150,
        "delivery": "人工确认",
        "limit": "REPEATABLE",
        "badge": "动手体验",
        "symbol": "艺",
        "accent": "#c27a2b",
    },
    {
        "code": "culture-talk-pass",
        "name": "校园文化讲座优先席",
        "subtitle": "坐到更靠前的位置，与文化讲述者面对面",
        "description": "获得合作讲座或非遗分享会优先预约资格，并收藏专属电子纪念票，不错过现场交流的机会。",
        "category": "EXPERIENCE",
        "categoryLabel": "文化体验",
        "points": 180,
        "delivery": "人工确认",
        "limit": "REPEATABLE",
        "badge": "优先入场",
        "symbol": "讲",
        "accent": "#40688c",
    },
    {
        "code": "lingchao-tote",
        "name": "岭潮校园帆布袋",
        "subtitle": "把木棉与校园建筑背进日常生活",
        "description": "木棉和建筑线稿限定设计，兼具实用收纳与校园文化表达，让完成高阶探索的成就每天可见。",
        "category": "CULTURAL",
        "categoryLabel": "文化文创",
        "points": 220,
        "delivery": "服务台领取",
        "limit": "ONCE",
        "badge": "高阶收藏",
        "symbol": "袋",
        "accent": "#3e594b",
    },
]
SHOP_PRODUCT_MAP = {product["code"]: product for product in SHOP_PRODUCTS}


def redemption_delivery(product: dict) -> dict:
    delivery = product["delivery"]
    if delivery in {"即时解锁", "即时到账"}:
        return {
            "fulfillment": "DIGITAL",
            "status": "AVAILABLE",
            "statusLabel": "已解锁",
            "actionLabel": "查看权益",
            "instruction": "数字权益已存入当前账号，可凭兑换码在对应功能中使用。",
        }
    if delivery == "服务台领取":
        return {
            "fulfillment": "PICKUP",
            "status": "READY_FOR_PICKUP",
            "statusLabel": "待领取",
            "actionLabel": "出示领取码",
            "instruction": "请在校园文化活动服务台出示兑换码，由工作人员核验后领取。",
        }
    return {
        "fulfillment": "EXPERIENCE",
        "status": "PENDING_CONFIRMATION",
        "statusLabel": "待预约",
        "actionLabel": "查看预约凭证",
        "instruction": "请保留预约凭证，活动时间确认后由工作人员通知具体场次。",
    }


def redemption_item(record: PointRecord) -> dict:
    parts = record.business_key.split(":", 2)
    product_code = parts[1] if len(parts) >= 2 else "archived-product"
    redemption_id = parts[2] if len(parts) >= 3 else str(record.id)
    product = SHOP_PRODUCT_MAP.get(product_code)
    if product:
        delivery_meta = redemption_delivery(product)
        return {
            "recordId": record.id,
            "redemptionId": redemption_id,
            "voucherCode": redemption_voucher(record),
            "productCode": product["code"],
            "productName": product["name"],
            "subtitle": product["subtitle"],
            "category": product["category"],
            "categoryLabel": product["categoryLabel"],
            "symbol": product["symbol"],
            "accent": product["accent"],
            "cost": abs(record.amount),
            "delivery": product["delivery"],
            "redeemedAt": record.created_at,
            **delivery_meta,
        }
    return {
        "recordId": record.id,
        "redemptionId": redemption_id,
        "voucherCode": redemption_voucher(record),
        "productCode": product_code,
        "productName": record.description.removeprefix("兑换商品："),
        "subtitle": "历史兑换商品",
        "category": "ARCHIVED",
        "categoryLabel": "历史兑换",
        "symbol": "兑",
        "accent": "#66736c",
        "cost": abs(record.amount),
        "delivery": "请联系活动服务台",
        "redeemedAt": record.created_at,
        "fulfillment": "PICKUP",
        "status": "READY_FOR_PICKUP",
        "statusLabel": "待核验",
        "actionLabel": "查看兑换凭证",
        "instruction": "该商品已下架，请凭兑换码联系活动服务台核验处理。",
    }


def redemption_voucher(record: PointRecord) -> str:
    message = f"{record.user_id}:{record.id}:{record.business_key}".encode()
    digest = hmac.new(
        settings.jwt_secret_key.encode(),
        message,
        hashlib.sha256,
    ).hexdigest()[:12]
    return f"LC-{digest.upper()}"


@router.get("/shop", summary="积分商城商品")
async def point_shop() -> dict:
    return success(
        {
            "categories": [
                {"code": "ALL", "name": "全部"},
                {"code": "DIGITAL", "name": "数字藏品"},
                {"code": "GUIDE", "name": "导览权益"},
                {"code": "CULTURAL", "name": "文化文创"},
                {"code": "CAMPUS", "name": "校园限定"},
                {"code": "CREATION", "name": "共创权益"},
                {"code": "EXPERIENCE", "name": "文化体验"},
            ],
            "products": SHOP_PRODUCTS,
        }
    )


@router.get("/redemptions", summary="我的积分商城兑换")
async def point_redemptions(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
) -> dict:
    filters = [
        PointRecord.user_id == current_user.id,
        PointRecord.reason_type == REWARD_REDEEM_REASON,
        PointRecord.business_key.like("redeem:%"),
    ]
    total = await db.scalar(select(func.count(PointRecord.id)).where(*filters))
    records = (
        await db.scalars(
            select(PointRecord)
            .where(*filters)
            .order_by(PointRecord.created_at.desc(), PointRecord.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    return success(
        {
            "total": total or 0,
            "items": [redemption_item(record) for record in records],
            "page": page,
            "pageSize": page_size,
        }
    )


@router.get("/summary", summary="我的积分概览")
async def point_summary(current_user: CurrentUser) -> dict:
    return success({"pointsTotal": current_user.points_total})


@router.get("/records", summary="我的积分流水")
async def point_records(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
) -> dict:
    filters = [PointRecord.user_id == current_user.id]
    return success(
        await paginated(
            db,
            stmt=select(PointRecord)
            .where(*filters)
            .order_by(PointRecord.created_at.desc()),
            count_stmt=select(func.count(PointRecord.id)).where(*filters),
            page=page,
            page_size=page_size,
            schema=PointRead,
        )
    )


@router.post("/redeem", summary="兑换积分商城商品（幂等）")
async def redeem_product(
    payload: PointRedeemRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    product = SHOP_PRODUCT_MAP.get(payload.product_code)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在或已下架")

    user = await db.scalar(
        select(User).where(User.id == current_user.id).with_for_update()
    )
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    business_key = f"redeem:{product['code']}:{payload.redemption_id}"
    existing = await db.scalar(
        select(PointRecord).where(
            PointRecord.user_id == current_user.id,
            PointRecord.business_key == business_key,
        )
    )
    if existing:
        return success(
            {
                "recordId": existing.id,
                "productCode": product["code"],
                "productName": product["name"],
                "cost": product["points"],
                "pointsTotal": user.points_total,
                "delivery": product["delivery"],
                "alreadyRedeemed": True,
            },
            "兑换请求已处理",
        )

    if product["limit"] == "ONCE":
        redeemed_once = await db.scalar(
            select(PointRecord.id).where(
                PointRecord.user_id == current_user.id,
                PointRecord.business_key.like(f"redeem:{product['code']}:%"),
            )
        )
        if redeemed_once:
            raise HTTPException(status_code=409, detail="该商品每位用户限兑一次")

    cost = int(product["points"])
    if user.points_total < cost:
        raise HTTPException(
            status_code=400,
            detail=f"积分不足，还需要 {cost - user.points_total} 积分",
        )

    user.points_total -= cost
    record = PointRecord(
        user_id=user.id,
        amount=-cost,
        balance_after=user.points_total,
        reason_type=REWARD_REDEEM_REASON,
        reason_id=None,
        business_key=business_key,
        description=f"兑换商品：{product['name']}",
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return success(
        {
            "recordId": record.id,
            "productCode": product["code"],
            "productName": product["name"],
            "cost": cost,
            "pointsTotal": user.points_total,
            "delivery": product["delivery"],
            "alreadyRedeemed": False,
        },
        "兑换成功",
    )
