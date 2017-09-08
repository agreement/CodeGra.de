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
                <b-btn-group>
                    <b-popover class="btn-popover" placement="top" content="View assignments" triggers="hover">
                        <b-btn size="sm" variant="success" @click.stop="gotoCourse(item.item)">
                            <icon name="list"></icon>
                        </b-btn>
                    </b-popover>
                    <b-popover class="btn-popover" placement="top" content="Manage course" triggers="hover">
                        <b-btn v-if="item.item.manageable" @click.stop="gotoCourseEdit(item.item) "size="sm" variant="warning">
                            <icon name="pencil"></icon>
                        </b-btn>
                    </b-popover>
                </b-btn-group>
            </template>
            <template slot="empty">
                No results found.
            </template>
        </b-table>
    </div>
</template>

<script>
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
        Icon,
    },
};
</script>

<style lang="less">
.btn-popover {
    &:not(:last-child) .btn {
        border-top-right-radius: 0;
        border-bottom-right-radius: 0;
    }

    &:not(:first-child) .btn {
        border-top-left-radius: 0;
        border-bottom-left-radius: 0;
    }
}
</style>
