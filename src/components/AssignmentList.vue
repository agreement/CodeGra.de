<template>
    <div>
        <b-form-fieldset class="table-control">
            <b-form-input v-model="filter" placeholder="Type to Search" v-on:keyup.enter="submit"/>
            <b-form-checkbox class="input-group-addon" v-model="checkbox_student">student</b-form-checkbox>
            <b-form-checkbox class="input-group-addon" v-model="checkbox_assistant">assistant</b-form-checkbox>
            <b-button-input-group class="buttons">
                <b-button-group>
                    <b-popover placement="top" triggers="hover" content="Hidden" v-if="canSeeHidden">
                        <b-button class="btn-info" :class="{ 'btn-outline-info': !toggles.hidden}"
                                  @click="toggleFilter('hidden')">
                            <icon name="eye-slash"></icon>
                        </b-button>
                    </b-popover>
                    <b-popover placement="top" triggers="hover" content="Submitting">
                        <b-button class="btn-danger" :class="{ 'btn-outline-danger': !toggles.submitting }"
                                  @click="toggleFilter('submitting')">
                            <icon name="download"></icon>
                        </b-button>
                    </b-popover>
                    <b-popover placement="top" triggers="hover" content="Grading">
                        <b-button class="btn-warning" :class="{ 'btn-outline-warning': !toggles.grading }"
                                  @click="toggleFilter('grading')">
                            <icon name="pencil"></icon>
                        </b-button>
                    </b-popover>
                    <b-popover placement="top" triggers="hover" content="Done">
                        <b-button class="btn-success" :class="{ 'btn-outline-success': !toggles.done }"
                                  @click="toggleFilter('done')">
                            <icon name="check"></icon>
                        </b-button>
                    </b-popover>
                </b-button-group>
            </b-button-input-group>
        </b-form-fieldset>

        <!-- Main table element -->
        <b-table striped hover
                @row-clicked="gotoAssignment"
                :items="assignments"
                :fields="fields"
                :current-page="currentPage"
                :filter="filterItems"
                :show-empty="true">
            <template slot="course_name" scope="item">
                {{item.value ? item.value : '-'}}
            </template>
            <template slot="course_role" scope="item">
                {{item.value ? item.value : '-'}}
            </template>
            <template slot="name" scope="item">
                {{item.value ? item.value : '-'}}
            </template>
            <template slot="deadline" scope="item">
                {{item.value ? item.value : '-'}}
            </template>
            <template slot="state" scope="item">
                <icon name="eye-slash" v-if="item.item.state == assignmentState.HIDDEN"></icon>
                <icon name="download" v-if="item.item.state == assignmentState.SUBMITTING"></icon>
                <icon name="pencil" v-else-if="item.item.state == assignmentState.GRADING"></icon>
                <icon name="check" v-else-if="item.item.state == assignmentState.DONE"></icon>
            </template>
            <template slot="empty">
                No results found.
            </template>
        </b-table>
    </div>
</template>

<script>
import { bButton, bButtonGroup, bFormInput, bInputGroup, bTooltip, bTable, bFormCheckbox } from
    'bootstrap-vue/lib/components';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/download';
import 'vue-awesome/icons/pencil';
import 'vue-awesome/icons/check';
import 'vue-awesome/icons/eye-slash';

import * as assignmentState from '../store/assignment-states';

export default {
    name: 'assignment-list',

    props: {
        assignments: {
            type: Array,
            default: [],
        },
        canSeeHidden: {
            type: Boolean,
            default: false,
        },
    },

    data() {
        return {
            assignmentState,
            filter: '',
            toggles: {
                hidden: false,
                submitting: true,
                grading: false,
                done: true,
            },
            currentPage: 1,
            fields: {
                course_name: {
                    label: 'Course',
                    sortable: true,
                },
                course_role: {
                    label: 'Role',
                    sortable: true,
                },
                name: {
                    label: 'Assignment',
                    sortable: true,
                },
                deadline: {
                    label: 'Deadline',
                    sortable: true,
                },
                state: {
                    label: 'State',
                    sortable: true,
                    class: 'text-center',
                },
            },
            checkbox_student: true,
            checkbox_assistant: true,
        };
    },

    mounted() {
        const q = this.$route.query;
        this.toggles.submitting = q.submitting == null ? true : q.submitting === 'true';
        this.toggles.grading = q.grading == null ? false : q.grading === 'true';
        this.toggles.done = q.done == null ? true : q.done === 'true';
        this.toggles.hidden = q.hidden == null ? true : q.hidden === 'true';
        this.filter = q.q;
    },

    methods: {
        filterItems(item) {
            if (!this.checkbox_student && !item.can_grade) {
                return false;
            } else if (!this.checkbox_assistant && item.can_grade) {
                return false;
            }

            if (!this.filterState(item)) {
                return false;
            } else if (!this.filter) {
                return true;
            }
            const terms = {
                name: item.name.toLowerCase(),
                course_name: item.course_name.toLowerCase(),
                course_role: item.course_role,
                deadline: item.deadline,
            };
            return this.filter.toLowerCase().split(' ')
                .every(word => this.matchesWord(terms, word));
        },

        filterState(item) {
            switch (item.state) {
            case assignmentState.SUBMITTING: return this.toggles.submitting;
            case assignmentState.GRADING: return this.toggles.grading;
            case assignmentState.DONE: return this.toggles.done;
            case assignmentState.HIDDEN: return this.toggles.hidden;
            default: throw TypeError(`Unknown assignment state "${item.state}"`);
            }
        },

        matchesWord(item, word) {
            return item.name.indexOf(word) >= 0 ||
                item.course_name.indexOf(word) >= 0 ||
                item.deadline.indexOf(word) >= 0;
        },

        toggleFilter(filter) {
            this.toggles[filter] = !this.toggles[filter];
            this.submit();
        },

        gotoAssignment(assignment) {
            this.submit();
            this.$router.push({
                name: 'assignment_submissions',
                params: {
                    courseId: assignment.course_id,
                    assignmentId: assignment.id,
                },
            });
        },

        submit() {
            const query = {
                submitting: this.toggles.submitting,
                grading: this.toggles.grading,
                done: this.toggles.done,
            };
            if (this.filter) {
                query.q = this.filter;
            }
            this.$router.replace({ query });
        },
    },

    components: {
        Icon,
        bButton,
        bButtonGroup,
        bFormInput,
        bInputGroup,
        bFormCheckbox,
        bTooltip,
        bTable,
    },
};
</script>

<style lang="less" scoped>
.input-group {
    margin-bottom: 30px;
}

.btn-group {
    button {
        border-top-left-radius: 0;
        border-bottom-left-radius: 0;
    }

    & > :not(:last-child) button {
        border-top-right-radius: 0;
        border-bottom-right-radius: 0;
    }
}

// <<<<<<< HEAD
// .custom-checkbox {
//     margin-right: 0;
//     padding-left: 2.25rem;
//     font-size: 0.95em;
//
//     .custom-control-indicator {
//         top: .75rem;
//         left: .75rem;
//     }
// =======
.table-control input {
    display: table-cell;
    width: 100%;
    border-bottom-right-radius: 0px;
    border-top-right-radius: 0px;
    height: 2.35em;
}

.table-control .buttons button {
    height: 2.35em;
}

.table-control .buttons {
    width: 1px;
    display: table-cell;
    vertical-align: middle;
}

.table,
button {
    cursor: pointer;
}
</style>

<style>
div.table-control > div {
    display: table !important;
    width: 100%;
}
</style>
