<template>
  <div :class="{ 'linter-feedback': feedback != null }">
    <b-popover placement="top" triggers="click" :content="getFeedback()" v-if="feedback != null">
      <div v-on:click="toggleShow"></div>
    </b-popover>
  </div>
</template>

<script>
import { bPopover } from 'bootstrap-vue/lib/components';

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

    components: {
        bPopover,
    },

    methods: {
        getFeedback() {
            const body = Object.keys(this.feedback).map((key) => {
                const val = this.feedback[key];
                let res = `<tr><td>${e(key)}</td><td>`;
                if (val.code) {
                    res = `${res}[${e(val.code)}] `;
                }
                return `${res}${e(val.msg)}</td></tr>`;
            }).join('');
            return `<table class="linter-feedbackt">${body}</table>`;
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
div.linter-feedback div {
    margin-left: -4em;
    min-width: 7em;
    min-height: 1.5em;
    top: 0;
    position: absolute;
}

table.linter-feedbackt td:first-child {
    padding-right: 1em;
    font-weight: bold;
}
</style>
