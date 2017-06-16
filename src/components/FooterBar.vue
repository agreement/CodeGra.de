<template>
    <footer class="footer">
        <div class="container">
            <span class="text-muted">&copy; {{ new Date().getFullYear() }} - CodeGra.de</span>
        </div>
    </footer>
</template>

<script>
export default {
    name: 'footer-bar',
};
</script>

<style>
html {
  position: relative;
  min-height: 100%;
}
body {
  /* Margin bottom by footer height */
  margin-bottom: 60px;
}
.footer {
  position: absolute;
  bottom: 0;
  width: 100%;
  /* Set the fixed height of the footer here */
  height: 60px;
  line-height: 60px; /* Vertically center the text there */
  background-color: #f5f5f5;
}
</style>
