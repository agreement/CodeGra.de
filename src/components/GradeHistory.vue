<template>
<loader v-if="loading"/>
<div class="grade-history" v-else>
    <b-table striped :items="history" :fields="fields">
        <span slot="user" slot-scope="data">{{ data.item.user.name }}</span>
        <span slot="grade" slot-scope="data">
            {{ data.item.grade >= 0 ? Math.round(data.item.grade * 100) / 100 : 'Deleted' }}
        </span>
        <span slot="rubric" slot-scope="data">
            <icon name="check" v-if="data.item.is_rubric"></icon>
            <icon name="times" v-else></icon>
        </span>
        <span v-if="isLTI" slot="lti" slot-scope="data">
            <icon name="check" v-if="data.item.passed_back"></icon>
            <icon name="times" v-else></icon>
        </span>
    </b-table>
</b-collapse>
</div>
</template>

<script>
import moment from 'moment';
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/bars';
import Loader from './Loader';

export default {
    name: 'grade-history',

    props: {
        showText: {
            type: String,
            default: 'Show grade history',
        },
        hideText: {
            type: String,
            default: 'Hide grade history',
        },
        submissionId: {
            type: Number,
            default: 0,
        },
        isLTI: {
            type: Boolean,
            default: false,
        },
    },

    data() {
        const fields = [
            {
                key: 'user',
                label: 'Grader',
            }, {
                key: 'grade',
                label: 'Grade',
            }, {
                key: 'changed_at',
                label: 'Date',
            }, {
                key: 'rubric',
                label: 'By rubric',
            },
        ];
        if (this.isLTI) {
            fields.push({ key: 'lti', label: 'In LTI' });
        }
        return {
            history: [],
            fields,
            loading: false,
        };
    },

    methods: {
        updateHistory() {
            this.loading = true;
            const req = this.$http.get(`/api/v1/submissions/${this.submissionId}/grade_history/`);
            return req.then(({ data }) => {
                for (let i = 0, len = data.length; i < len; i += 1) {
                    data[i].changed_at = moment
                        .utc(data[i].changed_at, moment.ISO_8601)
                        .local()
                        .format('YYYY-MM-DD HH:mm');
                }
                this.history = data;
                this.loading = false;
            });
        },
    },

    components: {
        Icon,
        Loader,
    },
};
</script>

<style lang="less">
.grade-history-submit .grade-history-submit span,
.grade-history .btn-group {
    display: block;
    width: 100%;
    button {
        width: 100%;
    }
}

.btn-group {

}
</style>

<style lang="less" scoped>
#grade-history-collapse {
    transition-property: all;
    transition-duration: .5s;
    transition-timing-function: cubic-bezier(0, 1, 0.5, 1);
    max-height: 0;
    overflow-x: hidden;
}

#grade-history-collapse.show {
    max-height: 16em;
    margin-bottom: 15px;
    &.collapse-leave-active {
        margin-bottom: 0;
    }
}

.table {
    th, td {
        padding: .25rem !important;
    }
    cursor: text !important;
}
.grade-history {
    width: 30em;
    margin: -.5rem -.75rem;
    max-height: 40em;
    overflow-y: auto;
    padding: .5rem .75rem;
}
</style>
