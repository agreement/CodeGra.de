<template>
    <div>
        <div class="row">
            <b-form-fieldset horizontal class="col-10" :label-size="0">
                <b-form-input v-model="filter" placeholder="Type to Search" v-on:keyup.enter="submit"></b-form-input>
            </b-form-fieldset>

            <b-form-fieldset horizontal class="col-2 text-right" :label-size="0">
                <b-button-group>
                    <b-button class="btn-danger" :class="{ 'btn-outline-danger': !filterSubmitting }"
                        @click="filterSubmitting = !filterSubmitting">
                        <icon name="plus"></icon>
                    </b-button>
                    <b-button class="btn-warning" :class="{ 'btn-outline-warning': !filterGrading }"
                        @click="filterGrading = !filterGrading">
                        <icon name="times"></icon>
                    </b-button>
                    <b-button class="btn-success" :class="{ 'btn-outline-success': !filterDone }"
                        @click="filterDone = !filterDone">
                        <icon name="check"></icon>
                    </b-button>
                </b-button-group>
            </b-form-fieldset>
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
                {{item.value ? item.value : '-'}}
            </template>
        </b-table>
    </div>
</template>

<script>
import { bButton, bButtonGroup, bFormFieldset, bTable } from
    'bootstrap-vue/lib/components';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/check';
import 'vue-awesome/icons/times';
import 'vue-awesome/icons/plus';

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
            filterDone: true,
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
        bTable,
    },
};
</script>

<style lang="less" scoped>
.table {
    cursor: pointer;
}
</style>
