<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api } from '@/services/api'
import type {
  PageData,
  PointRecord,
  ShopCategory,
  ShopProduct,
  ShopRedemption,
  ShopRedeemResult,
} from '@/types'

const props = defineProps<{
  pointsTotal: number
  loggedIn: boolean
  pointRecords: PointRecord[]
}>()
const emit = defineEmits<{
  login: []
  redeemed: [result: ShopRedeemResult]
}>()

const categories = ref<ShopCategory[]>([])
const products = ref<ShopProduct[]>([])
const activeCategory = ref('ALL')
const selectedProduct = ref<ShopProduct>()
const selectedRedemption = ref<ShopRedemption>()
const loading = ref(true)
const redeeming = ref(false)
const error = ref('')
const redemptionError = ref('')
const activeView = ref<'SHOP' | 'REDEMPTIONS'>('SHOP')
const redemptionItems = ref<ShopRedemption[]>([])
const redemptionLoading = ref(false)
const redemptionListError = ref('')
const redemptionFilter = ref('ALL')
const copiedVoucher = ref('')

const redemptionFilters = [
  { code: 'ALL', name: '全部' },
  { code: 'DIGITAL', name: '数字权益' },
  { code: 'PICKUP', name: '实体领取' },
  { code: 'EXPERIENCE', name: '体验预约' },
]

const visibleProducts = computed(() =>
  activeCategory.value === 'ALL'
    ? products.value
    : products.value.filter(item => item.category === activeCategory.value),
)
const visibleRedemptions = computed(() =>
  redemptionFilter.value === 'ALL'
    ? redemptionItems.value
    : redemptionItems.value.filter(item => item.fulfillment === redemptionFilter.value),
)

async function loadShop() {
  loading.value = true
  error.value = ''
  try {
    const response = await api.get<{
      data: { categories: ShopCategory[]; products: ShopProduct[] }
    }>('/points/shop')
    categories.value = response.data.data.categories
    products.value = response.data.data.products
  } catch (event) {
    error.value = (event as Error).message
  } finally {
    loading.value = false
  }
}

async function loadRedemptions() {
  if (!props.loggedIn) {
    redemptionItems.value = []
    return
  }
  redemptionLoading.value = true
  redemptionListError.value = ''
  try {
    const response = await api.get<{ data: PageData<ShopRedemption> }>('/points/redemptions', {
      params: { pageSize: 100 },
    })
    redemptionItems.value = response.data.data.items
  } catch (event) {
    redemptionListError.value = (event as Error).message
  } finally {
    redemptionLoading.value = false
  }
}

function isRedeemed(product: ShopProduct) {
  return product.limit === 'ONCE' && (
    redemptionItems.value.some(item => item.productCode === product.code)
    || props.pointRecords.some(record => record.business_key?.startsWith(`redeem:${product.code}:`))
  )
}

function buttonText(product: ShopProduct) {
  if (!props.loggedIn) return '登录后兑换'
  if (isRedeemed(product)) return '已兑换'
  if (props.pointsTotal < product.points) return '积分不足'
  return '立即兑换'
}

function openRedemption(product: ShopProduct) {
  if (!props.loggedIn) {
    emit('login')
    return
  }
  if (isRedeemed(product) || props.pointsTotal < product.points) return
  selectedProduct.value = product
  redemptionError.value = ''
}

async function confirmRedemption() {
  if (!selectedProduct.value || redeeming.value) return
  redeeming.value = true
  redemptionError.value = ''
  try {
    const redemptionId = globalThis.crypto?.randomUUID?.()
      || `${Date.now()}-${Math.random().toString(16).slice(2)}`
    const response = await api.post<{ data: ShopRedeemResult }>('/points/redeem', {
      product_code: selectedProduct.value.code,
      redemption_id: redemptionId,
    })
    emit('redeemed', response.data.data)
    selectedProduct.value = undefined
    await loadRedemptions()
    activeView.value = 'REDEMPTIONS'
  } catch (event) {
    redemptionError.value = (event as Error).message
  } finally {
    redeeming.value = false
  }
}

function formatRedemptionTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

async function copyVoucher(item: ShopRedemption) {
  try {
    await navigator.clipboard.writeText(item.voucherCode)
    copiedVoucher.value = item.voucherCode
    window.setTimeout(() => {
      if (copiedVoucher.value === item.voucherCode) copiedVoucher.value = ''
    }, 1800)
  } catch {
    copiedVoucher.value = ''
  }
}

watch(() => props.loggedIn, loggedIn => {
  if (loggedIn) loadRedemptions()
  else redemptionItems.value = []
})
onMounted(() => {
  loadShop()
  loadRedemptions()
})
</script>

<template>
  <section class="points-mall" aria-label="积分商店">
    <header class="mall-hero">
      <div class="mall-heading">
        <p>LINGCHAO POINTS MARKET</p>
        <h2>积分商店</h2>
        <span>完成校园任务、参与文化共创可获得积分。数字内容、校园文创、共创权益与文化体验均可使用积分兑换。</span>
        <div class="mall-view-switch" aria-label="积分商城视图">
          <button type="button" :class="{ active: activeView === 'SHOP' }" @click="activeView = 'SHOP'">兑换商城</button>
          <button type="button" :class="{ active: activeView === 'REDEMPTIONS' }" @click="activeView = 'REDEMPTIONS'">
            我的兑换 <b>{{ redemptionItems.length }}</b>
          </button>
        </div>
      </div>
      <div class="points-wallet">
        <small>{{ loggedIn ? '当前积分' : '登录后查看积分' }}</small>
        <strong>{{ loggedIn ? pointsTotal : '—' }}</strong>
        <span>{{ loggedIn ? '完成任务继续累积' : '登录后即可兑换奖励' }}</span>
      </div>
      <div class="mall-orbit" aria-hidden="true"><i /><i /><i /><b>兑</b></div>
    </header>

    <div v-if="activeView === 'SHOP'" class="mall-toolbar">
      <div class="mall-filters" aria-label="商品分类">
        <button
          v-for="category in categories"
          :key="category.code"
          type="button"
          :class="{ active: activeCategory === category.code }"
          @click="activeCategory = category.code"
        >
          {{ category.name }}
        </button>
      </div>
      <span>{{ visibleProducts.length }} 件可选好物</span>
    </div>

    <div v-if="activeView === 'SHOP' && loading" class="mall-state">正在准备积分好物…</div>
    <div v-else-if="activeView === 'SHOP' && error" class="mall-state error"><b>商城暂时无法加载</b><span>{{ error }}</span><button type="button" @click="loadShop">重新加载</button></div>
    <div v-else-if="activeView === 'SHOP'" class="product-grid">
      <article
        v-for="(product, index) in visibleProducts"
        :key="product.code"
        class="product-card"
        :class="{ featured: activeCategory === 'ALL' && index === 0, redeemed: isRedeemed(product) }"
        :style="{ '--accent': product.accent }"
      >
        <div class="product-art">
          <span>{{ product.symbol }}</span>
          <i /><i /><i />
          <small>{{ product.badge }}</small>
        </div>
        <div class="product-copy">
          <header><span>{{ product.categoryLabel }}</span><em>{{ product.delivery }}</em></header>
          <h3>{{ product.name }}</h3>
          <b>{{ product.subtitle }}</b>
          <p>{{ product.description }}</p>
          <footer>
            <div><strong>{{ product.points }}</strong><small>文化积分</small></div>
            <button
              type="button"
              :disabled="loggedIn && (isRedeemed(product) || pointsTotal < product.points)"
              @click="openRedemption(product)"
            >
              {{ buttonText(product) }}
            </button>
          </footer>
        </div>
      </article>
    </div>

    <section v-else class="redemption-shelf" aria-label="我的兑换记录">
      <header>
        <div>
          <p>MY REWARDS</p>
          <h3>我的兑换</h3>
          <span>数字权益随时查看，实体商品和活动体验凭兑换码核验。</span>
        </div>
        <div class="redemption-filters" aria-label="兑换记录分类">
          <button
            v-for="filter in redemptionFilters"
            :key="filter.code"
            type="button"
            :class="{ active: redemptionFilter === filter.code }"
            @click="redemptionFilter = filter.code"
          >
            {{ filter.name }}
          </button>
        </div>
      </header>

      <div v-if="!loggedIn" class="redemption-empty">
        <span>兑</span>
        <div><b>登录后查看我的兑换</b><p>兑换记录、数字权益和领取凭证都会保存在账号中。</p></div>
        <button type="button" @click="emit('login')">去登录</button>
      </div>
      <div v-else-if="redemptionLoading" class="redemption-empty"><span>载</span><div><b>正在加载兑换记录</b><p>正在整理你的文化权益与领取凭证。</p></div></div>
      <div v-else-if="redemptionListError" class="redemption-empty error">
        <span>!</span>
        <div><b>兑换记录加载失败</b><p>{{ redemptionListError }}</p></div>
        <button type="button" @click="loadRedemptions">重新加载</button>
      </div>
      <div v-else-if="!visibleRedemptions.length" class="redemption-empty">
        <span>空</span>
        <div><b>{{ redemptionItems.length ? '这个分类暂无记录' : '还没有兑换好物' }}</b><p>完成校园任务积累积分，再从商城选择喜欢的文化礼物。</p></div>
        <button type="button" @click="activeView = 'SHOP'">去逛商城</button>
      </div>
      <div v-else class="redemption-grid">
        <article
          v-for="item in visibleRedemptions"
          :key="item.recordId"
          :style="{ '--accent': item.accent }"
        >
          <div class="redemption-symbol">{{ item.symbol }}</div>
          <div class="redemption-copy">
            <header><span>{{ item.categoryLabel }}</span><em :class="item.fulfillment.toLowerCase()">{{ item.statusLabel }}</em></header>
            <h4>{{ item.productName }}</h4>
            <p>{{ item.subtitle }}</p>
            <dl>
              <div><dt>兑换码</dt><dd>{{ item.voucherCode }}</dd></div>
              <div><dt>消耗积分</dt><dd>{{ item.cost }}</dd></div>
            </dl>
            <footer>
              <small>{{ formatRedemptionTime(item.redeemedAt) }}</small>
              <button type="button" @click="selectedRedemption = item">{{ item.actionLabel }}</button>
            </footer>
          </div>
        </article>
      </div>
    </section>

    <div v-if="selectedProduct" class="mall-modal" role="dialog" aria-modal="true" aria-label="确认积分兑换" @click.self="selectedProduct = undefined">
      <article :style="{ '--accent': selectedProduct.accent }">
        <button class="modal-close" type="button" aria-label="关闭兑换确认" @click="selectedProduct = undefined">×</button>
        <div class="modal-symbol">{{ selectedProduct.symbol }}</div>
        <p>CONFIRM REDEMPTION</p>
        <h3>确认兑换{{ selectedProduct.name }}？</h3>
        <span>{{ selectedProduct.description }}</span>
        <dl>
          <div><dt>所需积分</dt><dd>{{ selectedProduct.points }}</dd></div>
          <div><dt>兑换后余额</dt><dd>{{ pointsTotal - selectedProduct.points }}</dd></div>
          <div><dt>领取方式</dt><dd>{{ selectedProduct.delivery }}</dd></div>
        </dl>
        <p v-if="redemptionError" class="redeem-error">{{ redemptionError }}</p>
        <button class="confirm-redeem" type="button" :disabled="redeeming" @click="confirmRedemption">
          {{ redeeming ? '正在兑换…' : '确认兑换' }}
        </button>
        <small>兑换后积分将立即扣除，实体商品请凭兑换记录到活动服务台领取。</small>
      </article>
    </div>

    <div v-if="selectedRedemption" class="mall-modal voucher-modal" role="dialog" aria-modal="true" aria-label="我的兑换凭证" @click.self="selectedRedemption = undefined">
      <article :style="{ '--accent': selectedRedemption.accent }">
        <button class="modal-close" type="button" aria-label="关闭兑换凭证" @click="selectedRedemption = undefined">×</button>
        <div class="modal-symbol">{{ selectedRedemption.symbol }}</div>
        <p>LINGCHAO REWARD PASS</p>
        <h3>{{ selectedRedemption.productName }}</h3>
        <span>{{ selectedRedemption.instruction }}</span>
        <div class="voucher-code">
          <small>兑换凭证</small>
          <strong>{{ selectedRedemption.voucherCode }}</strong>
          <button type="button" @click="copyVoucher(selectedRedemption)">
            {{ copiedVoucher === selectedRedemption.voucherCode ? '已复制' : '复制兑换码' }}
          </button>
        </div>
        <dl>
          <div><dt>当前状态</dt><dd>{{ selectedRedemption.statusLabel }}</dd></div>
          <div><dt>领取方式</dt><dd>{{ selectedRedemption.delivery }}</dd></div>
          <div><dt>兑换时间</dt><dd>{{ formatRedemptionTime(selectedRedemption.redeemedAt) }}</dd></div>
        </dl>
        <button class="confirm-redeem" type="button" @click="selectedRedemption = undefined">我知道了</button>
        <small>兑换记录长期保存在当前账号中，请勿向他人泄露兑换码。</small>
      </article>
    </div>
  </section>
</template>

<style scoped>
.points-mall{margin-top:42px;overflow:hidden;border:1px solid #dfe3dd;border-radius:16px;background:#fff}.mall-hero{position:relative;display:grid;grid-template-columns:minmax(0,1fr) 185px;align-items:center;gap:30px;min-height:235px;overflow:hidden;padding:34px 40px;color:#fff;background:linear-gradient(125deg,#173d31 0%,#285a47 64%,#336b54 100%)}.mall-heading{position:relative;z-index:2}.mall-heading>p{margin:0;color:#e8c273;font-size:10px;font-weight:900;letter-spacing:.18em}.mall-heading h2{max-width:690px;margin:9px 0;font-size:clamp(27px,4vw,42px);line-height:1.2}.mall-heading span{color:#c8d9d1;line-height:1.7}.points-wallet{position:relative;z-index:2;display:grid;justify-items:center;padding:22px;color:#714818;background:#f1cc7c;border:5px double rgba(255,255,255,.72);border-radius:50% 50% 46% 54%;box-shadow:0 18px 40px rgba(9,31,24,.25)}.points-wallet small{font-size:10px}.points-wallet strong{font-size:52px;line-height:1.1}.points-wallet span{font-size:9px}.mall-orbit{position:absolute;right:210px;width:230px;height:230px;border:1px solid rgba(255,255,255,.1);border-radius:50%}.mall-orbit:before,.mall-orbit:after{content:"";position:absolute;inset:28px;border:1px solid rgba(255,255,255,.1);border-radius:50%}.mall-orbit:after{inset:67px}.mall-orbit i{position:absolute;width:12px;height:12px;background:#e9c576;border-radius:50%}.mall-orbit i:first-child{left:20px;top:105px}.mall-orbit i:nth-child(2){right:43px;top:31px}.mall-orbit i:nth-child(3){right:22px;bottom:62px}.mall-orbit b{position:absolute;left:98px;top:96px;color:rgba(255,255,255,.18);font-family:serif;font-size:28px}.mall-toolbar{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:18px 24px;border-bottom:1px solid #e5e9e5}.mall-toolbar>span{flex-shrink:0;color:#78827d;font-size:10px}.mall-filters{display:flex;flex-wrap:wrap;gap:7px}.mall-filters button{min-height:34px;padding:0 12px;border:1px solid #dce2dd;border-radius:999px;color:#64716a;background:#fff;font-size:10px}.mall-filters button.active{color:#fff;background:#9f2d35;border-color:#9f2d35}.product-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;padding:24px;background:#f3f5f1}.product-card{display:grid;grid-template-columns:128px 1fr;min-height:230px;overflow:hidden;background:#fff;border:1px solid #dfe4df;border-radius:12px;box-shadow:0 10px 24px rgba(35,57,48,.06)}.product-card.featured{grid-column:span 2}.product-art{position:relative;display:grid;place-items:center;overflow:hidden;color:#fff;background:linear-gradient(145deg,var(--accent),color-mix(in srgb,var(--accent) 68%,#162c24));isolation:isolate}.product-art>span{position:relative;z-index:2;display:grid;place-items:center;width:70px;height:70px;border:1px solid rgba(255,255,255,.65);border-radius:50%;font-family:serif;font-size:32px;box-shadow:inset 0 0 0 7px rgba(255,255,255,.1)}.product-art>i{position:absolute;width:90px;height:18px;border:1px solid rgba(255,255,255,.18);transform:rotate(-35deg)}.product-art>i:nth-of-type(2){width:150px;transform:rotate(37deg)}.product-art>i:nth-of-type(3){width:65px;height:65px;border-radius:50%;transform:none}.product-art>small{position:absolute;z-index:2;top:10px;left:10px;padding:4px 7px;color:#29352f;background:#f2d38f;border-radius:999px;font-size:8px;font-weight:900}.product-copy{display:flex;min-width:0;flex-direction:column;padding:17px}.product-copy>header{display:flex;justify-content:space-between;gap:8px;color:var(--accent);font-size:8px;font-weight:900}.product-copy header em{color:#7b8580;font-style:normal;font-weight:500}.product-copy h3{margin:8px 0 2px;font-size:17px}.product-copy>b{color:#68746d;font-size:10px}.product-copy>p{margin:8px 0;color:#717c76;font-size:10px;line-height:1.6}.product-copy footer{display:flex;align-items:flex-end;justify-content:space-between;gap:8px;margin-top:auto;padding:0;color:inherit;background:none}.product-copy footer>div{display:grid}.product-copy footer strong{color:var(--accent);font-size:25px;line-height:1}.product-copy footer small{color:#7b8580;font-size:8px}.product-copy footer button{min-height:35px;padding:0 10px;border:0;border-radius:6px;color:#fff;background:var(--accent);font-size:9px;font-weight:800}.product-copy footer button:disabled{color:#7b8580;background:#e7ebe8;cursor:not-allowed}.product-card.redeemed{opacity:.72}.mall-state{display:grid;gap:8px;place-items:center;min-height:280px;padding:30px}.mall-state.error{color:#9f2d35}.mall-state button{min-height:38px;padding:0 12px;border:0;border-radius:6px;color:#fff;background:#9f2d35}.mall-modal{position:fixed;z-index:80;inset:0;display:grid;place-items:center;padding:16px;background:rgba(17,34,28,.68);backdrop-filter:blur(6px)}.mall-modal>article{position:relative;width:min(450px,100%);padding:30px;background:#fff;border-top:7px solid var(--accent);border-radius:14px;box-shadow:0 30px 90px rgba(9,25,19,.35);text-align:center}.modal-close{position:absolute;right:14px;top:10px;border:0;color:#7c8580;background:none;font-size:27px}.modal-symbol{display:grid;place-items:center;width:72px;height:72px;margin:auto;color:#fff;background:var(--accent);border-radius:50%;font-family:serif;font-size:31px;box-shadow:0 0 0 8px color-mix(in srgb,var(--accent) 15%,white)}.mall-modal article>p:not(.redeem-error){margin:20px 0 5px;color:var(--accent);font-size:9px;font-weight:900;letter-spacing:.15em}.mall-modal h3{margin:0;font-size:23px}.mall-modal article>span{display:block;margin-top:8px;color:#69756f;font-size:11px;line-height:1.65}.mall-modal dl{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;margin:20px 0;background:#dfe4df}.mall-modal dl div{display:grid;padding:12px 6px;background:#f5f7f4}.mall-modal dt{color:#758079;font-size:8px}.mall-modal dd{margin:4px 0 0;color:var(--accent);font-size:16px;font-weight:900}.confirm-redeem{width:100%;min-height:45px;border:0;border-radius:7px;color:#fff;background:var(--accent);font-weight:900}.confirm-redeem:disabled{opacity:.6}.mall-modal article>small{display:block;margin-top:10px;color:#7b8580;font-size:8px}.redeem-error{padding:9px;color:#9f2d35;background:#fff0f0;border-radius:6px;font-size:10px}
@media(max-width:1000px){.product-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.product-card.featured{grid-column:auto}.mall-hero{grid-template-columns:1fr 155px}.mall-orbit{right:170px}.points-wallet strong{font-size:43px}}@media(max-width:700px){.mall-hero{grid-template-columns:1fr;padding:26px}.points-wallet{justify-self:start;width:145px}.mall-orbit{right:-40px;bottom:-70px}.mall-toolbar{align-items:flex-start;flex-direction:column}.product-grid{grid-template-columns:1fr;padding:14px}.product-card{grid-template-columns:108px 1fr}.mall-modal dl{grid-template-columns:1fr}.mall-modal dl div{grid-template-columns:1fr 1fr}}@media(max-width:430px){.product-card{grid-template-columns:1fr}.product-art{min-height:130px}.product-copy h3{font-size:18px}}
.mall-view-switch{display:flex;gap:8px;margin-top:22px}.mall-view-switch button{min-height:38px;padding:0 15px;border:1px solid rgba(255,255,255,.36);border-radius:999px;color:#fff;background:rgba(255,255,255,.08);font-size:10px;font-weight:800}.mall-view-switch button.active{color:#78313a;background:#f2cd7d;border-color:#f2cd7d}.mall-view-switch b{display:inline-grid;place-items:center;min-width:18px;height:18px;margin-left:4px;padding:0 5px;color:inherit;background:rgba(255,255,255,.18);border-radius:999px;font-size:8px}.redemption-shelf{padding:26px;background:#f3f5f1}.redemption-shelf>header{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;margin-bottom:20px}.redemption-shelf>header p{margin:0;color:#9f2d35;font-size:9px;font-weight:900;letter-spacing:.15em}.redemption-shelf>header h3{margin:4px 0;font-size:26px}.redemption-shelf>header span{color:#6d7872;font-size:11px}.redemption-filters{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:7px}.redemption-filters button{min-height:34px;padding:0 12px;border:1px solid #d7ded8;border-radius:999px;color:#68746d;background:#fff;font-size:10px}.redemption-filters button.active{color:#fff;background:#285a47;border-color:#285a47}.redemption-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.redemption-grid>article{display:grid;grid-template-columns:94px 1fr;min-height:210px;overflow:hidden;border:1px solid #dfe4df;border-radius:12px;background:#fff;box-shadow:0 10px 24px rgba(35,57,48,.05)}.redemption-symbol{display:grid;place-items:center;color:#fff;background:linear-gradient(145deg,var(--accent),color-mix(in srgb,var(--accent) 70%,#162c24));font-family:serif;font-size:35px}.redemption-copy{display:flex;min-width:0;flex-direction:column;padding:17px}.redemption-copy>header{display:flex;align-items:center;justify-content:space-between;gap:8px}.redemption-copy>header>span{color:var(--accent);font-size:9px;font-weight:900}.redemption-copy>header em{padding:4px 7px;color:#285a47;background:#e5f1eb;border-radius:999px;font-size:8px;font-style:normal}.redemption-copy>header em.pickup{color:#8a552f;background:#f5eadc}.redemption-copy>header em.experience{color:#72547c;background:#efe8f3}.redemption-copy h4{margin:10px 0 2px;font-size:18px}.redemption-copy>p{margin:0;color:#707b75;font-size:10px}.redemption-copy dl{display:grid;grid-template-columns:1.4fr .6fr;gap:1px;margin:14px 0;background:#e3e7e3}.redemption-copy dl div{display:grid;padding:9px;background:#f6f8f5}.redemption-copy dt{color:#7b8580;font-size:8px}.redemption-copy dd{overflow:hidden;margin:3px 0 0;color:#2b4037;font-size:11px;font-weight:900;text-overflow:ellipsis;white-space:nowrap}.redemption-copy footer{display:flex;align-items:center;justify-content:space-between;gap:9px;margin-top:auto;padding:0;color:inherit;background:none}.redemption-copy footer small{color:#7c8680;font-size:8px}.redemption-copy footer button,.redemption-empty>button{min-height:34px;padding:0 11px;border:0;border-radius:6px;color:#fff;background:var(--accent,#9f2d35);font-size:9px;font-weight:800}.redemption-empty{display:grid;grid-template-columns:58px 1fr auto;align-items:center;gap:15px;min-height:160px;padding:24px;border:1px dashed #b9c9c0;border-radius:12px;background:#fff}.redemption-empty>span{display:grid;place-items:center;width:54px;height:54px;color:#fff;background:#285a47;border-radius:50%;font-family:serif;font-size:20px}.redemption-empty b{font-size:15px}.redemption-empty p{margin:5px 0 0;color:#6e7973;font-size:10px}.redemption-empty.error>span{background:#9f2d35}.voucher-code{display:grid;gap:5px;margin:19px 0;padding:16px;background:#f2f5f1;border:1px dashed var(--accent);border-radius:10px}.voucher-code small{color:#77817c;font-size:8px}.voucher-code strong{color:var(--accent);font-family:monospace;font-size:25px;letter-spacing:.08em}.voucher-code button{justify-self:center;min-height:30px;padding:0 10px;border:0;border-radius:999px;color:#fff;background:var(--accent);font-size:8px}.voucher-modal dl{margin-top:0}.voucher-modal dl dd{font-size:12px}.voucher-modal dl div:last-child dd{font-size:9px}
@media(max-width:800px){.redemption-shelf>header{align-items:flex-start;flex-direction:column}.redemption-filters{justify-content:flex-start}.redemption-grid{grid-template-columns:1fr}}@media(max-width:560px){.mall-view-switch{flex-wrap:wrap}.redemption-shelf{padding:16px}.redemption-grid>article{grid-template-columns:72px 1fr}.redemption-empty{grid-template-columns:54px 1fr}.redemption-empty>button{grid-column:1/-1}.redemption-copy dl{grid-template-columns:1fr}.voucher-code strong{font-size:20px}}
</style>
