<template>
  <div id="app">
    <header>
      <h1>IntelliScrape</h1>
      <nav>
        <router-link to="/">主题管理</router-link> |
        <router-link to="/tasks">抓取任务管理</router-link>
        <!-- Note: Workbench is typically navigated to from the Theme Management page -->
      </nav>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup>
// No script logic needed in the main App shell for now
</script>

<style>
/* Basic styling for the app shell */
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}
header {
  background-color: #f8f9fa;
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
  margin-bottom: 2rem;
  text-align: center;
}
header h1 {
  margin: 0;
}
nav {
  margin-top: 0.5rem;
}
nav a {
  font-weight: bold;
  color: #2c3e50;
  text-decoration: none;
  margin: 0 1rem;
}
nav a.router-link-exact-active {
  color: #007bff;
}
main {
  padding: 0 1rem;
}
</style>
