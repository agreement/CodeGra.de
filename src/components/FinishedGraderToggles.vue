<template>
<div class="finished-grader-toggles">
    <table class="table table-striped"
            v-if="internalGraders">
        <thead>
            <tr>
                <th>Grader</th>
                <th/>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="grader, i in internalGraders"
                :key="grader.id"
                class="grader">
                <td>{{ grader.name }}</td>
                <td>
                    <b-popover placement="top"
                                :show="!!(warningGraders[grader.id] || errorGraders[grader.id])"
                                :target="`grader-icon-${assignment.id}-${grader.id}`">
                        <span v-if="errorGraders[grader.id]">
                            {{ errorGraders[grader.id] }}
                        </span>
                        <span v-else>
                            {{ warningGraders[grader.id] }}
                        </span>
                    </b-popover>

                    <icon :name="iconStyle(grader.id)"
                            :spin="!(errorGraders[grader.id] || warningGraders[grader.id])"
                            :id="`grader-icon-${assignment.id}-${grader.id}`"
                            :class="iconClass(grader.id)"
                            :style="{
                                    opacity: warningGraders[grader.id] ||
                                            loadingGraders[grader.id] ||
                                            errorGraders[grader.id] ? 1 : 0,
                                    }"/>
                </td>
                <td>
                    <toggle label-on="Done"
                            label-off="Grading"
                            :disabled="!others && $store.getters['user/id'] != grader.id"
                            v-model="grader.done"
                            disabled-text="You cannot change the grader status of other graders"
                            @input="toggleGrader(grader)"/>
                </td>
        </tr>
        </tbody>
    </table>
    <span v-else>No graders found for this assignment</span>
</div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/times';
import 'vue-awesome/icons/circle-o-notch';
import 'vue-awesome/icons/exclamation-triangle';
import { parseWarningHeader, waitAtLeast } from '@/utils';

import Toggle from './Toggle';
import Loader from './Loader';

export default {
    props: {
        assignment: {
            type: Object,
            default: null,
        },

        graders: {
            type: Array,
            default: null,
        },

        others: {
            type: Boolean,
            default: false,
        },
    },

    data() {
        return {
            internalGraders: [],
            loadingGraders: {},
            errorGraders: {},
            warningGraders: {},
        };
    },

    mounted() {
        this.internalGraders = this.graders.map(g => Object.assign({}, g));
    },

    methods: {
        iconClass(graderId) {
            if (this.errorGraders[graderId]) {
                return 'text-danger';
            } else if (this.warningGraders[graderId]) {
                return 'text-warning';
            }
            return '';
        },
        iconStyle(graderId) {
            if (this.errorGraders[graderId]) {
                return 'times';
            } else if (this.warningGraders[graderId]) {
                return 'exclamation-triangle';
            }
            return 'circle-o-notch';
        },
        toggleGrader(grader) {
            this.$set(this.warningGraders, grader.id, undefined);
            delete this.warningGraders[grader.id];
            this.$set(this.loadingGraders, grader.id, true);

            let req;

            if (grader.done) {
                req = this.$http.post(`/api/v1/assignments/${this.assignment.id}/graders/${grader.id}/done`);
            } else {
                req = this.$http.delete(`/api/v1/assignments/${this.assignment.id}/graders/${grader.id}/done`);
            }

            waitAtLeast(500, req).then((res) => {
                if (res.headers.warning) {
                    const warning = parseWarningHeader(res.headers.warning);
                    this.$set(this.warningGraders, grader.id, warning.text);
                    this.$nextTick(() => setTimeout(() => {
                        this.$set(this.warningGraders, grader.id, undefined);
                        delete this.warningGraders[grader.id];
                    }, 2000));
                }
            }, (err) => {
                this.$set(this.errorGraders, grader.id, err.response.data.message);

                this.$nextTick(() => setTimeout(() => {
                    grader.done = !grader.done;

                    this.$set(this.errorGraders, grader.id, undefined);
                    delete this.errorGraders[grader.id];
                }, 2000));
            }).then(() => {
                this.$set(this.loadingGraders, grader.id, undefined);
                delete this.loadingGraders[grader.id];
            });
        },
    },

    components: {
        Icon,
        Toggle,
        Loader,
    },
};
</script>

<style lang="less" scoped>
.table {
    margin-bottom: 0;
}

.table th {
    border-top: none;
}

.table th:last-child {
    text-align: center;
}

.table td:not(:first-child) {
    padding: .5rem;
}

.table td:nth-child(2) {
    padding-top: .75rem;
}

.table td:nth-child(2),
.table td:last-child {
    // Fit content
    width: 1px;
    white-space: nowrap;
}
</style>
