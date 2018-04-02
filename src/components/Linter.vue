<template>
<div class="linter">
    <div class="align-middle description">
        <p>{{ description }}</p>
        <hr>
        <div v-if="state == 'new'"
             :class="{ 'lonely-start-button-wrapper' : Object.keys(options).length == 0 }">
            <div v-if="Object.keys(options).length > 0">
                <b-button-toolbar justify class="margin">
                    <b-dropdown :text="selectedOption">
                        <b-dropdown-header>Select your config file</b-dropdown-header>
                        <b-dropdown-item v-for="(_, optionName) in options"
                                         @click="clicked(false, optionName)"
                                         :key="optionName">
                            {{ optionName }}
                        </b-dropdown-item>
                        <b-dropdown-divider/>
                        <b-dropdown-item @click="clicked(true, 'Custom config')">Custom config</b-dropdown-item>
                    </b-dropdown>
                    <b-btn variant="primary"
                           :disabled="Object.keys(options).length !== 0 && selectedOption === 'Select config file'"
                           @click="run">
                        <loader :scale="1" v-if="starting"/>
                        <span v-else>Run</span>
                    </b-btn>
                </b-button-toolbar>

                <b-collapse :id="`sub_collapse_${name}_${assignment.id}`">
                    <form>
                        <textarea class="form-control margin"
                                  rows="10"
                                  placeholder="Enter your custom config"
                                  v-model="config"/>
                    </form>
                </b-collapse>
            </div>

            <b-btn variant="primary"
                   v-else
                   :disabled="Object.keys(options).length !== 0 && selectedOption === 'Select config file'"
                   @click="run">
                <loader :scale="1" v-if="starting"/>
                <span v-else>Run</span>
            </b-btn>
        </div>
        <div v-else-if="state == 'running'">
            <b-progress v-model="done"
                        :max="done + working + crashed"
                        :precision="1"
                        animated/>
            <span class="text-center progress-text">{{ done }} out of {{ working + done }}</span>
        </div>
        <div v-else>
            <div class="row justify-content-md-center">
                <b-btn class="text-center margin btn delete"
                       variant="danger"
                       @click="$root.$emit('bv::show::modal',`modal_${name}_${assignment.id}`)">
                    <span v-if="crashed > 0 || state === 'crashed'">Crashed! - </span>Remove output
                </b-btn>
                <b-modal :id="`modal_${name}_${assignment.id}`"
                         title="Are you sure?"
                         :hide-footer="true">
                    <div class="row justify-content-md-center"
                         v-if="deleting">
                        <b-btn class="text-center" variant="outline-danger"><loader :scale="1"/></b-btn>
                    </div>
                    <div v-else>
                        <b-btn class="text-center"
                               variant="outline-danger"
                               v-on:click="deleteFeedback">
                            Yes, delete this data.
                        </b-btn>
                        <b-btn class="text-center right-float"
                               variant="success"
                               v-on:click="$root.$emit('bv::hide::modal', `modal_${name}_${assignment.id}`)">
                            No!
                        </b-btn>
                    </div>
                </b-modal>
            </div>
        </div>
    </div>
</div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/check';
import 'vue-awesome/icons/times';

import Loader from './Loader';

export default {
    name: 'linter',

    props: [
        'name',
        'options',
        'initialState',
        'initialId',
        'assignment',
        'serverDescription',
    ],

    data() {
        return {
            selectedOption: 'Select config file',
            show: {},
            state: 'new',
            config: '',
            deleting: false,
            id: undefined,
            done: 0,
            working: 0,
            crashed: 0,
            starting: false,
        };
    },

    computed: {
        description() {
            return this.serverDescription;
        },
    },

    mounted() {
        this.state = this.initialState;
        this.id = this.initialId;
        if (this.state === 'running') {
            this.startUpdateLoop();
        }
    },

    components: {
        Loader,
        Icon,
    },

    methods: {
        strState() {
            return this.state.charAt(0).toUpperCase() + this.state.slice(1);
        },
        changeSubCollapse(state) {
            if (Boolean(this.collapseState) !== state) {
                this.$root.$emit('bv::toggle::collapse', `sub_collapse_${this.name}_${this.assignment.id}`);
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
                this.$root.$emit('bv::hide::modal', `modal_${this.name}_${this.assignment.id}`);

                this.selected = false;
                this.deleting = false;

                this.$root.$emit('collapse::toggle', `collapse_${this.name}_${this.assignment.id}`);

                this.$nextTick(() => {
                    this.state = 'new';
                });
            });
        },
        startUpdateLoop() {
            this.$http.get(`/api/v1/linters/${this.id}`)
                .then(({ data }) => this.updateData(data));
        },
        updateData(data) {
            this.done = data.done;
            this.working = data.working;
            this.crashed = data.crashed;
            this.id = data.id;

            if (this.crashed > 0) {
                this.state = 'crashed';
            } else if (this.working === 0) {
                this.state = 'done';
            } else {
                this.state = 'running';
                this.$nextTick(() => {
                    setTimeout(() => this.startUpdateLoop(), 1000);
                });
            }
        },

        run() {
            let cfg;
            if (this.selectedOption === 'Custom config') {
                cfg = this.config;
            } else if (this.selectedOption) {
                cfg = this.options[this.selectedOption];
            }

            this.done = 0;
            this.working = 0;
            this.crashed = 0;

            this.starting = true;

            this.$http.post(`/api/v1/assignments/${this.assignment.id}/linter`, {
                name: this.name,
                cfg: cfg || '',
            }).then(({ data }) => {
                this.starting = false;
                this.updateData(data);
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

.progress-text {
    display: block;
    margin: 15px 0;
}

.lonely-start-button-wrapper {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 15px;
}

.btn.delete {
    height: 3em;
    margin-top: 0;
    min-width: 14em;
}
</style>
