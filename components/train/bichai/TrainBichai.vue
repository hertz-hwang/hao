<script setup lang="ts">
import { shallowRef, watch, onMounted, inject, nextTick, computed } from 'vue'
import type { HanziCard } from '../share'
import CardLayout from '../CardLayout.vue'
import { useBichai } from './useBichai'

const p = defineProps<{
    cards: readonly HanziCard[]
    name: string
}>()

const zigenFontClass = inject('font') || 'outi-yima'
const highlightStrokes = inject('high') as Set<string> | undefined

const { progress, card, answer, restart, mistakes, clearMistakes } = useBichai(p.name, p.cards)

const isCorrect = shallowRef(true)
const userKeys = shallowRef('')

onMounted(() => {
    document.getElementById('bichai_input')?.focus()
})

watch(card, () => nextTick(() => document.getElementById('bichai_input')?.focus()))

watch(userKeys, (newKeys) => {
    if (!card.value) return
    if (newKeys.includes(' ')) {
        answer(false)
        isCorrect.value = false
        userKeys.value = ''
        return
    }
    const expected = card.value.key ?? ''
    if (newKeys.length < expected.length) return
    if (newKeys === expected) {
        answer(true)
        isCorrect.value = true
    } else {
        answer(false)
        isCorrect.value = false
    }
    userKeys.value = ''
})

function cusRestart() {
    if (!confirm('重置进度需要清空数据，无法撤回，您确定继续吗？')) return
    restart()
    isCorrect.value = true
    userKeys.value = ''
}

// ── 错拆复习 ──────────────────────────────────────────────
const activeTab = shallowRef<'normal' | 'mistakes'>('normal')

const mistakeList = computed(() =>
    p.cards
        .map((c, i) => ({ card: c, index: i, count: mistakes.value[i] ?? 0 }))
        .filter(item => item.count > 0)
        .sort((a, b) => b.count - a.count),
)
const totalMistakes = computed(() => mistakeList.value.reduce((s, m) => s + m.count, 0))

type PracticeItem = { card: HanziCard; index: number; count: number }
const isPracticing = shallowRef(false)
const practiceQueue = shallowRef<PracticeItem[]>([])
const practiceTotal = shallowRef(0)
const practiceCorrect = shallowRef(0)
const isDone = shallowRef(false)
const mIsCorrect = shallowRef(true)
const mUserKeys = shallowRef('')
/** 本轮已答错过的字 index，一旦答错就记进来，后面答对也不清计数 */
const roundDirty = shallowRef<Set<number>>(new Set())

const practiceCard = computed(() => practiceQueue.value[0]?.card)

function startPractice() {
    practiceQueue.value = [...mistakeList.value]
    practiceTotal.value = practiceQueue.value.length
    practiceCorrect.value = 0
    isDone.value = false
    mIsCorrect.value = true
    roundDirty.value = new Set()
    isPracticing.value = true
    nextTick(() => document.getElementById('bichai_mistake_input')?.focus())
}

function stopPractice() {
    isPracticing.value = false
    isDone.value = false
    mUserKeys.value = ''
}

function handlePracticeAnswer(correct: boolean) {
    const first = practiceQueue.value[0]
    if (!first) return
    if (correct) {
        mIsCorrect.value = true
        practiceCorrect.value++
        // 本轮未曾答错过这个字 → 认定掌握，从错拆统计里清掉；
        // 本轮答错过（哪怕后面对了）→ 保留错次，继续留在错拆统计中
        if (!roundDirty.value.has(first.index)) {
            mistakes.value[first.index] = 0
        }
        practiceQueue.value = practiceQueue.value.slice(1)
        if (practiceQueue.value.length === 0) {
            isDone.value = true
            isPracticing.value = false
        }
    } else {
        mIsCorrect.value = false
        // 答错不换卡，提示本卡答案，重输正确才前进；错误次数计入统计
        mistakes.value[first.index] += 1
        roundDirty.value.add(first.index)
    }
}

watch(mUserKeys, (newKeys) => {
    if (!practiceCard.value) return
    if (newKeys.includes(' ')) {
        handlePracticeAnswer(false)
        mUserKeys.value = ''
        return
    }
    const expected = practiceCard.value.key ?? ''
    if (newKeys.length < expected.length) return
    handlePracticeAnswer(newKeys === expected)
    mUserKeys.value = ''
})

function clearMistakesConfirm() {
    if (!confirm('确定清空所有错拆记录吗？')) return
    clearMistakes()
}
</script>

<template>
    <div class="tabs tabs-border mb-4">
        <button :class="['tab', { 'tab-active': activeTab === 'normal' }]" @click="activeTab = 'normal'">必拆字练习</button>
        <button :class="['tab', { 'tab-active': activeTab === 'mistakes' }]" @click="activeTab = 'mistakes'">错拆复习</button>
    </div>

    <!-- 正常练习 -->
    <template v-if="activeTab === 'normal'">
        <CardLayout :progress :max="cards.length" :isCorrect :id="name" @restart="cusRestart">
            <div v-if="card" class="flex justify-around mb-8">
                <div :key="card.name"
                    :class="['text-6xl animate__animated kaiti-zigen', { 'text-red-400': !isCorrect, 'animate__headShake': !isCorrect }]">
                    {{ card.name }}
                </div>
            </div>
            <div v-else class="text-center text-2xl text-green-600 dark:text-green-400 py-10">
                🎉 所有必拆字都已掌握！
            </div>
            <div v-if="card" class="flex justify-center p-5">
                <input id="bichai_input" type="text" placeholder="输入编码" v-model="userKeys"
                    :class="['input w-half max-w-xs input-bordered text-center input-sm dark:bg-slate-800 bg-white', { 'input-error': !isCorrect }]" />
            </div>
            <div v-if="card" :class="['text-center', { 'opacity-0': isCorrect }]">答案是
                <b class="font-mono">{{ card.key }}</b>
                <span v-if="card.rootKeys?.length" :class="[zigenFontClass, 'tracking-widest opacity-80 ml-2']">
                    <ruby v-for="(rk, i) of card.rootKeys" :key="i" class="mr-1">
                        <span :class="{ 'round-bg': highlightStrokes?.has(rk.zigen) }">{{ rk.zigen }}</span>
                        <rp>(</rp><rt class="font-mono uppercase text-blue-500 dark:text-blue-300">{{ rk.key }}</rt><rp>)</rp>
                    </ruby>
                </span>
                <span v-else-if="card.comp" :class="[zigenFontClass, 'tracking-widest opacity-80']">
                    （{{ card.comp }}）
                </span>
            </div>
        </CardLayout>
    </template>

    <!-- 错拆复习 -->
    <template v-else>
        <div v-if="isDone" class="md:w-2/3 w-full my-6 text-center">
            <div class="text-4xl font-bold text-green-600 dark:text-green-400 mb-6">练习完成！</div>
            <div class="text-gray-500 mb-8">本轮共练习 {{ practiceTotal }} 个错拆</div>
            <button class="btn btn-success" @click="stopPractice">返回统计</button>
        </div>

        <div v-else-if="isPracticing"
            :class="['md:w-2/3 w-full shadow-sm my-6 pb-16 bg-opacity-10 transition-color rounded-md', { 'bg-red-700': !mIsCorrect, 'bg-slate-500': mIsCorrect }]">
            <div class="flex justify-center mb-10">
                <progress class="progress w-full" :value="practiceCorrect" :max="practiceTotal" />
            </div>
            <div class="flex justify-around mb-8">
                <div :key="practiceCard?.name"
                    :class="['text-6xl animate__animated kaiti-zigen', { 'text-red-400': !mIsCorrect, 'animate__headShake': !mIsCorrect }]">
                    {{ practiceCard?.name }}
                </div>
            </div>
            <div class="flex justify-center p-5">
                <input id="bichai_mistake_input" type="text" placeholder="输入编码" v-model="mUserKeys"
                    :class="['input w-half max-w-xs input-bordered text-center input-sm dark:bg-slate-800 bg-white', { 'input-error': !mIsCorrect }]" />
            </div>
            <div :class="['text-center', { 'opacity-0': mIsCorrect }]">答案是
                <b class="font-mono">{{ practiceCard?.key }}</b>
                <span v-if="practiceCard?.rootKeys?.length" :class="[zigenFontClass, 'tracking-widest opacity-80 ml-2']">
                    <ruby v-for="(rk, i) of practiceCard.rootKeys" :key="i" class="mr-1">
                        <span :class="{ 'round-bg': highlightStrokes?.has(rk.zigen) }">{{ rk.zigen }}</span>
                        <rp>(</rp><rt class="font-mono uppercase text-blue-500 dark:text-blue-300">{{ rk.key }}</rt><rp>)</rp>
                    </ruby>
                </span>
            </div>
            <div class="text-center text-gray-500 text-sm mt-2">
                剩余 {{ practiceQueue.length }} / {{ practiceTotal }}
            </div>
            <div class="flex justify-center mt-6">
                <button class="btn btn-ghost btn-sm" @click="stopPractice">退出练习</button>
            </div>
        </div>

        <div v-else class="md:w-2/3 w-full my-6">
            <div v-if="mistakeList.length === 0" class="text-center text-gray-400 py-16">
                暂无错拆记录，继续加油！
            </div>
            <template v-else>
                <div class="flex items-center justify-between mb-4">
                    <span class="text-gray-500 text-sm">共 {{ mistakeList.length }} 个错拆字，累计答错 {{ totalMistakes }} 次</span>
                    <div class="flex gap-2">
                        <button class="btn btn-primary btn-sm" @click="startPractice">开始练习</button>
                        <button class="btn btn-ghost btn-sm text-gray-400" @click="clearMistakesConfirm">清空记录</button>
                    </div>
                </div>
                <div class="overflow-x-auto">
                    <table class="table table-sm w-full">
                        <thead>
                            <tr class="text-gray-400">
                                <th>字</th>
                                <th>拆分</th>
                                <th>编码</th>
                                <th class="text-right">错误次数</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="item in mistakeList" :key="item.index" class="hover">
                                <td><span class="text-2xl kaiti-zigen">{{ item.card.name }}</span></td>
                                <td :class="[zigenFontClass, 'tracking-widest']">
                                    <template v-if="item.card.rootKeys?.length">
                                        <ruby v-for="(rk, i) of item.card.rootKeys" :key="i" class="mr-1">
                                            <span>{{ rk.zigen }}</span>
                                            <rp>(</rp><rt class="font-mono uppercase text-blue-500 dark:text-blue-300">{{ rk.key }}</rt><rp>)</rp>
                                        </ruby>
                                    </template>
                                    <template v-else>{{ item.card.comp }}</template>
                                </td>
                                <td class="font-mono">{{ item.card.key }}</td>
                                <td class="text-right"><span class="badge badge-error badge-sm">{{ item.count }}</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </template>
        </div>
    </template>
</template>
