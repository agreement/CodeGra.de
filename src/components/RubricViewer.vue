<template>
    <b-form-fieldset
        class="rubric-viewer"
        :class="{ editable }">
        <b-input-group>
            <b-input-group-button>
                <b-button
                    @click="goToPrev"
                    :disabled="current <= 0">
                    <icon name="angle-left"/>
                </b-button>
            </b-input-group-button>
            <div class="form-control outer-container">
                <div
                    class="inner-container"
                    ref="rubricContainer">
                    <div
                        class="rubric"
                        v-for="(rubric, i) in rubrics"
                        :key="`rubric-${i}`">
                        <b-card no-block>
                            <div class="card-header rubric-header">
                                <span class="title">
                                    <b>{{ rubric.header }}</b> - {{ rubric.description }}
                                </span>
                                <span class="index">
                                    {{ i + 1 }} / {{ rubrics.length }}
                                </span>
                            </div>
                            <b-card-group>
                                <b-card
                                    class="rubric-item"
                                    v-for="item in rubric.items"
                                    :key="`rubric-${i}-${item.id}`"
                                    @click.native="select(i, item)"
                                    :class="{ selected: selected[i] === item }">
                                    <span>
                                        <b>{{ item.points }}</b> - {{ item.description }}
                                    </span>
                                </b-card>
                            </b-card-group>
                        </b-card>
                    </div>
                </div>
            </div>
            <b-input-group-button>
                <b-button
                    @click="goToNext"
                    :disabled="current >= rubrics.length - 1">
                    <icon name="angle-right"/>
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
        submission: {
            type: Object,
            default: null,
        },
        rubric: {
            type: Object,
            default: null,
        },
        editable: {
            type: Boolean,
            default: false,
        },
    },

    data() {
        return {
            rubrics: [],
            selected: [],
            current: 0,
        };
    },

    watch: {
        rubric(rubric) {
            this.rubricUpdated(rubric);
        },
    },

    mounted() {
        this.rubricUpdated(this.rubric);
        console.log(this.rubric.points);
    },

    methods: {
        rubricUpdated({ rubrics, selected, points }) {
            this.rubrics = rubrics;

            if (selected) {
                const allItems = rubrics.reduce((arr, { items }) => arr.concat(items), []);
                this.selected = selected.map(({ id }) => allItems.find(item => item.id === id));
            }

            if (points) {
                this.$emit('input', points);
            }

            this.$refs.rubricContainer.style.width = `${rubrics.length * 100}%`;
        },

        select(row, item) {
            if (!this.editable) return;
            this.$set(this.selected, row, item);

            this.$http.patch(
                `/api/v1/submissions/${this.submission.id}/rubricitems/${item.id}`,
            ).then(({ data }) => {
                this.$emit('input', data);
            }, (err) => {
                // eslint-disable-next-line
                console.dir(err);
            });
        },

        goToPrev() {
            this.current = Math.max(this.current - 1, 0);
            this.slide();
        },

        goToNext() {
            this.current = Math.min(this.current + 1, this.rubrics.length - 1);
            this.slide();
        },

        slide() {
            this.$refs.rubricContainer.style.transform =
                `translateX(-${100 * (this.current / this.rubrics.length)}%)`;
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
    align-items: center;
    transition: transform 500ms;
}

.rubric {
    flex: 1 1 0;
    padding-left: .75rem;
    padding-right: .75rem;
}

.rubric-header {
    display: flex;
    flex-direction: row;

    .title {
        flex: 1 1 0;
    }

    .index {
        flex: 0 0 auto;
        margin-left: 1em;
    }
}

.rubric-item {
    border-width: 0;

    &:not(:last-child) {
        border-right-width: 1px;
    }

    .editable & {
        cursor: pointer;

        &:hover {
            background: rgba(0, 0, 0, 0.075);
        }
    }

    &.selected {
        background: rgba(0, 0, 0, 0.05);
    }
}
</style>

<style lang="less">
.rubric-viewer {
    .card-header,
    .card-block {
        padding: .5rem .75rem;
    }
}
</style>
