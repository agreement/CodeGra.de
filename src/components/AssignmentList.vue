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
            </b-input-group>
        </div>

        <!-- Main table element -->
        <b-table striped hover
                v-on:row-clicked="gotoAssignment"
                :items="assignments"
                :fields="fields"
                :current-page="currentPage"
                :filter="filterItems">
            <template slot="course_name" scope="item">
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
        };
    },

    mounted() {
        this.toggles.submitting = this.$route.query.submitting === 'true';
        this.toggles.grading = this.$route.query.grading === 'true';
        this.toggles.done = this.$route.query.done === 'true';
        this.filter = this.$route.query.q;
    },

    methods: {
        filterItems(item) {
            if (!this.filterState(item)) {
                return false;
            }
            const terms = {
                name: item.name.toLowerCase(),
                course_name: item.course_name.toLowerCase(),
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
