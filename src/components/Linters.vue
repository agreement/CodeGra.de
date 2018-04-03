<template>
<!-- TODO: Fix issues with iterations by relying on order !-->
<div class="row justify-content-md-center linters" v-if="loading">
    <loader/>
</div>
<div v-else class="linters">
    <b-tabs no-fade>
        <b-tab :title="linter.name"
               :key="linter.id"
               v-for="linter in linters">
            <linter :name="linter.name"
                    :options="linter.opts"
                    :server-description="linter.desc"
                    :initialId="linter.id"
                    :initialState="linter.state"
                    :assignment="assignment"/>
        </b-tab>
    </b-tabs>
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


<style lang="less">
@import "~mixins.less";

.linters .tab-content {
    #app.dark & {
        border-color: @color-primary-darker;
    }
    border: 1px solid #dee2e6;
    border-top: 0;
    border-bottom-right-radius: 0.25rem;
    border-bottom-left-radius: 0.25rem;
    padding: 1em;
    padding-bottom: 0;
}
</style>
