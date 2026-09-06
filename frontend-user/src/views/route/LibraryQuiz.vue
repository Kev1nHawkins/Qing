<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CulturalTokenReveal from '@/components/CulturalTokenReveal.vue'
import { api } from '@/services/api'
import type { CultureRoute, RouteTask, TaskCompleteResult } from '@/types'
import {
  culturalTokenForTask,
  libraryQuizQuestions,
} from '@/views/route/culturalTokens'

const route = useRoute()
const router = useRouter()
const task = ref<RouteTask>()
const answers = ref<string[]>(libraryQuizQuestions.map(() => ''))
const currentIndex = ref(0)
const loading = ref(true)
const submitting = ref(false)
const error = ref('')
const result = ref<TaskCompleteResult>()
const showToken = ref(false)

const routeId = computed(() => Number(route.params.routeId))
const taskId = computed(() => Number(route.params.taskId))
const currentQuestion = computed(() => libraryQuizQuestions[currentIndex.value])
const answeredCount = computed(() => answers.value.filter(Boolean).length)
const score = computed(() =>
  libraryQuizQuestions.reduce(
    (total, item, index) => total + (answers.value[index] === item.answer ? 1 : 0),
    0,
  ),
)
const token = computed(() =>
  task.value ? culturalTokenForTask(task.value) : undefined,
)

function chooseAnswer(value: string) {
  answers.value[currentIndex.value] = value
}

function nextQuestion() {
  if (!answers.value[currentIndex.value]) {
    error.value = '请先选择当前题目的答案'
    return
  }
  error.value = ''
  if (currentIndex.value < libraryQuizQuestions.length - 1) {
    currentIndex.value += 1
  }
}

async function submitQuiz() {
  if (answeredCount.value !== libraryQuizQuestions.length || !task.value) {
    error.value = '请完成全部题目后再提交'
    return
  }
  submitting.value = true
  error.value = ''
  try {
    await api.post(`/routes/${routeId.value}/start`)
    const answerSummary = `广州文化知识闯关:${score.value}/${libraryQuizQuestions.length}`
    const response = await api.post<{ data: TaskCompleteResult }>(
      `/tasks/${taskId.value}/complete`,
      { answer: answerSummary },
    )
    result.value = response.data.data
    showToken.value = true
  } catch (event) {
    error.value = (event as Error).message
  } finally {
    submitting.value = false
  }
}

async function loadTask() {
  if (!localStorage.getItem('accessToken')) {
    await router.replace({
      path: '/login',
      query: { redirect: route.fullPath },
    })
    return
  }
  if (!Number.isInteger(routeId.value) || !Number.isInteger(taskId.value)) {
    error.value = '问答任务地址无效'
    loading.value = false
    return
  }
  try {
    const response = await api.get<{ data: CultureRoute }>(`/routes/${routeId.value}`)
    const loadedTask = response.data.data.tasks?.find(item => item.id === taskId.value)
    if (!loadedTask || loadedTask.task_type !== 'QUIZ') {
      error.value = '当前任务不是文化问答'
      return
    }
    task.value = loadedTask
  } catch (event) {
    error.value = (event as Error).message
  } finally {
    loading.value = false
  }
}

function closeToken() {
  showToken.value = false
  router.push('/routes/journey')
}

onMounted(loadTask)
</script>

<template>
  <section class="library-quiz">
    <header>
      <button type="button" @click="router.push('/routes/journey')">← 返回路线</button>
      <div><p>LIBRARY CULTURE QUIZ</p><h1>图书馆 · 羊城求知闯关</h1><span>五道题认识广州文化。分数用于反馈学习成果，不影响文化令牌发放。</span></div>
      <strong>{{ answeredCount }}/{{ libraryQuizQuestions.length }}</strong>
    </header>

    <div v-if="loading" class="quiz-state">正在加载问答任务…</div>
    <div v-else-if="error && !task" class="quiz-state error">{{ error }}</div>

    <template v-else-if="task">
      <div class="quiz-progress"><i :style="{ width: `${answeredCount * 100 / libraryQuizQuestions.length}%` }" /></div>
      <article class="question-card">
        <aside>
          <span>{{ String(currentIndex + 1).padStart(2, '0') }}</span>
          <small>GUANGZHOU CULTURE</small>
          <h2>{{ currentQuestion.question }}</h2>
          <p>选择后可查看相关文化知识，全部完成即可领取“羊城求知令”。</p>
        </aside>
        <main>
          <button
            v-for="option in currentQuestion.options"
            :key="option"
            type="button"
            :class="{ selected: answers[currentIndex] === option }"
            @click="chooseAnswer(option)"
          >
            <span>{{ String.fromCharCode(65 + currentQuestion.options.indexOf(option)) }}</span>
            {{ option }}
          </button>
          <div v-if="answers[currentIndex]" class="knowledge-note">
            <b>{{ answers[currentIndex] === currentQuestion.answer ? '回答正确' : `参考答案：${currentQuestion.answer}` }}</b>
            <p>{{ currentQuestion.fact }}</p>
          </div>
        </main>
      </article>

      <nav class="quiz-navigation">
        <button type="button" :disabled="currentIndex === 0" @click="currentIndex -= 1">上一题</button>
        <div>
          <button
            v-for="(_, index) in libraryQuizQuestions"
            :key="index"
            type="button"
            :class="{ active: currentIndex === index, answered: answers[index] }"
            @click="currentIndex = index"
          >
            {{ index + 1 }}
          </button>
        </div>
        <button
          v-if="currentIndex < libraryQuizQuestions.length - 1"
          class="primary"
          type="button"
          @click="nextQuestion"
        >
          下一题
        </button>
        <button v-else class="primary" type="button" :disabled="submitting" @click="submitQuiz">
          {{ submitting ? '正在提交…' : '完成闯关并领取令牌' }}
        </button>
      </nav>
      <p v-if="error" class="quiz-error">{{ error }}</p>
    </template>

    <CulturalTokenReveal
      v-if="showToken && token && result"
      :token="token"
      :points="result.alreadyCompleted ? 0 : result.awardedPoints"
      :score="`${score}/${libraryQuizQuestions.length}`"
      @close="closeToken"
    />
  </section>
</template>

<style scoped>
.library-quiz{min-height:calc(100vh - 170px);padding-bottom:40px}.library-quiz>header{display:grid;grid-template-columns:auto 1fr auto;align-items:start;gap:24px;padding:32px 0}.library-quiz>header>button{min-height:38px;padding:0 12px;border:1px solid #d5ddd7;border-radius:7px;background:#fff}.library-quiz>header p{margin:0;color:#9f2d35;font-size:9px;font-weight:900;letter-spacing:.16em}.library-quiz>header h1{margin:7px 0;font-size:clamp(34px,6vw,58px)}.library-quiz>header span{color:#65716b}.library-quiz>header>strong{display:grid;place-items:center;width:72px;height:72px;color:#fff;background:#285a47;border-radius:50%;font-size:20px}.quiz-progress{height:7px;overflow:hidden;background:#dfe6e1;border-radius:999px}.quiz-progress i{display:block;height:100%;background:linear-gradient(90deg,#9f2d35,#d6a54c);transition:width .25s ease}.question-card{display:grid;grid-template-columns:.85fr 1.15fr;min-height:430px;margin-top:20px;overflow:hidden;border:1px solid #dce2de;border-radius:18px;background:#fff;box-shadow:0 20px 55px rgba(40,63,53,.1)}.question-card>aside{padding:42px;color:#fff;background:linear-gradient(145deg,#285a47,#173c31)}.question-card>aside>span{display:grid;place-items:center;width:58px;height:58px;color:#6f4511;background:#e7c476;border:5px double rgba(255,255,255,.8);border-radius:50%;font-family:serif;font-size:21px}.question-card small{display:block;margin-top:34px;color:#dfc37f;font-weight:900;letter-spacing:.13em}.question-card h2{font-size:30px;line-height:1.35}.question-card aside p{color:#c9ddd3;line-height:1.75}.question-card>main{display:grid;align-content:center;gap:11px;padding:42px}.question-card>main>button{display:flex;align-items:center;gap:14px;min-height:54px;padding:8px 15px;border:1px solid #d6ded8;border-radius:10px;background:#fff;text-align:left}.question-card>main>button>span{display:grid;place-items:center;width:32px;height:32px;background:#edf2ef;border-radius:50%;font-weight:900}.question-card>main>button.selected{color:#fff;background:#9f2d35;border-color:#9f2d35}.question-card>main>button.selected>span{color:#7d4c12;background:#efcc82}.knowledge-note{margin-top:7px;padding:14px 16px;background:#f3efe4;border-left:4px solid #d0a249}.knowledge-note p{margin:5px 0 0;color:#68736d;font-size:12px;line-height:1.65}.quiz-navigation{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:16px;margin-top:18px}.quiz-navigation>button{min-height:42px;padding:0 15px;border:1px solid #ccd6cf;border-radius:8px;background:#fff}.quiz-navigation>button.primary{color:#fff;background:#9f2d35;border-color:#9f2d35}.quiz-navigation>button:disabled{opacity:.45}.quiz-navigation>div{display:flex;justify-content:center;gap:7px}.quiz-navigation>div button{width:34px;height:34px;border:1px solid #cfd8d2;border-radius:50%;background:#fff}.quiz-navigation>div button.answered{color:#fff;background:#769080}.quiz-navigation>div button.active{box-shadow:0 0 0 4px rgba(159,45,53,.16);border-color:#9f2d35}.quiz-error,.quiz-state{padding:14px;color:#8f222c;background:#fff0f0;border-radius:9px}.quiz-state{display:grid;place-items:center;min-height:300px}.quiz-state.error{color:#8f222c}
@media(max-width:760px){.library-quiz>header{grid-template-columns:1fr}.library-quiz>header>strong{display:none}.question-card{grid-template-columns:1fr}.question-card>aside,.question-card>main{padding:28px}.question-card small{margin-top:20px}.quiz-navigation{grid-template-columns:1fr 1fr}.quiz-navigation>div{grid-column:1/-1;grid-row:1}.quiz-navigation>button:last-child{grid-column:2}}
</style>
