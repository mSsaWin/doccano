<template>
  <v-menu :value="opened" :position-x="x" :position-y="y" absolute offset-y @input="close">
    <v-list dense min-width="200" max-height="500" class="overflow-y-auto">
      <v-list-item>
        <v-text-field
          v-model="searchQuery"
          :loading="isSearching"
          autofocus
          dense
          hide-details
          label="Search labels..."
          clearable
        />
      </v-list-item>
      <v-divider />
      <template v-if="showNoResults">
        <v-subheader>Результаты поиска</v-subheader>
        <v-list-item>
          <v-list-item-content>
            <v-list-item-title class="text-center grey--text">Не найдено</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
      </template>
      <template v-else-if="displayedListLabels.length > 0">
        <v-subheader>{{ searchQuery ? 'Результаты поиска' : 'Быстрый выбор' }}</v-subheader>
        <v-list-item
          v-for="(label, i) in displayedListLabels"
          :key="i"
          @click="onLabelSelected(label.id)"
        >
          <v-list-item-action v-if="hasAnySuffixKey">
            <v-chip
              v-if="label.suffixKey"
              :color="label.backgroundColor"
              outlined
              small
              v-text="label.suffixKey"
            />
            <span v-else class="mr-8" />
          </v-list-item-action>
          <v-list-item-content>
            <v-list-item-title v-text="label.text" />
          </v-list-item-content>
        </v-list-item>
      </template>
    </v-list>
  </v-menu>
</template>

<script lang="ts">
import Vue from 'vue'
export default Vue.extend({
  props: {
    labels: {
      type: Array,
      default: () => [],
      required: true
    },
    opened: {
      type: Boolean,
      default: false,
      required: true
    },
    selectedLabel: {
      type: Object,
      default: null,
      required: false
    },
    x: {
      type: Number,
      default: 0,
      required: true
    },
    y: {
      type: Number,
      default: 0,
      required: true
    },
    projectId: {
      type: String,
      required: false,
      default: null
    },
    labelService: {
      type: Object,
      required: false,
      default: null
    }
  },

  data() {
    return {
      startOffset: 0,
      endOffset: 0,
      entity: null as any,
      fromEntity: null as any,
      toEntity: null as any,
      searchQuery: '',
      searchResults: [] as any[],
      isSearching: false,
      searchTimeout: null as any
    }
  },

  computed: {
    hasAnySuffixKey(): boolean {
      return this.displayLabels.some((label: any) => label.suffixKey !== null)
    },

    displayLabels(): any[] {
      if (this.searchQuery && this.searchQuery.trim() !== '') {
        return this.searchResults
      }
      // Show first 100 labels by default when no search
      return this.labels.slice(0, 100)
    },

    displayedListLabels(): any[] {
      // Show top 10 in the list
      return this.displayLabels.slice(0, 10)
    },

    showNoResults(): boolean {
      // Show "Not found" only when searching and no results
      return !!(this.searchQuery && this.searchQuery.trim() !== '' && this.searchResults.length === 0 && !this.isSearching)
    },

  },

  watch: {
    searchQuery(newVal: string) {
      this.debouncedSearch(newVal)
    },
    opened(newVal: boolean) {
      if (newVal) {
        this.searchQuery = ''
        this.searchResults = []
      }
    }
  },

  methods: {
    close() {
      this.searchQuery = ''
      this.searchResults = []
      this.$emit('close')
    },

    onLabelSelected(labelId: number) {
      this.$emit('click:label', labelId)
      this.close()
    },

    debouncedSearch(query: string) {
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout)
      }

      if (!query || query.trim() === '') {
        this.searchResults = []
        this.isSearching = false
        return
      }

      this.isSearching = true
      this.searchTimeout = setTimeout(() => {
        this.performSearch(query)
      }, 300)
    },

    async performSearch(query: string) {
      try {
        // Use server-side search if available
        if (this.labelService && this.projectId) {
          const results = await this.labelService.search(this.projectId, query, 100)
          this.searchResults = results
        } else {
          // Fallback to local filtering (for backward compatibility)
          const lowerQuery = query.toLowerCase()
          this.searchResults = this.labels.filter((label: any) =>
            label.text.toLowerCase().includes(lowerQuery)
          ).slice(0, 100)
        }
      } catch (e) {
        console.error('Search failed, using local filter', e)
        // Fallback to local filtering on error
        const lowerQuery = query.toLowerCase()
        this.searchResults = this.labels.filter((label: any) =>
          label.text.toLowerCase().includes(lowerQuery)
        ).slice(0, 100)
      } finally {
        this.isSearching = false
      }
    }
  }
})
</script>