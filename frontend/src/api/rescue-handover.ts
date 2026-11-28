/** 抢录交接接口封装：交接任务、续采证据委托单、片段签收与查核。 */
import { fetchJson, request } from './client'

export type HandoverSegment = {
  片段号: string
  交接号: string
  序号: number
  状态: string
  回执号: string | null
}

export type HandoverTask = {
  交接号: string
  抢救项目ID: number
  采集任务ID: number
  状态: string
  当前证据编号: string | null
  后续使用范围: string
  片段列表: HandoverSegment[]
  待办片段: string[]
  已交付片段: string[]
  签收回执: { 回执号: string; 片段号: string; 签收归属: string }[]
  保管记录: { 保管记录号: string; 片段号: string; 保管人: string }[]
  交付进度: { 已交付片段: string[]; 待办片段: string[]; 持久保存: boolean } | null
}

export type Commission = {
  委托单号: string
  证据编号: string
  交接号: string
  状态: string
  待办片段: string[]
}

async function postJson<T>(path: string, body: unknown): Promise<T & { ok: boolean; message: string }> {
  const response = await request(path, { method: 'POST', body: JSON.stringify(body) })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data?.detail || `接口返回 ${response.status}`)
  }
  return data
}

export async function listHandoverTasks(): Promise<HandoverTask[]> {
  const data = await fetchJson<{ tasks: HandoverTask[] }>('/api/rescue-handover/tasks')
  return data.tasks || []
}

export function openHandover(rescueId: number, digitizationId: number, segmentCount: number, usageScope: string) {
  return postJson<{ task: HandoverTask }>('/api/rescue-handover/open', {
    rescue_id: rescueId,
    digitization_id: digitizationId,
    segment_count: segmentCount,
    usage_scope: usageScope || null,
  })
}

export async function getHandover(handoverNo: string): Promise<HandoverTask> {
  const data = await fetchJson<{ task: HandoverTask }>(`/api/rescue-handover/${encodeURIComponent(handoverNo)}`)
  return data.task
}

export function issueCommission(handoverNo: string, rescueId: number) {
  return postJson<{ commission: Commission }>(`/api/rescue-handover/${encodeURIComponent(handoverNo)}/commission`, {
    rescue_id: rescueId,
  })
}

export function reenterHandover(handoverNo: string, commissionNo: string) {
  return postJson<{ task: HandoverTask; 证据编号: string }>(`/api/rescue-handover/${encodeURIComponent(handoverNo)}/reenter`, {
    commission_no: commissionNo,
  })
}

export function submitSegment(handoverNo: string, segmentNo: string) {
  return postJson<{ receipt: { 回执号: string } }>(`/api/rescue-handover/${encodeURIComponent(handoverNo)}/segments/submit`, {
    segment_no: segmentNo,
  })
}

export function transmitSegment(handoverNo: string, segmentNo: string) {
  return postJson(`/api/rescue-handover/${encodeURIComponent(handoverNo)}/segments/transmit`, {
    segment_no: segmentNo,
  })
}

export function signSegment(handoverNo: string, segmentNo: string) {
  return postJson<{ receipt: { 回执号: string } }>(`/api/rescue-handover/${encodeURIComponent(handoverNo)}/segments/sign`, {
    segment_no: segmentNo,
  })
}

export async function getUsageScope(handoverNo: string): Promise<string> {
  const data = await fetchJson<{ 后续使用范围: string }>(`/api/rescue-handover/${encodeURIComponent(handoverNo)}/usage-scope`)
  return data.后续使用范围
}
