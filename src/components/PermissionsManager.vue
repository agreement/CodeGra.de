<template>
<loader v-if="loading" page-loader/>
<div class="permissions-manager" v-else>
    <b-table striped
             class="permissions-table"
             :fields="fields"
             :items="items"
             :filter="filter"
             ref="permissionTable"
             :response="true">
        <template slot="name" slot-scope="item">
            <span v-if="item.value !== 'Remove'">
                {{ item.item.title }}
                <description-popover
                    hug-text
                    :description="item.item.description"
                    placement="right"/>
            </span>
            <b v-else-if="showDeleteRole">{{ item.value }}</b>
        </template>
        <template v-for="(field, i) in fields"
                  :slot="field.key === 'name' ? `|||____$name$__||||${Math.random()}` : field.key"
                  slot-scope="item"
                  v-if="field.key != 'name'">
            <b-input-group v-if="item.item.name !== 'Remove'">
                <loader :scale="1"
                        v-if="item.item[field.key] === 'loading'"/>
                <span v-else-if="item.item.name === fixedPermission && field.own"
                      v-b-popover.top.hover="'You cannot disable this permission for yourself'">
                    <b-form-checkbox :checked="item.item[field.key]"
                                     disabled/>
                </span>
                <b-form-checkbox :checked="item.item[field.key]"
                                 @change="changeButton(item.item.name, field)"
                                 v-else/>
            </b-input-group>
            <b-input-group v-else-if="showDeleteRole">
                <submit-button :ref="`delete-perm-${i}`"
                               label="Remove"
                               default="danger"
                               @click="removeRole(i)"/>
            </b-input-group>
        </template>
    </b-table>
    <b-form-fieldset class="add-role" v-if="showAddRole">
        <b-input-group>
            <input v-model="newRoleName"
                   class="form-control"
                   placeholder="Name of new role"
                   @keyup.ctrl.enter="addRole"/>

            <submit-button label="Add"
                           ref="addUserBtn"
                               @click="addRole"/>
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
import SubmitButton from './SubmitButton';

export default {
    name: 'permissions-manager',

    props: {
        courseId: {},

        filter: {
            type: String,
            default: '',
        },

        fixedPermission: {
            default: 'can_edit_course_roles',
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
            fields: [],
            items: [],
            newRoleName: '',
        };
    },

    watch: {
        courseId() {
            this.loadData();
        },
    },

    methods: {
        async loadData() {
            this.loading = true;
            await this.getAllPermissions();
            this.loading = false;
        },

        getAllPermissions() {
            return this.$http.get(this.getRetrieveUrl(this.courseId)).then(({ data }) => {
                const fields = [{
                    key: 'name',
                    label: 'Name',
                    sortable: true,
                }];

                this.items = [];

                data.forEach((item) => {
                    fields.push({
                        key: item.name,
                        label: item.name,
                        sortable: true,
                        id: item.id,
                        own: item.own,
                    });

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

                this.fields = fields;
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
            const newValue = !item[field.key];
            item[field.key] = 'loading';
            this.$set(this.items, i, item);
            this.$http.patch(this.getChangePermUrl(this.courseId, field.id), {
                value: newValue,
                permission: item.name,
            }).then(() => {
                item[field.key] = newValue;
                this.$set(this.items, i, item);
            });
        },

        removeRole(index) {
            const perm = this.fields[index];
            const button = this.$refs[`delete-perm-${index}`][0];

            const req = this.$http.delete(
                this.getDeleteRoleUrl(
                    this.courseId,
                    perm.id,
                ),
            ).catch(({ response }) => {
                throw response.data.message;
            });

            button.submit(req).then(() => {
                this.fields.splice(index, 1);
            });
        },

        addRole() {
            const button = this.$refs.addUserBtn;
            if (this.newRoleName === '') {
                button.fail('The name cannot be empty!');
            } else {
                const req = this.$http.post(`/api/v1/courses/${this.courseId}/roles/`, {
                    name: this.newRoleName,
                }).then(() => {
                    this.getAllPermissions().then(() => {
                        this.newRole = '';
                        this.newRoleName = '';
                    });
                }, ({ response }) => {
                    throw response.data.message;
                });
                button.submit(req);
            }
        },
    },

    mounted() {
        this.loadData();
    },

    components: {
        Icon,
        Loader,
        SubmitButton,
        DescriptionPopover,
    },
};
</script>

<style lang="less">
.permissions-manager {
    table.permissions-table {
        margin-bottom: 0;
        .delete .loader {
            height: 1.25rem;
        }
        th {
            border-top: none;
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
        }
    }
    .add-role {
        .btn {
            border-top-left-radius: 0;
            border-bottom-left-radius: 0;
        }
    }
}
</style>

<style lang="less" scoped>
.info-popover {
    cursor: pointer;
    display: inline-block;

    sup {
        padding: 0 .25em;
    }
}

.add-role {
    margin-top: 1rem;
}
</style>
