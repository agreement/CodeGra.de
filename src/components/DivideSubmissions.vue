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
                <submit-button label="Divide submissions" @click="divideAssignments" ref="submitButton" v-if="graders.length"/>
                <span v-else>No graders found for this assignment</span>
            </div>
        </b-form-fieldset>
    </div>
</template>

<script>
import Loader from './Loader';
import SubmitButton from './SubmitButton';

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
        this.loading = true;
        this.$http.get(`/api/v1/assignments/${this.assignment.id}/graders/`).then((data) => {
            this.graders = data.data;
            this.loading = false;
        });
    },

    methods: {
        divideAssignments() {
            const req = this.$http.patch(
                `/api/v1/assignments/${this.assignment.id}/divide`, {
                    graders: Object.values(this.graders)
                        .filter(x => x.divided)
                        .map(x => x.id),
                },
            );
            req.then(() => {
                this.$emit('submit');
            }, (err) => {
                // TODO: give feedback
                // eslint-disable-next-line
                console.dir(err);
            });
            this.$refs.submitButton.submit(req.catch((x) => {
                throw x.response.data.message;
            }));
        },
    },

    components: {
        Loader,
        SubmitButton,
    },
};
</script>
