<template>
    <loader v-if="loading"/>
    <div class="users-manager" v-else>
        <b-form-fieldset>
            <b-form-input v-model="filter"
                          placeholder="Type to Search"
                          v-on:keyup.enter="submit"/>
        </b-form-fieldset>
        <b-table striped
                 ref="table"
                 class="users-table"
                 :items="users"
                 :fields="fields"
                 :filter="filter"
                 :sort-compare="sortTable"
                 sort-by="User"
                 :response="true">

            <template slot="User" scope="item">
                <span>{{item.value.name}} ({{item.value.username}})</span>
            </template>

            <template slot="CourseRole" scope="item">
                <loader :scale="1" v-if="updating[item.item.User.id]"/>
                <b-popover content="You cannot change your own role"
                           triggers="hover"
                           v-else-if="item.item.User.name == userName">
                    <b-dropdown :text="item.value.name"
                                disabled/>
                </b-popover>
                <b-dropdown :text="item.value.name"
                            :disabled="item.item.User.name == userName"
                            v-else>
                    <b-dropdown-header>Select the new role</b-dropdown-header>
                    <b-dropdown-item v-for="role in roles"
                                     v-on:click="changed(item.item, role)"
                                     :key="role.id">
                        {{ role.name }}
                    </b-dropdown-item>
                </b-dropdown>
            </template>
        </b-table>

        <b-popover class="new-user-popover"
                :triggers="course.is_lti ? 'hover' : ''"
                content="You cannot add users to a lti course.">
            <b-form-fieldset class="add-student">
                <b-input-group>
                    <b-form-input v-model="newStudentUsername"
                                  placeholder="New students username"
                                  :disabled="course.is_lti"
                                  @keyup.native.ctrl.enter="addUser"/>

                    <b-dropdown class="drop"
                                :text="newRole ? newRole.name : 'Role'"
                                :disabled="course.is_lti">
                        <b-dropdown-item v-for="role in roles"
                                        v-on:click="() => {newRole = role; error = '';}"
                                        :key="role.id">
                            {{ role.name }}
                        </b-dropdown-item>
                    </b-dropdown>

                    <b-input-group-button>
                            <submit-button label="Add" ref="addUserButton" @click="addUser" :disabled="course.is_lti"/>
                    </b-input-group-button>
                </b-input-group>
            </b-form-fieldset>
        </b-popover>

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

export default {
    name: 'users-manager',
    props: ['course'],

    data() {
        return {
            roles: [],
            courseId: this.$route.params.courseId,
            users: [],
            loading: true,
            filter: '',
            updating: {},
            newStudentUsername: '',
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
    },

    methods: {
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
            } else if (this.newStudentUsername === '') {
                btn.fail('You have to add a non empty username!');
            } else {
                btn.submit(this.$http.put(`/api/v1/courses/${this.courseId}/users/`, {
                    username: this.newStudentUsername,
                    role_id: this.newRole.id,
                }).then(({ data }) => {
                    this.newRole = '';
                    this.newStudentUsername = '';
                    this.users.push(data);
                }, (({ response }) => {
                    throw response.data.message;
                })));
            }
        },
    },

    mounted() {
        Promise.all([
            this.getAllUsers(),
            this.getAllRoles(),
        ]).then(() => {
            this.loading = false;
            this.$nextTick(() => {
                this.$refs.table.sortBy = 'User';
            });
        });
    },

    components: {
        Icon,
        Loader,
        SubmitButton,
    },
};
</script>

<style lang="less">
table.users-table tr th:first-child {
    width: 50%;
}
table.users-table tr th:nth-child(2) {
    width: 50%;
}

table.users-table tr :nth-child(2) {
    text-align: center;
}
table.users-table tr {
    td {
        vertical-align: middle;
    }
    td:first-child span {
        line-height: 1.25;
        padding: 0.5rem 0;
        display: block;
    }
}

table.users-table .dropdown {
    width: 25%;
    .btn {
        width: 100%;
    }
}

.add-student .drop .btn {
    border-radius: 0;
}

.new-user-popover button {
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
}
</style>

<style lang="less" scoped>
.add-student {
    .btn-group {
        height: 100%;
    }
    .btn {
        border-top-left-radius: 0;
        border-bottom-left-radius: 0;
    }
}
</style>
