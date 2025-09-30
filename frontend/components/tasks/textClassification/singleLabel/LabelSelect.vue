<template>
  <v-autocomplete
    :value="annotatedLabel"
    chips
    :items="displayLabels"
    :loading="isSearching"
    :search-input.sync="search"
    item-text="text"
    item-value="id"
    hide-details
    hide-selected
    return-object
    class="pt-0"
    label="Search and select label..."
    no-filter
    clearable
    @change="addOrRemove"
  >
    <template #selection="{ attrs, item, select, selected }">
      <v-chip
        v-if="item && item.backgroundColor"
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
    annotatedLabel() {
      const labelIds = this.annotations.map((item) => item.label)
      return this.labels.find((item) => labelIds.includes(item.id))
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
    addOrRemove(val) {
      if (val) {
        this.add(val)
      } else if (this.annotatedLabel) {
        this.remove(this.annotatedLabel)
      }
    },

    add(label) {
      this.$emit('add', label.id)
    },

    remove(label) {
      const annotation = this.annotations.find((item) => item.label === label.id)
      if (annotation) {
        this.$emit('remove', annotation.id)
      }
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