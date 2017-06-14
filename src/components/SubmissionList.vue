<template>
  <div>
    <div class="justify-content-centermy-1 row">

      <b-form-fieldset horizontal label="Rows per page" class="col-4" :label-size="6">
        <b-form-select :options="[{text:15,value:15},{text:30,value:30},{text:'all',value:10000}]" v-model="perPage">
        </b-form-select>
      </b-form-fieldset>

      <b-form-fieldset horizontal label="Filter" class="col-6" :label-size="2">
        <b-form-input v-model="filter" placeholder="Type to Search"></b-form-input>
      </b-form-fieldset>

      <b-form-checkbox v-model="latestOnly" class="col-2 text-right"
          v-if="latest.length !== submissions.length">
        Only show latest assignments
      </b-form-checkbox>
    </div>

    <!-- Main table element -->
    <b-table striped hover v-on:row-clicked='gotoSubmission' :items="latestOnly
        ? latest : submissions" :fields="fields" :current-page="currentPage" :per-page="perPage" :filter="filter">
      <template slot="user_name" scope="item">
        {{item.value ? item.value : '-'}}
      </template>
      <template slot="grade" scope="item">
        {{item.value ? item.value : '-'}}
      </template>
      <template slot="created_at" scope="item">
        {{item.value ? item.value : '-'}}
      </template>
    </b-table>

    <div class="justify-content-center row my-1" v-if="this.submissions.length > this.perPage">
      <b-pagination size="md" :total-rows="this.submissions.length" :per-page="perPage" v-model="currentPage" />
    </div>
  </div>
</template>

<script>
export default {
    name: 'submission-list',

    props: {
        submissions: {
            type: Array,
            default: [],
        },
    },

    data() {
        return {
            latestOnly: true,
            currentPage: 1,
            perPage: 15,
            filter: null,
            latest: [],
            fields: {
                user_name: {
                    label: 'User',
                    sortable: true,
                },
                grade: {
                    label: 'Grade',
                    sortable: true,
                },
                created_at: {
                    label: 'Created at',
                    sortable: true,
                },
            },
        };
    },

    watch: {
        submissions(data) {
            console.log('watch');
            this.latest = [];
            const seen = {};
            const len = data.length;
            for (let i = 0; i < len; i += 1) {
                if (seen[this.submissions[i].user_id] !== true) {
                    this.latest.push(this.submissions[i]);
                    seen[this.submissions[i].user_id] = true;
                }
            }
        },
    },

    methods: {
        submissionURL(submission) {
            return `/assignments/${this.assignmentId}/submissions/${submission.id}/`;
        },
        gotoSubmission(_, i) {
            this.$router.push(this.submissionURL(this.submissions[i]));
        },
    },
};
</script>

<style lang="less">
.table tr {
    cursor: pointer;
}
</style>
