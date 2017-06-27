<template>
    <div :class="{ 'linter-feedback-inner': feedback != null }">
        <b-popover placement="top" triggers="hover" :content="getFeedback()" v-if="feedback != null">
            <div class="linter-toggle" v-on:click="toggleShow"></div>
        </b-popover>
    </div>
</template>

<script>
const entityRE = /[&<>]/g;
const entityMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
};
const e = text => String(text).replace(entityRE, entity => entityMap[entity]);

export default {
    name: 'linter-feedback-area',

    props: ['feedback'],

    data() {
        return {
            show: false,
        };
    },

    methods: {
        getFeedback() {
            const body = Object.keys(this.feedback).map((key) => {
                const val = this.feedback[key];
                let res = `<tr><td><b>${e(key)}</b></td><td>`;
                if (val.code) {
                    res = `${res}[${e(val.code)}] `;
                }
                return `${res}${e(val.msg)}</td></tr>`;
            }).join('');
            return `<table class="linter-feedback">${body}</table>`;
        },
        toggleShow(ev) {
            ev.preventDefault();
            ev.stopPropagation();
            this.show = !this.show;
        },
    },
};
</script>

<style lang="less">

.popover-content-wrapper table.linter-feedback tr td:nth-child(2) {
    padding-left: 15px;
}

</style>
