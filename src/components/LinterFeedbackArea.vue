<template>
    <div :class="{ 'linter-feedback-inner': feedback != null }">
        <b-popover placement="bottom" triggers="hover" v-if="feedback != null">
            <div class="linter-toggle" v-on:click="toggleShow"></div>
            <div slot="content">
                <table class="linter-feedback">
                    <tr v-for="(val, i) in feedback"
                        :key="i">
                        <td>
                            <b>{{ val[0] }}</b>
                        </td>
                        <td style="text-align: left">
                            <span v-if="val[1].code">
                                [{{ val[1].code }}]
                            </span>
                            {{ val[1].msg }}
                        </td>
                    </tr>
                </table>
            </div>
        </b-popover>
    </div>
</template>

<script>

export default {
    name: 'linter-feedback-area',

    props: ['feedback'],

    data() {
        return {
            show: false,
        };
    },

    methods: {
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
