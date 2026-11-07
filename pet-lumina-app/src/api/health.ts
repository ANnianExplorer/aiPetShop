import request from './request'
import type { HealthPlan, PageResult, PetHealthData } from '@/types'

export const healthApi = {
  dashboard: (petId: string | number): Promise<PetHealthData> =>
    request.get<PetHealthData>('/health/dashboard', { params: { petId: String(petId) } }),

  addRecord: (data: {
    petId: string | number; date?: string; heartRate?: number; sleepHours?: number;
    steps?: number; calories?: number; exercise?: number; weight?: number;
    waterIntake?: number; mood?: string
  }): Promise<string> => request.post<string>('/health/record/add', data),

  recordListPage: (data: { petId: string | number; current?: number; pageSize?: number; startDate?: string; endDate?: string }): Promise<PageResult<PetHealthData>> =>
    request.post<PageResult<PetHealthData>>('/health/record/list/page', data),

  weekly: (petId: string | number): Promise<PetHealthData[]> =>
    request.get<PetHealthData[]>('/health/record/weekly', { params: { petId: String(petId) } }),

  addPlan: (data: {
    petId: string | number; type: string; title: string; time?: string;
    frequency?: string; standard?: string; standardValue?: number; notes?: string
  }): Promise<string> => request.post<string>('/health/plan/add', data),

  editPlan: (data: {
    id: string | number; type?: string; title?: string; time?: string;
    frequency?: string; standard?: string; standardValue?: number; notes?: string; isActive?: number
  }): Promise<boolean> => request.post<boolean>('/health/plan/edit', data),

  deletePlan: (id: string | number): Promise<boolean> =>
    request.post<boolean>('/health/plan/delete', { id }),

  planListPage: (data: { petId: string | number; current?: number; pageSize?: number; type?: string; isActive?: number }): Promise<PageResult<HealthPlan>> =>
    request.post<PageResult<HealthPlan>>('/health/plan/list/page', data),
}
