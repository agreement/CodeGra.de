<template>
    <div>
        <div class="row">
            <b-input-group class="col-12">
                <b-form-input v-model="filter" placeholder="Type to Search" v-on:keyup.enter="submit"></b-form-input>
            </b-input-group>
        </div>

        <!-- Main table element -->
        <b-table striped hover
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
                <b-btn size="sm" variant="success" @click="gotoCourse(item.item)">
                    <icon name="list"></icon>
                </b-btn>
                <b-btn v-if="canEdit(item.item)" @click="gotoCourseEdit(item.item) "size="sm" variant="warning">
                    <icon name="pencil"></icon>
                </b-btn>
            </template>
            <template slot="empty">
                No results found.
            </template>
        </b-table>
    </div>
</template>

<script>
import { bInputGroup, bTable, bButton } from
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

        canEdit(course) {
            return course.role !== 'student';
        },
    },

    components: {
        bInputGroup,
        bTable,
        bButton,
        Icon,
    },
};
</script>

<style lang="less" scoped>
</style>
