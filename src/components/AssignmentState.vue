<template>
<div v-if="editable">
    <b-button-group @click="updateState">
        <b-button class="state-button larger"
                  v-if="assignment.is_lti"
                  :size="size"
                  value="open"
                  :variant="ltiHiddenOpenVariant"
                  v-b-popover.bottom.hover="'Hidden or open, managed by LTI'">
            <loader v-if="isLoadingLTIHiddenOpen" :scale="0.75"/>
            <span v-else>
                <icon :name="icons[states.HIDDEN]" :scale="0.75"/>
                <icon :name="icons[states.OPEN]" :scale="0.75"/>
            </span>
        </b-button>

        <b-button-group v-else>
            <b-button class="state-button"
                      :size="size"
                      value="hidden"
                      :variant="hiddenVariant"
                      v-b-popover.bottom.hover="labels[states.HIDDEN]">
                <loader v-if="isLoadingHidden" :scale="0.75"/>
                <icon :name="icons[states.HIDDEN]" :scale="0.75" v-else/>
            </b-button>

            <b-button class="state-button"
                      :size="size"
                      value="open"
                      :variant="openVariant"
                      v-b-popover.bottom.hover="labels[states.OPEN]">
                <loader v-if="isLoadingOpen" :scale="0.75"/>
                <icon :name="icons[states.OPEN]" :scale="0.75" v-else/>
            </b-button>
        </b-button-group>

        <b-button class="state-button"
                  :size="size"
                  value="done"
                  :variant="doneVariant"
                  v-b-popover.bottom.hover="labels[states.DONE]">
            <loader v-if="isLoadingDone" :scale="0.75"/>
            <icon :name="icons[states.DONE]" :scale="0.75" v-else/>
        </b-button>
    </b-button-group>
</div>
<icon :name="icons[assignment.state]"
      class="state-icon"
      v-b-popover.bottom.hover="labels[assignment.state]"
      v-else/>
</template>

<script>
import { mapActions } from 'vuex';

import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/eye-slash';
import 'vue-awesome/icons/clock-o';
import 'vue-awesome/icons/pencil';
import 'vue-awesome/icons/check';

import * as states from '../store/assignment-states';

import { waitAtLeast } from '../utils';

import Loader from './Loader';

export default {
    name: 'assignment-state',

    props: {
        assignment: {
            type: Object,
            default: null,
        },

        editable: {
            type: Boolean,
            default: false,
        },

        size: {
            type: String,
            default: 'md',
        },
    },

    data() {
        return {
            pendingState: '',
            states,
            labels: {
                [states.HIDDEN]: 'Hidden',
                [states.SUBMITTING]: 'Submitting',
                [states.GRADING]: 'Grading',
                [states.OPEN]: 'Open',
                [states.DONE]: 'Done',
            },
            icons: {
                [states.HIDDEN]: 'eye-slash',
                [states.SUBMITTING]: 'clock-o',
                [states.GRADING]: 'pencil',
                [states.OPEN]: 'clock-o',
                [states.DONE]: 'check',
            },
        };
    },

    computed: {
        ltiHiddenOpenVariant() {
            const st = this.assignment.state;
            return st !== states.DONE ? 'primary' : 'outline-primary';
        },

        hiddenVariant() {
            const st = this.assignment.state;
            return st === states.HIDDEN ? 'danger' : 'outline-danger';
        },

        openVariant() {
            const st = this.assignment.state;
            return st === states.SUBMITTING || st === states.GRADING || st === states.OPEN ?
                'warning' : 'outline-warning';
        },

        doneVariant() {
            const st = this.assignment.state;
            return st === states.DONE ? 'success' : 'outline-success';
        },

        isLoadingLTIHiddenOpen() {
            return this.assignment.is_lti && this.pendingState === states.OPEN;
        },

        isLoadingHidden() {
            return this.pendingState === states.HIDDEN;
        },

        isLoadingOpen() {
            const st = this.pendingState;
            return st === states.SUBMITTING || st === states.GRADING || st === states.OPEN;
        },

        isLoadingDone() {
            return this.pendingState === states.DONE;
        },
    },

    methods: {
        ...mapActions('courses', ['updateAssignment']),

        updateState({ target }) {
            const button = target.closest('.state-button');
            if (!button) return;

            this.pendingState = button.getAttribute('value');

            waitAtLeast(
                500,
                this.$http.patch(`/api/v1/assignments/${this.assignment.id}`, {
                    state: this.pendingState,
                }),
            ).then(() => {
                this.updateAssignment({
                    assignmentId: this.assignment.id,
                    assignmentProps: {
                        state: this.pendingState,
                    },
                });
                this.pendingState = '';
            }, (err) => {
                // TODO: visual feedback
                // eslint-disable-next-line
                console.dir(err);
            });
        },
    },

    components: {
        Icon,
        Loader,
    },
};
</script>

<style lang="less" scoped>
.state-button.larger {
    width: 4em;

    .fa-icon {
        margin-left: 0;
    }
}
</style>
