import ApiService from '@/services/api.service'
import { LabelRepository } from '@/domain/models/label/labelRepository'
import { LabelItem } from '@/domain/models/label/label'

function toModel(item: { [key: string]: any }): LabelItem {
  return new LabelItem(
    item.id,
    item.text,
    item.prefix_key,
    item.suffix_key,
    item.background_color,
    item.text_color
  )
}

function toPayload(item: LabelItem): { [key: string]: any } {
  return {
    id: item.id,
    text: item.text,
    prefix_key: item.prefixKey,
    suffix_key: item.suffixKey,
    background_color: item.backgroundColor,
    text_color: item.textColor
  }
}

export interface LabelListOptions {
  limit?: number
  offset?: number
  search?: string
  ordering?: string
  no_page?: boolean
}

export class APILabelRepository implements LabelRepository {
  constructor(private readonly baseUrl = 'label', private readonly request = ApiService) {}

  async list(projectId: string, options?: LabelListOptions): Promise<LabelItem[]> {
    const url = `/projects/${projectId}/${this.baseUrl}s`
    const params: any = {}
    
    if (options) {
      if (options.limit !== undefined) params.limit = options.limit
      if (options.offset !== undefined) params.offset = options.offset
      if (options.search) params.q = options.search
      if (options.ordering) params.ordering = options.ordering
      if (options.no_page) params.no_page = 'true'
    }
    
    const response = await this.request.get(url, { params })
    
    // Handle paginated response
    if (response.data.results) {
      return response.data.results.map((item: { [key: string]: any }) => toModel(item))
    }
    
    // Handle non-paginated response
    return response.data.map((item: { [key: string]: any }) => toModel(item))
  }
  
  async listPopular(projectId: string, limit: number = 50): Promise<LabelItem[]> {
    const url = `/projects/${projectId}/${this.baseUrl}s/popular`
    const response = await this.request.get(url, { params: { limit } })
    return response.data.map((item: { [key: string]: any }) => toModel(item))
  }
  
  async search(projectId: string, query: string, limit: number = 50): Promise<LabelItem[]> {
    return await this.list(projectId, { search: query, limit, ordering: '-usage_count,text' })
  }

  async findById(projectId: string, labelId: number): Promise<LabelItem> {
    const url = `/projects/${projectId}/${this.baseUrl}s/${labelId}`
    const response = await this.request.get(url)
    return toModel(response.data)
  }

  async create(projectId: string, item: LabelItem): Promise<LabelItem> {
    const url = `/projects/${projectId}/${this.baseUrl}s`
    const payload = toPayload(item)
    const response = await this.request.post(url, payload)
    return toModel(response.data)
  }

  async update(projectId: string, item: LabelItem): Promise<LabelItem> {
    const url = `/projects/${projectId}/${this.baseUrl}s/${item.id}`
    const payload = toPayload(item)
    const response = await this.request.patch(url, payload)
    return toModel(response.data)
  }

  async bulkDelete(projectId: string, labelIds: number[]): Promise<void> {
    const url = `/projects/${projectId}/${this.baseUrl}s`
    await this.request.delete(url, { ids: labelIds })
  }

  async uploadFile(projectId: string, payload: FormData): Promise<void> {
    const url = `/projects/${projectId}/${this.baseUrl}-upload`
    const config = {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }
    try {
      await this.request.post(url, payload, config)
    } catch (e: any) {
      const data = e.response.data
      if ('detail' in data) {
        throw new Error(data.detail)
      } else {
        throw new Error('Text field is required')
      }
    }
  }
  
  async listAll(projectId: string): Promise<LabelItem[]> {
    return await this.list(projectId, { no_page: true })
  }
}
