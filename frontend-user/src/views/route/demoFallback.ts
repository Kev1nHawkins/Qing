import type { CultureRoute, Location, RouteTask } from '@/types'

const locations: Location[] = [
  { id: -1, name: '广州大学正门', address: '大学城外环西路入口', description: '校园轴线起点', latitude: '23.0391000', longitude: '113.3683000', image_url: null, culture_item_id: null },
  { id: -2, name: '广州大学图书馆', address: '广州大学大学城校区图书馆', description: '校园文化知识问答点', latitude: '23.0387000', longitude: '113.3701000', image_url: null, culture_item_id: null },
  { id: -3, name: '何世杰体育馆广场', address: '何世杰体育馆正门广场', description: '连接广州亚运会、全运会与校园体育精神', latitude: '23.0379000', longitude: '113.3714000', image_url: null, culture_item_id: null },
  { id: -4, name: '校史馆门口', address: '广州大学校史馆门口', description: '认识广州十三行与海上商都记忆', latitude: '23.0371000', longitude: '113.3699000', image_url: null, culture_item_id: null },
  { id: -5, name: '红色长廊', address: '广州大学红色文化长廊', description: '了解广州革命先烈与青年担当', latitude: '23.0359000', longitude: '113.3689000', image_url: null, culture_item_id: null },
]

function makeTask(
  id: number,
  location: Location,
  order: number,
  title: string,
  description: string,
  taskType: string,
  question: string,
  points: number,
): RouteTask {
  return {
    id,
    route_id: -1,
    culture_item_id: null,
    location_id: location.id,
    order_no: order,
    title,
    description,
    task_type: taskType,
    question,
    options: taskType === 'QUIZ' ? ['木棉', '桂花', '紫荆花', '荷花'] : null,
    points,
    latitude: location.latitude,
    longitude: location.longitude,
    radius_meters: order === 1 ? 120 : 100,
  }
}

const tasks: RouteTask[] = [
  makeTask(-1, locations[0], 1, '正门启程', '在大学正门开启岭潮路线，认识醒狮所代表的勇气、协作与广府精气神。', 'CHECK_IN', '请上传包含广州大学正门或校名标识的现场照片', 10),
  makeTask(-2, locations[1], 2, '图书馆文化问答', '通过广州文化知识问答，连接校园阅读与岭南城市记忆。', 'QUIZ', '广州的市花是什么？', 10),
  makeTask(-3, locations[2], 3, '活力羊城打卡', '在体育馆广场感受广州从亚运会到全运会延续的城市体育活力。', 'CHECK_IN', '请上传包含何世杰体育馆或广场标识的现场照片', 15),
  makeTask(-4, locations[3], 4, '海丝商都打卡', '从广州大学校史空间连接十三行、海上丝绸之路与广州商贸文化。', 'CHECK_IN', '请上传包含校史馆门口或馆名标识的现场照片', 20),
  makeTask(-5, locations[4], 5, '英雄薪火打卡', '沿红色长廊认识广州革命先烈，把城市记忆转化为青年担当。', 'CHECK_IN', '请上传包含红色长廊主题展板或标识的现场照片', 15),
]

export const demoRouteFallback: { routes: CultureRoute[]; locations: Location[] } = {
  locations,
  routes: [{
    id: -1,
    title: '红棉寻迹',
    slug: 'kapok-trail-offline-preview',
    summary: '大学城校区文化路线离线预览；恢复 MySQL 后可领取路线、提交任务和获得积分。',
    cover_image_url: null,
    duration_minutes: 90,
    distance_km: '2.4',
    status: 'PREVIEW',
    tasks,
  }],
}
