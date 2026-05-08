---
aside: false
---
<script setup>
import Train from "../components/train/TrainHanzi.vue"
</script>

# 琉璃必拆字练习

必拆字练的是拆字能力，所以不要求速度能到多少，过完 3 遍必拆字后，再开始下一步。

<Train zigenFont="ChaiPUA-0.2.7" name="liuli-bichai" chaiJson="/liuli/bichai.json" zigenJson="/liuli/zigen.json"/>

:::info 提示
必拆字指没有简码、必须打全码的字。含两类：
1. 单根字（字根字），需要打「字根大码 + 字根小码 + 字根小码」。
2. 二根字，需要打「首根大码 + 末根大码 + 末根小码」，注意末字根。

练习建议：
1. 按对会自动跳下一个。
2. 按错会很快重复出现。
3. 五秒内想不起来就按空格。
:::
