<template>
    <footer class="footer">
        <small>
            &copy; {{ new Date().getFullYear() }} - CodeGra.de ({{ version }}) - Made with ❤️ &amp 🍺 -
            <a class="codegra-email" :href="`mailto:${email}`">{{ email }}</a> -
            <a class="privacy-statement" @click="showModal = !showModal">Privacy statement</a>
        </small>
        <b-modal id="privacyModal"
                 v-model="showModal"
                 :hide-footer="true">
            <privacy-note/>
        </b-modal>
    </footer>
</template>

<script>
import PrivacyNote from './PrivacyNote';

export default {
    name: 'footer-bar',

    data() {
        return {
            showModal: false,
            email: UserConfig.email,
            version: UserConfig.version,
        };
    },


    components: {
        PrivacyNote,
    },
};
</script>

<style lang="less" scoped>
@import '~mixins.less';

.footer {
    padding: 20px;
    /* Vertically center the text there */
    line-height: 100%;
    text-align: center;

    a {
        .default-link-colors;
        cursor: pointer;

        &, &:hover {
            text-decoration: underline;
        }
    }
}

</style>

<style lang="less">
#privacyModal .modal-dialog.modal-md {
    max-width: 786px;
}
</style>
