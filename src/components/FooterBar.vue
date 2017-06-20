<template>
    <footer class="footer">
        <small>&copy; {{ new Date().getFullYear() }} - CodeGra.de</small>
    </footer>
</template>

<script>
export default {
    name: 'footer-bar',
};
</script>

<style>
.footer {
    text-align: center;
    width: 100%;
    /* Set the fixed height of the footer here */
    height: 60px;
    line-height: 60px; /* Vertically center the text there */
    background-color: #f5f5f5;
}
</style>
