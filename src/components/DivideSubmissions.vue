<template>
<div class="divide-submissions">
    <table class="table table-striped grader-list">
        <thead>
            <tr>
                <th class="name">Grader</th>
                <th class="weight">Weight</th>
                <th class="percentage">Percent</th>
            </tr>
        </thead>

        <tbody>
            <tr v-for="grader, i in graders"
                class="grader">
                <td class="name">
                    <b-form-checkbox @change="graderChanged(i)"
                                    :checked="grader.weight != 0">
                        {{ grader.name }}
                    </b-form-checkbox>
                </td>
                <td class="weight">
                    <input class="form-control"
                        type="number"
                        min="0"
                        step="0.5"
                        :ref="`inputField${i}`"
                        style="min-width: 3em;"
                        v-model.number="grader.weight"/>
                </td>
                <td class="percentage">
                    {{ (100 * grader.weight / totalWeight).toFixed(1) }}%
                </td>
            </tr>
        </tbody>
    </table>

    <submit-button label="Divide"
                   @click="divideAssignments"
                   ref="submitButton"
                   v-if="graders.length"/>
    <span v-else>No graders found for this assignment</span>
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
        graderChanged(i) {
            this.graders[i].weight = this.graders[i].weight ? 0 : 1;
            const field = this.$refs[`inputField${i}`][0];
            field.focus();
        },

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
@import "~mixins.less";

.grader-list {
    margin-bottom: 1rem;
}

th {
    border-top: 0;
}

.grader {
    border-bottom: 1px solid #dee2e6;

    #app.dark & {
        border-bottom: 1px solid @color-primary-darker;
    }
}

tbody .weight {
    padding: 0;

    input {
        padding: .75rem;
        border: none;
        border-bottom: 1px solid transparent !important;
        border-radius: 0;
        background: transparent !important;

        &:not(:disabled):hover {
            border-color: @color-primary !important;

            #app.dark & {
                border-color: @color-primary-darkest !important;
            }
        }
    }
}

.weight,
.percentage {
    text-align: right;
}

.name,
.percentage {
    width: 1px;
    white-space: nowrap;
}

.submit-button {
    display: flex;
    justify-content: flex-end;
    margin-right: 1rem;
}
</style>

<style lang="less">
.grader-list {
    .custom-checkbox {
        display: flex;

        label {
            width: 100%;
        }
    }
}
</style>
