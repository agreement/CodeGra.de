<template>
    <loader v-if="loading"/>
    <div class="permission-manager" v-else>
        <b-form-fieldset>
            <b-form-input v-model="filter"
                          placeholder="Type to Search"
                          v-on:keyup.enter="submit"/>
        </b-form-fieldset>
        <div class="table-wrapper">
            <b-table striped
                    class="permissions-table"
                    :fields="fields"
                    :items="items"
                    :filter="filter"
                    :response="true">

                <template slot="name" scope="item">
                    <span v-if="item.value !== 'Remove'">
                        {{ item.item.title }}
                        <description-popover
                            hug-text
                            :description="item.item.description"
                            placement="right"/>
                    </span>
                    <b v-else-if="showDeleteRole">{{ item.value }}</b>
                </template>
                <template v-for="(_, field) in fields" :slot="field === 'name' ? `|||____$name$__||||${Math.random()}` : field" scope="item" v-if="field != 'name'">
                    <b-input-group v-if="item.item.name !== 'Remove'">
                        <loader :scale="1"
                                v-if="item.item[field] === 'loading'"/>
                        <b-popover content="You cannot disable this permission for yourself"
                                triggers="hover"
                                v-else-if="item.item.name === fixedPermission && fields[field].own">
                            <b-form-checkbox :checked="item.item[field]"
                                            disabled class="disabled"/>
                        </b-popover>
                        <b-form-checkbox :checked="item.item[field]"
                                        @change="changeButton(item.item.name, field)"
                                        v-else/>
                    </b-input-group>
                    <b-input-group v-else-if="showDeleteRole">
                        <b-popover :show="!!errors[field]"
                                :content="errors[field] ? errors[field] : ''">
                            <b-button class="delete"
                                    :variant="deleted[field] ? 'success' : 'danger'"
                                    @click="removeRole(field)">
                                <loader :scale="1" v-if="deleting[field]"/>
                                <span v-else>Remove</span>
                            </b-button>
                        </b-popover>
                    </b-input-group>
                </template>
            </b-table>
        </div>
        <b-form-fieldset class="add-role" v-if="showAddRole">
            <b-input-group>
                <b-form-input v-model="newRoleName"
                              placeholder="Name of new role"
                              @keyup.native.ctrl.enter="addRole"/>

                <b-popover :show="addError !== ''" :content="addError">
                    <b-button-group>
                        <b-button :variant="done ? 'success' : 'primary'"
                                  @click="addRole">
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
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/times';
import 'vue-awesome/icons/pencil';
import 'vue-awesome/icons/floppy-o';
import 'vue-awesome/icons/ban';
import 'vue-awesome/icons/info';

import DescriptionPopover from './DescriptionPopover';
import Loader from './Loader';

export default {
    name: 'permissions-manager',

    props: {
        courseId: {},

        fixedPermission: {
            default: 'can_manage_course',
            type: String,
        },

        showDeleteRole: {
            type: Boolean,
            default: true,
        },

        showAddRole: {
            type: Boolean,
            default: true,
        },

        getRetrieveUrl: {
            type: Function,
            default: courseId => `/api/v1/courses/${courseId}/roles/?with_roles=true`,
        },

        getChangePermUrl: {
            type: Function,
            default: (courseId, roleId) => `/api/v1/courses/${courseId}/roles/${roleId}`,
        },

        getDeleteRoleUrl: {
            type: Function,
            default: (courseId, roleId) => `/api/v1/courses/${courseId}/roles/${roleId}`,
        },
    },

    data() {
        return {
            loading: true,
            filter: '',
            roles: [],
            fields: {},
            items: [],
            deleting: {},
            deleted: {},
            errors: {},
            addError: '',
            newRoleName: '',
            done: false,
            adding: false,
        };
    },

    methods: {
        getAllPermissions() {
            return this.$http.get(this.getRetrieveUrl(this.courseId)).then(({ data }) => {
                this.roles = data;
                this.fields = {
                    name: {
                        label: 'Name',
                        sortable: true,
                    },
                };
                this.items = [];
                data.forEach((item) => {
                    this.fields[item.name] = {
                        label: item.name,
                        sortable: true,
                        id: item.id,
                        own: item.own,
                    };
                    let i = 0;
                    Object.entries(item.perms).forEach(([name, value]) => {
                        if (!this.items[i]) {
                            this.items[i] = {
                                name,
                                title: Permissions[name].short_description,
                                description: Permissions[name].long_description,
                            };
                        }
                        this.items[i][item.name] = value;
                        i += 1;
                    });
                });
                if (this.showDeleteRole) {
                    this.items.push({ name: 'Remove' });
                }
            });
        },
        changeButton(permName, field) {
            let i = 0;
            for (let len = this.items.length; i < len; i += 1) {
                if (permName === this.items[i].name) {
                    break;
                }
            }
            const item = this.items[i];
            const newValue = !item[field];
            item[field] = 'loading';
            this.$set(this.items, i, item);
            this.$http.patch(this.getChangePermUrl(this.courseId, this.fields[field].id), {
                value: newValue,
                permission: item.name,
            }).then(() => {
                item[field] = newValue;
                this.$set(this.items, i, item);
            });
        },
        removeRole(perm) {
            this.$set(this.deleting, perm, true);
            this.$http.delete(this.getDeleteRoleUrl(this.courseId, this.fields[perm].id))
                .then(() => {
                    this.$set(this.deleting, perm, false);
                    delete this.deleting[perm];
                    this.$set(this.deleted, perm, true);
                    this.$nextTick(() => setTimeout(() => {
                        this.$set(this.deleted, perm, false);
                        this.$set(this.fields, perm, {});
                        delete this.fields[perm];
                    }, 1000));
                }).catch(({ response }) => {
                    this.$set(this.deleting, perm, false);
                    delete this.deleting[perm];

                    this.$set(this.errors, perm, response.data.message);

                    this.$nextTick(() => setTimeout(() => {
                        this.$set(this.errors, perm, false);
                    }, 1000));
                });
        },
        addRole() {
            this.done = false;
            const clearErr = out => this.$nextTick(() => setTimeout(() => {
                this.addError = '';
            }, out));
            if (this.newRoleName === '') {
                this.error = 'The name cannot be empty!';
                clearErr(4000);
            } else {
                this.addError = '';
                this.adding = true;
                this.$http.post(`/api/v1/courses/${this.courseId}/roles/`, {
                    name: this.newRoleName,
                }).then(() => {
                    this.getAllPermissions().then(() => {
                        this.adding = false;
                        this.newRole = '';
                        this.newRoleName = '';
                        this.done = true;
                        this.$nextTick(() => setTimeout(() => {
                            this.done = false;
                        }, 4000));
                    });
                }).catch(({ response }) => {
                    this.adding = false;
                    this.addError = `${response.data.message}!`;
                    clearErr(6000);
                });
            }
        },
    },

    mounted() {
        Promise.all([
            this.getAllPermissions(),
        ]).then(() => {
            this.loading = false;
        });
    },

    components: {
        Icon,
        Loader,
        DescriptionPopover,
    },
};
</script>

<style lang="less">
table.permissions-table {
    .delete .loader {
        height: 1.25rem;
    }
    tr {
        :first-child {
            vertical-align: middle;
        }
        :not(:first-child) {
            vertical-align: middle;
            text-align: center;
            .input-group {
                align-items: center;
                justify-content: center;
            }
        }
        .custom-checkbox.disabled {
            cursor: not-allowed !important;
        }
    }
}
</style>

<style lang="less" scoped>
.add-role {
    .btn-group {
        height: 100%;
    }
    .btn {
        border-top-left-radius: 0;
        border-bottom-left-radius: 0;
    }
}
.table-wrapper {
    width: 100%;
    overflow-x: auto;
    margin-bottom: 0.3em;
}

.info-popover {
    cursor: pointer;
    display: inline-block;

    sup {
        padding: 0 .25em;
    }
}
</style>
