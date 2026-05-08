---
aside: false
---
<script setup>
import Train from "../components/train/TrainBichaiLoader.vue"
</script>

# 琉璃必拆字练习

必拆字练的是拆字能力，所以不要求速度能到多少，过完 3 遍必拆字后，再开始下一步。

<Train zigenFont="ChaiPUA-0.2.7" name="liuli" chaiJson="/liuli/bichai.json"/>

:::info 提示
必拆字指没有简码、必须打全码的字。含两类：
1. 单根字（字根字），需要打「字根大码 + 字根小码 + 字根小码」。
2. 二根字，需要打「首根大码 + 末根大码 + 末根小码」，注意末字根。

练习规则：
1. 答对一次即算已掌握，不再重复。
2. 答错会留在当前字并显示提示，重新输对才前进；该字同时被记入「错拆复习」。
3. 空格键 = 认输，直接显示答案。
4. 切换到「错拆复习」可以单独定向练习答错过的字；本轮有任一错次的字会继续留在统计里，一次性答对的才会被清掉。
:::
