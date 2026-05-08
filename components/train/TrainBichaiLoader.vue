<script setup lang="ts">
/** 必拆字练习加载器：fetch JSON，传给 TrainBichai。 */
import { shallowRef, onMounted, provide } from 'vue'
import { HanziCard, cache, fetchJsonWithCache } from './share'
import TrainBichai from './bichai/TrainBichai.vue'

const p = defineProps<{
    name: string
    /** 必拆字数据 JSON，要求含 name/key/comp/rootKeys */
    chaiJson: string
    zigenFont?: string
    high?: string
}>()

provide('font', p.zigenFont)
provide('high', new Set(p.high))

const cardsName = p.name + '_bichai'
const cards = shallowRef<HanziCard[]>(cache[cardsName])

onMounted(async () => {
    if (cards.value) return
    const list = await fetchJsonWithCache(p.chaiJson) as HanziCard[]
    cache[cardsName] = list
    cards.value = list
})
</script>

<template>
    <TrainBichai v-if="cards" :name="cardsName" :cards />
    <h2 class="text-gray-700" v-else>下载数据中……</h2>
</template>
