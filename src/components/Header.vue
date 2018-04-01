<template>
<div class="Header">
    <slot name="default"/>
    <b-btn v-if="hasExtraSlot">
        hello
    </b-btn>
    <slot name="extra"
          v-if="false"/>
</div>
</template>

<script>

export default {
    name: 'local-header',

    computed: {
        hasExtraSlot() {
            return !!this.$slots.extra;
        },
    },
};
</script>
