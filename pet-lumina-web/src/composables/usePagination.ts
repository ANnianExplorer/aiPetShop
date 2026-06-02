import { ref } from 'vue'

export function usePagination(fetchFn: () => Promise<void>) {
  const currentPage = ref(1)
  const pageSize = ref(10)
  const total = ref(0)

  const handleCurrentChange = (page: number) => {
    currentPage.value = page
    fetchFn()
  }

  const handleSizeChange = (size: number) => {
    pageSize.value = size
    currentPage.value = 1
    fetchFn()
  }

  return { currentPage, pageSize, total, handleCurrentChange, handleSizeChange }
}
