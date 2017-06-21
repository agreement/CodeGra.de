<template>
    <b-button :href="link">Export feedback</b-button>
</template>

<script>
import { bButton } from 'bootstrap-vue/lib/components';

export default {
    name: 'feedback-exporter',

    components: {
        bButton,
    },

    props: ['id'],

    computed: {
        link: function link() {
            return `/api/v1/submissions/${this.id}?type=feedback`;
        },
    },
};
</script>

<style lang="less" scoped>
button {
    cursor: pointer;
}
</style>
