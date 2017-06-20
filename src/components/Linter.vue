<template>
    <tr>
        <!-- TODO: Fix issues with iterations by relying on order !-->
        <td class="align-middle">{{ name }}</td>

        <td class="align-middle">
            {{ description }}
            <b-collapse :id="`collapse_${name}`" class="mt-2">
            <div v-if="state == -1">
                <div>
                <b-dropdown :text="selectedOption" class="margin">
                    <b-dropdown-header>Select your config file</b-dropdown-header>
                    <b-dropdown-item v-for="(_, optionName) in options" v-on:click="clicked(false, optionName)" :key="optionName">
                        {{ optionName }}
                    </b-dropdown-item>
                    <b-dropdown-divider></b-dropdown-divider>
                    <b-dropdown-item v-on:click="clicked(true, 'Custom config')">Custom config</b-dropdown-item>
                </b-dropdown>
                <b-collapse :id="`sub_collapse_${name}`">
                    <form>
                        <b-form-input class="margin" :textarea="true" :rows="10" placeholder="Enter your custom config" v-model="config">
                        </b-form-input>
                    </form>
                </b-collapse>
                </div>
                <b-btn variant="primary" :disabled="selectedOption === 'Select config file'" v-on:click="run">Run!</b-btn>
            </div>
            <div v-else-if="state == 1">
                <table class="table trans center-table">
                    <thead>
                        <tr>
                        <th>Name</th>
                        <th>State</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="(item, _) in children">
                        <td>{{ item[0] }}</td>
                        <td align="center">
                            <loader :scale="1" v-if="item[1] == 1"/>
                            <icon name="check" v-else-if="item[1] == 2"/>
                            <icon name="times" v-else-if="item[1] == 3"/>
                        </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <div v-else-if="state == 2 || state == 3">
                <div class="row justify-content-md-center">
                    <b-btn class="text-center margin large-btn" variant="danger" @click="$root.$emit('show::modal',`modal_${name}`)">Remove output</b-btn>
                    <b-modal :id="`modal_${name}`" title="Are you sure?" :hide-footer="true">
                        <div class="row justify-content-md-center" v-if="deleting">
                            <b-btn class="text-center" variant="outline-danger"><loader :scale="1"/></b-btn>
                        </div>
                        <div v-else>
                            <b-btn class="text-center" variant="outline-danger" v-on:click="deleteFeedback">Yes, delete this data.</b-btn>
                            <b-btn class="text-center right-float" variant="success" v-on:click="$root.$emit('hide::modal', `modal_${name}`)">No!</b-btn>
                        </div>
                    </b-modal>
                </div>
            </div>
            </b-collapse>
        </td>
        <td class="align-middle">{{ strState() }}</td>
        <td><b-btn v-b-toggle="`collapse_${name}`" v-on:click="opened = !opened" variant="primary">{{ opened ? 'Less' : 'More' }}</b-btn></td>
    </tr>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/check';
import 'vue-awesome/icons/times';

import Loader from './Loader';

export default {
    name: 'linter',

    props: ['name', 'options', 'description', 'initialState', 'initialId', 'assignment'],

    data() {
        return {
            selectedOption: 'Select config file',
            show: {},
            state: -1,
            config: '',
            deleting: false,
            opened: false,
            id: undefined,
        };
    },

    mounted() {
        this.state = this.initialState;
        this.id = this.initialId;
        if (this.state === 1) {
            this.startUpdateLoop();
        }
    },

    components: {
        Loader,
        Icon,
    },

    methods: {
        strState() {
            switch (this.state) {
            case -1: return 'New';
            case 1: return 'Running';
            case 2: return 'Done';
            case 3: return 'Crashed';
            default: throw new TypeError('Wrong State!');
            }
        },
        changeSubCollapse(state) {
            if (Boolean(this.collapseState) !== state) {
                this.$root.$emit('collapse::toggle', `sub_collapse_${this.name}`);
                this.collapseState = !this.collapseState;
            }
        },

        clicked(collapseState, selectedName) {
            this.selectedOption = selectedName;
            this.$nextTick(() => {
                this.linter = this.changeSubCollapse(collapseState);
            });
        },

        deleteFeedback() {
            this.deleting = true;
            this.$http.delete(`/api/v1/linters/${this.id}`).then(() => {
                this.$root.$emit('hide::modal', `modal_${this.name}`);

                this.selected = false;
                this.opened = false;
                this.deleting = false;
                this.$root.$emit('collapse::toggle', `collapse_${this.name}`);

                this.$nextTick(() => {
                    this.state = -1;
                });
            });
        },
        startUpdateLoop(time) {
            const timeout = time === undefined ? 1000 : time;
            this.$http.get(`/api/v1/linters/${this.id}`).then((data) => {
                this.children = data.data.children;
                this.state = 1;
                if (!data.data.done) {
                    this.$nextTick(() => {
                        setTimeout(() => this.startUpdateLoop(timeout * 2), timeout);
                    });
                } else {
                    this.state = data.data.crashed ? 3 : 2;
                }
            });
        },
        run() {
            let cfg;
            if (this.selected === 'Custom config') {
                cfg = this.config === undefined ? '' : this.config;
            } else {
                cfg = this.options[this.selectedOption];
            }
            this.$http.post(`/api/v1/assignments/${this.assignment.id}/linter`, {
                name: this.name,
                cfg,
            }).then((data) => {
                this.state = 1;
                this.children = data.data.children;
                this.id = data.data.id;
                this.$nextTick(() => {
                    setTimeout(() => this.startUpdateLoop(), 3000);
                });
            });
        },
    },
};
</script>

<style lang="less" scoped>
.margin {
    margin-bottom: 15px;
}

.large-btn {
    margin-top: 1em;
    padding: 15px 5em;
}
.right-float {
    float: right;
}

.center-table {
    text-align: center;
}
.center-table th {
    text-align: center;
}

.table-striped tbody tr:nth-of-type(even) table.trans tr {
    background-color: rgba(0, 0, 0, 0.05);
}
.table-striped tbody tr:nth-of-type(odd) table.trans tr {
    background-color: #fff;
}

button {
    cursor: pointer;
}
</style>
