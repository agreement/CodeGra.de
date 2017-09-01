<template>
    <!-- TODO: Fix issues with iterations by relying on order !-->
    <div class="row justify-content-md-center" v-if="loading">
        <loader/>
    </div>
    <div v-else>
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
                <linter v-for="linter in linters"
                    :name="linter.name"
                    :options="linter.opts"
                    :description="linter.desc"
                    :initialId="linter.id"
                    :initialState="linter.state"
                    :key="linter.id"
                    :assignment="assignment"/>
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

    props: {
        assignment: {
            type: Object,
            default: null,
        },
    },

    data() {
        return {
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
            this.$http.get(`/api/v1/assignments/${this.assignment.id}/linters/`).then((data) => {
                this.linters = data.data;
                this.loading = false;
            });
        },
    },
};
</script>
