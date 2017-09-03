<template>
    <footer class="footer">
        <small>&copy; {{ new Date().getFullYear() }} - CodeGra.de - Made with ❤️ & 🍺</small>
    </footer>
</template>

<script>
export default {
    name: 'footer-bar',
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
</style>
