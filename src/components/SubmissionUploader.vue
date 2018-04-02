<template>
<div class="submission-uploader">
    <b-modal id="wrong-files-modal"
             hide-footer
             title="Probably superfluous files found!">
        <p>
            The following files should not be in your archive according to
            the <code style="margin: 0 0.25rem;">.cgignore</code> file. This
            means the following files are probably not necessary to hand
            in:
        </p>
        <ul style="list-style-type: none">
            <li style="margin-right: 2px; padding: 0.5em;" v-for="file in wrongFiles">
                <code style="margin-right: 0.25rem">{{ file[0] }}</code> is ignored by <code>{{ file[1] }}</code>
            </li>
        </ul>
        <p>
            This could be a mistake so please make sure no necessary code is
            present in these files before you delete them!
        </p>
        <b-button-toolbar justify>
            <submit-button ref="submitDelete"
                           label="Delete files" default="danger"
                           @click="overrideSubmit('delete', $refs.submitDelete)"/>
            <submit-button ref="submitKeep"
                           label="Keep files" default="warning"
                           @click="overrideSubmit('keep', $refs.submitKeep)"/>
            <submit-button label="Cancel submission"
                           @click="$root.$emit('bv::hide::modal', 'wrong-files-modal');"/>
        </b-button-toolbar>
    </b-modal>

    <b-popover :show.sync="showWarn"
               :target="uploaderId"
               placement="top"
               :disabled="!showWarn"
               @hidden="$emit('warn-popover-hidden')">
        <p>You are now submitting with yourself as author, are you sure you want to continue?</p>
        <b-button-toolbar justify>
            <b-btn variant="danger" @click="rejectWarn">Stop</b-btn>
            <b-btn variant="success" @click="acceptWarn">Ok</b-btn>
        </b-button-toolbar>
    </b-popover>
    <file-uploader ref="uploader"
                   :button-id="uploaderId"
                   :url="getUploadUrl()"
                   :show-empty="true"
                   :disabled="disabled"
                   :before-upload="checkUpload"
                   @error="uploadError"
                   @clear="author = null"
                   @response="data => $emit('created', data)">
        <user-selector v-model="author"
                       select-label=""
                       :disabled="disabled"
                       v-if="forOthers"
                       :placeholder="`${defaultAuthor.name} (${defaultAuthor.username})`"/>
    </file-uploader>
</div>
</template>

<script>
import { mapGetters } from 'vuex';

import Loader from './Loader';
import FileUploader from './FileUploader';
import SubmitButton from './SubmitButton';
import UserSelector from './UserSelector';

let i = 0;

export default {
    name: 'submission-uploader',

    props: {
        assignment: {
            required: true,
            type: Object,
        },

        disabled: {
            default: false,
            type: Boolean,
        },

        forOthers: {
            type: Boolean,
            required: true,
        },
    },

    watch: {
        showWarn(newVal, oldVal) {
            if (oldVal && !newVal && this.rejectWarn) {
                this.rejectWarn(true);
            }
        },
    },

    computed: {
        ...mapGetters('user', { myUsername: 'username', myName: 'name' }),

        defaultAuthor() {
            return { name: this.myName, username: this.myUsername };
        },

        warnForSelf() {
            return this.forOthers;
        },
    },

    data() {
        return {
            wrongFiles: [],
            author: null,
            showWarn: false,
            rejectWarn: null,
            acceptWarn: null,
            uploaderId: `submission-uploader-${i++}`,
        };
    },

    destroyed() {
        // Make sure we don't leak the promise and event handler
        // set in the checkUpload method.
        this.$emit('warn-popover-hidden');
    },

    methods: {
        uploadError(err) {
            if (err.data.code !== 'INVALID_FILE_IN_ARCHIVE') return;

            this.wrongFiles = err.data.invalid_files;
            this.$root.$emit('bv::show::modal', 'wrong-files-modal');

            // We need the double next ticks as next ticks are executed before
            // data updates of the next tick.
            this.$nextTick(() => {
                this.$nextTick(() => {
                    this.$refs.uploader.$refs.submitButton.reset();
                });
            });
        },

        checkUpload() {
            if (this.warnForSelf && (this.author == null ||
                                     this.defaultAuthor.username === this.author.username)) {
                this.showWarn = true;
                return new Promise((resolve) => {
                    const resetData = () => {
                        this.showWarn = false;
                        this.acceptWarn = null;
                        this.rejectWarn = null;
                        // eslint-disable-next-line
                        this.$off('warn-popover-hidden', continueUpload);
                    };

                    const continueUpload = () => {
                        resetData();
                        resolve(false);
                    };
                    const stopUpload = () => {
                        resetData();
                        resolve(true);
                    };

                    this.acceptWarn = continueUpload;
                    this.rejectWarn = stopUpload;
                    this.$on('warn-popover-hidden', stopUpload);
                });
            }

            return Promise.resolve();
        },

        getUploadUrl(ignored = 'error') {
            let res = `/api/v1/assignments/${this.assignment.id}/submission?ignored_files=${ignored}`;
            if (this.forOthers && this.author) {
                res += `&author=${this.author.username}`;
            }
            return res;
        },

        overrideSubmit(type, btn) {
            const { requestData } = this.$refs.uploader;
            const url = this.getUploadUrl(type);

            btn.submit(this.$http.post(url, requestData).then((res) => {
                this.$emit('created', res);
            }, ({ response }) => {
                this.$emit('error', response);
                throw response.data.message;
            }));
        },
    },

    components: {
        FileUploader,
        SubmitButton,
        UserSelector,
        Loader,
    },
};
</script>

<style lang="less" scoped>
.form-group {
    margin-bottom: 0;
}
</style>

<style lang="less">
.submission-uploader .multiselect {
    min-height: 0px;
    margin: 0 1px;
    .multiselect__tags {
        border-radius: 0;
        min-height: 0px;
    }
}
</style>
