<script setup lang="ts">
import type { CulturalToken } from '@/views/route/culturalTokens'

defineProps<{
  token: CulturalToken
  points: number
  score?: string
}>()

const emit = defineEmits<{ close: [] }>()
</script>

<template>
  <div class="token-backdrop" role="presentation" @click.self="emit('close')">
    <section class="token-reveal" :class="`tone-${token.tone}`" role="dialog" aria-modal="true" :aria-label="token.name">
      <p class="token-kicker">CULTURE TOKEN · {{ token.code }}</p>
      <div class="token-medallion">
        <i /><i /><i />
        <strong>{{ token.glyph }}</strong>
        <small>{{ token.figure }}</small>
      </div>
      <div class="token-copy">
        <small>岭潮文化令牌已点亮</small>
        <h2>{{ token.name }}</h2>
        <b>{{ token.theme }}</b>
        <p>{{ token.message }}</p>
        <blockquote>{{ token.knowledge }}</blockquote>
        <div class="token-result">
          <span>本次积分 <strong>+{{ points }}</strong></span>
          <span v-if="score">知识闯关 <strong>{{ score }}</strong></span>
        </div>
        <button type="button" @click="emit('close')">收下令牌，继续寻迹</button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.token-backdrop{position:fixed;z-index:90;inset:0;display:grid;place-items:center;padding:20px;background:rgba(18,29,24,.72);backdrop-filter:blur(8px)}
.token-reveal{--token:#a52d35;--token-dark:#671921;--token-light:#f1ca7e;position:relative;display:grid;grid-template-columns:230px minmax(0,1fr);gap:34px;width:min(760px,100%);overflow:hidden;padding:38px;color:#fff;background:radial-gradient(circle at 20% 35%,color-mix(in srgb,var(--token) 82%,#fff),var(--token-dark) 58%);border:2px solid var(--token-light);border-radius:24px;box-shadow:0 32px 100px rgba(0,0,0,.42)}
.token-reveal:before,.token-reveal:after{content:"";position:absolute;width:240px;height:240px;border:1px solid rgba(255,255,255,.15);border-radius:50%}.token-reveal:before{left:-100px;top:-110px}.token-reveal:after{right:-90px;bottom:-140px}
.tone-jade{--token:#2f7159;--token-dark:#173e31;--token-light:#d9c17a}.tone-gold{--token:#b97725;--token-dark:#6d3518;--token-light:#ffe09a}.tone-ocean{--token:#2c6e82;--token-dark:#173d4d;--token-light:#d6c184}.tone-flame{--token:#b43a2c;--token-dark:#641c22;--token-light:#f3cb76}
.token-kicker{position:absolute;z-index:2;top:18px;left:30px;margin:0;color:var(--token-light);font-size:9px;font-weight:900;letter-spacing:.16em}
.token-medallion{position:relative;z-index:2;align-self:center;display:grid;place-items:center;width:210px;height:260px;padding:30px 20px;color:#6b3d11;background:linear-gradient(145deg,#ffe5a8,#d5a64e);border:8px double rgba(255,255,255,.75);border-radius:48% 48% 42% 42%;box-shadow:inset 0 0 0 5px rgba(110,60,10,.12),0 20px 40px rgba(40,18,5,.3)}
.token-medallion:before{content:"";position:absolute;inset:17px;border:1px solid rgba(104,54,10,.35);border-radius:inherit}.token-medallion>strong{font-family:serif;font-size:82px;line-height:1}.token-medallion>small{font-weight:900;letter-spacing:.16em}.token-medallion i{position:absolute;top:24px;width:7px;height:7px;background:#a97120;border-radius:50%}.token-medallion i:nth-child(1){left:55px}.token-medallion i:nth-child(2){left:98px}.token-medallion i:nth-child(3){right:55px}
.token-copy{position:relative;z-index:2;align-self:center}.token-copy>small{color:var(--token-light);font-weight:800}.token-copy h2{margin:5px 0 3px;font-family:serif;font-size:38px}.token-copy>b{font-size:12px;letter-spacing:.14em}.token-copy>p{margin:18px 0 12px;color:rgba(255,255,255,.9);line-height:1.8}.token-copy blockquote{margin:0;padding:13px 15px;color:#3c2a14;background:rgba(255,244,210,.9);border-left:3px solid var(--token-light);border-radius:0 8px 8px 0;font-size:12px;line-height:1.65}
.token-result{display:flex;gap:12px;margin:16px 0}.token-result span{padding:8px 11px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);border-radius:999px;font-size:11px}.token-result strong{color:var(--token-light)}.token-copy button{min-height:44px;padding:0 17px;color:var(--token-dark);background:var(--token-light);border:0;border-radius:8px;font-weight:900;cursor:pointer}
@media(max-width:700px){.token-reveal{grid-template-columns:1fr;gap:18px;max-height:92vh;overflow:auto;padding:48px 24px 28px}.token-medallion{width:160px;height:190px;justify-self:center}.token-medallion>strong{font-size:60px}.token-copy h2{font-size:31px}}
</style>
