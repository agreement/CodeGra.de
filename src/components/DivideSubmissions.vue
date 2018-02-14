<template>
<div class="divide-submissions">
    <div class="form-control">
        <div class="grader-list">
            <b-input-group class="grader">
                <b-input-group-text slot="prepend"><b>Grader</b></b-input-group-text>
                <input class="form-control"
                       style="text-align: right;"
                       disabled
                       value="Weight"/>
                <b-input-group-text slot="append"
                                    style="width: 5em;">
                    Percent
                </b-input-group-text>
            </b-input-group>
            <b-input-group v-for="grader, i in graders"
                           :key="grader.id"
                           class="grader">
                <b-input-group-text slot="prepend"
                                    >
                    <b-form-checkbox @change="grader.weight = grader.weight ? 0 : 1"
                                     :checked="grader.weight != 0">
                        {{ grader.name }}
                    </b-form-checkbox>
                </b-input-group-text>
                <input class="form-control"
                       type="number"
                       min="0"
                       step="0.5"
                       style="min-width: 3em;"
                       v-model.number="grader.weight"/>
                <b-input-group-text slot="append" class="grader-percentage"
                                    style="width: 5em;">
                    {{ (100 * grader.weight / totalWeight).toFixed(1) }}%
                </b-input-group-text>
            </b-input-group>
        </div>
        <submit-button label="Divide" @click="divideAssignments" ref="submitButton" v-if="graders.length"/>
        <span v-else>No graders found for this assignment</span>
    </div>
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

        graders: {
            type: Array,
            default: null,
        },
    },

    computed: {
        totalWeight() {
            const graderWeight = this.graders.reduce(
                (tot, grader) => tot + (grader.weight || 0),
                0,
            );
            return Math.max(graderWeight, 1);
        },
    },

    methods: {
        divideAssignments() {
            const req = this.$http.patch(`/api/v1/assignments/${this.assignment.id}/divide`, {
                graders: Object.values(this.graders)
                    .filter(x => x.weight !== 0)
                    .reduce((res, g) => {
                        res[`${g.id}`] = g.weight;
                        return res;
                    }, {}),
            });
            this.$refs.submitButton.submit(req.then(() => {
                this.$emit('divided');
            }, (err) => {
                throw err.response.data.message;
            }));
        },
    },

    components: {
        Loader,
        SubmitButton,
    },
};
</script>

<style lang="less" scoped>
.grader-list {
    margin-bottom: .5rem;
    .grader:not(:first-child) .input-group-append .input-group-text {
        border-top-right-radius: 0;
    }
    .grader:not(:last-child) .input-group-append .input-group-text {
        border-bottom-right-radius: 0;
    }
}

.grader {
    width: 100%;

    &:not(:first-child) * {
        border-top-left-radius: 0;
        border-top-right-radius: 0;
    }

    &:not(:last-child) * {
        border-bottom-left-radius: 0;
        border-bottom-right-radius: 0;
        margin-bottom: -1px;
    }
}

.grader-percentage {
    text-align: right;
}
</style>
