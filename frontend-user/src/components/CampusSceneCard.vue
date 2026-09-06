<script setup lang="ts">
import huangpuCharacter from '@/assets/culture/黄埔-方略略.png'

defineProps<{
  variant: 'university' | 'guihuagang' | 'huangpu'
  index: string
  eyebrow: string
  name: string
  identity: string
  description: string
  tags: string[]
  status?: string
  interactive?: boolean
}>()
defineEmits<{ select: [] }>()
</script>

<template>
  <component
    :is="interactive ? 'button' : 'article'"
    class="campus-scene-card"
    :class="[`is-${variant}`, { 'is-interactive': interactive }]"
    :type="interactive ? 'button' : undefined"
    :aria-disabled="interactive ? undefined : 'true'"
    @click="interactive && $emit('select')"
  >
    <span v-if="status" class="campus-status">{{ status }}</span>
    <div class="campus-scene" aria-hidden="true">
      <div class="scene-sky"><i class="scene-sun" /><i class="scene-cloud one" /><i class="scene-cloud two" /></div>

      <template v-if="variant === 'university'">
        <div class="library-building"><i /><i /><i /><i /><i /><i /></div>
        <div class="library-steps"><i /><i /><i /></div>
        <div class="scene-tree left"><i /><b /></div><div class="scene-tree right"><i /><b /></div>
        <div class="kapok-mark"><i /><i /><i /><i /><i /><b /></div>
      </template>

      <template v-else-if="variant === 'guihuagang'">
        <div class="old-building"><i /><i /><i /><i /></div>
        <div class="old-arch"><i /><i /><i /></div>
        <div class="city-lane" /><div class="city-sign">桂花岗</div>
        <div class="scene-tree left"><i /><b /></div>
      </template>

      <template v-else>
        <div class="innovation-tower one"><i /><i /><i /></div>
        <div class="innovation-tower two"><i /><i /><i /></div>
        <div class="innovation-hall"><i /><i /><i /></div>
        <div class="tech-orbit"><i /><i /><i /><b /></div>
        <img class="huangpu-character" :src="huangpuCharacter" alt="黄埔校区代表形象方略略" />
      </template>

      <span class="scene-floor" />
    </div>
    <div class="campus-scene-copy">
      <small>{{ index }} · {{ eyebrow }}</small>
      <h3>{{ name }}</h3>
      <strong>{{ identity }}</strong>
      <p>{{ description }}</p>
      <div><span v-for="tag in tags" :key="tag">{{ tag }}</span></div>
    </div>
  </component>
</template>

<style scoped>
.campus-scene-card{position:relative;min-width:0;overflow:hidden;border:1px solid #d9ded9;border-radius:8px;background:#fff;box-shadow:0 14px 35px rgba(28,45,37,.09);transition:transform .2s ease,box-shadow .2s ease}.campus-scene-card:hover{transform:translateY(-4px);box-shadow:0 20px 42px rgba(28,45,37,.14)}.campus-scene{position:relative;height:245px;overflow:hidden;isolation:isolate;background:#dfece4}.scene-sky{position:absolute;inset:0;background:linear-gradient(#dcece5 0 64%,#a9c8b5 64%)}.scene-sun{position:absolute;right:34px;top:26px;width:42px;height:42px;border-radius:50%;background:#efc46f;box-shadow:0 0 0 10px rgba(239,196,111,.18)}.scene-cloud{position:absolute;width:80px;height:18px;border-radius:20px;background:rgba(255,255,255,.7)}.scene-cloud:before,.scene-cloud:after{content:"";position:absolute;bottom:0;border-radius:50%;background:inherit}.scene-cloud:before{left:14px;width:30px;height:30px}.scene-cloud:after{right:10px;width:38px;height:38px}.scene-cloud.one{left:30px;top:40px}.scene-cloud.two{right:78px;top:88px;transform:scale(.68)}.scene-floor{position:absolute;z-index:1;left:-10%;right:-10%;bottom:-46px;height:115px;border-radius:50% 50% 0 0;background:#779c84;box-shadow:inset 0 14px 0 rgba(255,255,255,.15)}.campus-scene>strong{position:absolute;z-index:8;right:18px;bottom:13px;color:rgba(255,255,255,.78);font-family:serif;font-size:28px}.campus-scene-copy{padding:22px}.campus-scene-copy small{font-size:9px;font-weight:900}.campus-scene-copy h3{margin:6px 0 2px;font-size:25px}.campus-scene-copy>strong{font-size:13px}.campus-scene-copy p{min-height:66px;margin:12px 0;color:#66716b;font-size:13px;line-height:1.7}.campus-scene-copy>div{display:flex;flex-wrap:wrap;gap:6px}.campus-scene-copy>div span{padding:5px 8px;border-radius:999px;font-size:9px;font-weight:700}.scene-tree{position:absolute;z-index:5;bottom:51px;width:58px;height:95px}.scene-tree.left{left:20px}.scene-tree.right{right:22px;transform:scale(.86)}.scene-tree b{position:absolute;left:26px;bottom:0;width:8px;height:51px;background:#6e5137}.scene-tree i,.scene-tree i:before,.scene-tree i:after{position:absolute;width:46px;height:52px;border-radius:55% 45% 50% 50%;background:#285a47}.scene-tree i:before,.scene-tree i:after{content:"";top:24px;transform:scale(.74)}.scene-tree i:before{left:-17px}.scene-tree i:after{right:-18px}.library-building{position:absolute;z-index:3;left:50%;bottom:58px;width:218px;height:112px;transform:translateX(-50%);background:#f0e3cc;border-top:12px solid #9f2d35;box-shadow:0 15px 25px rgba(45,55,43,.24)}.library-building:before{content:"";position:absolute;left:50%;top:-42px;width:96px;height:42px;transform:translateX(-50%);background:#f3e8d7;clip-path:polygon(50% 0,100% 100%,0 100%)}.library-building:after{content:"图书馆";position:absolute;left:50%;top:14px;transform:translateX(-50%);color:#79252c;font-family:serif;font-size:12px;white-space:nowrap}.library-building i{position:relative;display:inline-block;width:18px;height:50px;margin:43px 7px 0;background:#557568;box-shadow:inset 0 0 0 3px #d8c9ad}.library-steps{position:absolute;z-index:4;left:50%;bottom:48px;width:170px;transform:translateX(-50%)}.library-steps i{display:block;height:7px;margin:auto;background:#d8c8aa;box-shadow:0 2px 2px rgba(42,45,36,.16)}.library-steps i:nth-child(1){width:120px}.library-steps i:nth-child(2){width:145px}.library-steps i:nth-child(3){width:170px}.kapok-mark{position:absolute;z-index:6;right:28px;top:22px;width:48px;height:48px}.kapok-mark i{position:absolute;left:16px;top:3px;width:17px;height:26px;border-radius:70% 30%;background:#d64640;transform-origin:50% 20px}.kapok-mark i:nth-child(2){transform:rotate(72deg)}.kapok-mark i:nth-child(3){transform:rotate(144deg)}.kapok-mark i:nth-child(4){transform:rotate(216deg)}.kapok-mark i:nth-child(5){transform:rotate(288deg)}.kapok-mark b{position:absolute;left:19px;top:17px;width:12px;height:12px;border-radius:50%;background:#e8ad38}.is-university .campus-scene-copy small,.is-university .campus-scene-copy h3{color:#9f2d35}.is-university .campus-scene-copy span{color:#8c2730;background:#f8e7e5}.is-guihuagang .scene-sky{background:linear-gradient(#f4dfb7 0 62%,#c89453 62%)}.is-guihuagang .scene-floor{background:#a56c36}.old-building{position:absolute;z-index:2;left:36px;right:32px;bottom:53px;height:126px;background:#c77e43;border-top:9px solid #8d4d2e;box-shadow:0 15px 25px rgba(71,43,25,.28)}.old-building:before{content:"";position:absolute;left:-14px;right:-14px;top:-22px;height:20px;background:#82452b;clip-path:polygon(4% 100%,9% 0,91% 0,96% 100%)}.old-building i{display:inline-block;width:31px;height:43px;margin:24px 10px 0;border:4px solid #f1d6a8;border-bottom:0;border-radius:20px 20px 0 0;background:#684b3e}.old-arch{position:absolute;z-index:4;left:50%;bottom:51px;width:130px;height:92px;transform:translateX(-50%);background:#ad6537;border:6px solid #e2bb7e;border-bottom:0;border-radius:70px 70px 0 0}.old-arch i{display:inline-block;width:18px;height:57px;margin:26px 8px 0;border-radius:12px 12px 0 0;background:#4f4037}.city-lane{position:absolute;z-index:4;left:50%;bottom:-9px;width:94px;height:91px;transform:translateX(-50%) perspective(90px) rotateX(38deg);background:repeating-linear-gradient(90deg,#d9b579 0 2px,#b98651 2px 20px)}.city-sign{position:absolute;z-index:6;right:20px;top:28px;padding:7px 9px;color:#fff5df;background:#8a4930;font-family:serif;font-size:12px;box-shadow:4px 5px 0 rgba(91,49,31,.22)}.is-guihuagang .scene-tree{transform:scale(.72);transform-origin:bottom}.is-guihuagang .campus-scene-copy small,.is-guihuagang .campus-scene-copy h3{color:#97631e}.is-guihuagang .campus-scene-copy span{color:#7c531d;background:#f8eedb}.is-huangpu .scene-sky{background:linear-gradient(#d9ece8 0 64%,#88b9aa 64%)}.is-huangpu .scene-floor{background:#4e8978}.innovation-tower{position:absolute;z-index:3;bottom:57px;width:72px;background:#e6f1ed;border:5px solid #2f6f5c;box-shadow:10px 14px 22px rgba(24,61,51,.22);transform:skewY(-3deg)}.innovation-tower.one{left:54px;height:135px}.innovation-tower.two{right:56px;height:162px}.innovation-tower i{display:block;height:9px;margin:14px 8px;background:#80b9aa;box-shadow:0 18px 0 #80b9aa,0 36px 0 #80b9aa}.innovation-hall{position:absolute;z-index:4;left:50%;bottom:55px;width:164px;height:78px;transform:translateX(-50%);background:#f2f6f3;border:5px solid #275e4d;box-shadow:0 13px 20px rgba(22,57,47,.2)}.innovation-hall:before{content:"研究院";position:absolute;left:50%;top:9px;transform:translateX(-50%);color:#285a47;font-family:serif;font-size:11px}.innovation-hall i{display:inline-block;width:26px;height:28px;margin:35px 10px 0;background:#78aa9d}.tech-orbit{position:absolute;z-index:7;inset:18px}.tech-orbit:before,.tech-orbit:after{content:"";position:absolute;left:10%;right:10%;top:50%;height:1px;background:rgba(230,196,127,.75);transform:rotate(18deg)}.tech-orbit:after{transform:rotate(-24deg)}.tech-orbit i{position:absolute;width:12px;height:12px;border:3px solid #e6c47f;border-radius:50%;background:#285a47;box-shadow:0 0 0 5px rgba(230,196,127,.14)}.tech-orbit i:nth-child(1){left:8%;top:30%}.tech-orbit i:nth-child(2){right:12%;top:18%}.tech-orbit i:nth-child(3){right:25%;bottom:16%}.is-huangpu .campus-scene-copy small,.is-huangpu .campus-scene-copy h3{color:#285a47}.is-huangpu .campus-scene-copy span{color:#285a47;background:#e7f1ec}@media(max-width:950px){.campus-scene-card{display:grid;grid-template-columns:.85fr 1.15fr}.campus-scene{height:auto;min-height:300px}.campus-scene-copy p{min-height:auto}}@media(max-width:620px){.campus-scene-card{display:block}.campus-scene{height:225px;min-height:0}}
.huangpu-character{position:absolute;z-index:8;right:14px;bottom:4px;width:145px;height:218px;object-fit:contain;object-position:center bottom;filter:drop-shadow(0 10px 8px rgba(20,63,53,.2))}.campus-scene-card.is-huangpu:hover .huangpu-character{transform:translateY(-3px) rotate(1deg);transition:transform .25s ease}
.campus-scene-card.is-interactive{width:100%;padding:0;text-align:left;font:inherit;color:inherit;cursor:pointer}.campus-scene-card[aria-disabled="true"]{cursor:default}.campus-status{position:absolute;z-index:12;top:16px;left:16px;padding:7px 11px;border-radius:999px;color:#fff;background:rgba(31,91,70,.9);font-size:11px;font-weight:800;letter-spacing:.06em;box-shadow:0 5px 16px rgba(24,51,42,.18)}.campus-scene-card:not(.is-interactive) .campus-status{background:rgba(83,89,86,.82)}
</style>
