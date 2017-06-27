<template>
    <b-form-fieldset
        class="rubric-viewer">
        <b-input-group>
            <b-input-group-button>
                <b-button
                    @click="goToPrev"
                    :disabled="current <= 0">
                    <icon name="angle-left"></icon>
                </b-button>
            </b-input-group-button>
            <div
                class="form-control outer-container">
                <div
                    class="inner-container"
                    ref="rubricContainer">
                    <b-card-group
                        class="rubric"
                        v-for="(rubric, i) in rubrics"
                        :key="`rubric-${i}`">
                        <b-card
                            class="rubric-item"
                            v-for="item in rubric.items"
                            :key="`rubric-${i}-${item.id}`"
                            @click.native="select(i, item)"
                            :class="{ selected: isSelected(i, item) }">
                            <span>
                                <b>{{ item.points }}</b> - {{ item.description }}
                            </span>
                        </b-card>
                    </b-card-group>
                </div>
            </div>
            <b-input-group-button>
                <b-button
                    @click="goToNext"
                    :disabled="current >= rubrics.length - 1">
                    <icon name="angle-right"></icon>
                </b-button>
            </b-input-group-button>
        </b-input-group>
    </b-form-fieldset>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/angle-left';
import 'vue-awesome/icons/angle-right';

export default {
    name: 'rubric-viewer',

    props: {
        assignment: {
            type: Object,
            default: {},
        },
        submission: {
            type: Object,
            default: {},
        },
        rubrics: {
            type: Array,
            default: [],
        },
        value: {
            type: Object,
            default: {},
        },
    },

    data() {
        return {
            selected: this.rubrics.map(() => null),
            current: 0,
        };
    },

    watch: {
        rubrics() {
            this.adjustRubricElements();
        },

        current(curr) {
            this.$refs.rubricContainer.style.transform =
                `translateX(-${100 * (curr / this.rubrics.length)}%)`;
        },
    },

    mounted() {
        this.adjustRubricElements();
    },

    methods: {
        select(row, item) {
            this.$set(this.selected, row, item);
            this.$emit('input', {
                total: this.totalPoints(),
                max: this.maxPoints(),
                selected: this.selected.map(sel => (sel ? sel.id : -1)),
            });
        },

        totalPoints() {
            return this.selected.filter(x => x).reduce(
                (sum, item) => sum + item.points, 0);
        },

        maxPoints() {
            return this.rubrics.reduce((sum, rubric) =>
                sum + rubric.items[rubric.items.length - 1].points, 0);
        },

        isSelected(row, item) {
            return this.selected[row] === item;
        },

        goToPrev() {
            this.current = Math.max(this.current - 1, 0);
        },

        goToNext() {
            this.current = Math.min(this.current + 1, this.rubrics.length - 1);
        },

        adjustRubricElements() {
            this.$refs.rubricContainer.style.width = `${this.rubrics.length * 100}%`;
        },
    },

    components: {
        Icon,
    },
};
</script>

<style lang="less" scoped>
.outer-container {
    overflow: hidden;
    padding-left: 0;
    padding-right: 0;
}

.inner-container {
    display: flex;
    flex-direction: row;
    transition: transform 500ms;
}

.rubric {
    flex: 1 1 0;

    padding-left: .75rem;
    padding-right: .75rem;
}

.rubric-item {
    cursor: pointer;

    &:hover {
        background: rgba(0, 0, 0, 0.075);
    }

    &.selected {
        font-weight: bold;
        background: rgba(0, 0, 0, 0.075);
    }
}
</style>
