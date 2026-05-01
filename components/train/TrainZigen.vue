<script setup lang="ts">
import { provide, onMounted, shallowRef, computed } from "vue";
import { fetchJsonWithCache, cache, type ZigenCard } from "./share";
import { getSchemaNameFromRoute } from "../search/share";
import Train from "./basic/TrainCard.vue";
import MistakeCard from "./basic/MistakeCard.vue";

const p = defineProps<{
    /** 方案的ID, 通常为方案里 public 目录里的名称 ,省略则自动推断 */
    name?: string
    /** 字根练习的数据JSON文件的路径, 要加 /, 省略则自动根据URL推断 */
    zigenJson?: string,
    /** 字根的字体CSS名称, 默认是 欧体 */
    zigenFont?: string
    /** 是否训练小码,
     * 要确保 zigen.json 里有 secondary 字段,
     * 用于奕码 */
    trainSecondary?: boolean
    /**
     * 同时训练大小码模式，
     * 要确保 zigen.json 里有 secondary 字段,
     * 用于逸码 */
    trainBoth?: boolean
    /** 字根有归并信息 */
    hasClass?: boolean
}>()

provide("font", p.zigenFont)

const schemaName = getSchemaNameFromRoute()
const name = p.name || schemaName
const cardsName = `${name}_gen`
const realJsonName = (json: string | undefined, jsonMainName: string) => json ? json : `/${schemaName}/${jsonMainName}.json`

const rawCards = shallowRef<ZigenCard[]>(cache[cardsName])

onMounted(async () => {
    if (rawCards.value) return;
    const zgJson = await fetchJsonWithCache(realJsonName(p.zigenJson, 'zigen')) as ZigenCard[]
    if (p.trainSecondary) {
        rawCards.value = zgJson.filter(zg => 'secondary' in zg)
            .map(zg => ({ ...zg, key: zg.secondary! }))
    } else if (p.trainBoth) {
        rawCards.value = zgJson.filter(zg => 'secondary' in zg)
            .map(zg => ({ ...zg, key: zg.key + zg.secondary! }))
    } else {
        rawCards.value = zgJson
    }
    cache[cardsName] = rawCards.value
})

const cards = computed<ZigenCard[]>(() => {
    if (!rawCards.value) return []
    if (!p.hasClass) return rawCards.value

    const src = rawCards.value.map((c, i) => ({ ...c, _idx: i }))
    const mainCards: ZigenCard[] = []
    const mainCardsMap = new Map<string, ZigenCard>()
    const extraCards: ZigenCard[] = []
    for (const c of src) {
        if (!c.class || c.class === c.name) {
            mainCards.push(c)
            mainCardsMap.set(c.name, c)
        } else {
            extraCards.push(c)
        }
    }
    let hasError = false
    for (const c of extraCards) {
        const mainCard = mainCardsMap.get(c.class!)
        if (!mainCard) {
            console.error(`字根${c.name}的归类是「${c.class}」，但没有找到这个字根`)
            mainCards.push(c)
            mainCardsMap.set(c.name, c)
            hasError = true
            continue
        }
        if (mainCard._classZigen) mainCard._classZigen.push(c)
        else mainCard._classZigen = [c]
    }
    if (hasError) mainCards.sort((a, b) => a._idx! - b._idx!)
    return mainCards
})

const activeTab = shallowRef<'normal' | 'mistakes'>('normal')
</script>

<template>
    <div v-if="rawCards">
        <div class="tabs tabs-border mb-4">
            <button :class="['tab', { 'tab-active': activeTab === 'normal' }]" @click="activeTab = 'normal'">字根练习</button>
            <button :class="['tab', { 'tab-active': activeTab === 'mistakes' }]" @click="activeTab = 'mistakes'">错根复习</button>
        </div>
        <Train v-if="activeTab === 'normal'" :id="cardsName" :cards />
        <MistakeCard v-else :id="cardsName" :cards />
    </div>
    <h2 class="text-gray-700 text-center" v-else>
        下载数据中……
    </h2>
</template>