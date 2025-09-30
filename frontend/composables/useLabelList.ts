import { computed, reactive } from '@nuxtjs/composition-api'
import { LabelDTO } from '@/services/application/label/labelData'
import { CreateLabelCommand, UpdateLabelCommand } from '@/services/application/label/labelCommand'
import { LabelApplicationService } from '@/services/application/label/labelApplicationService'

export const useLabelList = (service: LabelApplicationService) => {
  const state = reactive({
    labels: [] as LabelDTO[],
    popularLabels: [] as LabelDTO[],
    isLoading: false,
    searchQuery: ''
  })

  const getLabelList = async (projectId: string, options?: any) => {
    state.isLoading = true
    try {
      state.labels = await service.list(projectId, options)
    } finally {
      state.isLoading = false
    }
  }
  
  const getPopularLabels = async (projectId: string, limit: number = 50) => {
    try {
      const popular = await service.listPopular(projectId, limit)
      state.popularLabels = popular
      state.labels = popular
      
      // If popular labels are empty, fallback to regular list
      if (popular.length === 0) {
        state.labels = await service.list(projectId, { limit })
      }
    } catch (e) {
      console.error('Failed to load popular labels', e)
      // Fallback to regular list
      try {
        state.labels = await service.list(projectId, { limit })
      } catch (fallbackError) {
        console.error('Fallback list also failed', fallbackError)
        state.labels = []
      }
    }
  }
  
  const searchLabels = async (projectId: string, query: string, limit: number = 50) => {
    state.searchQuery = query
    state.isLoading = true
    try {
      state.labels = await service.search(projectId, query, limit)
    } finally {
      state.isLoading = false
    }
  }

  const createLabel = async (projectId: string, command: CreateLabelCommand) => {
    await service.create(projectId, command)
    await getLabelList(projectId)
  }

  const updateLabel = async (projectId: string, command: UpdateLabelCommand) => {
    await service.update(projectId, command)
  }

  const deleteLabelList = async (projectId: string, items: LabelDTO[]) => {
    await service.bulkDelete(projectId, items)
    await getLabelList(projectId)
  }

  const findLabelById = (labelId: number) => {
    return state.labels.find((item) => item.id === labelId)
  }

  const shortKeys = computed(() => {
    return Object.fromEntries(state.labels.map((item) => [item.id, [item.suffixKey]]))
  })

  return {
    state,
    getLabelList,
    getPopularLabels,
    searchLabels,
    findLabelById,
    createLabel,
    updateLabel,
    deleteLabelList,
    shortKeys
  }
}
