import request from './request'

export const healthApi = {
  dashboard: (petId: number) =>
    request.get('/health/dashboard', { params: { petId } }),

  addRecord: (data: {
    petId: number; date?: string; heartRate?: number; sleepHours?: number;
    steps?: number; calories?: number; exercise?: number; weight?: number;
    waterIntake?: number; mood?: string
  }) => request.post('/health/record/add', data),

  recordListPage: (data: { petId: number; current?: number; pageSize?: number; startDate?: string; endDate?: string }) =>
    request.post('/health/record/list/page', data),

  weekly: (petId: number) =>
    request.get('/health/record/weekly', { params: { petId } }),

  addPlan: (data: {
    petId: number; type: string; title: string; time?: string;
    frequency?: string; standard?: string; standardValue?: number; notes?: string
  }) => request.post('/health/plan/add', data),

  editPlan: (data: {
    id: number; type?: string; title?: string; time?: string;
    frequency?: string; standard?: string; standardValue?: number; notes?: string; isActive?: number
  }) => request.post('/health/plan/edit', data),

  deletePlan: (id: number) =>
    request.post('/health/plan/delete', { id }),

  planListPage: (data: { petId: number; current?: number; pageSize?: number; type?: string; isActive?: number }) =>
    request.post('/health/plan/list/page', data),
}
