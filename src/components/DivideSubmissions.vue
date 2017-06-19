<template>
    <div class="divide-submissions">
        <loader class="text-center" v-if="loading"></loader>
        <div class="form-control" v-else>
            <div v-for="name_id in graders">
                <input type="checkbox" :id="name_id[1]" :value="name_id[1]" v-model="checkedNames">
                <label :for="name_id[1]">{{ name_id[0] }}</label>
            </div>
            <span v-if="graders.length == 0"> No possible graders found for this assignment!</span>
            <b-button v-else variant="primary" v-on:click="divideAssignments()">
                Divide Submissions
            </b-button>
        </div>
    </div>
</template>

<script>
import { bButton, bInputGroup, bInputGroupButton } from 'bootstrap-vue/lib/components';
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
                this.graders = data.data.names_ids;
                this.loading = false;
            });
        },

        divideAssignments() {
            this.loading = true;
            this.$http.patch(`/api/v1/assignments/${this.assignment.id}/divide`,
                {
                    graders: this.checkedNames,
                },
                {
                    headers: { 'Content-Type': 'application/json' },
                },
            ).then(() => {
                // eslint-disable-next-line
                this.$emit('submit');
                this.loading = false;
            });
        },
    },

    components: {
        bButton,
        bInputGroup,
        bInputGroupButton,
        Loader,
    },
};
</script>
