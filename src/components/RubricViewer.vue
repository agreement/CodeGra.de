<template>
<div class="rubric-viewer"
     :class="{ editable }">
    <b-tabs no-fade>
        <b-tab class="rubric"
               :head-html="getHeadHtml(rubric)"
               v-for="(rubric, i) in rubrics"
               :key="`rubric-${rubric.id}`">
            <b-card class="rubric-category"
                    :header="rubric.description"
                    body-class="rubric-items">
                <b-card-group>
                    <b-card class="rubric-item"
                            v-for="item in rubric.items"
                            :key="`rubric-${rubric.id}-${item.id}`"
                            @click="toggleItem(rubric, item)"
                            :class="{ selected: selected[item.id] }"
                            body-class="rubric-item-body">
                        <div slot="header" class="header">
                            <b class="header-title">{{ item.points }} - {{ item.header }}</b>
                            <div v-if="itemStates[item.id] === '__LOADING__'"
                                class="rubric-item-icon">
                                <loader :scale="1"/>
                            </div>
                            <div v-else-if="selected[item.id]"
                                class="rubric-item-icon">
                                <icon name="check"/>
                            </div>
                            <div v-else-if="itemStates[item.id]"
                                class="rubric-item-icon">
                                <b-popover show
                                        :target="`rubric-error-icon-${rubric.id}-${item.id}`"
                                        :content="itemStates[item.id]"
                                        placement="top">
                                </b-popover>
                                <icon name="times"
                                    :scale="1"
                                    :id="`rubric-error-icon-${rubric.id}-${item.id}`"
                                    class="text-danger"/>
                            </div>
                        </div>

                        <p class="rubric-item-description">
                            {{ item.description }}
                        </p>
                    </b-card>
                </b-card-group>
            </b-card>
        </b-tab>
    </b-tabs>
</div>
</template>

<script>
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/angle-left';
import 'vue-awesome/icons/angle-right';
import 'vue-awesome/icons/times';
import 'vue-awesome/icons/check';

import { waitAtLeast } from '../utils';

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
            selected: {},
            selectedPoints: 0,
            selectedRows: {},
            current: 0,
            maxPoints: 0,
            itemStates: {},
            origSelected: [],
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

        outOfSync() {
            const origSet = new Set(this.origSelected);
            Object.keys(this.selected).forEach((item) => {
                if (origSet.has(item)) {
                    origSet.delete(item);
                } else {
                    origSet.add(item);
                }
            });
            return origSet;
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
        getHeadHtml(rubric) {
            const selected = this.selectedRows[rubric.id];
            const maxPoints = this.$htmlEscape(Math.max(...rubric.items.map(i => i.points)));
            const header = this.$htmlEscape(`${rubric.header}`) || '<span class="unnamed">Unnamed category</span>';

            const getFraction = (upper, lower) => `<sup>${upper}</sup>&frasl;<sub>${lower}</sub>`;
            let res;

            if (selected) {
                const selectedPoints = this.$htmlEscape(selected.points);
                res = `<span>${header}</span> - <span>${getFraction(selectedPoints, maxPoints)}</span>`;
            } else if (this.editable) {
                res = header;
            } else {
                res = `<span>${header}</span> - <span>${getFraction('Nothing', maxPoints)}<span>`;
            }

            return `<div class="tab-header">${res}</div>`;
        },

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
            } else {
                clear();
                return Promise.resolve({ data: {} });
            }
        },

        submitAllItems() {
            if (Object.keys(this.outOfSync).length === 0) {
                return Promise.resolve();
            }
            const items = Object.keys(this.selected);

            return this.$http.patch(`/api/v1/submissions/${this.submission.id}/rubricitems/`, {
                items,
            }).then(() => {
                this.origSelected = items;
            });
        },

        rubricUpdated({ rubrics, selected, points }, initial = false) {
            this.rubrics = this.sortRubricItems(rubrics);
            this.origSelected = [];

            if (selected) {
                this.selected = selected.reduce((res, item) => {
                    res[item.id] = item;
                    return res;
                }, {});
                this.origSelected = Object.keys(this.selected);
                this.selectedPoints = selected.reduce(
                    (res, item) => res + item.points,
                    0,
                );
                this.selectedRows = rubrics.reduce((res, row) => {
                    res[row.id] = row.items.reduce(
                        (cur, item) => cur || this.selected[item.id],
                        false,
                    );
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
        },

        sortRubricItems(rubrics) {
            return rubrics.map((rubric) => {
                rubric.items.sort((x, y) => x.points - y.points);
                return rubric;
            });
        },

        toggleItem(row, item) {
            if (!this.editable) return;
            this.$set(this.itemStates, item.id, '__LOADING__');

            let req;
            const selectItem = !this.selected[item.id];
            const doRequest = UserConfig.features.incremental_rubric_submission;

            if (!doRequest) {
                req = Promise.resolve().then(() => {
                });
            } else if (selectItem) {
                req = this.$http.patch(`/api/v1/submissions/${this.submission.id}/rubricitems/${item.id}`);
            } else {
                req = this.$http.delete(`/api/v1/submissions/${this.submission.id}/rubricitems/${item.id}`);
            }

            if (doRequest) {
                req = waitAtLeast(500, req);
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
                    this.$set(this.selected, item.id, item);
                } else {
                    this.$set(this.selected, item.id, undefined);
                    delete this.selected[item.id];
                }
                this.$set(this.selectedRows, row.id, selectItem ? item : false);

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

.rubric-viewer .rubric-category {
    border-top-width: 0;

    &,
    .card-header {
        border-top-left-radius: 0;
        border-top-right-radius: 0;
    }
}

.rubric-items {
    padding: 0;
}

.rubric-item {
    border-width: 0;

    &:not(:last-child) {
        border-right-width: 1px;
    }

    &.selected {
        background-color: @active-color;

        #app.dark & {
            background-color: @color-primary-darkest;
        }
    }

    .editable & {
        cursor: pointer;

        &:hover {
            background-color: @active-color;

            #app.dark & {
                background-color: @color-primary-darkest;
            }
        }
    }

    &-body {
        padding: .5rem 0 0 .75rem;
    }

    &-description {
        display: block;
        max-height: 5rem;
        margin: .5rem 0 0;
        padding-right: .5rem;
        overflow: auto;
        font-size: smaller;

        &::after {
            content: "";
            display: block;
            height: .5rem;
        }
    }

    .rubric-item-body {
        padding-top: 0;
    }

    .card-header {
        background: inherit !important;
        border-bottom: 0;
        padding-bottom: 0;

        .header {
            display: flex;
            background: initial;

            .header-title {
                white-space: nowrap;
                text-overflow: ellipsis;
                overflow: hidden;
                flex: 1 1 auto;
            }
            .rubric-item-icon {
                margin-left: 2px;
            }
        }
    }
}
</style>

<style lang="less">
@import "~mixins.less";

.rubric-viewer .nav-tabs li.nav-item > .nav-link {

    &.active {
        background-color: #f7f7f7;
        border-bottom-color: #f7f7f7;
        font-weight: bold;

        #app.dark & {
            background-color: @color-primary-darker;
        }
    }

    .unnamed {
        color: @color-light-gray;
    }
}
</style>
