<template>
    <div>
        <div class="row">
            <b-input-group class="col-12">
                <b-form-input v-model="filter" placeholder="Type to Search" v-on:keyup.enter="submit"></b-form-input>
                <b-button-group>
                    <b-popover placement="top" triggers="hover" content="Submitting">
                        <b-button class="btn-danger" :class="{ 'btn-outline-danger': !filterSubmitting }"
                            @click="filterSubmitting = !filterSubmitting">
                            <icon name="download"></icon>
                        </b-button>
                    </b-popover>
                    <b-popover placement="top" triggers="hover" content="Grading">
                        <b-button class="btn-warning" :class="{ 'btn-outline-warning': !filterGrading }"
                            @click="filterGrading = !filterGrading">
                            <icon name="pencil"></icon>
                        </b-button>
                    </b-popover>
                    <b-popover placement="top" triggers="hover" content="Done">
                        <b-button class="btn-success" :class="{ 'btn-outline-success': !filterDone }"
                            @click="filterDone = !filterDone">
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
            <template slot="assignment_name" scope="item">
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
            filter: null,
            filterHidden: false,
            filterSubmitting: true,
            filterGrading: true,
            filterDone: false,
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
                },
            },
        };
    },

    mounted() {
        if (this.$route.query.latest == null) {
            this.latestOnly = true;
        } else {
            this.latestOnly = this.$route.query.latest === 'true';
        }
        this.filter = this.$route.query.q;
    },

    methods: {
        filterItems(item) {
            switch (item.state) {
            case 0: return this.filterHidden;
            case 1: return this.filterSubmitting;
            case 2: return this.filterGrading;
            case 3: return this.filterDone;
            default: return 1;
            // default: throw TypeError('Unknown assignment state');
            }
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
            const query = { latest: this.latestOnly };
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

.table {
    cursor: pointer;
}
</style>
