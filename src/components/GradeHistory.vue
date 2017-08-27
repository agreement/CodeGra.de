<template>
    <div>
        <b-collapse id="grade-history-collapse" style="max-height: 16em; overflow-y: auto;">
            <table class="table b-table table-striped">
                <thead>
                    <tr>
                        <th>Grader</th>
                        <th>Grade</th>
                        <th>Date</th>
                        <th>By rubric</th>
                        <th v-if="isLTI">In LTI</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="item in history">
                        <td>{{ item.user.name }}</td>
                        <td>{{ item.grade >= 0 ? Math.round(item.grade * 100) / 100 : 'Deleted' }}</td>
                        <td>{{ item.changed_at }}</td>
                        <td>
                            <icon name="check" v-if="item.is_rubric"></icon>
                            <icon name="times" v-else></icon>
                        </td>
                        <td v-if="isLTI">
                            <icon name="check" v-if="item.passed_back"></icon>
                            <icon name="times" v-else></icon>
                        </td>
                    </tr>
                </tbody>
            </table>
        </b-collapse>
        <submit-button @click="toggleHistory"
                       :label="content"
                       class="grade-history-submit"
                       ref="toggleButton"
                       default="secondary"
                       success="secondary"/>
    </div>
</template>

<script>
import moment from 'moment';
import Icon from 'vue-awesome/components/Icon';
import 'vue-awesome/icons/bars';
import SubmitButton from './SubmitButton';

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
        return {
            show: false,
            content: '',
            history: null,
        };
    },

    mounted() {
        this.content = this.showText;
    },

    methods: {
        toggleHistory() {
            if (this.history === null) {
                this.updateHistory().then(() => {
                    this.$nextTick(this.toggleHistory);
                });
            } else {
                this.$root.$emit('collapse::toggle', 'grade-history-collapse');
                this.content = this.show ? this.showText : this.hideText;
                this.show = !this.show;
            }
        },
        updateHistory() {
            const req = this.$http.get(`/api/v1/submissions/${this.submissionId}/grade_history/`);
            this.$refs.toggleButton.submit(req.catch((err) => {
                throw err.response.data.message;
            }));
            return req.then(({ data }) => {
                for (let i = 0, len = data.length; i < len; i += 1) {
                    data[i].changed_at = moment
                        .utc(data[i].changed_at, moment.ISO_8601)
                        .local()
                        .format('YYYY-MM-DD HH:mm');
                }
                this.history = data;
            });
        },
    },

    components: {
        Icon,
        SubmitButton,
    },
};
</script>

<style lang="less">
.grade-history-submit span {
    display: block;
    width: 100%;
    button {
        width: 100%;
    }
}
</style>

<style lang="less" scoped>
#grade-history-collapse {
}
</style>
