import { shallowRef, computed } from 'vue'
import { useLocalStorage } from '@vueuse/core'
import type { HanziCard } from '../share'

/** 必拆字专用的练习进度管理：
 * - 每张卡只要答对一次即算「已掌握」。
 * - 记录每张卡的错误次数，用于错拆复习。
 * - 队列从头到尾线性推进，答错的卡延后再出现。
 */
export function useBichai(id: string, cards: readonly HanziCard[]) {
    const cardLength = cards.length

    /** 0 = 未掌握，1 = 已掌握 */
    const statusRef = useLocalStorage<number[]>(
        `yima_${id}_bichai_status`,
        () => Array.from({ length: cardLength }, () => 0),
    )
    /** 每张卡累计的错误次数 */
    const mistakesRef = useLocalStorage<number[]>(
        `yima_${id}_bichai_mistakes`,
        () => Array.from({ length: cardLength }, () => 0),
    )

    // 卡片数量变化时对齐
    const alignLength = (arr: number[]) => {
        if (arr.length < cardLength) {
            for (let i = arr.length; i < cardLength; i++) arr.push(0)
        } else if (arr.length > cardLength) {
            arr.length = cardLength
        }
    }
    alignLength(statusRef.value)
    alignLength(mistakesRef.value)

    /** 还没掌握的卡索引队列，按原顺序推进 */
    const pendingQueue = shallowRef<number[]>(
        Array.from({ length: cardLength }, (_, i) => i).filter(i => !statusRef.value[i]),
    )

    const progress = computed(() => statusRef.value.reduce((s, v) => s + (v ? 1 : 0), 0))
    const currentIndex = computed(() => pendingQueue.value[0])
    const card = computed<HanziCard | undefined>(() =>
        currentIndex.value == null ? undefined : cards[currentIndex.value],
    )

    const answer = (correct: boolean) => {
        const idx = pendingQueue.value[0]
        if (idx == null) return

        if (correct) {
            statusRef.value[idx] = 1
            pendingQueue.value = pendingQueue.value.slice(1)
        } else {
            mistakesRef.value[idx] += 1
            // 答错不换卡：保留在队首，让提示对应当前这张，重输正确才前进
        }
    }

    const restart = () => {
        statusRef.value = Array.from({ length: cardLength }, () => 0)
        mistakesRef.value = Array.from({ length: cardLength }, () => 0)
        pendingQueue.value = Array.from({ length: cardLength }, (_, i) => i)
    }

    const clearMistakes = () => {
        mistakesRef.value = Array.from({ length: cardLength }, () => 0)
    }

    return {
        progress,
        card,
        currentIndex,
        answer,
        restart,
        clearMistakes,
        status: statusRef,
        mistakes: mistakesRef,
    }
}
