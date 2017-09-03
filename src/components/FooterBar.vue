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
footer {
    @footer-height: 60px;
    height: @footer-height;
    /* Vertically center the text there */
    line-height: @footer-height;
    text-align: center;
}

a.codegra-email, a.privacy-statement {
    cursor: pointer;
    text-decoration: underline;
    color: #2c3e50;
    &:hover {
        color: #315171;
    }
}

</style>

<style lang="less">
#privacyModal .modal-dialog.modal-md {
    max-width: 786px;
    width: 100%;
}
</style>
