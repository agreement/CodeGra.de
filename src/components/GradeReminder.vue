<template>
<div>
    <b-input-group left="Time to send">
        <input type="datetime-local"
               class="form-control"
               v-model="assignment.reminder_time"/>
    </b-input-group>
    <div class="grade-options custom-controls-stacked">
        <label class="custom-control custom-radio"
               v-for="item in options">
            <input type="radio"
                   class="custom-control-input"
                   :id="`${assignment.id}-${item.value}`"
                   :value="item.value"
                   v-model="assignment.reminder_type"/>
            <span aria-hidden="true"
                  class="custom-control-indicator"/>
            <span>{{ item.text }}</span>
            <description-popover
                :description="item.help"
                hug-text
                placement="bottom"/>
        </label>
    </div>
    <submit-button @click="updateReminder" ref="updateReminder" label="Set reminder"/>
</div>
</template>

<script>
import { convertToUTC } from '@/utils';

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
            options: [
                {
                    text: 'No graders',
                    value: 'none',
                    help: 'Do not send a reminder email.',
                },
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
                    help: `
Send a reminder e-mail to all graders. This will also probably you.`,
                },
            ],
        };
    },

    methods: {
        updateReminder() {
            const req = this.$http.patch(this.assignmentUrl, {
                reminder_type: this.assignment.reminder_type,
                reminder_time: convertToUTC(this.assignment.reminder_time),
            });
            this.$refs.updateReminder.submit(req.catch((err) => {
                throw err.response.data.message;
            }));
        },

    },

    components: {
        SubmitButton,
        DescriptionPopover,
    },
};
</script>

<style lang="less">
.grade-options {
    margin: .75em 0;

    & > .custom-control:last-child {
        margin-bottom: 0;
    }
}
</style>
