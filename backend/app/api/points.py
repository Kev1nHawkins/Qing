from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.dependencies import CurrentUser, DbSession
from app.api.helpers import paginated
from app.core.response import success
from app.models.enums import PointReason
from app.models.points import PointRecord
from app.models.user import User
from app.schemas.points import PointRead, PointRedeemRequest

router = APIRouter(prefix="/points", tags=["Points"])

SHOP_PRODUCTS = [
    {
        "code": "kapok-wallpaper",
        "name": "木棉花期手机壁纸",
        "subtitle": "四季校园数字收藏",
        "description": "解锁一组广州木棉与广大校园主题高清壁纸。",
        "category": "DIGITAL",
        "categoryLabel": "数字藏品",
        "points": 10,
        "delivery": "即时解锁",
        "limit": "ONCE",
        "badge": "入门好礼",
        "symbol": "花",
        "accent": "#b9333d",
    },
    {
        "code": "xiaomian-stickers",
        "name": "小棉表情贴纸包",
        "subtitle": "校园聊天专属表情",
        "description": "包含问候、打卡、加油和岭南文化主题表情。",
        "category": "DIGITAL",
        "categoryLabel": "数字藏品",
        "points": 20,
        "delivery": "即时解锁",
        "limit": "ONCE",
        "badge": "人气",
        "symbol": "棉",
        "accent": "#df7b45",
    },
    {
        "code": "library-bookplate",
        "name": "图书馆电子藏书票",
        "subtitle": "生成个人文化身份卡",
        "description": "以姓名、路线成就和木棉纹样生成专属电子藏书票。",
        "category": "DIGITAL",
        "categoryLabel": "数字藏品",
        "points": 35,
        "delivery": "即时解锁",
        "limit": "REPEATABLE",
        "badge": "可定制",
        "symbol": "藏",
        "accent": "#315f77",
    },
    {
        "code": "xiaomian-audio",
        "name": "小棉语音导览包",
        "subtitle": "三条路线文化讲解",
        "description": "解锁木棉、岭南建筑与校园湖畔主题语音内容。",
        "category": "GUIDE",
        "categoryLabel": "导览权益",
        "points": 50,
        "delivery": "即时解锁",
        "limit": "ONCE",
        "badge": "推荐",
        "symbol": "声",
        "accent": "#386b5a",
    },
    {
        "code": "lingnan-bookmarks",
        "name": "岭南纹样书签套装",
        "subtitle": "广彩、木棉、骑楼三款",
        "description": "纸质书签三枚装，适合阅读与校园文化传播。",
        "category": "CULTURAL",
        "categoryLabel": "文化文创",
        "points": 60,
        "delivery": "服务台领取",
        "limit": "REPEATABLE",
        "badge": "实体",
        "symbol": "书",
        "accent": "#8a552f",
    },
    {
        "code": "kapok-postcard",
        "name": "红棉种子纸明信片",
        "subtitle": "可书写、可种植",
        "description": "使用环保种子纸制作，记录一次校园寻迹故事。",
        "category": "CULTURAL",
        "categoryLabel": "文化文创",
        "points": 70,
        "delivery": "服务台领取",
        "limit": "REPEATABLE",
        "badge": "环保",
        "symbol": "信",
        "accent": "#a73b43",
    },
    {
        "code": "campus-map-foldout",
        "name": "广大文化地图折页",
        "subtitle": "三校区文化地标收藏版",
        "description": "收录大学城、桂花岗与黄埔校区的文化地标。",
        "category": "CAMPUS",
        "categoryLabel": "校园限定",
        "points": 80,
        "delivery": "服务台领取",
        "limit": "REPEATABLE",
        "badge": "校园限定",
        "symbol": "图",
        "accent": "#346455",
    },
    {
        "code": "kapok-pin",
        "name": "岭潮木棉珐琅徽章",
        "subtitle": "校园寻迹纪念徽章",
        "description": "以木棉花与广州大学校园轮廓为核心设计。",
        "category": "CAMPUS",
        "categoryLabel": "校园限定",
        "points": 100,
        "delivery": "服务台领取",
        "limit": "ONCE",
        "badge": "限定",
        "symbol": "徽",
        "accent": "#9e3138",
    },
    {
        "code": "poster-hd-export",
        "name": "AI 海报高清导出券",
        "subtitle": "解锁无水印高清文件",
        "description": "用于一次文化共创作品的高清导出与展示。",
        "category": "CREATION",
        "categoryLabel": "共创权益",
        "points": 120,
        "delivery": "即时到账",
        "limit": "REPEATABLE",
        "badge": "创作者",
        "symbol": "创",
        "accent": "#72547c",
    },
    {
        "code": "culture-workshop",
        "name": "岭南手作工坊预约",
        "subtitle": "广彩或醒狮主题体验",
        "description": "兑换一次校内文化体验活动优先预约资格。",
        "category": "EXPERIENCE",
        "categoryLabel": "文化体验",
        "points": 150,
        "delivery": "人工确认",
        "limit": "REPEATABLE",
        "badge": "体验",
        "symbol": "艺",
        "accent": "#c27a2b",
    },
    {
        "code": "culture-talk-pass",
        "name": "校园文化讲座优先席",
        "subtitle": "前排席位与电子纪念票",
        "description": "用于平台合作讲座或非遗分享会的优先预约。",
        "category": "EXPERIENCE",
        "categoryLabel": "文化体验",
        "points": 180,
        "delivery": "人工确认",
        "limit": "REPEATABLE",
        "badge": "活动",
        "symbol": "讲",
        "accent": "#40688c",
    },
    {
        "code": "lingchao-tote",
        "name": "岭潮校园帆布袋",
        "subtitle": "木棉与建筑线稿限定款",
        "description": "可重复使用的校园文创帆布袋，展示青年文化表达。",
        "category": "CULTURAL",
        "categoryLabel": "文化文创",
        "points": 220,
        "delivery": "服务台领取",
        "limit": "ONCE",
        "badge": "高阶奖励",
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
            "voucherCode": f"LC-{record.id:06d}",
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
        "voucherCode": f"LC-{record.id:06d}",
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
        PointRecord.reason_type == PointReason.REWARD_REDEEM.value,
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
                "pointsTotal": existing.balance_after,
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

    user = await db.scalar(
        select(User).where(User.id == current_user.id).with_for_update()
    )
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
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
        reason_type=PointReason.REWARD_REDEEM.value,
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
