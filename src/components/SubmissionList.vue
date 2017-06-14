<template>
  <div>
    <div class="justify-content-centermy-1 row">

      <b-form-fieldset horizontal label="Filter" class="col-10" :label-size="2">
        <b-form-input v-model="filter" placeholder="Type to Search" v-on:keyup.enter="submit"></b-form-input>
      </b-form-fieldset>

      <b-form-checkbox v-model="latestOnly" class="col-2 text-right"
          v-if="latest.length !== submissions.length" checked="latestOnly" v-on:change="submit">
        Only show latest assignments
      </b-form-checkbox>
    </div>

    <!-- Main table element -->
    <b-table striped hover v-on:row-clicked='gotoSubmission' :items="latestOnly
        ? latest : submissions" :fields="fields" :current-page="currentPage" :per-page="submissions.length + 1" :filter="filter">
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

    mounted() {
        if (this.$route.query.latest === null) {
            this.latestOnly = true;
        } else {
            this.latestOnly = this.$route.query.latest === 'true';
        }
        this.filter = this.$route.query.q;
        this.updateSubmissions(null);
    },

    watch: {
        submissions() {
            this.updateSubmissions();
        },
    },

    methods: {
        updateSubmissions() {
            this.latest = [];
            const seen = {};
            const len = this.submissions.length;
            for (let i = 0; i < len; i += 1) {
                if (seen[this.submissions[i].user_id] !== true) {
                    this.latest.push(this.submissions[i]);
                    seen[this.submissions[i].user_id] = true;
                }
            }
        },
        gotoSubmission(_, i) {
            this.submit();
            this.$emit('goto', this.latestOnly ? this.latest[i] :
                                                 this.submissions[i]);
        },
        submit() {
            const query = { latest: this.latestOnly };
            if (this.filter) {
                query.q = this.filter;
            }
            this.$router.replace({ query });
        },
    },
};
</script>

<style lang="less">
.table tr {
    cursor: pointer;
}
</style>
