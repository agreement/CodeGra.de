<template>
    <div>
        <div class="row">
            <b-input-group class="col-12">
                <b-form-input v-model="filter" placeholder="Type to Search" v-on:keyup.enter="submit"></b-form-input>
            </b-input-group>
        </div>

        <!-- Main table element -->
        <b-table striped hover
                @row-clicked="gotoCourse"
                :items="courses"
                :fields="fields"
                :current-page="currentPage"
                :filter="filter"
                :show-empty="true">
            <template slot="name" scope="item">
                {{item.value ? item.value : '-'}}
            </template>
            <template slot="role" scope="item">
                {{item.value ? item.value : '-'}}
            </template>
            <template slot="actions" scope="item">
                <div class="row">
                    <b-tooltip placement="bottom" :delay="500" content="View assignments">
                        <b-btn size="sm" variant="success" @click="gotoCourse(item.item)">
                            <icon name="list"></icon>
                        </b-btn>
                    </b-tooltip>
                    <b-tooltip placement="bottom" :delay="500" content="Manage course">
                        <b-btn v-if="item.item.manageable" @click="gotoCourseEdit(item.item) "size="sm" variant="warning">
                            <icon name="pencil"></icon>
                        </b-btn>
                    </b-tooltip>
                </div>
            </template>
            <template slot="empty">
                No results found.
            </template>
        </b-table>
    </div>
</template>

<script>
import { bInputGroup, bTable, bButton, bTooltip } from
    'bootstrap-vue/lib/components';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/pencil';
import 'vue-awesome/icons/list';

export default {
    name: 'course-list',

    props: {
        courses: {
            type: Array,
            default: [],
        },
    },

    data() {
        return {
            filter: null,
            currentPage: 1,
            fields: {
                name: {
                    label: 'Name',
                    sortable: true,
                },
                role: {
                    label: 'Role',
                    sortable: true,
                },
                actions: {
                    label: 'Actions',
                    sortable: false,
                },
            },
        };
    },

    mounted() {
        this.filter = this.$route.query.q;
    },

    methods: {
        gotoCourse(course) {
            this.submit();
            this.$router.push({
                name: 'assignments',
                query: { q: course.name },
            });
        },

        gotoCourseEdit(course) {
            this.submit();
            this.$router.push({
                name: 'assignment_manage',
                params: {
                    courseId: course.id,
                },
            });
        },


        submit() {
            if (this.filter) {
                this.$router.replace({ query: { q: this.filter } });
            }
        },
    },

    components: {
        bInputGroup,
        bTable,
        bButton,
        bTooltip,
        Icon,
    },
};
</script>

<style lang="less" scoped>
    .btn {
        margin-right: 10px;
    }
</style>
