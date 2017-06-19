<template>
  <!-- TODO: Fix issues with iterations by relying on order !-->
  <div class="row justify-content-md-center" v-if="loading">
    <loader/>
  </div>
  <div class="" v-else>
    <table class="table table-striped">
      <thead>
        <tr>
          <th>Name</th>
          <th>Description</th>
          <th>State</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(linter, key) in linters">
          <td class="align-middle">{{ key }}</td>

          <td class="align-middle">
            {{ linter.desc }}
            <b-collapse :id="`collapse_${key}`" class="mt-2">
              <div v-if="linter.state == -1">
                <div>
                  <b-dropdown :text="linter.selected ? linter.selected : `Select config file`" class="margin">
                    <b-dropdown-header>Select your config file</b-dropdown-header>
                    <b-dropdown-item v-for="(_, name) in linter.opts" v-on:click="clicked(false, key, name)">
                      {{ name }}
                    </b-dropdown-item>
                    <b-dropdown-divider></b-dropdown-divider>
                    <b-dropdown-item v-on:click="clicked(true, key, 'Custom config')">Custom config</b-dropdown-item>
                  </b-dropdown>
                  <b-collapse :id="`sub_collapse_${key}`">
                    <form>
                      <b-form-input class="margin" :textarea="true" :rows="10" placeholder="Enter your custom config" v-model="linters[key].config">
                      </b-form-input>
                    </form>
                  </b-collapse>
                </div>
                <loader v-if="linter.loading"></loader>
                <b-btn variant="primary" :disabled="!linter.selected" v-on:click="runLinter(linter, key)">Run!</b-btn>
              </div>
              <div v-else-if="linter.state == 1">
                <table class="table trans center-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>State</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, _) in linter.children">
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
              <div v-else-if="linter.state == 2 || linter.state == 3">
                <div class="row justify-content-md-center">
                  <b-btn class="text-center margin large-btn" variant="danger" @click="$root.$emit('show::modal',`modal_${key}`)">Remove output</b-btn>
                  <b-modal :id="`modal_${key}`" title="Are you sure?" :hide-footer="true">
                    <div class="row justify-content-md-center" v-if="linter.deleting">
                      <b-btn class="text-center" variant="outline-danger"><loader :scale="1"/></b-btn>
                    </div>
                    <div v-else>
                      <b-btn class="text-center" variant="outline-danger" v-on:click="deleteLinterFeedback(key)">Yes, delete this data.</b-btn>
                      <b-btn class="text-center right-float" variant="success" v-on:click="$root.$emit('hide::modal', `modal_${key}`)">No!</b-btn>
                    </div>
                  </b-modal>
                </div>
              </div>
            </b-collapse>
          </td>
          <td class="align-middle">{{ getLinterState(linter) }}</td>
          <td><b-btn v-b-toggle="`collapse_${key}`" v-on:click="$set(linter, 'opened', !linter.opened)" variant="primary">{{ linter.opened ? 'Less' : 'More' }}</b-btn></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/check';
import 'vue-awesome/icons/times';

import Loader from './Loader';

export default {
    name: 'linters',

    props: ['feedback'],

    data() {
        return {
            assignmentId: this.$route.params.assignmentId,
            linters: null,
            loading: true,
            show: {},
        };
    },

    components: {
        Loader,
        Icon,
    },

    mounted() {
        this.getLinters();
    },

    methods: {
        getLinterState(linter) {
            switch (linter.state) {
            case -1: return 'New';
            case 1: return 'Running';
            case 2: return 'Done';
            case 3: return 'Crashed';
            default: throw new TypeError('Wrong State!');
            }
        },
        changeSubCollapse(state, linter, key) {
            const curState = linter.collapseState;
            if (Boolean(curState) !== state) {
                this.$root.$emit('collapse::toggle', `sub_collapse_${key}`);
                this.$set(linter, 'collapseState', !curState);
            }
            return linter;
        },

        clicked(collapseState, key, selectedName) {
            const linter = this.linters[key];
            this.$set(linter, 'selected', selectedName);
            this.$set(this.linters, key, linter);
            this.$nextTick(() => this.$set(this.linters,
                                           key,
                                           this.changeSubCollapse(collapseState, linter, key)));
        },

        getLinters() {
            this.$http.get(`/api/v1/assignments/${this.assignmentId}/linters/`).then((data) => {
                this.linters = data.data;
                this.loading = false;
                Object.keys(this.linters).forEach((key) => {
                    if (this.linters[key].state === 1) {
                        this.startUpdateLoop(key);
                    }
                });
            });
        },
        deleteLinterFeedback(key) {
            const linter = this.linters[key];
            this.$set(linter, 'deleting', true);
            this.$set(this.linters, key, linter);
            this.$http.delete(`/api/v1/linters/${linter.id}`).then(() => {
                this.$root.$emit('hide::modal', `modal_${key}`);

                this.$set(linter, 'selected', false);
                this.$set(linter, 'opened', false);
                this.$set(this.linters, key, linter);
                this.$root.$emit('collapse::toggle', `collapse_${key}`);

                this.$nextTick(() => {
                    this.$set(linter, 'state', -1);
                    this.$set(this.linters, key, linter);
                });
            });
        },
        startUpdateLoop(key, time) {
            const timeout = time === undefined ? 1000 : time;
            this.$http.get(`/api/v1/linters/${this.linters[key].id}`).then((data) => {
                const linter = this.linters[key];
                this.$set(linter, 'children', data.data.children);
                this.$set(linter, 'state', 1);
                this.$set(this.linters, key, linter);
                if (!data.data.done) {
                    this.$nextTick(() => {
                        setTimeout(() => this.startUpdateLoop(key, timeout * 2), timeout);
                    });
                } else {
                    this.$set(linter, 'state', data.data.crashed ? 3 : 2);
                    this.$set(this.linters, key, linter);
                }
            });
        },
        runLinter(linter, key) {
            let cfg;
            if (linter.selected === 'Custom config') {
                cfg = linter.config === undefined ? '' : linter.config;
            } else {
                cfg = linter.opts[linter.selected];
            }
            this.$http.post(`/api/v1/assignments/${this.assignmentId}/linter`, {
                name: key,
                cfg,
            }).then((data) => {
                linter.state = 1;
                this.$set(linter, 'children', data.data.children);
                linter.id = data.data.id;
                this.$set(this.linters, key, linter);
                this.$nextTick(() => {
                    setTimeout(() => this.startUpdateLoop(key), 3000);
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
