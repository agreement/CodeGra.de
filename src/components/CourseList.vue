<template>
<div class="course-list">
    <div class="row">
        <b-input-group class="col-12">
            <input v-model="filter"
                   class="form-control"
                   placeholder="Type to Search"
                   v-on:keyup.enter="submit"/>
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
        <a class="invisible-link"
           href="#"
           @click.prevent
           slot-scope="item">
            {{item.value ? item.value : '-'}}
        </a>
        <template slot="role" slot-scope="item">
            {{item.value ? item.value : '-'}}
        </template>
        <b-button-group slot="actions" slot-scope="item">
            <b-btn size="sm"
                   variant="success"
                   @click.stop="gotoCourse(item.item)"
                   v-b-popover.hover.top="'View assignments'">
                <icon name="list"/>
            </b-btn>
            <b-btn v-if="item.item.manageable"
                   @click.stop="gotoCourseEdit(item.item)"
                   size="sm"
                   variant="warning"
                   v-b-popover.hover.top="'Manage course'">
                <icon name="pencil"/>
            </b-btn>
        </b-button-group>
        <template slot-scope="empty">
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
