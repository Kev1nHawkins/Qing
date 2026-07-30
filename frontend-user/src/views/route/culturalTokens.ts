import type { RouteTask } from '@/types'

export interface CulturalToken {
  code: string
  name: string
  glyph: string
  figure: string
  theme: string
  message: string
  knowledge: string
  tone: 'kapok' | 'jade' | 'gold' | 'ocean' | 'flame'
}

const kapokTrailTokens: Record<number, CulturalToken> = {
  1: {
    code: 'START-LION',
    name: '广府启程令',
    glyph: '狮',
    figure: '醒狮少年',
    theme: '勇气 · 协作 · 启程',
    message: '欢迎加入岭潮寻迹。从广州大学正门出发，让醒狮的精气神陪你走进校园里的广州故事。',
    knowledge: '醒狮集武术、舞蹈和锣鼓于一体，是广府文化中迎祥纳福、奋发向前的鲜明形象。',
    tone: 'kapok',
  },
  2: {
    code: 'KNOWLEDGE-RAM',
    name: '羊城求知令',
    glyph: '穗',
    figure: '五羊衔穗',
    theme: '求知 · 分享 · 传承',
    message: '知识不只看分数。你已经完成一次广州文化探索，把今天学到的故事讲给下一位同行者吧。',
    knowledge: '广州又称羊城、穗城，五羊衔穗的传说寄托着人们对丰足、友善与共享的城市愿望。',
    tone: 'jade',
  },
  3: {
    code: 'SPORTS-GUANGZHOU',
    name: '活力羊城令',
    glyph: '跃',
    figure: '亚运活力使者',
    theme: '拼搏 · 开放 · 同行',
    message: '你已点亮校园体育坐标。从广州亚运会到全运会，城市体育精神在每一次奔跑与协作中延续。',
    knowledge: '广州曾承办第十六届亚洲运动会，并持续以大型综合体育赛事连接城市更新、志愿服务与全民健身。',
    tone: 'gold',
  },
  4: {
    code: 'THIRTEEN-FACTORIES',
    name: '海丝商都令',
    glyph: '舶',
    figure: '十三行商船',
    theme: '交流 · 海贸 · 城市记忆',
    message: '从校史馆回望广州城。十三行见证了广州连接世界的商贸往来，也留下跨文化交流的城市基因。',
    knowledge: '清代广州十三行曾是重要的对外贸易机构群体，广州由此形成海贸、工艺与多元文化交汇的历史图景。',
    tone: 'ocean',
  },
  5: {
    code: 'HERO-FLAME',
    name: '英雄薪火令',
    glyph: '炬',
    figure: '红色薪火',
    theme: '信念 · 担当 · 纪念',
    message: '你已走到本路线的精神坐标。铭记广州革命先烈，把历史中的理想与勇气化作今天的青年担当。',
    knowledge: '广州是一座具有深厚革命传统的英雄城市，黄花岗起义、广州起义等历史共同构成珍贵的红色记忆。',
    tone: 'flame',
  },
}

const fallbackToken: CulturalToken = {
  code: 'LINGCHAO-EXPLORER',
  name: '岭潮探索令',
  glyph: '潮',
  figure: '岭潮文化使者',
  theme: '观察 · 共创 · 分享',
  message: '你完成了一个校园文化节点。带着这份观察继续前进，让文化在行走、创作与分享中被重新看见。',
  knowledge: '校园文化与城市文化并非彼此分离，每一次现场观察都能成为理解地方文化的新入口。',
  tone: 'jade',
}

export function culturalTokenForTask(task: RouteTask): CulturalToken {
  return kapokTrailTokens[task.order_no] || fallbackToken
}

export const libraryQuizQuestions = [
  {
    question: '广州的市花是什么？',
    options: ['木棉', '紫荆', '桂花'],
    answer: '木棉',
    fact: '木棉花色鲜红、树姿挺拔，也被称为“英雄花”。',
  },
  {
    question: '广州“羊城”“穗城”的别称与哪一则传说有关？',
    options: ['五羊衔穗', '鲤鱼跃龙门', '嫦娥奔月'],
    answer: '五羊衔穗',
    fact: '五羊传说表达了先民对风调雨顺、五谷丰登的愿望。',
  },
  {
    question: '粤剧最具代表性的文化身份是？',
    options: ['岭南传统戏曲', '北方曲艺', '西洋歌剧'],
    answer: '岭南传统戏曲',
    fact: '粤剧使用粤语演唱，融合唱、做、念、打等表演方式。',
  },
  {
    question: '清代广州十三行主要承担什么功能？',
    options: ['对外贸易', '科举考试', '水利管理'],
    answer: '对外贸易',
    fact: '十三行让广州成为当时连接中国与世界的重要商贸窗口。',
  },
  {
    question: '广州骑楼长廊最适应哪一种气候需求？',
    options: ['遮阳避雨', '抵御暴雪', '储存冰块'],
    answer: '遮阳避雨',
    fact: '骑楼下连续的公共空间适应岭南炎热多雨的气候，也便利街市交往。',
  },
]
