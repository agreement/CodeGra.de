<template>
    <div class="cgignore-file form-control">
        <textarea class="form-control" id="" name="" rows="10" v-model="content"/>
        <submit-button style="margin-top: 0.25em"
                       label="Update"
                       ref="submitBtn"
                       @click="updateIgnore"/>
    </div>
</template>

<script>
import SubmitButton from './SubmitButton';

export default {
    name: 'ignore-file',

    props: {
        assignment: {
            type: Object,
            default: null,
        },
    },

    data() {
        return {
            content: this.assignment.cgignore === null ? (
                this.parseInitialString('This file enables you to filter files from submissions. Its format is the same as `.gitignore`. If a file should be excluded according to this list a user will get a warning popup when submitting.')
            ) : this.assignment.cgignore,
        };
    },

    computed: {
    },

    methods: {
        parseInitialString(str) {
            const maxLineSize = 50;
            let res = '';
            let init = str;
            while (init) {
                let lastWord = null;
                for (let i = 0; i < maxLineSize; i += 1) {
                    if (init[i] === ' ') lastWord = i;
                }
                if (init.length <= maxLineSize) lastWord = maxLineSize;
                res += `# ${init.substring(0, lastWord || maxLineSize)}\n`;
                init = init.substring(lastWord ? lastWord + 1 : maxLineSize);
            }
            return res;
        },

        updateIgnore() {
            this.$refs
                .submitBtn
                .submit(this.$http.patch(`/api/v1/assignments/${this.assignment.id}`, {
                    ignore: this.content,
                }).catch(({ response }) => {
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
</style>
