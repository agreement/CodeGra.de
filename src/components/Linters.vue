<template>
  <!-- TODO: Fix issues with iterations by relying on order !-->
  <div class="row justify-content-md-center" v-if="loading">
    <loader/>
  </div>
  <div class="" v-else>
    <table class="table table-striped">
      <thead>
        <tr>
          <th>Name</th>
          <th>Description</th>
          <th>State</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <linter v-for="(linter, key) in linters"
                :name="key"
                :options="linter.opts"
                :description="linter.desc"
                :initialId="linter.id"
                :initialState="linter.state"/>
      </tbody>
    </table>
  </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/check';
import 'vue-awesome/icons/times';

import Loader from './Loader';
import Linter from './Linter';

export default {
    name: 'linters',

    props: ['feedback'],

    data() {
        return {
            assignmentId: this.$route.params.assignmentId,
            linters: null,
            loading: true,
            show: {},
        };
    },

    components: {
        Loader,
        Icon,
        Linter,
    },

    mounted() {
        this.getLinters();
    },

    methods: {
        getLinters() {
            this.$http.get(`/api/v1/assignments/${this.assignmentId}/linters/`).then((data) => {
                console.log(data);
                this.linters = data.data;
                this.loading = false;
                console.log(this.linters);
                Object.keys(this.linters).forEach((key) => {
                    if (this.linters[key].state === 1) {
                        this.startUpdateLoop(key);
                    }
                });
            });
        },
    },
};
</script>

<style lang="less" scoped>
.margin {
    margin-bottom: 15px;
}

.large-btn {
    margin-top: 1em;
    padding: 15px 5em;
}
.right-float {
    float: right;
}

.center-table {
    text-align: center;
}
.center-table th {
    text-align: center;
}

.table-striped tbody tr:nth-of-type(even) table.trans tr {
    background-color: rgba(0, 0, 0, 0.05);
}
.table-striped tbody tr:nth-of-type(odd) table.trans tr {
    background-color: #fff;
}

button {
    cursor: pointer;
}
</style>
