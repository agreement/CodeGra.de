<template>
<loader v-if="loading" page-loader/>
<div class="users-manager" v-else>
    <b-table striped
             ref="table"
             class="users-table"
             :items="users"
             :fields="fields"
             :filter="filter"
             :sort-compare="sortTable"
             sort-by="User"
             :response="true">

        <template slot="User" slot-scope="item">
            <span class="username">{{item.value.name}} ({{item.value.username}})</span>
        </template>

        <template slot="CourseRole" slot-scope="item">
            <loader :scale="1" v-if="updating[item.item.User.id]"/>
            <b-dropdown :text="item.value.name"
                        disabled
                        v-b-popover.top.hover="'You cannot change your own role'"
                        v-else-if="item.item.User.name == userName"/>
            <b-dropdown :text="item.value.name"
                        :disabled="item.item.User.name == userName"
                        v-else>
                <b-dropdown-header>Select the new role</b-dropdown-header>
                <b-dropdown-item v-for="role in roles"
                                 @click="changed(item.item, role)"
                                 :key="role.id">
                    {{ role.name }}
                </b-dropdown-item>
            </b-dropdown>
        </template>
    </b-table>

    <b-popover class="new-user-popover"
               :triggers="course.is_lti ? 'hover' : ''"
               target="new-users-input-field">
        You cannot add users to a lti course.
    </b-popover>
    <b-form-fieldset class="add-student"
                     id="new-users-input-field">
        <b-input-group>
            <user-selector v-model="newStudentUsername"
                           placeholder="New student"
                           :disabled="course.is_lti"/>

            <template slot="append">
                <b-dropdown class="drop"
                            :text="newRole ? newRole.name : 'Role'"
                            :disabled="course.is_lti">
                    <b-dropdown-item v-for="role in roles"
                                     v-on:click="() => {newRole = role; error = '';}"
                                     :key="role.id">
                        {{ role.name }}
                    </b-dropdown-item>
                </b-dropdown>
                <submit-button label="Add"
                               ref="addUserButton"
                               @click="addUser"
                               class="add-user-button"
                               :disabled="course.is_lti"/>
            </template>
        </b-input-group>
    </b-form-fieldset>
</div>
</template>

<script>
import { mapGetters } from 'vuex';
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/times';
import 'vue-awesome/icons/pencil';
import 'vue-awesome/icons/floppy-o';
import 'vue-awesome/icons/ban';

import { cmpNoCase, cmpOneNull } from '@/utils';
import Loader from './Loader';
import SubmitButton from './SubmitButton';
import UserSelector from './UserSelector';

export default {
    name: 'users-manager',
    props: {
        course: {
            type: Object,
            default: null,
        },

        filter: {
            type: String,
            default: '',
        },
    },

    data() {
        return {
            roles: [],
            users: [],
            loading: true,
            updating: {},
            newStudentUsername: null,
            newRole: '',
            error: '',
            fields: {
                User: {
                    label: 'Name',
                    sortable: true,
                },
                CourseRole: {
                    label: 'role',
                    sortable: true,
                },
            },
        };
    },

    computed: {
        ...mapGetters('user', {
            userName: 'name',
        }),

        courseId() {
            return this.course.id;
        },
    },

    watch: {
        course() {
            this.loadData();
        },
    },

    mounted() {
        this.loadData();
    },

    methods: {
        async loadData() {
            this.loading = true;

            await Promise.all([
                this.getAllUsers(),
                this.getAllRoles(),
            ]);

            this.loading = false;
            this.$nextTick(() => {
                this.$refs.table.sortBy = 'User';
            });
        },

        sortTable(a, b, sortBy) {
            if (typeof a[sortBy] === 'number' && typeof b[sortBy] === 'number') {
                return a[sortBy] - b[sortBy];
            } else if (sortBy === 'User') {
                const first = a[sortBy];
                const second = b[sortBy];

                const ret = cmpOneNull(first, second);

                return ret === null ? cmpNoCase(first.name, second.name) : ret;
            } else if (sortBy === 'CourseRole') {
                const first = a.CourseRole;
                const second = b.CourseRole;

                const ret = cmpOneNull(first, second);

                return ret === null ? cmpNoCase(first.name, second.name) : ret;
            }
            return 0;
        },

        getAllUsers() {
            return this.$http.get(`/api/v1/courses/${this.courseId}/users/`).then(({ data }) => {
                this.users = data;
            });
        },

        getAllRoles() {
            return this.$http.get(`/api/v1/courses/${this.courseId}/roles/`).then(({ data }) => {
                this.roles = data;
            });
        },

        changed(user, role) {
            for (let i = 0, len = this.users.length; i < len; i += 1) {
                if (this.users[i].User.id === user.User.id) {
                    this.$set(user, 'CourseRole', role);
                    this.$set(this.users, i, user);
                    break;
                }
            }
            this.$set(this.updating, user.User.id, true);
            this.$http.put(`/api/v1/courses/${this.courseId}/users/`, {
                user_id: user.User.id,
                role_id: role.id,
            }).then(() => {
                this.$set(this.updating, user.User.id, false);
                delete this.updating[user.User.id];
            }).catch((err) => {
                // eslint-disable-next-line
                console.dir(err)
            });
        },

        addUser() {
            const btn = this.$refs.addUserButton;

            if (this.newRole === '') {
                btn.fail('You have to select a role!');
            } else if (this.newStudentUsername == null || this.newStudentUsername.username === '') {
                btn.fail('You have to add a non empty username!');
            } else {
                btn.submit(this.$http.put(`/api/v1/courses/${this.courseId}/users/`, {
                    username: this.newStudentUsername.username,
                    role_id: this.newRole.id,
                }).then(({ data }) => {
                    this.newRole = '';
                    this.newStudentUsername = null;
                    this.users.push(data);
                }, ({ response }) => {
                    throw response.data.message;
                }));
            }
        },
    },

    components: {
        Icon,
        Loader,
        SubmitButton,
        UserSelector,
    },
};
</script>

<style lang="less">
.users-table tr :nth-child(2) {
    text-align: center;
}

.users-table th,
.users-table td {
    &:last-child {
        width: 1px;
    }
}

.users-table td {
    vertical-align: middle;
}

.users-table .dropdown .btn {
    width: 10rem;
}

.add-student .drop .btn {
    border-radius: 0;
}

.new-user-popover button {
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
}

.username {
    word-wrap: break-word;
    word-break: break-word;
    -ms-word-break: break-all;

    -webkit-hyphens: auto;
    -moz-hyphens: auto;
    -ms-hyphens: auto;
    hyphens: auto;
}
</style>

<style lang="less">
.add-user-button {
    .btn {
        border-top-left-radius: 0;
        border-bottom-left-radius: 0;
        height: 100%;
    }
}
</style>
