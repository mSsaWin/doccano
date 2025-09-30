<template>
  <v-row>
    <v-col cols="12">
      <member-progress />
    </v-col>
    <v-col v-if="!!project.canDefineCategory" cols="12">
      <label-distribution
        title="Category Distribution"
        :distribution="categoryDistribution"
        :label-types="categoryTypes"
      />
    </v-col>
    <v-col v-if="!!project.canDefineSpan" cols="12">
      <label-distribution
        title="Span Distribution"
        :distribution="spanDistribution"
        :label-types="spanTypes"
      />
    </v-col>
    <v-col v-if="!!project.canDefineRelation" cols="12">
      <label-distribution
        title="Relation Distribution"
        :distribution="relationDistribution"
        :label-types="relationTypes"
      />
    </v-col>
  </v-row>
</template>

<script>
import { mapGetters } from 'vuex'
import LabelDistribution from '~/components/metrics/LabelDistribution'
import MemberProgress from '~/components/metrics/MemberProgress'

export default {
  components: {
    LabelDistribution,
    MemberProgress
  },

  layout: 'project',

  middleware: ['check-auth', 'auth', 'setCurrentProject', 'isProjectAdmin'],

  validate({ params }) {
    return /^\d+$/.test(params.id)
  },

  data() {
    return {
      categoryTypes: [],
      categoryDistribution: {},
      relationTypes: [],
      relationDistribution: {},
      spanTypes: [],
      spanDistribution: {}
    }
  },

  computed: {
    ...mapGetters('projects', ['project']),

    projectId() {
      return this.$route.params.id
    }
  },

  async created() {
    // Load distribution first to see which labels are actually used
    if (this.project.canDefineCategory) {
      this.categoryDistribution = await this.$repositories.metrics.fetchCategoryDistribution(
        this.projectId
      )
      // Load only labels that are actually used in the distribution
      this.categoryTypes = await this.getUsedLabels(
        this.categoryDistribution,
        this.$services.categoryType
      )
    }
    if (this.project.canDefineSpan) {
      this.spanDistribution = await this.$repositories.metrics.fetchSpanDistribution(this.projectId)
      this.spanTypes = await this.getUsedLabels(
        this.spanDistribution,
        this.$services.spanType
      )
    }
    if (this.project.canDefineRelation) {
      this.relationDistribution = await this.$repositories.metrics.fetchRelationDistribution(
        this.projectId
      )
      this.relationTypes = await this.getUsedLabels(
        this.relationDistribution,
        this.$services.relationType
      )
    }
  },

  methods: {
    /**
     * Extract used labels from distribution and fetch only their data
     * This loads only labels that users have actually used, not all 18k labels
     */
    async getUsedLabels(distribution, labelService) {
      // Extract unique label names from distribution
      const usedLabelNames = new Set()
      for (const user in distribution) {
        for (const labelName in distribution[user]) {
          usedLabelNames.add(labelName)
        }
      }

      // If no labels used, return empty array
      if (usedLabelNames.size === 0) {
        return []
      }

      // Strategy: Try to fetch labels by searching for each used label name
      // This is much faster than loading all 18k labels
      const labelPromises = Array.from(usedLabelNames).map(async (labelName) => {
        try {
          // Search for exact label name
          const results = await labelService.search(this.projectId, labelName, 10)
          // Find exact match (search might return partial matches)
          return results.find(label => label.text === labelName)
        } catch (error) {
          console.warn(`Failed to fetch label ${labelName}:`, error)
          return null
        }
      })

      const labels = await Promise.all(labelPromises)
      // Filter out nulls and undefined
      return labels.filter(label => label != null)
    }
  }
}
</script>
