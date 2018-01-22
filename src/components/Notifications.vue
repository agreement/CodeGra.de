<template>
<div>
    <div>
        <label class="custom-control custom-checkbox">
            <input class="custom-control-input"
                   type="checkbox"
                   v-model="graders"/>
            <span aria-hidden="true"
                  class="custom-control-indicator"/>
            <span><b>Graders</b><description-popover
                                    description="Toggle this checkbox to send a
                                                 reminder to the graders that
                                                 are causing the grading to not
                                                 be done at the given
                                                 time."
                                    placement="right"/></span>
        </label>
        <b-input-group left="Time to send"
                       :class="{ show: graders }"
                       class="animate email-time extra-box">
            <input type="datetime-local"
                   @keyup.ctrl.enter="updateReminder"
                   class="form-control"
                   v-model="assignment.reminder_time"/>
        </b-input-group>
    </div>
    <hr/>
    <div>
        <label class="custom-control custom-checkbox">
            <input class="custom-control-input"
                   type="checkbox"
                   v-model="finished"/>
            <span aria-hidden="true"
                  class="custom-control-indicator"/>
            <span><b>Finished</b><description-popover
                                     description="Toggle this checkbox to send
                                                  the given email address a
                                                  reminder when the grading is
                                                  done. You can select multiple
                                                  address in the same as in your
                                                  email client."
                                     placement="right"/></span>
        </label>
        <b-input-group class="animate extra-box"
                       left="Send to"
                       :class="{ show: finished }">
            <input type="text"
                   @keyup.ctrl.enter="updateReminder"
                   class="form-control animate"
                   v-model="assignment.done_email"/>
        </b-input-group>
    </div>
    <hr/>
    <div class="grade-options custom-controls-stacked animate"
         :style="{maxHeight: ((graders || finished) ? '8em' : 0)}">
        <label class="custom-control custom-radio"
               v-for="item in options">
            <input type="radio"
                   class="custom-control-input"
                   :id="`${assignment.id}-${item.value}`"
                   :value="item.value"
                   v-model="assignment.done_type"/>
            <span aria-hidden="true" class="custom-control-indicator"/>
            <span>{{ item.text }}</span>
            <description-popover
                :description="item.help"
                hug-text
                placement="right"/>
        </label>
        <hr style="width: 100%"/>
    </div>

    <submit-button ref="updateReminder" @click="updateReminder"/>
</div>
</template>

<script>
import moment from 'moment';

import { convertToUTC, parseWarningHeader } from '@/utils';

import SubmitButton from './SubmitButton';
import DescriptionPopover from './DescriptionPopover';

export default {
    props: {
        assignment: {
            type: Object,
            default: null,
        },
    },

    computed: {
        assignmentUrl() {
            return `/api/v1/assignments/${this.assignment.id}`;
        },
    },

    data() {
        return {
            graders: this.assignment.has_reminder_time,
            origReminderTime: this.assignment.reminder_time,
            finished: this.assignment.done_email != null,
            options: [
                {

                    text: 'Assigned graders only',
                    value: 'assigned_only',
                    help: `
Only send to graders that have work assigned to them. This can be because they were
divided or because they were assigned work manually.`,
                },
                {
                    text: 'All graders',
                    value: 'all_graders',
                    help: 'Send a reminder e-mail to all graders.',
                },
            ],
        };
    },

    watch: {
        finished(val) {
            if (!val && !this.graders) {
                this.assignment.reminder_type = null;
            }
        },

        graders(val) {
            if (!val && !this.finished) {
                this.assignment.reminder_type = null;
            }
        },
    },

    methods: {
        updateReminder() {
            const type = this.graders || this.finished ? String(this.assignment.done_type) : null;
            const time = this.graders ? convertToUTC(this.assignment.reminder_time) : null;
            const email = this.finished ? String(this.assignment.done_email) : null;
            const button = this.$refs.updateReminder;

            if ((this.graders || this.finished) && !this.assignment.done_type) {
                let msg = 'Please select when grading on this assignment should be considered finished.';
                if (this.graders) {
                    msg += ' This also indicates who should get a notification when they are not yet done grading.';
                }
                button.fail(msg);
                return;
            }

            const req = this.$http.patch(this.assignmentUrl, {
                done_type: type,
                reminder_time: time,
                done_email: email,
            }).then((res) => {
                this.assignment.done_type = type;

                if (type == null) {
                    this.assignment.reminder_time = this.origReminderTime;
                } else {
                    this.assignment.reminder_time = moment.utc(time).local().format('YYYY-MM-DDTHH:mm');
                }

                this.assignment.done_email = email;

                if (res.headers.warning) {
                    button.cancel();
                    button.warn(parseWarningHeader(res.headers.warning).text);
                }
            }, (err) => {
                throw err.response.data.message;
            });

            button.submit(req);
        },
    },

    components: {
        SubmitButton,
        DescriptionPopover,
    },
};
</script>

<style lang="less" scoped>
hr {
    margin-top: .5rem;
    margin-bottom: .5rem;
}

.grade-options {
    padding-left: 3px;
    & > .custom-control:last-child {
        margin-bottom: 0;
    }
}

.animate {
    transition: max-height .25s ease-in-out, margin .25s ease-in-out;
    overflow: hidden;
}

label {
    margin-bottom: 0;
}

.extra-box {
    max-height: 0;
    margin: 0;

    &.show {
        margin: 0.75em 0;
        max-height: 6em;
    }
}
</style>
