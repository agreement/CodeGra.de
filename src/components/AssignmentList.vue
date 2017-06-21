<template>
    <div>
        <div class="row">
            <b-input-group class="col-12">
                <b-form-input v-model="filter" placeholder="Type to Search" v-on:keyup.enter="submit"></b-form-input>
                <b-button-group>
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
                <div class="col-3">
                    <b-form-checkbox v-model="cb_student">student</b-form-checkbox>
                    <b-form-checkbox v-model="cb_ta">assistant</b-form-checkbox>
                    <!-- <input type="checkbox" value="student" v-model="roles_selected">
                    <label>student</label>
                    <input type="checkbox" value="assistant" v-model="roles_selected">
                    <label>assistant</label> -->
                </div>
            </b-input-group>
            {{ roles_selected }}
        </div>

        <!-- Main table element -->
        <b-table striped hover
                v-on:row-clicked="gotoAssignment"
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
            <template slot="date" scope="item">
                {{item.value ? item.value : '-'}}
            </template>
            <template slot="state" scope="item">
                <icon name="download" v-if="item.item.state == 1"></icon>
                <icon name="pencil" v-else-if="item.item.state == 2"></icon>
                <icon name="check" v-else-if="item.item.state == 3"></icon>
            </template>
            <template slot="empty">
                No results found.
            </template>
        </b-table>
    </div>
</template>

<script>
import { bButton, bButtonGroup, bFormFieldset, bInputGroup, bPopover, bTable } from
    'bootstrap-vue/lib/components';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/download';
import 'vue-awesome/icons/pencil';
import 'vue-awesome/icons/check';

export default {
    name: 'assignment-list',

    props: {
        assignments: {
            type: Array,
            default: [],
        },
    },

    data() {
        return {
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
                date: {
                    label: 'Due date',
                    sortable: true,
                },
                state: {
                    label: 'State',
                    sortable: true,
                    class: 'text-center',
                },
            },
            cb_student: true,
            cb_ta: true,
        };
    },

    mounted() {
        const q = this.$route.query;
        this.toggles.submitting = q.submitting == null ? true : q.submitting === 'true';
        this.toggles.grading = q.grading == null ? false : q.grading === 'true';
        this.toggles.done = q.done == null ? true : q.done === 'true';
        this.filter = q.q;
    },

    methods: {
        filterItems(item) {
            if (!this.cb_student && !item.can_grade) {
                return false;
            } else if (!this.cb_ta && item.can_grade) {
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
                date: item.date,
            };
            return this.filter.toLowerCase().split(' ')
                .every(word => this.matchesWord(terms, word));
        },

        filterState(item) {
            switch (item.state) {
            case 0: return this.toggles.hidden;
            case 1: return this.toggles.submitting;
            case 2: return this.toggles.grading;
            case 3: return this.toggles.done;
            default: throw TypeError('Unknown assignment state');
            }
        },

        matchesWord(item, word) {
            return item.name.indexOf(word) >= 0 ||
                item.course_name.indexOf(word) >= 0 ||
                item.date.indexOf(word) >= 0;
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
        bFormFieldset,
        bInputGroup,
        bPopover,
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

.table,
button {
    cursor: pointer;
}
</style>
