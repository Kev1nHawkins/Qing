# 成员 5：社区与文化内容补充交付

## 协作边界

本次只补充现有文化与社区演示数据，不修改 API、数据库结构、文化页面、
移动端样式、AI 生成、路线任务、积分徽章或审核逻辑。成员 2 可直接使用既有
`GET /api/v1/cultures` 列表和详情响应展示新增内容。

## 文化内容清单

| slug | 标题 | 分类 | 封面 |
|---|---|---|---|
| `lingnan-culture-overview` | 岭南文化概述 | 岭南概览 | 前端回退图 |
| `kapok-hero-flower` | 木棉：广州的英雄花 | 广州城市文化 | `/demo/kapok.jpg` |
| `cantonese-opera-culture` | 粤剧文化 | 非遗艺术 | `/demo/cantonese-opera-ai.png` |
| `lingnan-arcades` | 岭南骑楼 | 建筑与园林 | 前端回退图 |
| `xiguan-mansions` | 西关大屋 | 建筑与园林 | 前端回退图 |
| `lingnan-gardens` | 岭南园林 | 建筑与园林 | 前端回退图 |
| `guangzhou-morning-tea` | 广州早茶文化 | 饮食文化 | 前端回退图 |
| `cantonese-cuisine-guangzhou` | 粤菜与广州饮食 | 饮食文化 | 前端回退图 |
| `guangzhou-university-history` | 广州大学历史沿革 | 校园文化 | `/demo/dexin-pavilion.jpg` |
| `guangzhou-university-motto` | 广州大学校训 | 校园文化 | `/demo/dexin-pavilion.jpg` |
| `guangzhou-university-emblem` | 广州大学校徽文化 | 校园文化 | `/demo/dexin-pavilion.jpg` |
| `guangzhou-university-three-campuses` | 一校三园与广州城市连接 | 校园文化 | `/demo/dexin-pavilion.jpg` |

每条内容均包含摘要、分段正文、来源名称与来源 URL；所有条目均为
`PUBLISHED`。来源以仓库 `data/knowledge_base/` 中已整理的政府、非遗机构和
广州大学官方资料为依据。

## 社区关联

`community-posts.json` 的 `culture_slug` 只用于种子脚本解析现有
`culture_item_id`，不会出现在 HTTP 响应中。

| 社区主题 | 关联文化 |
|---|---|
| 木棉、红棉活动与木棉角色 | `kapok-hero-flower` |
| 粤剧海报与水袖草案 | `cantonese-opera-culture` |
| 广彩、醒狮、粤语、剪纸和待核验旧照片 | `lingnan-culture-overview` |
| 骑楼观察 | `lingnan-arcades` |
| 未来校园海报 | `guangzhou-university-three-campuses` |
| 校园打卡与校园公告 | 不关联文化，保持 `CAMPUS` 分类 |

社区公开数据仍为 15 条：AI 作品 6 条、校园打卡 5 条、文化寻迹 4 条；
管理端另保留 2 条待审核、1 条驳回和 2 条下架内容。

## 既有 API 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 12,
    "items": [
      {
        "id": 1,
        "title": "木棉：广州的英雄花",
        "slug": "kapok-hero-flower",
        "category": "广州城市文化",
        "summary": "从木棉的花期、形态与广州城市记忆出发……",
        "content": "分段正文由 API 原样返回",
        "cover_image_url": "/demo/kapok.jpg",
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

