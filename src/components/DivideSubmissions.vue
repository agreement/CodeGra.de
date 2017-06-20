<template>
    <div class="divide-submissions">
        <loader class="text-center" v-if="loading"></loader>
        <b-form-fieldset label="Divide submissions" v-else>
            <div class="form-control">
                <div v-for="grader in graders">
                <b-form-checkbox v-model="grader.divided">
                    {{ grader.name }}
                </b-form-checkbox>
                </div>
                <span v-if="graders.length == 0"> No possible graders found for this assignment!</span>
                <b-button v-else variant="primary" v-on:click="divideAssignments()">
                    Divide Submissions
                </b-button>
            </div>
        </b-form-fieldset>
    </div>
</template>

<script>
import { bButton, bFormCheckbox, bFormFieldset, bInputGroup, bInputGroupButton } from 'bootstrap-vue/lib/components';
import Loader from './Loader';

export default {
    name: 'divide-submissions',

    props: {
        assignment: {
            type: Object,
            default: null,
        },
    },

    data() {
        return {
            graders: [],
            checkedNames: [],
            loading: true,
        };
    },

    mounted() {
        this.getGraders();
    },

    methods: {
        getGraders() {
            this.$http.get(`/api/v1/assignments/${this.assignment.id}/graders`).then((data) => {
                this.graders = data.data;
                this.loading = false;
            });
        },

        divideAssignments() {
            this.loading = true;
            const data = {
                graders: Object.keys(this.graders)
                    .filter(item => this.graders[item].divided)
                    .map(item => this.graders[item].id),
            };
            this.$http.patch(`/api/v1/assignments/${this.assignment.id}/divide`, data).then(() => {
                // eslint-disable-next-line
                this.$emit('submit');
                this.loading = false;
            }).catch(() => {
                // TODO give feedback!!
                this.loading = false;
            });
        },
    },

    components: {
        bButton,
        bFormCheckbox,
        bFormFieldset,
        bInputGroup,
        bInputGroupButton,
        Loader,
    },
};
</script>

<style lang="less">
.custom-checkbox {
    align-items: center;
}
</style>
