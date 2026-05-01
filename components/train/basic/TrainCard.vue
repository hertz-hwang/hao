<script setup lang="ts">
import { shallowRef, watch, onMounted, inject } from "vue";
import { useReview } from "./useReview";
import { Card, ZigenCard } from "../share";
import CardLayout from "../CardLayout.vue";

const p = defineProps<{
    /** 复习卡片的数据 */
    cards: readonly Card[]
    /** 复习卡片的名字, 决定localstorage里的名字 */
    id: string
}>()

const zigenFontClass = inject('font') || 'outi-yima'

const { card, restart, answer, progress, isFirst } = useReview(p.id, p.cards)

const isCorrect = shallowRef(true)
const userKeys = shallowRef('')

const focusInputElement = () => {
    const element = document.getElementById('input_el')
    element?.focus()
}

onMounted(() => {
    focusInputElement()
})

function cusRestart() {
    if (!confirm(`重置进度需要清空数据，无法撤回，您确定继续吗？`)) return;
    restart()
    focusInputElement()
}

watch(userKeys, (newKeys) => {
    //空格直接判定为错误
    if (newKeys.includes(' ')) {
        answer(false)
        isCorrect.value = false
        userKeys.value = '' // 清空输入
        return // 直接返回不执行后续逻辑
    }
    // 多个编码没有打完就不提示错误
    if (newKeys.length < card.value.key!.length)
        return
    // 检查回答
    if (newKeys === card.value.key) {
        answer(true)
        isCorrect.value = true
    } else {
        answer(false)
        isCorrect.value = false
    }
    userKeys.value = ''
})

</script>

<template>
    <CardLayout :progress :max="p.cards.length" :isCorrect :id @restart="cusRestart">
        <div class="flex flex-col md:flex-row justify-center items-center md:mb-8 mb-4">
            <div
                 :class="['md:text-6xl md:mr-3 text-4xl mr-0 align-middle animate__animated', zigenFontClass, { 'text-red-400': !isCorrect, 'animate__headShake': !isCorrect }]">
                {{ card.name }}</div>

            <div class="flex flex-col" v-if="'rel' in card || 'kind' in card">
                <div class="flex tracking-widest flex-col opacity-80" v-if="'rel' in card">
                    <div class="text-gray-500 md:text-sm text-xs">
                        例字：</div>
                        <div class="md:text-base text-sm">{{ card.rel }}</div>
                    <template v-if="card._classZigen">
                        <div class="text-gray-500 text-sm mt-4 mb-2">
                            相似字根：</div>
                        <div v-for="c in card._classZigen" class="my-1">
                            <span :class="['opacity-100 text-xl mr-2', zigenFontClass, { 'text-red-400': !isCorrect, 'animate__headShake': !isCorrect }]">
                                {{ c.name }}
                            </span>
                            <span class="text-sm">{{ c.rel }}</span>

                        </div>
                    </template>
                </div>

                <div class=" tracking-widest pt-6 text-blue-600 dark:text-blue-300" v-if="'kind' in card && card.kind == 'b'">
                    五个基础笔画</div>
                <div class=" tracking-widest pt-6 text-blue-600 dark:text-blue-300" v-if="'kind' in card && card.kind == 'eb'">
                    25个二笔小码</div>
            </div>
        </div>
        <div class="flex justify-center p-5">
            <input id="input_el" type="text" placeholder="输入编码" v-model="userKeys" :class="['input w-half max-w-xs input-bordered text-center input-sm dark:bg-slate-800 bg-white', { 'input-error': !isCorrect }]" />
        </div>
        <div :class="['text-center', { 'opacity-0': !isFirst }]">答案是 <b class="font-mono">
                {{ card.key }}</b>
            <span :class="[zigenFontClass]" v-if="'comp' in card">
                （{{ card.comp }}）</span>
        </div>
    </CardLayout>
</template>
