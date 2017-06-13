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

      <b-form-checkbox v-model="latestOnly" class="col-2 text-right" v-if="latest.length !== items.length">
        Only show latest assignments
      </b-form-checkbox>
    </div>

    <!-- Main table element -->
    <b-table striped hover v-on:row-clicked='gotoSubmission' :items="latestOnly ? latest : items" :fields="fields" :current-page="currentPage" :per-page="perPage" :filter="filter">
      <template slot="user_name" scope="item">
        {{item.value ? item.value : '-'}}
      </template>
      <template slot="grade" scope="item">
        {{item.value ? item.value : '-'}}
      </template>
    </b-table>

    <div class="justify-content-center row my-1">
      <b-pagination size="md" :total-rows="this.items.length" :per-page="perPage" v-model="currentPage" />
    </div>
  </div>
</template>

<script>
export default {
    name: 'submission-list',

    props: {
        assignmentId: {
            type: Number,
            default: 0,
        },
    },

    data() {
        return {
            latestOnly: true,
            currentPage: 1,
            perPage: 15,
            filter: null,
            items: [],
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
            },
        };
    },

    mounted() {
        this.$http.get(`/api/v1/assignments/${this.assignmentId}/works`).then((data) => {
            this.latest = [];
            this.items = data.data;
            const seen = {};
            const len = data.data.length;
            for (let i = 0; i < len; i += 1) {
                if (seen[this.items[i].user_id] !== true) {
                    this.latest.push(this.items[i]);
                    seen[this.items[i].user_id] = true;
                }
            }
        });
    },

    methods: {
        submissionURL(submission) {
            return `/assignments/${this.assignmentId}/submissions/${submission.id}/`;
        },
        gotoSubmission(_, i) {
            console.log(this.submissionURL(this.items[i]));
            this.$router.push(this.submissionURL(this.items[i]));
        },
    },
};
</script>

<style lang="less">
.table tr {
    cursor: pointer;
}
</style>
