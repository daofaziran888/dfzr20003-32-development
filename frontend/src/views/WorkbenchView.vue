<template>
  <section class="page" :data-module="meta.key">
    <header class="page-head">
      <div>
        <h2>{{ meta.name }}</h2>
        <p class="page-desc">{{ meta.desc }}</p>
      </div>
      <div class="page-actions">
        <button class="btn primary" data-testid="open-create" type="button" @click="openCreate">
          登记{{ meta.entity }}
        </button>
        <button class="btn" data-testid="export" type="button" @click="exportRows">
          导出{{ meta.name }}清单
        </button>
        <button v-if="showHeritageChainButton" class="btn accent" data-testid="heritage-chain" type="button" @click="loadHeritageChain">
          传承链追溯
        </button>
      </div>
    </header>

    <div class="stat-row">
      <article v-for="item in stats" :key="item.label" class="stat-card">
        <span class="stat-label">{{ item.label }}</span>
        <strong class="stat-value">{{ item.value }}</strong>
      </article>
    </div>

    <p class="status-legend">
      <span v-for="item in statusSummary" :key="item.status" class="legend-item">
        {{ item.status }}：{{ item.count }}
      </span>
    </p>

    <form class="filter-bar" @submit.prevent="reload">
      <label v-for="field in filterFields" :key="field" class="filter-item">
        <span>{{ field }}</span>
        <input v-model="filters[field]" :data-testid="`filter-${field}`" :placeholder="`按${field}检索`" />
      </label>
      <button class="btn" data-testid="query" type="submit">查询</button>
      <button class="btn ghost" data-testid="reset" type="button" @click="resetFilters">重置条件</button>
    </form>

    <table class="data-table">
      <thead>
        <tr>
          <th v-for="column in meta.fields" :key="column">{{ column }}</th>
          <th>当前状态</th>
          <th>可执行动作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="String(row.id)" :data-testid="`row-${row.id}`" :data-status="String(row.status)">
          <td v-for="column in meta.fields" :key="column">{{ row[column] ?? '—' }}</td>
          <td>{{ row.status }}</td>
          <td class="row-actions">
            <button
              v-for="action in meta.actions"
              :key="action"
              class="link"
              type="button"
              :data-testid="`action-${row.id}-${action}`"
              @click="runAction(action, row)"
            >
              {{ action }}
            </button>
          </td>
        </tr>
        <tr v-if="!rows.length">
          <td :colspan="meta.fields.length + 2" class="empty-state">
            暂无{{ meta.name }}数据，可先登记{{ meta.entity }}
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="showCreate" class="modal-backdrop" data-testid="create-modal">
      <form class="modal" @submit.prevent="submitCreate">
        <h3>登记{{ meta.entity }}</h3>
        <label v-for="field in meta.fields" :key="field" class="create-field">
          <span>{{ field }}</span>
          <input v-model="createValues[field]" :data-testid="`create-${field}`" required />
        </label>
        <div class="page-actions">
          <button class="btn" type="button" @click="showCreate = false">取消</button>
          <button class="btn primary" data-testid="submit-create" type="submit" :disabled="creating">
            {{ creating ? '提交中…' : '确认登记' }}
          </button>
        </div>
      </form>
    </div>

    <footer class="page-foot">
      <span>共 {{ total }} 条{{ meta.name }}记录</span>
      <span v-if="errorMessage" class="error-text">{{ errorMessage }}</span>
      <span v-if="crossRefInfo" class="cross-ref-info">{{ crossRefInfo }}</span>
    </footer>

    <!-- 跨模块传承链面板 -->
    <aside v-if="showHeritagePanel" class="heritage-panel" data-testid="heritage-panel">
      <div class="panel-head">
        <h3>技艺传承链</h3>
        <button class="link" type="button" @click="showHeritagePanel = false">收起</button>
      </div>
      <div v-if="chainLoading" class="panel-loading">加载传承链中…</div>
      <div v-else-if="chainError" class="error-text">{{ chainError }}</div>
      <div v-else class="chain-display">
        <div class="chain-section" v-for="node in chainNodes" :key="node.id">
          <span class="chain-type-badge" :data-type="node.type">{{ node.type === 'craft_category' ? '门类' : node.type === 'artisan' ? '传承人' : node.type === 'apprentice' ? '学徒' : node.type === 'skill_card' ? '技艺' : node.type === 'creation_work' ? '作品' : node.type }}</span>
          <span class="chain-label">{{ node.label }}</span>
          <span v-if="node.data && node.data.status" class="chain-status" :data-status="node.data.status">{{ node.data.status }}</span>
        </div>
        <div v-if="!chainNodes.length" class="empty-state">暂无传承链数据，请先建立跨模块引用</div>
        <div class="chain-edges" v-if="chainEdges.length">
          <div class="edge-item" v-for="(edge, idx) in chainEdges" :key="idx">
            {{ edge.from }} → {{ edge.to }}: {{ edge.label }}
          </div>
        </div>
      </div>
    </aside>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import {
  createEntry,
  downloadEntries,
  listEntries,
  moduleMeta,
  runAction as applyAction,
} from '@/api/backend-service'
import { fetchJson } from '@/api/client'
import type { EntryRow } from '@/data/types'

const props = defineProps<{ moduleKey: string }>()
const meta = moduleMeta(props.moduleKey)
const rows = ref<EntryRow[]>([])
const total = ref(0)
const errorMessage = ref('')
const filters = ref<Record<string, string>>({})
const filterFields = meta.fields.slice(0, 3)
const showCreate = ref(false)
const creating = ref(false)
const createValues = ref<Record<string, string>>({})

// 跨模块显示
const crossRefInfo = ref('')
const showHeritagePanel = ref(false)
const chainLoading = ref(false)
const chainError = ref('')
const chainNodes = ref<any[]>([])
const chainEdges = ref<any[]>([])

const showHeritageChainButton = computed(() =>
  ['skill_card', 'artisan'].includes(meta.key)
)
const stats = computed(() => [
  { label: meta.metrics[0], value: total.value },
  { label: meta.metrics[1], value: rows.value.filter((row) => row.status === meta.statuses[1]).length },
  {
    label: meta.metrics[2],
    value: rows.value.filter((row) => row.status === meta.statuses[meta.statuses.length - 1]).length,
  },
])
const statusSummary = computed(() =>
  meta.statuses.map((status) => ({
    status,
    count: rows.value.filter((row) => String(row.status) === status).length,
  })),
)

function resetFilters() {
  filters.value = {}
  void reload()
}

async function exportRows() {
  errorMessage.value = ''
  try {
    await downloadEntries(meta.key, filters.value)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '导出失败'
  }
}

function openCreate() {
  createValues.value = Object.fromEntries(meta.fields.map((field) => [field, '']))
  errorMessage.value = ''
  showCreate.value = true
}

async function submitCreate() {
  creating.value = true
  errorMessage.value = ''
  try {
    const result = await createEntry(meta.key, createValues.value)
    if (!result.ok) throw new Error(result.message)
    showCreate.value = false
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '登记失败'
  } finally {
    creating.value = false
  }
}

async function runAction(action: string, row: EntryRow) {
  errorMessage.value = ''
  try {
    const result = await applyAction(meta.key, Number(row.id), action)
    if (!result.ok) throw new Error(result.message)
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '操作失败'
  }
}

async function loadHeritageChain() {
  showHeritagePanel.value = !showHeritagePanel.value
  if (!showHeritagePanel.value) return
  chainLoading.value = true
  chainError.value = ''
  try {
    const params = new URLSearchParams()
    if (meta.key === 'skill_card' && rows.value.length > 0) {
      params.set('skill_card_id', String((rows.value[0] as any).id || 1))
    } else if (meta.key === 'artisan' && rows.value.length > 0) {
      params.set('artisan_id', String((rows.value[0] as any).id || 1))
    }
    const data = await fetchJson<any>(`/api/cross/heritage-chain?${params.toString()}`)
    const chain = data.chain || data
    chainNodes.value = chain.nodes || []
    chainEdges.value = chain.edges || []
  } catch (e: any) {
    chainError.value = e?.message || '传承链加载失败'
  } finally {
    chainLoading.value = false
  }
}

async function reload() {
  errorMessage.value = ''
  try {
    const payload = await listEntries(meta.key, filters.value)
    rows.value = payload.items
    total.value = payload.total
    // 显示跨模块引用提示
    loadCrossRefInfo()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '业务列表读取失败'
  }
}

async function loadCrossRefInfo() {
  try {
    const data = await fetchJson<any>('/api/cross/overview-refs')
    const links = data.cross_links
    if (!links) return
    const infoParts: string[] = []
    if (meta.key === 'artisan' && links.artisan_with_category !== undefined) infoParts.push(`${links.artisan_with_category} 位传承人已关联门类`)
    if (meta.key === 'apprentice' && links.apprentice_with_artisan !== undefined) infoParts.push(`${links.apprentice_with_artisan} 位学徒已关联师傅`)
    if (meta.key === 'skill_card' && links.skill_card_with_category !== undefined) infoParts.push(`${links.skill_card_with_category} 项技艺已归入门类`)
    if (meta.key === 'raw_material' && links.raw_material_with_skill !== undefined) infoParts.push(`${links.raw_material_with_skill} 批原料已关联技艺`)
    if (meta.key === 'tooling' && links.tooling_with_skill !== undefined) infoParts.push(`${links.tooling_with_skill} 件工具已关联技艺`)
    if (meta.key === 'creation_work' && links.creation_work_with_relations !== undefined) infoParts.push(`${links.creation_work_with_relations} 件作品已关联技艺和传承人`)
    if (meta.key === 'authentication' && links.authentication_with_work !== undefined) infoParts.push(`${links.authentication_with_work} 条认证已关联作品`)
    crossRefInfo.value = infoParts.length ? '跨模块引用: ' + infoParts.join('；') : ''
  } catch {
    crossRefInfo.value = ''
  }
}

onMounted(reload)
</script>
