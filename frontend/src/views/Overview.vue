<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，先看总量再看异常。</p>
      </div>
    </header>
    <div class="stat-row">
      <article v-for="card in cards" :key="card.label" class="stat-card">
        <span class="stat-label">{{ card.label }}</span>
        <strong class="stat-value">{{ card.value }}</strong>
      </article>
    </div>
    <table class="data-table">
      <thead>
        <tr><th>业务模块</th><th>今日新增</th><th>待处理</th><th>异常量</th></tr>
      </thead>
      <tbody>
        <tr v-for="row in moduleRows" :key="row.name">
          <td>{{ row.name }}</td>
          <td>{{ row.created }}</td>
          <td>{{ row.pending }}</td>
          <td>{{ row.abnormal }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchJson } from '@/api/client'

type Overview = {
  cards: { label: string; value: number }[]
  modules: { name: string; created: number; pending: number; abnormal: number }[]
}

const cards = ref<Overview['cards']>([])
const moduleRows = ref<Overview['modules']>([])

onMounted(async () => {
  try {
    const payload = await fetchJson<Overview>('/api/overview')
    cards.value = payload.cards
    moduleRows.value = payload.modules
  } catch {
    cards.value = [{"label": "业务模块", "value": 0}, {"label": "今日新增", "value": 0}]
    moduleRows.value = [{"name": "技艺分类", "created": 0, "pending": 0, "abnormal": 0}, {"name": "传承人档案", "created": 0, "pending": 0, "abnormal": 0}, {"name": "学徒培养", "created": 0, "pending": 0, "abnormal": 0}, {"name": "技艺图谱", "created": 0, "pending": 0, "abnormal": 0}, {"name": "原材料管理", "created": 0, "pending": 0, "abnormal": 0}, {"name": "工具器械", "created": 0, "pending": 0, "abnormal": 0}, {"name": "传习所管理", "created": 0, "pending": 0, "abnormal": 0}, {"name": "培训方案", "created": 0, "pending": 0, "abnormal": 0}, {"name": "作品创作", "created": 0, "pending": 0, "abnormal": 0}, {"name": "作品认证", "created": 0, "pending": 0, "abnormal": 0}, {"name": "展览策划", "created": 0, "pending": 0, "abnormal": 0}, {"name": "资助经费", "created": 0, "pending": 0, "abnormal": 0}, {"name": "田野调查", "created": 0, "pending": 0, "abnormal": 0}, {"name": "数字化采集", "created": 0, "pending": 0, "abnormal": 0}, {"name": "出版成果", "created": 0, "pending": 0, "abnormal": 0}, {"name": "知识产权", "created": 0, "pending": 0, "abnormal": 0}, {"name": "传承评估", "created": 0, "pending": 0, "abnormal": 0}, {"name": "濒危抢救", "created": 0, "pending": 0, "abnormal": 0}]
  }
})
</script>
