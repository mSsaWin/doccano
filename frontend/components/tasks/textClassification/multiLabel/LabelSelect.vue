<template>
  <v-autocomplete
    v-model="annotatedLabels"
    chips
    :items="displayLabels"
    :loading="isSearching"
    :search-input.sync="search"
    item-text="text"
    item-value="id"
    hide-details
    hide-selected
    multiple
    class="pt-0"
    label="Search and select labels..."
    no-filter
    return-object
    @change="onLabelsChange"
  >
    <template #selection="{ attrs, item, select, selected }">
      <v-chip
        v-bind="attrs"
        :input-value="selected"
        :color="item.backgroundColor"
        :text-color="$contrastColor(item.backgroundColor)"
        close
        @click="select"
        @click:close="remove(item)"
      >
        <v-avatar v-if="item.suffixKey" left color="white" class="black--text font-weight-bold">
          {{ item.suffixKey }}
        </v-avatar>
        {{ item.text }}
      </v-chip>
    </template>
    <template #item="{ item }">
      <v-chip :color="item.backgroundColor" :text-color="$contrastColor(item.backgroundColor)">
        <v-avatar v-if="item.suffixKey" left color="white" class="black--text font-weight-bold">
          {{ item.suffixKey }}
        </v-avatar>
        {{ item.text }}
      </v-chip>
    </template>
  </v-autocomplete>
</template>

<script>
export default {
  props: {
    labels: {
      type: Array,
      default: () => [],
      required: true
    },
    annotations: {
      type: Array,
      default: () => [],
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
      search: '',
      searchResults: [],
      isSearching: false,
      searchTimeout: null
    }
  },

  computed: {
    annotatedLabels: {
      get() {
        const labelIds = this.annotations.map((item) => item.label)
        return this.labels.filter((item) => labelIds.includes(item.id))
      },
      set(_newValue) {
        // Handled by onLabelsChange
      }
    },

    displayLabels() {
      if (this.search && this.searchResults.length > 0) {
        return this.searchResults
      }
      // Show only first 100 labels by default
      return this.labels.slice(0, 100)
    }
  },

  watch: {
    search(newVal) {
      this.debouncedSearch(newVal)
    }
  },

  methods: {
    onLabelsChange(newValue) {
      if (newValue.length > this.annotations.length) {
        const label = newValue[newValue.length - 1]
        if (typeof label === 'object') {
          this.add(label)
        }
      } else {
        const annotatedLabels = this.labels.filter((item) =>
          this.annotations.map((a) => a.label).includes(item.id)
        )
        const label = annotatedLabels.find((x) => !newValue.some((y) => y.id === x.id))
        if (typeof label === 'object') {
          this.remove(label)
        }
      }
    },

    add(label) {
      this.$emit('add', label.id)
    },

    remove(label) {
      const annotation = this.annotations.find((item) => item.label === label.id)
      this.$emit('remove', annotation.id)
    },

    debouncedSearch(query) {
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

    async performSearch(query) {
      try {
        // Use server-side search if available
        if (this.labelService && this.projectId) {
          const results = await this.labelService.search(this.projectId, query, 100)
          this.searchResults = results
        } else {
          // Fallback to local filtering
          const lowerQuery = query.toLowerCase()
          this.searchResults = this.labels
            .filter((label) => label.text.toLowerCase().includes(lowerQuery))
            .slice(0, 100)
        }
      } catch (e) {
        console.error('Search failed, using local filter', e)
        const lowerQuery = query.toLowerCase()
        this.searchResults = this.labels
          .filter((label) => label.text.toLowerCase().includes(lowerQuery))
          .slice(0, 100)
      } finally {
        this.isSearching = false
      }
    }
  }
}
</script>