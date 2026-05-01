<script setup lang="ts">
import { shallowRef, computed, inject, watch, onMounted, nextTick } from 'vue'
import { useLocalStorage } from '@vueuse/core'
import type { Card, ZigenCard } from '../share'

const p = defineProps<{
    cards: readonly Card[]
    id: string
}>()

const zigenFontClass = inject('font') || 'outi-yima'

const mistakesRef = useLocalStorage<number[]>(`yima_${p.id}_mistakes`, () => Array.from({ length: p.cards.length }, () => 0))

// Sync length in case cards grew
if (mistakesRef.value.length < p.cards.length) {
    for (let i = mistakesRef.value.length; i < p.cards.length; i++) {
        mistakesRef.value.push(0)
    }
}

const mistakeList = computed(() =>
    p.cards
        .map((card, i) => ({ card, index: i, count: mistakesRef.value[i] ?? 0 }))
        .filter(item => item.count > 0)
        .sort((a, b) => b.count - a.count)
)

const totalMistakes = computed(() => mistakeList.value.reduce((s, m) => s + m.count, 0))

// ── Practice mode ──────────────────────────────────────────────
type PracticeItem = { card: Card; index: number; count: number }

const isPracticing = shallowRef(false)
const practiceQueue = shallowRef<PracticeItem[]>([])
const practiceTotal = shallowRef(0)
const practiceCorrect = shallowRef(0)
const isDone = shallowRef(false)
const isCorrect = shallowRef(true)
const userKeys = shallowRef('')

const currentCard = computed(() => practiceQueue.value[0]?.card as ZigenCard | undefined)

function startPractice() {
    practiceQueue.value = [...mistakeList.value]
    practiceTotal.value = practiceQueue.value.length
    practiceCorrect.value = 0
    isDone.value = false
    isCorrect.value = true
    isPracticing.value = true
    focusInput()
}

function stopPractice() {
    isPracticing.value = false
    isDone.value = false
    userKeys.value = ''
}

function focusInput() {
    nextTick(() => document.getElementById('mistake_input')?.focus())
}

watch(userKeys, (newKeys) => {
    if (!currentCard.value) return
    if (newKeys.includes(' ')) {
        handleAnswer(false)
        userKeys.value = ''
        return
    }
    if (newKeys.length < (currentCard.value.key?.length ?? 1)) return
    handleAnswer(newKeys === currentCard.value.key)
    userKeys.value = ''
})

function handleAnswer(correct: boolean) {
    if (correct) {
        isCorrect.value = true
        practiceCorrect.value++
        practiceQueue.value = practiceQueue.value.slice(1)
        if (practiceQueue.value.length === 0) {
            isDone.value = true
            isPracticing.value = false
        }
    } else {
        isCorrect.value = false
        const first = practiceQueue.value[0]
        practiceQueue.value = [...practiceQueue.value.slice(1), first]
    }
}

function clearMistakes() {
    if (!confirm('确定清空所有错根记录吗？')) return
    mistakesRef.value = Array.from({ length: p.cards.length }, () => 0)
}
</script>

<template>
    <!-- 练习完成 -->
    <div v-if="isDone" class="md:w-2/3 w-full my-6 text-center">
        <div class="text-4xl font-bold text-green-600 dark:text-green-400 mb-6">练习完成！</div>
        <div class="text-gray-500 mb-8">本轮共练习 {{ practiceTotal }} 个错根</div>
        <button class="btn btn-success" @click="stopPractice">返回统计</button>
    </div>

    <!-- 练习中 -->
    <div v-else-if="isPracticing"
         :class="['md:w-2/3 w-full shadow-sm my-6 pb-16 bg-opacity-10 transition-color rounded-md', { 'bg-red-700': !isCorrect, 'bg-slate-500': isCorrect }]">
        <div class="flex justify-center mb-10">
            <progress class="progress w-full" :value="practiceCorrect" :max="practiceTotal" />
        </div>
        <div class="flex flex-col md:flex-row justify-center items-center md:mb-8 mb-4">
            <div :class="['md:text-6xl md:mr-3 text-4xl mr-0 align-middle animate__animated', zigenFontClass,
                          { 'text-red-400': !isCorrect, 'animate__headShake': !isCorrect }]">
                {{ currentCard?.name }}
            </div>
            <div class="flex flex-col" v-if="currentCard && ('rel' in currentCard || 'kind' in currentCard)">
                <div class="flex tracking-widest flex-col opacity-80" v-if="currentCard && 'rel' in currentCard">
                    <div class="text-gray-500 md:text-sm text-xs">例字：</div>
                    <div class="md:text-base text-sm">{{ (currentCard as ZigenCard).rel }}</div>
                    <template v-if="(currentCard as ZigenCard)._classZigen">
                        <div class="text-gray-500 text-sm mt-4 mb-2">相似字根：</div>
                        <div v-for="c in (currentCard as ZigenCard)._classZigen" class="my-1">
                            <span :class="['opacity-100 text-xl mr-2', zigenFontClass]">{{ c.name }}</span>
                            <span class="text-sm">{{ c.rel }}</span>
                        </div>
                    </template>
                </div>
                <div class="tracking-widest pt-6 text-blue-600 dark:text-blue-300"
                     v-if="currentCard && 'kind' in currentCard && (currentCard as ZigenCard).kind == 'b'">五个基础笔画</div>
                <div class="tracking-widest pt-6 text-blue-600 dark:text-blue-300"
                     v-if="currentCard && 'kind' in currentCard && (currentCard as ZigenCard).kind == 'eb'">25个二笔小码</div>
            </div>
        </div>
        <div class="flex justify-center p-5">
            <input id="mistake_input" type="text" placeholder="输入编码" v-model="userKeys"
                   :class="['input w-half max-w-xs input-bordered text-center input-sm dark:bg-slate-800 bg-white', { 'input-error': !isCorrect }]" />
        </div>
        <div class="text-center text-gray-500 text-sm">
            剩余 {{ practiceQueue.length }} / {{ practiceTotal }}
        </div>
        <div class="flex justify-center mt-6">
            <button class="btn btn-ghost btn-sm" @click="stopPractice">退出练习</button>
        </div>
    </div>

    <!-- 统计列表 -->
    <div v-else class="md:w-2/3 w-full my-6">
        <div v-if="mistakeList.length === 0" class="text-center text-gray-400 py-16">
            暂无错根记录，继续加油！
        </div>
        <template v-else>
            <div class="flex items-center justify-between mb-4">
                <span class="text-gray-500 text-sm">共 {{ mistakeList.length }} 个错根，累计答错 {{ totalMistakes }} 次</span>
                <div class="flex gap-2">
                    <button class="btn btn-primary btn-sm" @click="startPractice">开始练习</button>
                    <button class="btn btn-ghost btn-sm text-gray-400" @click="clearMistakes">清空记录</button>
                </div>
            </div>
            <div class="overflow-x-auto">
                <table class="table table-sm w-full">
                    <thead>
                        <tr class="text-gray-400">
                            <th>字根</th>
                            <th>编码</th>
                            <th>例字</th>
                            <th class="text-right">错误次数</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="item in mistakeList" :key="item.index" class="hover">
                            <td>
                                <span :class="['text-2xl', zigenFontClass]">{{ item.card.name }}</span>
                            </td>
                            <td class="font-mono">{{ item.card.key }}</td>
                            <td class="text-gray-500 text-sm">{{ 'rel' in item.card ? (item.card as ZigenCard).rel : '' }}</td>
                            <td class="text-right">
                                <span class="badge badge-error badge-sm">{{ item.count }}</span>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </template>
    </div>
</template>
