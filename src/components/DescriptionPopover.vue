<template>
<span class="description-popover"
      :style="{ float: hugText ? 'none' : 'right' }">
    <b-popover :placement="placement"
               :triggers="triggers"
               class="description-popover"
               :show="show"
               :target="compId"
               :title="title">
        <slot name="description"><span/>{{ description }}</slot>
    </b-popover>
    <component :is="hugText ? 'sup' : 'span'"
               class="desc-pop-span"
               :id="compId">
        <icon name="info" scale="0.75"/>
    </component>
</span>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/info';

let i = 0;

export default {
    name: 'description-popover',

    data() {
        return {
            compId: `description-popover-i-${i++}`,
        };
    },

    props: {
        description: {
            type: String,
        },

        triggers: {
            type: [String, Array],
            default: 'hover',
        },

        show: {
            type: Boolean,
            default: undefined,
        },

        hugText: {
            type: Boolean,
            default: false,
        },

        title: {
            type: String,
            default: undefined,
        },

        placement: {
            type: String,
            default: 'right',
        },
    },

    components: {
        Icon,
    },
};
</script>

<style lang="less">
.desc-pop-span {
    padding: 0 0.5em;
    height: 100%;
    display: inline-block;
}

.description-popover {
    display: inline;
    cursor: help;
}
</style>
