<template>
  <section class="handover-panel" data-testid="rescue-handover-panel">
    <div class="panel-head">
      <h3>抢录交接与续采</h3>
      <button class="link" type="button" data-testid="ho-toggle" @click="toggle">
        {{ expanded ? '收起' : '展开' }}
      </button>
    </div>

    <div v-if="expanded" class="handover-body">
      <form v-if="context === 'emer_rescue'" class="handover-form" data-testid="ho-open-form" @submit.prevent="openTask">
        <label>
          <span>抢救项目ID</span>
          <input v-model="openForm.rescueId" data-testid="ho-open-rescue-id" placeholder="已启动的抢救项目" />
        </label>
        <label>
          <span>采集任务ID</span>
          <input v-model="openForm.digitizationId" data-testid="ho-open-digitization-id" placeholder="数字化采集任务" />
        </label>
        <label>
          <span>片段数</span>
          <input v-model="openForm.segmentCount" data-testid="ho-open-segment-count" type="number" min="1" />
        </label>
        <label>
          <span>后续使用范围</span>
          <input v-model="openForm.usageScope" data-testid="ho-open-usage-scope" placeholder="默认取抢救方案" />
        </label>
        <button class="btn primary" data-testid="ho-open-submit" type="submit">开通交接任务</button>
      </form>

      <div class="handover-toolbar">
        <label class="handover-select">
          <span>交接号</span>
          <select v-model="selectedNo" data-testid="ho-task-select" @change="refreshTask">
            <option value="">请选择交接任务</option>
            <option v-for="item in tasks" :key="item.交接号" :value="item.交接号">
              {{ item.交接号 }}（{{ item.状态 }}）
            </option>
          </select>
        </label>
        <button class="btn" type="button" data-testid="ho-refresh" @click="loadTasks">刷新列表</button>
      </div>

      <div v-if="task" class="handover-view" data-testid="ho-task-view">
        <p class="handover-meta">
          状态：<strong data-testid="ho-task-status">{{ task.状态 }}</strong>
          ｜证据编号：<span data-testid="ho-evidence-no">{{ task.当前证据编号 || '—' }}</span>
        </p>
        <p class="handover-meta" data-testid="ho-usage-scope">
          已获准后续使用范围：{{ task.后续使用范围 || '—' }}
        </p>
        <p class="handover-meta" data-testid="ho-progress">
          交付进度：已交付 {{ task.已交付片段.length }} 段 / 共 {{ task.片段列表.length }} 段
          <span v-if="task.待办片段.length">｜待办片段：{{ task.待办片段.join('、') }}</span>
          <span v-else>｜待办片段：无</span>
        </p>

        <table class="data-table">
          <thead>
            <tr><th>片段号</th><th>状态</th><th>回执号</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="segment in task.片段列表" :key="segment.片段号" :data-testid="`ho-segment-${segment.片段号}`">
              <td>{{ segment.片段号 }}</td>
              <td>{{ segment.状态 }}</td>
              <td>{{ segment.回执号 || '—' }}</td>
              <td class="row-actions">
                <button
                  v-if="segment.状态 === '待采集'"
                  class="link"
                  type="button"
                  :data-testid="`ho-submit-${segment.片段号}`"
                  @click="submit(segment.片段号)"
                >提交片段</button>
                <button
                  v-if="segment.状态 === '传输完成'"
                  class="link"
                  type="button"
                  :data-testid="`ho-sign-${segment.片段号}`"
                  @click="sign(segment.片段号)"
                >补签回执</button>
                <button
                  v-if="segment.状态 === '已签收'"
                  class="link"
                  type="button"
                  :data-testid="`ho-resend-${segment.片段号}`"
                  @click="submit(segment.片段号)"
                >按旧号重发</button>
              </td>
            </tr>
          </tbody>
        </table>

        <div class="handover-lists">
          <div>
            <h4>签收回执</h4>
            <ul data-testid="ho-receipts">
              <li v-for="receipt in task.签收回执" :key="receipt.回执号">
                {{ receipt.回执号 }}（{{ receipt.片段号 }}，{{ receipt.签收归属 }}）
              </li>
              <li v-if="!task.签收回执.length" class="empty-state">暂无回执</li>
            </ul>
          </div>
          <div>
            <h4>原片保管记录</h4>
            <ul data-testid="ho-custody">
              <li v-for="record in task.保管记录" :key="record.保管记录号">
                {{ record.保管记录号 }}（{{ record.片段号 }}）
              </li>
              <li v-if="!task.保管记录.length" class="empty-state">暂无保管记录</li>
            </ul>
          </div>
        </div>

        <div v-if="context === 'emer_rescue'" class="handover-actions">
          <button class="btn accent" type="button" data-testid="ho-issue-commission" @click="issue">
            签发续采证据委托单
          </button>
          <p v-if="commission" class="handover-meta" data-testid="ho-commission">
            委托单号：{{ commission.委托单号 }} ｜证据编号：{{ commission.证据编号 }}
            ｜待办片段：{{ commission.待办片段.join('、') || '无' }}
          </p>
        </div>

        <form v-if="context === 'digitization'" class="handover-form" data-testid="ho-reenter-form" @submit.prevent="reenter">
          <label>
            <span>续采证据委托单号</span>
            <input v-model="commissionNo" data-testid="ho-commission-no" placeholder="CM-交接号-序号" />
          </label>
          <button class="btn primary" data-testid="ho-reenter" type="submit">凭单重新进入</button>
        </form>
      </div>

      <p v-if="message" class="handover-message" data-testid="ho-message">{{ message }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'

import {
  getHandover,
  issueCommission,
  listHandoverTasks,
  openHandover,
  reenterHandover,
  signSegment,
  submitSegment,
  type Commission,
  type HandoverTask,
} from '@/api/rescue-handover'

defineProps<{ context: string }>()

const expanded = ref(false)
const tasks = ref<HandoverTask[]>([])
const selectedNo = ref('')
const task = ref<HandoverTask | null>(null)
const commission = ref<Commission | null>(null)
const commissionNo = ref('')
const message = ref('')
const openForm = ref({ rescueId: '', digitizationId: '', segmentCount: 2, usageScope: '' })

function toggle() {
  expanded.value = !expanded.value
  if (expanded.value) void loadTasks()
}

async function guard(action: () => Promise<void>) {
  message.value = ''
  try {
    await action()
  } catch (error) {
    message.value = error instanceof Error ? error.message : '操作失败'
  }
}

async function loadTasks() {
  await guard(async () => {
    tasks.value = await listHandoverTasks()
    if (selectedNo.value) await refreshTask()
  })
}

async function refreshTask() {
  if (!selectedNo.value) {
    task.value = null
    return
  }
  await guard(async () => {
    task.value = await getHandover(selectedNo.value)
  })
}

async function openTask() {
  await guard(async () => {
    const result = await openHandover(
      Number(openForm.value.rescueId),
      Number(openForm.value.digitizationId),
      Number(openForm.value.segmentCount) || 1,
      openForm.value.usageScope,
    )
    message.value = result.message
    selectedNo.value = result.task.交接号
    await loadTasks()
  })
}

async function issue() {
  if (!task.value) return
  await guard(async () => {
    const result = await issueCommission(task.value!.交接号, task.value!.抢救项目ID)
    commission.value = result.commission
    message.value = result.message
    await refreshTask()
  })
}

async function reenter() {
  if (!task.value) return
  await guard(async () => {
    const result = await reenterHandover(task.value!.交接号, commissionNo.value.trim())
    message.value = `已重新进入，证据编号 ${result.证据编号}`
    await refreshTask()
  })
}

async function submit(segmentNo: string) {
  if (!task.value) return
  await guard(async () => {
    const result = await submitSegment(task.value!.交接号, segmentNo)
    message.value = result.message
    await refreshTask()
  })
}

async function sign(segmentNo: string) {
  if (!task.value) return
  await guard(async () => {
    const result = await signSegment(task.value!.交接号, segmentNo)
    message.value = result.message
    await refreshTask()
  })
}
</script>
