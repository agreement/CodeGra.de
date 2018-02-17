<template>
<div v-if="editable">
    <b-button-group @click="updateState">
        <b-button class="state-button larger"
                  :size="size"
                  :variant="ltiHiddenOpenVariant"
                  :disabled="true"
                  v-if="assignment.is_lti"
                  v-b-popover.top.hover="'Hidden or open, managed by LTI'">
            <icon :name="icons[states.HIDDEN]" scale="0.75"/>
            <icon :name="icons[states.OPEN]" scale="0.75"/>
        </b-button>

        <b-button-group v-else>
            <b-button class="state-button"
                      :size="size"
                      value="hidden"
                      :variant="hiddenVariant"
                      v-b-popover.top.hover="labels[states.HIDDEN]">
                <loader :scale="1" v-if="isLoadingHidden" scale="0.75"/>
                <icon :name="icons[states.HIDDEN]" scale="0.75" v-else/>
            </b-button>

            <b-button class="state-button"
                      :size="size"
                      value="open"
                      :variant="openVariant"
                      v-b-popover.top.hover="labels[states.OPEN]">
                <loader :scale="1" v-if="isLoadingOpen" scale="0.75"/>
                <icon :name="icons[states.OPEN]" scale="0.75" v-else/>
            </b-button>
        </b-button-group>

        <b-button class="state-button"
                  :size="size"
                  value="done"
                  :variant="doneVariant"
                  v-b-popover.top.hover="labels[states.DONE]">
            <loader :scale="1" v-if="isLoadingDone" scale="0.75"/>
            <icon :name="icons[states.DONE]" scale="0.75" v-else/>
        </b-button>
    </b-button-group>
</div>
<icon :name="icons[assignment.state]"
      class="state-icon"
      v-b-popover.top.hover="labels[assignment.state]"
      v-else/>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/eye-slash';
import 'vue-awesome/icons/clock-o';
import 'vue-awesome/icons/pencil';
import 'vue-awesome/icons/check';

import * as states from '../store/assignment-states';

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
            return this.assignment.state !== states.DONE ? 'primary' : 'outline-primary';
        },

        hiddenVariant() {
            return this.assignment.state === states.HIDDEN ? 'danger' : 'outline-danger';
        },

        openVariant() {
            const st = this.assignment.state;
            return st === states.SUBMITTING || st === states.GRADING || st === states.OPEN ?
                'warning' : 'outline-warning';
        },

        doneVariant() {
            return this.assignment.state === states.DONE ? 'success' : 'outline-success';
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
        updateState({ target }) {
            const button = target.closest('button');
            if (!button) return;

            this.pendingState = button.getAttribute('value');

            this.$http.patch(`/api/v1/assignments/${this.assignment.id}`, {
                state: this.pendingState,
            }).then(() => {
                this.assignment.state = this.pendingState;
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
.state-button, .state-icon {
    width: 1.75em;
    margin-top: .5em;
    margin-left: .375em;
}
.state-button {
    margin-top: 0;
}

.state-icon {
    margin-top: .6em;
}

.state-button {
    padding-left: .375rem;

    &.larger {
        width: 3.5em;
        margin-left: 0;

        .btn-group {
            display: block;
        }

        .fa-icon {
            margin-left: 0;
        }
    }
}
</style>
