<template>
<div class="toggle-container" :class="{ disabled }">
    <b-popover :triggers="disabled ? ['hover'] : []"
               content="You cannot change the grader status of other graders">
        <div class="toggle" @click="toggle">
            <b-button class="off" variant="default">
                {{ labelOff }}
            </b-button>
            <b-button class="on" variant="primary">
                {{ labelOn }}
            </b-button>
        </div>
    </b-popover>
</div>
</template>

<script>
export default {
    name: 'toggle',

    props: {
        value: {
            default: false,
        },
        labelOn: {
            type: String,
            default: 'on',
        },
        labelOff: {
            type: String,
            default: 'off',
        },
        valueOn: {
            default: true,
        },
        valueOff: {
            default: false,
        },
        disabled: {
            default: false,
        },
    },

    data() {
        return {
            current: this.value === this.valueOn,
        };
    },

    watch: {
        value(newVal) {
            this.current = newVal;
            this.update();
        },
    },

    mounted() {
        this.update();
    },

    methods: {
        toggle() {
            if (this.disabled) return;

            this.current = !this.current;
            this.$emit('input', this.current ? this.valueOn : this.valueOff);
            this.update();
        },

        update() {
            if (this.current) {
                this.$el.setAttribute('checked', 'checked');
            } else {
                this.$el.removeAttribute('checked');
            }
        },
    },
};
</script>

<style lang="less" scoped>
@import '~mixins.less';

#app.dark ~ .popover .toggle {
    // TODO: Find better colors here.
    .off {
        background: white;
        color: @text-color;
    }
    .on {
        background: @color-primary-darker;
        color: @text-color-dark;
    }
}

.toggle-container {
    display: inline-block;
    overflow: hidden;
    cursor: pointer;
    border-radius: .25rem;
    width: 4rem;
}

.toggle {
    position: relative;
    width: 100%;
    height: 2.25rem;

    .on,
    .off {
        position: absolute;
        top: 0;
        left: 0;
        display: block;
        width: 100%;
        height: 100%;
        transition: transform 300ms ease-out 0;
        padding: .375rem;
        pointer-events: none;
        text-align: center;
    }

    .off {
        transform: translateX(0);
    }

    .on {
        transform: translateX(100%);
    }

    [checked] & {
        .off {
            transform: translateX(-100%);
        }

        .on {
            transform: translateX(0);
        }
    }
}

.disabled .toggle {
    cursor: not-allowed;
    opacity: 0.4;
}
</style>
