<template>
<div class="linter-feedback-inner">
    <b-popover placement="top"
               triggers="hover"
               :target="divId">
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
    </b-popover>
    <div :id="divId"
         class="linter-toggle"/>
</div>
</template>

<script>
let i = 0;

export default {
    name: 'linter-feedback-area',

    props: ['feedback'],

    data() {
        return {
            show: false,
            divId: `linterFeedback-${i++}`,
        };
    },
};
</script>

<style lang="less">
table.linter-feedback tr td:nth-child(2) {
    padding-left: 15px;
}
</style>
