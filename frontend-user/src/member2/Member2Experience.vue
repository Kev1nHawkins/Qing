<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '@/services/api'
import MediaImage from '@/components/MediaImage.vue'
import PageState from '@/components/PageState.vue'
import XiaomianMascot from '@/components/XiaomianMascot.vue'
import CampusSceneCard from '@/components/CampusSceneCard.vue'
import PosterStudio from '@/components/PosterStudio.vue'
import { cultureVisual, visuals } from '@/data/visuals'
import gzuOfficialLogo from '@/assets/culture/gzu-official-logo.png'
import type { Badge, CreationTemplate, Culture, CultureRoute, PageData, Post } from '@/types'

type ViewName = 'home' | 'cultures' | 'detail' | 'guide' | 'create' | 'profile'
const supportedViews: ViewName[] = ['home', 'cultures', 'detail', 'guide', 'create', 'profile']
const requestedView = new URLSearchParams(window.location.search).get('view') as ViewName | null
const view = ref<ViewName>(requestedView && supportedViews.includes(requestedView) ? requestedView : 'home')
const cultures = ref<Culture[]>([])
const routes = ref<CultureRoute[]>([])
const templates = ref<CreationTemplate[]>([])
const posts = ref<Post[]>([])
const badges = ref<Badge[]>([])
const backendConnected = ref(false)
const platformError = ref('')
const selected = ref<Culture | null>(null)
const loading = ref(false)
const error = ref('')
const keyword = ref('')
const category = ref('全部')
const question = ref('')
const authForm = ref({ username: '', password: '' })
const authLoading = ref(false)
const authError = ref('')
const currentUser = ref<{ username: string; nickname: string; points_total: number } | null>(null)
const mine = ref({ badges: 0, creations: 0, records: 0 })
const messages = ref([
  { from: 'guide', text: '你好，我是小棉。我们可以从广州的市花木棉出发，一起寻找岭南文化在广州大学校园里的当代表达。' },
])
const categories = computed(() => ['全部', ...new Set(cultures.value.map(item => item.category))])
const filtered = computed(() => cultures.value.filter(item => {
  const byCategory = category.value === '全部' || item.category === category.value
  const byKeyword = !keyword.value || `${item.title}${item.summary}`.includes(keyword.value.trim())
  return byCategory && byKeyword
}))

async function loadCultures() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get<{ data: PageData<Culture> }>('/cultures', { params: { pageSize: 100 } })
    cultures.value = data.data.items
  } catch (event) {
    error.value = (event as Error).message
  } finally { loading.value = false }
}
async function loadPlatform() {
  platformError.value = ''
  const [routeResult, templateResult, postResult, badgeResult] = await Promise.allSettled([
    api.get<{ data: PageData<CultureRoute> }>('/routes', { params: { pageSize: 10 } }),
    api.get<{ data: PageData<CreationTemplate> }>('/creations/templates', { params: { pageSize: 10 } }),
    api.get<{ data: PageData<Post> }>('/community/posts', { params: { pageSize: 10 } }),
    api.get<{ data: Badge[] }>('/badges'),
  ])
  if (routeResult.status === 'fulfilled') {
    routes.value = routeResult.value.data.data.items
    if (routes.value[0]) {
      const detail = await api.get<{ data: CultureRoute }>(`/routes/${routes.value[0].id}`)
      routes.value[0] = detail.data.data
    }
  }
  if (templateResult.status === 'fulfilled') templates.value = templateResult.value.data.data.items
  if (postResult.status === 'fulfilled') posts.value = postResult.value.data.data.items
  if (badgeResult.status === 'fulfilled') badges.value = badgeResult.value.data.data
  const results = [routeResult, templateResult, postResult, badgeResult]
  backendConnected.value = results.some(result => result.status === 'fulfilled')
  if (results.some(result => result.status === 'rejected')) platformError.value = '部分服务暂时不可用，其余真实数据已正常展示。'
}
function navigate(next: ViewName) {
  view.value = next
  const url = new URL(window.location.href)
  url.searchParams.set('view', next)
  window.history.replaceState(null, '', url)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
function openCulture(item: Culture) { selected.value = item; navigate('detail') }
function ask(text?: string) {
  const content = (text || question.value).trim()
  if (!content) return
  messages.value.push({ from: 'user', text: content })
  messages.value.push({ from: 'guide', text: '文化问答服务正在由成员 3 接入。当前你可以继续查看权威文化条目，或进入“红棉寻迹”体验校园中的文化线索。' })
  question.value = ''
}
async function loadProfile() {
  const [me, badgeList, creationList, pointList] = await Promise.all([
    api.get('/auth/me'), api.get('/badges/mine'), api.get('/creations'), api.get('/points/records'),
  ])
  currentUser.value = me.data.data
  mine.value = { badges: badgeList.data.data.length, creations: creationList.data.data.total, records: pointList.data.data.total }
}
async function login() {
  authLoading.value = true
  authError.value = ''
  try {
    const response = await api.post('/auth/login', authForm.value)
    localStorage.setItem('accessToken', response.data.data.access_token)
    await loadProfile()
  } catch (event) { authError.value = (event as Error).message }
  finally { authLoading.value = false }
}
function logout() { localStorage.removeItem('accessToken'); currentUser.value = null; mine.value = { badges: 0, creations: 0, records: 0 } }
onMounted(() => { loadCultures(); loadPlatform(); if (localStorage.getItem('accessToken')) loadProfile().catch(logout) })
</script>

<template>
  <div class="m2-app">
    <header class="m2-header">
      <button class="m2-brand" type="button" aria-label="返回探索首页" @click="navigate('home')"><span>岭</span><b>岭潮共创<small>LINGNAN · GZHU</small></b><img class="m2-official-logo" :src="gzuOfficialLogo" alt="广州大学" /></button>
      <nav aria-label="成员2预览导航">
        <button :class="{ active: view === 'home' }" @click="navigate('home')">探索</button>
        <button :class="{ active: ['cultures','detail'].includes(view) }" @click="navigate('cultures')">文化</button>
        <button :class="{ active: view === 'guide' }" @click="navigate('guide')">小棉导览</button>
        <button :class="{ active: view === 'create' }" @click="navigate('create')">AI 共创</button>
        <button :class="{ active: view === 'profile' }" @click="navigate('profile')">我的</button>
      </nav>
    </header>

    <main>
      <template v-if="view === 'home'">
        <div class="m2-live-status" :class="{ online: backendConnected }"><span aria-hidden="true" /><b>{{ backendConnected ? '后端实时连接中' : '正在连接后端' }}</b><small>FastAPI · /api/v1 · 统一响应已接入</small><button type="button" @click="loadPlatform">刷新数据</button></div>
        <section class="m2-hero">
          <div class="m2-hero-photo"><MediaImage :src="visuals.campus" alt="广州大学大学城校区创新大楼" eager /></div>
          <div class="m2-hero-shade" />
          <div class="m2-hero-copy">
            <p class="m2-kicker">岭南文化与校园文化传承 AI 传播平台</p>
            <h1>让岭南文化，<br />在广大校园里继续生长。</h1>
            <p>从一朵木棉出发，听数字人“小棉”讲述广州，在校园寻迹中理解文化，再用 AI 创作属于这一代大学生的岭南表达。</p>
            <div class="m2-actions"><button class="m2-primary" @click="navigate('cultures')">开始文化探索</button><button class="m2-secondary" @click="navigate('guide')">遇见数字人小棉</button></div>
          </div>
          <aside class="m2-hero-guide"><div class="m2-hero-guide-portrait"><XiaomianMascot /></div><div class="m2-hero-guide-copy"><small>YOUR CULTURE GUIDE</small><strong>你好，我是小棉</strong><span>先从“红棉寻迹”认识广州与广大校园，再一起完成文化共创。</span><button type="button" @click="navigate('guide')">开始导览</button></div></aside>
        </section>

        <section class="m2-guide-strip">
          <div class="m2-guide-mascot"><XiaomianMascot /></div>
          <div><p class="m2-kicker">MEET XIAOMIAN</p><h2>让数字人把文化故事讲进校园生活</h2><p>小棉以广州木棉为形象线索，把权威文化内容转化为更自然的校园导览。她会带你认识一处地点、一段历史，再推荐下一条寻迹路线和共创主题。</p><div class="m2-guide-topics"><span>木棉与广州</span><span>广大校园记忆</span><span>岭南非遗</span></div></div>
          <button class="m2-primary" type="button" @click="navigate('guide')">和小棉聊聊</button>
        </section>

        <section class="m2-campus-signals" aria-label="广州大学校园文化元素">
          <article class="m2-motto-tile"><div class="m2-gzhu-seal"><span>广大</span><small>1927</small></div><div><img class="m2-motto-logo" :src="gzuOfficialLogo" alt="广州大学官方标识" /><h3>博学笃行<br />与时俱进</h3><small>把大学精神写进每一次文化探索</small></div></article>
          <article class="m2-three-campus-tile"><p>THREE CAMPUSES</p><h3>一校三园 · 文化共生</h3><div><span><i>01</i>大学城校区</span><span><i>02</i>桂花岗校区</span><span><i>03</i>黄埔校区</span></div><small>共同构成广州大学校园文化地图</small></article>
          <article class="m2-mini-route"><header><span>红棉寻迹<small>大学城校区示范线</small></span><b>2.4 KM</b></header><div class="m2-route-line"><i /><i /><i /><i /><i /></div><footer><span>正门</span><span>图书馆</span><span>体育馆</span><span>校史馆</span><span>红色长廊</span></footer></article>
          <article class="m2-kapok-season"><div class="m2-kapok-symbol"><i /><i /><i /><i /><i /><b /></div><div><p>KAPOK SEASON</p><strong>03—04</strong><span>木棉花期 · 城市英雄花</span></div></article>
        </section>

        <section class="m2-section m2-campus-personalities">
          <div class="m2-section-head"><div><p class="m2-kicker">THREE CAMPUSES · ONE GZHU</p><h2>三种校园气质，一张广大文化地图</h2></div><img :src="gzuOfficialLogo" alt="广州大学" /></div>
          <div class="m2-campus-card-grid">
            <CampusSceneCard variant="university" index="01" eyebrow="MAIN CAMPUS" name="大学城校区" identity="综合校园 · 青春共同体" description="以正门、图书馆、何世杰体育馆、校史馆和红色长廊为节点，连接学习、体育、商都记忆与红色文化。" :tags="['红棉寻迹','校园地标','学生共创']" />
            <CampusSceneCard variant="guihuagang" index="02" eyebrow="URBAN MEMORY" name="桂花岗校区" identity="城市文脉 · 校园记忆" description="身处广州中心城区，让校园历史与城市街区相互映照，延展校史、建筑和社区文化主题。" :tags="['校史记忆','老城文脉','社区连接']" />
            <CampusSceneCard variant="huangpu" index="03" eyebrow="FUTURE INNOVATION" name="黄埔校区" identity="科创引擎 · 研究生教育" description="连接黄埔研究院、研究生院与区域创新实践，为 AI、科技传播和产学研共创提供未来场景。" :tags="['黄埔研究院','科技创新','产学研共创']" />
          </div>
        </section>

        <section class="m2-section">
          <div class="m2-section-head"><div><p class="m2-kicker">CULTURE IN ACTION</p><h2>不止观看，更要理解、参与和传播</h2></div></div>
          <div class="m2-values">
            <article><span>01</span><b>文化探索</b><p>以权威来源梳理木棉、粤剧、广彩等岭南文化，并连接广州大学校园记忆。</p></article>
            <article><span>02</span><b>校园寻迹</b><p>把图书馆、德信亭与校园空间变成可行走、可完成的文化课堂。</p></article>
            <article><span>03</span><b>AI 共创</b><p>选择岭南元素和广大地标，生成海报，让传统文化获得青年表达。</p></article>
          </div>
        </section>

        <section class="m2-section">
          <div class="m2-section-head"><div><p class="m2-kicker">LIVE PLATFORM DATA</p><h2>一条真实数据驱动的文化传播链路</h2></div><span v-if="platformError" class="m2-partial-error">{{ platformError }}</span></div>
          <div class="m2-live-metrics">
            <article><strong>{{ cultures.length }}</strong><span>文化条目</span><small>GET /cultures</small></article>
            <article><strong>{{ routes.length }}</strong><span>校园路线</span><small>GET /routes</small></article>
            <article><strong>{{ routes[0]?.tasks?.length || 0 }}</strong><span>寻迹任务</span><small>GET /routes/{id}</small></article>
            <article><strong>{{ templates.length }}</strong><span>AI 模板</span><small>GET /creations/templates</small></article>
            <article><strong>{{ posts.length }}</strong><span>社区作品</span><small>GET /community/posts</small></article>
            <article><strong>{{ badges.length }}</strong><span>文化徽章</span><small>GET /badges</small></article>
          </div>
        </section>

        <section v-if="routes[0]" class="m2-section m2-route-live">
          <div class="m2-route-copy"><p class="m2-kicker">CAMPUS TRAIL · REAL API</p><h2>{{ routes[0].title }}</h2><p>{{ routes[0].summary }}</p><div><span>{{ routes[0].distance_km }} KM</span><span>{{ routes[0].duration_minutes }} 分钟</span><span>{{ routes[0].tasks?.length || 0 }} 个任务点</span></div></div>
          <ol><li v-for="task in routes[0].tasks" :key="task.id"><b>{{ String(task.order_no).padStart(2,'0') }}</b><span><strong>{{ task.title }}</strong><small>{{ task.description }} · +{{ task.points }} 积分</small></span><em>{{ task.task_type }}</em></li></ol>
        </section>

        <section class="m2-section m2-creation-entry">
          <div><p class="m2-kicker">STEP 05 · AI CO-CREATION</p><h2>完成寻迹，再把文化变成你的作品</h2><p>选择文化元素、校园地标与视觉风格，提交一张属于你的文化海报。首页不提前展示结果，创作由你亲手开始。</p><button class="m2-primary" type="button" @click="navigate('create')">进入 AI 共创工作台</button></div>
          <ol aria-label="文化传播主流程"><li><span>01</span><b>探索</b><small>选择红棉主题</small></li><li><span>02</span><b>导览</b><small>听小棉讲文化</small></li><li><span>03</span><b>寻迹</b><small>完成校园任务</small></li><li><span>04</span><b>解锁</b><small>获得积分模板</small></li><li class="active"><span>05</span><b>共创</b><small>组合并生成海报</small></li><li><span>06</span><b>传播</b><small>发布社区获徽章</small></li></ol>
        </section>

        <section class="m2-section">
          <div class="m2-section-head"><div><p class="m2-kicker">COMMUNITY & ACHIEVEMENT</p><h2>从校园体验到社区传播</h2></div></div>
          <div class="m2-community-live">
            <article v-if="posts[0]" class="m2-live-post"><div><MediaImage :src="posts[0].cover_image_url || visuals.kapok" :alt="posts[0].title" /></div><section><span>社区真实数据</span><h3>{{ posts[0].title }}</h3><p>{{ posts[0].content }}</p><small>赞 {{ posts[0].like_count }} · 评论 {{ posts[0].comment_count }} · 收藏 {{ posts[0].favorite_count }}</small></section></article>
            <div class="m2-badges"><article v-for="badge in badges" :key="badge.id"><span>徽</span><div><b>{{ badge.name }}</b><p>{{ badge.description }}</p><small>{{ badge.rule_type }} · {{ badge.rule_value }}</small></div></article></div>
          </div>
        </section>

        <section class="m2-section m2-campus-band">
          <div class="m2-campus-photo"><MediaImage :src="visuals.pavilion" alt="广州大学大学城校区校园实景" /></div>
          <div class="m2-campus-copy"><p class="m2-kicker">THREE CAMPUSES · ONE GZHU</p><h2>大学城、桂花岗、黄埔</h2><p>三个校区拥有不同的空间记忆与学科气质，共同组成广州大学的校园文化地图。当前红棉寻迹以大学城校区为示范，后续可把桂花岗的城市文脉与黄埔的创新实践接入同一平台。</p><div class="m2-campus-pills"><span>大学城校区</span><span>桂花岗校区</span><span>黄埔校区</span></div><button class="m2-link" @click="navigate('cultures')">查看三校区文化条目 →</button></div>
        </section>

        <section class="m2-section">
          <div class="m2-section-head"><div><p class="m2-kicker">FEATURED STORIES</p><h2>从这些岭南故事开始</h2></div><button class="m2-link" @click="navigate('cultures')">查看全部 →</button></div>
          <PageState :loading="loading" :error="error" :empty="!loading && !error && cultures.length === 0" @retry="loadCultures" />
          <div v-if="!loading && cultures.length" class="m2-card-grid">
            <button v-for="(item,index) in cultures.slice(0,3)" :key="item.id" class="m2-card" @click="openCulture(item)"><div class="m2-card-photo"><MediaImage :src="item.cover_image_url || cultureVisual(item.category,index)" :alt="item.title" /></div><div class="m2-card-body"><span>{{ item.category }}</span><h3>{{ item.title }}</h3><p>{{ item.summary }}</p><small>来源：{{ item.source_title }}</small></div></button>
          </div>
        </section>
      </template>

      <template v-else-if="view === 'cultures'">
        <section class="m2-page-head"><p class="m2-kicker">LINGNAN ARCHIVE</p><h1>文化探索</h1><p>从岭南非遗、广州城市文化到广州大学校园记忆，找到传统与当代生活的连接。</p></section>
        <div class="m2-tools"><label><span>搜索文化内容</span><input v-model="keyword" type="search" placeholder="搜索木棉、粤剧、校园……" /></label><div class="m2-filters"><button v-for="item in categories" :key="item" :class="{ active: category === item }" @click="category = item">{{ item }}</button></div></div>
        <PageState :loading="loading" :error="error" :empty="!loading && !error && filtered.length === 0" empty-text="没有匹配的文化条目" @retry="loadCultures" />
        <div v-if="!loading && filtered.length" class="m2-card-grid">
          <button v-for="(item,index) in filtered" :key="item.id" class="m2-card" @click="openCulture(item)"><div class="m2-card-photo"><MediaImage :src="item.cover_image_url || cultureVisual(item.category,index)" :alt="item.title" /></div><div class="m2-card-body"><span>{{ item.category }}</span><h3>{{ item.title }}</h3><p>{{ item.summary }}</p><small>权威来源：{{ item.source_title }}</small></div></button>
        </div>
      </template>

      <template v-else-if="view === 'detail' && selected">
        <button class="m2-back" @click="navigate('cultures')">← 返回文化探索</button>
        <section class="m2-detail"><div class="m2-detail-photo"><MediaImage :src="selected.cover_image_url || cultureVisual(selected.category)" :alt="selected.title" /></div><div class="m2-detail-copy"><span>{{ selected.category }}</span><h1>{{ selected.title }}</h1><p>{{ selected.summary }}</p><button class="m2-primary" @click="navigate('guide')">问问数字人小棉</button></div></section>
        <article class="m2-prose"><p v-for="paragraph in selected.content.split('\n').filter(Boolean)" :key="paragraph">{{ paragraph }}</p><div class="m2-source"><b>内容来源</b><a v-if="selected.source_url" :href="selected.source_url" target="_blank" rel="noreferrer">{{ selected.source_title }} ↗</a><span v-else>{{ selected.source_title }}</span></div></article>
      </template>

      <template v-else-if="view === 'guide'">
        <section class="m2-page-head"><p class="m2-kicker">AI CULTURE GUIDE</p><h1>你好，我是小棉</h1><p>以木棉为文化名片，陪你连接广州城市记忆与广州大学校园生活。</p></section>
        <section class="m2-guide"><aside><XiaomianMascot /><h2>数字人 · 小棉</h2><p>岭南文化校园导览员</p><small>问答服务契约待成员 3 接入</small></aside><div class="m2-chat"><div class="m2-messages"><p v-for="(message,index) in messages" :key="index" :class="message.from">{{ message.text }}</p></div><div class="m2-prompts"><button @click="ask('木棉为什么是广州的市花？')">木棉与广州</button><button @click="ask('岭南文化在广大校园里有哪些线索？')">广大校园线索</button><button @click="ask('如何参加红棉寻迹？')">红棉寻迹</button></div><form @submit.prevent="ask()"><input v-model="question" aria-label="向小棉提问" placeholder="输入你想了解的岭南文化问题" /><button type="submit">发送</button></form></div></section>
      </template>

      <template v-else-if="view === 'create'">
        <section class="m2-page-head m2-create-head"><p class="m2-kicker">AI CULTURE CREATION</p><h1>文化海报共创工作台</h1><p>按照主流程完成元素组合并生成海报。本地交互版式用于前端演示；登录后会把同一组参数提交到后端真实创作任务队列。</p></section>
        <PosterStudio :template="templates[0]" :cultures="cultures" @login="navigate('profile')" />
      </template>

      <template v-else-if="view === 'profile'">
        <section class="m2-page-head"><p class="m2-kicker">MY LINGCHAO</p><h1>我的岭潮</h1><p>你的每一次探索、创作与传播，都会成为个人文化足迹的一部分。</p></section>
        <div v-if="!currentUser" class="m2-profile-welcome"><div class="m2-profile-mascot"><XiaomianMascot /></div><form class="m2-login-live" @submit.prevent="login"><div><p class="m2-kicker">JWT AUTH · REAL API</p><h2>领取你的岭潮文化身份</h2><p>登录后，小棉会同步你的校园路线、AI 共创、积分流水与文化徽章。</p></div><label>用户名<input v-model="authForm.username" autocomplete="username" required /></label><label>密码<input v-model="authForm.password" type="password" autocomplete="current-password" required /></label><p v-if="authError" class="m2-auth-error">{{ authError }}</p><button class="m2-primary" type="submit" :disabled="authLoading">{{ authLoading ? '正在登录…' : '进入我的岭潮' }}</button></form></div>
        <template v-else>
          <section class="m2-profile"><div class="m2-profile-identity"><span class="m2-user-avatar">{{ currentUser.nickname.slice(0,1) }}</span><div><small>岭潮文化身份 · 已连接后端</small><h2>{{ currentUser.nickname }}</h2><p>@{{ currentUser.username }} · 广州大学校园文化探索者</p></div></div><div class="m2-points-orbit"><strong>{{ currentUser.points_total }}</strong><small>文化积分</small></div><button type="button" class="m2-profile-logout" @click="logout">退出登录</button></section>
          <div class="m2-profile-grid"><article><b>积分足迹</b><p>任务完成产生的积分流水会实时记录并保持幂等。</p><span>{{ mine.records }} 条积分记录</span></article><article><b>我的共创</b><p>模板提交后作品会进入 PENDING、PROCESSING、SUCCESS 或 FAILED 状态。</p><span>{{ mine.creations }} 个创作任务</span></article><article><b>文化徽章</b><p>红棉初见、文化行者、岭潮共创者等待解锁。</p><span>{{ mine.badges }} / {{ badges.length }}</span></article></div>
        </template>
      </template>
    </main>
    <footer><b>岭潮共创</b><span>岭南文化与校园文化传承 AI 传播平台 · 广州大学</span><small>视觉图片来源与许可见 src/assets/culture/ATTRIBUTION.md</small></footer>
  </div>
</template>
