<template>
    <loader class="text-center" v-if="courses == null"/>
    <div class="course-list" v-else>
        <div class="row">
            <b-input-group class="col-12">
                <b-form-input v-model="filter" placeholder="Type to Search" v-on:keyup.enter="submit"/>
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
                    <b-popover class="btn-popover"
                               placement="top"
                               content="View assignments"
                               triggers="hover">
                        <b-btn class="action-button"
                               size="sm"
                               variant="success"
                               @click.stop="gotoCourse(item.item)">
                            <icon name="list"/>
                        </b-btn>
                    </b-popover>
                    <b-popover class="btn-popover"
                               placement="top"
                               content="Manage course"
                               triggers="hover"
                               v-if="canManage[item.item.id]">
                        <b-btn class="action-button"
                               @click.stop="gotoCourseEdit(item.item)"
                               size="sm"
                               variant="warning">
                            <icon name="pencil"/>
                        </b-btn>
                    </b-popover>
                    <b-popover class="btn-popover"
                            placement="top"
                            content="Delete course"
                            triggers="hover"
                            v-if="canDelete">
                        <b-button class="action-button"
                                size="sm"
                                variant="danger"
                                @click.stop="$root.$emit('show::modal',`modal_delete-${item.item.id}`)"
                                label="">
                            <icon name="times"/>
                        </b-button>
                    </b-popover>
                </b-btn-group>
                <div v-if="canDelete">
                    <b-modal :id="`modal_delete-${item.item.id}`"
                             title="Are you sure?"
                             :hide-footer="true">
                        <p style="text-align: center;">
                            By deleting this course, all related information
                            will be lost forever! This includes assignments,
                            submissions etc. Are you reallysure you want to
                            delete this course?
                        </p>
                        <b-button-toolbar justify>
                            <submit-button class="delete-confirm"
                                           :ref="`deleteButton-${item.item.id}`"
                                           default="outline-danger"
                                           @click="deleteCourse(item.item)"
                                           label="Yes"/>
                            <b-btn class="text-center"
                                   variant="success"
                                   @click="$root.$emit('hide::modal', `modal_delete-${item.item.id}`)">
                                No!
                            </b-btn>
                        </b-button-toolbar>
                    </b-modal>
                </div>
            </template>
            <template slot="empty">
                No results found.
            </template>
        </b-table>
    </div>
</template>

<script>
import { mapActions } from 'vuex';
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/pencil';
import 'vue-awesome/icons/list';
import 'vue-awesome/icons/times';

import Loader from './Loader';
import SubmitButton from './SubmitButton';

export default {
    name: 'course-list',

    data() {
        return {
            courses: null,
            canDelete: false,
            canManage: [],
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

        this.$http.get('/api/v1/permissions/', {
            params: {
                permission: 'can_manage_course',
                course_id: 'all',
            },
        }).then(({ data: canManage }) => {
            this.canManage = canManage;
        });

        this.hasPermission({
            name: 'can_create_courses',
        }).then((canDelete) => {
            this.canDelete = canDelete;
        });

        this.$http.get('/api/v1/courses/').then(({ data: courses }) => {
            this.courses = courses;
        });
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

        deleteCourse(course) {
            this.$refs[`deleteButton-${course.id}`].submit(
                this.$http.delete(`/api/v1/courses/${course.id}`).catch(({ response }) => {
                    throw response.data.message;
                }),
            ).then(() => {
                this.$root.$emit('hide::modal', `modal_delete-${course.id}`);
                this.courses = this.courses.filter(c => c.id !== course.id);
            });
        },


        submit() {
            if (this.filter) {
                this.$router.replace({ query: { q: this.filter } });
            }
        },

        ...mapActions({
            hasPermission: 'user/hasPermission',
        }),
    },

    components: {
        Icon,
        Loader,
        SubmitButton,
    },
};
</script>

<style lang="less">
.btn-popover {
    &:not(:last-child) .action-button {
        border-top-right-radius: 0;
        border-bottom-right-radius: 0;
    }

    &:not(:first-child) .action-button {
        border-top-left-radius: 0;
        border-bottom-left-radius: 0;
    }
}
</style>
