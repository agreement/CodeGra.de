<template>
    <loader v-if="loading"/>
    <div class="users-manager" v-else>
        <b-form-fieldset>
            <b-form-input v-model="filter"
                          placeholder="Type to Search"
                          v-on:keyup.enter="submit"/>
        </b-form-fieldset>
        <b-table striped hover
                 class="users-table"
                 :items="users"
                 :fields="fields"
                 :filter="filter"
                 :response="true">

            <template slot="User" scope="item">
                <span>{{item.value.name}}</span>
            </template>

            <template slot="CourseRole" scope="item">
                <loader :scale="1" v-if="updating[item.item.User.id]"/>
                <b-popover content="You cannot change your own role"
                           triggers="hover"
                           v-if="item.item.User.name == userName">
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

        <b-form-fieldset class="add-student">
            <b-input-group>
                <b-form-input v-model="newStudentEmail"
                              placeholder="New students e-mail"/>

                <b-dropdown class="drop" :text="newRole ? newRole.name : 'Role'">
                    <b-dropdown-item v-for="role in roles"
                                     v-on:click="() => {newRole = role; error = '';}"
                                     :key="role.id">
                        {{ role.name }}
                    </b-dropdown-item>
                </b-dropdown>

                <b-popover :show="error !== ''" :content="error">
                <b-button-group>
                    <b-button :variant="done ? 'success' : 'primary'"
                              @click="addUser">
                        <loader :scale="1"
                                class=""
                                v-if="adding"/>
                        <span v-else>Add</span>
                    </b-button>
                </b-button-group>
                </b-popover>
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

import Loader from './Loader';

const validator = require('email-validator');

export default {
    name: 'users-manager',

    data() {
        return {
            roles: [],
            courseId: this.$route.params.courseId,
            users: [],
            loading: true,
            filter: '',
            updating: {},
            newStudentEmail: '',
            newRole: '',
            error: '',
            done: false,
            adding: false,
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
            }).catch(err => console.dir(err));
        },
        addUser() {
            this.done = false;
            const clearErr = out => this.$nextTick(() => setTimeout(() => {
                this.error = '';
            }, out));
            if (this.newRole === '') {
                this.error = 'You have to select a role!';
            } else if (!validator.validate(this.newStudentEmail)) {
                this.error = 'You have to add a valid email!';
                clearErr(4000);
            } else {
                this.error = '';
                this.adding = true;
                this.$http.put(`/api/v1/courses/${this.courseId}/users/`, {
                    user_email: this.newStudentEmail,
                    role_id: this.newRole.id,
                }).then(({ data }) => {
                    this.adding = false;
                    this.newRole = '';
                    this.newStudentEmail = '';
                    this.users.push(data);
                    this.done = true;
                    this.$nextTick(() => setTimeout(() => {
                        this.done = false;
                    }, 1000));
                }).catch(({ response }) => {
                    this.error = `${response.data.message}!`;
                    clearErr(6000);
                });
            }
        },
    },

    mounted() {
        Promise.all([
            this.getAllUsers(),
            this.getAllRoles(),
        ]).then(() => {
            this.loading = false;
        });
    },

    components: {
        Icon,
        Loader,
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
