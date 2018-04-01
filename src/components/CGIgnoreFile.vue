<template>
    <div class="cgignore-file">
        <textarea class="form-control"
                  rows="6"
                  v-model="content"
                  @keyup.ctrl.enter="updateIgnore"/>
        <submit-button label="Update"
                       ref="submitBtn"
                       @click="updateIgnore"/>
    </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';

import SubmitButton from './SubmitButton';

export default {
    name: 'ignore-file',

    props: {
        assignmentId: {
            type: Number,
            required: true,
        },
    },

    computed: {
        ...mapGetters('courses', ['assignments']),

        assignment() {
            return this.assignments[this.assignmentId];
        },
    },

    data() {
        return {
            content: '',
        };
    },

    mounted() {
        this.content = this.assignment.cgignore || '';
    },

    methods: {
        ...mapActions('courses', ['updateAssignment']),

        updateIgnore() {
            this.$refs
                .submitBtn
                .submit(this.$http.patch(`/api/v1/assignments/${this.assignment.id}`, {
                    ignore: this.content,
                }).then(() => {
                    this.updateAssignment({
                        assignmentId: this.assignmentId,
                        assignmentProps: {
                            cgignore: this.content,
                        },
                    });
                }, ({ response }) => {
                    throw response.data.message;
                }));
        },
    },

    components: {
        SubmitButton,
    },
};
</script>

<style lang="less" scoped>
.submit-button {
    display: flex;
    margin-top: 15px;
    justify-content: flex-end;
}
</style>
