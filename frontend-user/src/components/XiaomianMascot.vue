<script setup lang="ts">
import { computed, ref } from 'vue'

withDefaults(defineProps<{ compact?: boolean }>(), { compact: false })

const hovering = ref(false)
const pinned = ref(false)
const showBubble = computed(() => hovering.value || pinned.value)
</script>

<template>
  <div
    class="mascot"
    :class="{ compact, 'has-bubble': showBubble }"
    role="button"
    tabindex="0"
    aria-label="数字人小棉，一位佩戴木棉发饰的岭南文化校园导览员。悬停或点击查看欢迎语"
    @mouseenter="hovering = true"
    @mouseleave="hovering = false"
    @focusin="hovering = true"
    @focusout="hovering = false"
    @click.stop="pinned = !pinned"
    @keydown.enter.prevent="pinned = !pinned"
    @keydown.space.prevent="pinned = !pinned"
  >
    <div v-if="showBubble" class="mascot-bubble" role="status">
      欢迎来到岭潮共创！跟我一起探索广州大学的岭南文化吧～
    </div>
    <div class="kapok"><i /><i /><i /><i /><i /><b /></div>
    <div class="hair-back" />
    <div class="ear left" /><div class="ear right" />
    <div class="face"><i class="brow left" /><i class="brow right" /><i class="eye left" /><i class="eye right" /><i class="nose" /><i class="mouth" /><i class="blush left" /><i class="blush right" /></div>
    <div class="hair-front"><i /><b /></div>
    <div class="neck" />
    <div class="body"><i class="collar left" /><i class="collar right" /><span>岭</span></div>
    <div class="shoulder left" /><div class="shoulder right" />
  </div>
</template>

<style scoped>
.mascot{position:relative;width:210px;height:250px;margin:auto;isolation:isolate;animation:mascot-float 3.8s ease-in-out infinite}.hair-back{position:absolute;z-index:1;left:34px;top:28px;width:142px;height:172px;background:#25201f;border-radius:70px 70px 42px 42px}.face{position:absolute;z-index:3;left:55px;top:55px;width:100px;height:118px;background:#f4c9a5;border-radius:48% 48% 44% 44%}.ear{position:absolute;z-index:2;top:96px;width:24px;height:36px;background:#eebf9a;border-radius:50%}.ear.left{left:43px}.ear.right{right:43px}.hair-front{position:absolute;z-index:4;left:48px;top:38px;width:115px;height:63px;border-radius:55px 55px 30px 10px;background:#282220;transform:rotate(-3deg)}.hair-front:after{content:"";position:absolute;right:-9px;top:27px;width:34px;height:64px;background:#282220;border-radius:0 35px 30px 25px;transform:rotate(-8deg)}.hair-front i{position:absolute;left:43px;bottom:-17px;width:25px;height:44px;background:#282220;border-radius:0 0 20px 20px;transform:rotate(14deg)}.hair-front b{position:absolute;left:12px;bottom:-7px;width:28px;height:35px;background:#282220;border-radius:0 0 22px 20px;transform:rotate(22deg)}.brow,.eye,.blush,.nose,.mouth{position:absolute;display:block}.brow{top:39px;width:19px;height:5px;border-top:2px solid #584238;border-radius:50%}.brow.left{left:18px}.brow.right{right:18px}.eye{top:49px;width:12px;height:15px;background:#332927;border-radius:50%;box-shadow:inset 3px 3px 0 rgba(255,255,255,.85);animation:mascot-blink 5.5s ease-in-out infinite}.eye.left{left:23px}.eye.right{right:23px}.nose{left:48px;top:65px;width:5px;height:8px;border-right:2px solid #c1846e;border-bottom:2px solid #c1846e;border-radius:0 0 4px}.mouth{left:41px;top:85px;width:20px;height:10px;border-bottom:3px solid #a34f50;border-radius:0 0 50% 50%}.blush{top:72px;width:18px;height:8px;background:rgba(218,111,105,.25);border-radius:50%;filter:blur(2px)}.blush.left{left:8px}.blush.right{right:8px}.neck{position:absolute;z-index:2;left:88px;top:161px;width:34px;height:40px;background:#eab991}.body{position:absolute;z-index:2;left:52px;top:184px;width:106px;height:65px;background:#a82e37;border-radius:45px 45px 8px 8px;overflow:hidden}.body:after{content:"";position:absolute;left:48px;top:0;width:10px;height:65px;background:#e7b458}.body span{position:absolute;z-index:2;left:42px;top:28px;color:#fff5dd;font-family:serif;font-size:18px}.collar{position:absolute;z-index:2;top:0;width:43px;height:31px;background:#f5e7ce}.collar.left{left:9px;clip-path:polygon(0 0,100% 0,100% 100%)}.collar.right{right:9px;clip-path:polygon(0 0,100% 0,0 100%)}.shoulder{position:absolute;z-index:1;top:207px;width:67px;height:42px;background:#8b242c;border-radius:40px}.shoulder.left{left:25px;transform:rotate(-13deg)}.shoulder.right{right:25px;transform:rotate(13deg)}.kapok{position:absolute;z-index:6;right:23px;top:24px;width:52px;height:52px;animation:mascot-sway 3.2s ease-in-out infinite;transform-origin:50% 80%}.kapok i{position:absolute;left:17px;top:3px;width:19px;height:28px;background:#d8453f;border-radius:70% 30% 70% 30%;transform-origin:50% 23px}.kapok i:nth-child(2){transform:rotate(72deg)}.kapok i:nth-child(3){transform:rotate(144deg)}.kapok i:nth-child(4){transform:rotate(216deg)}.kapok i:nth-child(5){transform:rotate(288deg)}.kapok b{position:absolute;z-index:2;left:20px;top:19px;width:13px;height:13px;background:#e9ad3d;border-radius:50%}.compact{width:150px;height:180px;transform:scale(.72);transform-origin:center bottom}@keyframes mascot-float{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}@keyframes mascot-blink{0%,43%,47%,100%{transform:scaleY(1)}44%,46%{transform:scaleY(.12)}}@keyframes mascot-sway{0%,100%{transform:rotate(-3deg)}50%{transform:rotate(4deg)}}@media(prefers-reduced-motion:reduce){.mascot,.mascot .eye,.mascot .kapok{animation:none}}
.mascot{cursor:pointer;outline:none}.mascot:focus-visible{filter:drop-shadow(0 0 0.35rem rgba(207,145,56,.65))}.mascot-bubble{position:absolute;z-index:20;left:50%;top:-14px;width:max-content;max-width:min(300px,calc(100vw - 40px));padding:10px 14px;color:#285a47;background:#fffdf4;border:1px solid #e2bd71;border-radius:14px;box-shadow:0 10px 24px rgba(31,57,46,.18);font-size:12px;font-weight:700;line-height:1.55;text-align:center;transform:translate(-50%,-100%);animation:bubble-in .18s ease-out}.mascot-bubble:after{content:"";position:absolute;left:50%;bottom:-8px;width:14px;height:14px;background:#fffdf4;border-right:1px solid #e2bd71;border-bottom:1px solid #e2bd71;transform:translateX(-50%) rotate(45deg)}.compact .mascot-bubble{top:-7px;font-size:11px}@keyframes bubble-in{from{opacity:0;transform:translate(-50%,-92%) scale(.96)}to{opacity:1;transform:translate(-50%,-100%) scale(1)}}
@media(max-width:620px){.mascot-bubble{max-width:240px}}
@media(prefers-reduced-motion:reduce){.mascot-bubble{animation:none}}
</style>
