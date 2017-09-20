<template>
    <b-form-fieldset
        class="rubric-viewer"
        :class="{ editable }">
        <b-input-group>
            <div class="form-control outer-container">
                <b-card-group class="tab-container">
                    <b-card v-for="(row, i) in rubrics"
                            :key="`rubric-row-${row.id}`"
                            :class="{active: i === current}"
                            @click.native="gotoItem(i)">
                        <b>{{ row.header }}</b>
                        <icon name="check"
                              v-if="selectedRows[row.id]"
                              style="float: right;"/>
                    </b-card>
                </b-card-group>
                <div class="inner-container"
                     ref="rubricContainer">
                    <div class="rubric"
                         v-for="(rubric, i) in rubrics"
                         :key="`rubric-${rubric.id}`">
                        <b-card no-block>
                            <div class="card-header rubric-header">
                                <span class="title">
                                    {{ rubric.description }}
                                </span>
                            </div>
                            <b-card-group>
                                <b-card class="rubric-item"
                                        v-for="item in rubric.items"
                                        :key="`rubric-${rubric.id}-${item.id}`"
                                        @click.native="selectOrUnselect(rubric, item)"
                                        :class="{ selected: selected[item.id] }">
                                    <div class="rubric-item-wrapper row">
                                        <div class="col-12"
                                             style="position: relative;">
                                            <b>{{ item.points }} - {{ item.header }}</b>
                                            <div v-if="itemStates[item.id] === '__LOADING__'"
                                                 class="rubric-icon">
                                                <loader :scale="1"/>
                                            </div>
                                            <div v-else-if="itemStates[item.id]"
                                                 class="rubric-icon">
                                                <b-popover show
                                                           :content="itemStates[item.id]"
                                                           placement="top">
                                                    <icon name="times"
                                                          :scale="1"
                                                          style="color: red;"/>
                                                </b-popover>
                                            </div>
                                            <p class="item-description">
                                                {{ item.description }}
                                            </p>
                                        </div>
                                    </div>
                                </b-card>
                            </b-card-group>
                        </b-card>
                    </div>
                </div>
            </div>
        </b-input-group>
    </b-form-fieldset>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/angle-left';
import 'vue-awesome/icons/angle-right';
import 'vue-awesome/icons/times';
import 'vue-awesome/icons/check';

import Loader from './Loader';

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
            outOfSync: {},
            selected: {},
            selectedPoints: 0,
            selectedRows: {},
            current: 0,
            maxPoints: 0,
            itemStates: {},
        };
    },

    watch: {
        rubric(rubric) {
            this.rubricUpdated(rubric);
        },
    },

    computed: {
        hasSelectedItems() {
            return Object.keys(this.selected).length !== 0;
        },

        grade() {
            let grade = Math.max(0, (this.selectedPoints / this.maxPoints) * 10);
            if (Object.keys(this.selected).length === 0) {
                grade = null;
            }
            return grade;
        },
    },

    mounted() {
        this.rubricUpdated(this.rubric, true);
    },

    methods: {
        clearSelected() {
            const clear = () => {
                this.selected = {};
                this.selectedPoints = 0;
                this.selectedRows = {};
                this.$emit('input', {
                    selected: 0,
                    max: this.maxPoints,
                    grade: null,
                });
                return { data: { grade: null } };
            };

            if (UserConfig.features.incremental_rubric_submission) {
                return this.$http.patch(`/api/v1/submissions/${this.submission.id}/rubricitems/`, {
                    items: [],
                }).then(clear);
            }

            this.outOfSync = this.selected;
            clear();
            return Promise.resolve({ data: {} });
        },

        submitAllItems() {
            if (Object.keys(this.outOfSync).length === 0) {
                return Promise.resolve();
            }
            return this.$http.patch(`/api/v1/submissions/${this.submission.id}/rubricitems/`, {
                items: Object.keys(this.selected),
            }).then(() => {
                this.outOfSync = {};
            });
        },

        rubricUpdated({ rubrics, selected, points }, initial = false) {
            this.rubrics = this.sortRubricItems(rubrics);

            if (selected) {
                this.selected = selected.reduce((res, item) => {
                    res[item.id] = true;
                    return res;
                }, {});
                this.selectedPoints = selected.reduce((res, item) => res + item.points,
                                                      0);
                this.selectedRows = rubrics.reduce((res, row) => {
                    res[row.id] = row.items.some(item => this.selected[item.id]);
                    return res;
                }, {});
            }

            if (points) {
                this.maxPoints = points.max;
                if (!initial) {
                    points.grade = this.grade;
                }
                this.$emit('input', points);
            }

            this.$refs.rubricContainer.style.width = `${rubrics.length * 100}%`;
        },

        sortRubricItems(rubrics) {
            return rubrics.map((rubric) => {
                rubric.items.sort((x, y) => x.points - y.points);
                return rubric;
            });
        },

        selectOrUnselect(row, item) {
            if (!this.editable) return;
            this.$set(this.itemStates, item.id, '__LOADING__');

            let req;
            const selectItem = !this.selected[item.id];
            const doRequest = UserConfig.features.incremental_rubric_submission;

            if (!doRequest) {
                req = Promise.resolve().then(() => {
                    if (this.outOfSync[item.id]) {
                        this.$set(this.outOfSync, item.id, false);
                        delete this.outOfSync[item.id];
                    } else {
                        this.$set(this.outOfSync, item.id, true);
                    }
                });
            } else if (selectItem) {
                req = this.$http.patch(
                    `/api/v1/submissions/${this.submission.id}/rubricitems/${item.id}`,
                );
            } else {
                req = this.$http.delete(
                    `/api/v1/submissions/${this.submission.id}/rubricitems/${item.id}`,
                );
            }

            req.then(() => {
                row.items.forEach(({ id, points }) => {
                    if (this.selected[id]) {
                        this.selectedPoints -= points;
                    }
                    delete this.selected[id];
                });
                if (selectItem) {
                    this.selectedPoints += item.points;
                    this.$set(this.selected, item.id, true);
                } else {
                    this.$set(this.selected, item.id, false);
                    delete this.selected[item.id];
                }
                this.$set(this.selectedRows, row.id, selectItem);

                this.$emit('input', {
                    selected: this.selectedPoints,
                    max: this.maxPoints,
                    grade: this.grade,
                });

                this.$nextTick(() => {
                    this.$set(this.itemStates, item.id, false);
                    delete this.itemStates[item.id];
                });
            }, (err) => {
                this.$set(this.itemStates, item.id, err.response.data.message);
                setTimeout(() => {
                    this.$nextTick(() => {
                        this.$set(this.itemStates, item.id, false);
                        delete this.itemStates[item.id];
                    });
                }, 3000);
            });
        },

        gotoItem(i) {
            this.current = i;
            this.slide();
        },

        slide() {
            this.$refs.rubricContainer.style.transform =
                `translateX(-${100 * (this.current / this.rubrics.length)}%)`;
        },
    },

    components: {
        Icon,
        Loader,
    },
};
</script>

<style lang="less" scoped>
@import '~mixins.less';

@active-color: #e6e6e6;

.outer-container {
    overflow: hidden;
    padding: 0;
}

.tab-container {
    .card {
        border-top: 0px;
        border-bottom: 0px;
        cursor: pointer;
        border-bottom-left-radius: 0;
        border-bottom-right-radius: 0;
    }
    .card:first-child {
        border-left: 0;
    }
    .card:last-child {
        border-right: 0;
    }
    .card:hover, .card.active {
        background: @active-color;
        #app.dark & {
            background: @color-primary-darkest;
        }
    }
}

.inner-container {
    display: flex;
    flex-direction: row;
    align-items: center;
    transition: transform 500ms;
}

.rubric {
    flex: 1 1 0;
    .card {
        border-top-left-radius: 0;
        border-top-right-radius: 0;
    }
}

.rubric-header {
    display: flex;
    flex-direction: row;
    flex-grow: 1;

    .title {
        flex: 1 1 0;
        word-break: break-all;
    }

    .index {
        flex: 0 0 auto;
        margin-left: 1em;
    }
}

.inner-container > .rubric {
    height: 100%;

    & > .card {
        justify-content: space-between;
        display: flex;
        flex-direction: column;
        height: 100%;
    }
}

.rubric-item {
    border-width: 0;
    border-bottom: 0;

    &:first-child {
        border-top-left-radius: 0;
    }
    &:last-child {
        border-top-right-radius: 0;
    }

    &:not(:last-child) {
        border-right-width: 1px;
    }

    .editable & {
        cursor: pointer;

        &:hover {
            background: @active-color;
            #app.dark & {
                background: @color-primary-darkest;
            }
        }
    }

    &.selected {
        background: @active-color;
        #app.dark & {
            background: @color-primary-darkest;
        }
    }
}

.item-state {
    float: right;
}

.rubric-icon {
    position: absolute;
    top: 0;
    right: 15px;
}

.item-description {
    margin: 0;
    max-height: 5em;
    overflow-y: auto;
    margin-top: 0.5em;
    padding-right: 0.5em;
}
</style>

<style lang="less">
.rubric-viewer {
    .card-header,
    .card-block {
        padding: .5rem .75rem;
        .rubric-item-wrapper {
            margin: -0.5em;
            padding: 0.5em;
            align-items: center;
        }
    }
}
</style>
