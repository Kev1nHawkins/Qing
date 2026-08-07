# 成员 5：社区与文化内容补充交付

## 协作边界

本次只扩充现有文化与社区演示数据，不修改 API、数据库结构、文化页面、
移动端样式、AI Provider、路线任务、积分徽章或审核逻辑。成员 2 可以继续通过
既有 `GET /api/v1/cultures` 列表和详情响应自动消费新增内容。

## 文化内容矩阵

共 30 条、7 个分类。每条均包含 50～120 字摘要、5 段正文、权威来源和本地
分类封面；状态均为 `PUBLISHED`。

| 分类 | 数量 | 条目 |
|---|---:|---|
| 岭南概览 | 2 | 岭南文化概述、粤语与广府话 |
| 广州城市文化 | 5 | 木棉、珠江、海上丝绸之路、十三行、花城花事 |
| 非遗艺术 | 6 | 粤剧、醒狮、广彩、广绣、广东音乐、广州玉雕 |
| 建筑与园林 | 5 | 骑楼、西关大屋、岭南园林、陈家祠、永庆坊 |
| 饮食文化 | 4 | 广州早茶、粤菜、凉茶、广式月饼 |
| 民俗节庆 | 3 | 迎春花市、广州龙舟、波罗诞 |
| 校园文化 | 5 | 广大历史、校训、校徽、一校三园、校歌 |

完整 slug、正文、来源及封面映射以 `backend/app/scripts/seed.py` 中的
`CULTURE_SPECS` 为准。种子仍通过 slug 幂等新增或更新。

## 统一封面

7 张封面均为 1536×1024、3:2 横幅，使用暖米色纸张、木棉红、岭南青绿、
靛蓝和少量金色的编辑插画体系。封面只表达分类主题，不冒充史料照片或具体文物实拍。

| 分类 | 封面路径 |
|---|---|
| 岭南概览 | `/demo/culture-covers/lingnan-overview.jpg` |
| 广州城市文化 | `/demo/culture-covers/guangzhou-city.jpg` |
| 非遗艺术 | `/demo/culture-covers/intangible-arts.jpg` |
| 建筑与园林 | `/demo/culture-covers/architecture-gardens.jpg` |
| 饮食文化 | `/demo/culture-covers/food-culture.jpg` |
| 民俗节庆 | `/demo/culture-covers/folk-festivals.jpg` |
| 校园文化 | `/demo/culture-covers/campus-culture.jpg` |

文件同时放在 `frontend-user` 与 `frontend-admin` 的 `public/demo/culture-covers/`
目录，保证两个前端离线运行时使用同一画面。生成方式、提示词规范和素材说明见
`data/demo/cultural-materials.md`。

## 社区关联

`community-posts.json` 的 `culture_slug` 只用于种子脚本解析现有
`culture_item_id`，不会进入 HTTP API 契约。

- 公开内容 30 条：AI 作品 12 条、校园打卡 10 条、文化寻迹 8 条。
- 管理演示 10 条：待审核 4 条、驳回 2 条、下架 4 条。
- AI 帖始终包含 `creation_id`，并按 `culture_slug` 关联文化内容。
- 文化帖只包含 `culture_item_id`，不包含 `creation_id`。
- 校园帖两个关联字段始终为空，避免被现有接口归入文化寻迹。

社区封面也只使用同一套 7 张分类封面；校园帖统一使用校园文化封面。帖子内容
覆盖资料核验、肖像与版权、非遗语境、健康边界、标识规范和社区隐私等演示场景。

## 既有 API 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 30,
    "items": [
      {
        "id": 1,
        "title": "木棉：广州的英雄花",
        "slug": "kapok-hero-flower",
        "category": "广州城市文化",
        "summary": "从木棉的花期、形态与广州城市记忆出发……",
        "content": "五段正文由 API 原样返回",
        "cover_image_url": "/demo/culture-covers/guangzhou-city.jpg",
        "source_title": "广州市林业和园林局：《植物百科——木棉》",
        "source_url": "https://lyylj.gz.gov.cn/kpyd/dwbk/zw/content/post_3032236.html",
        "status": "PUBLISHED"
      }
    ],
    "page": 1,
    "pageSize": 100
  },
  "requestId": "运行时生成"
}
```

实际 `id`、时间字段和 `requestId` 以本地数据库及请求结果为准。

## 不变项

红棉路线、地点、任务和 `kapok-poster` 模板仍只关联
`kapok-hero-flower`。本轮没有修改 `Member2Experience.vue`、文化页样式、
前端类型、路由、数据库字段或 API 响应结构。
