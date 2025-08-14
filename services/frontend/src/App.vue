<template>
  <div id="app">
    <header>
      <h1>IntelliScrape</h1>
      <nav>
        <!-- Basic navigation would go here -->
        <a href="#">Dashboard</a> |
        <a href="#">Theme Management</a>
      </nav>
    </header>
    <main>
      <!-- Vue Router's <router-view> would render the current page component here -->
      <h2>Welcome to IntelliScrape</h2>
      <p>This is the main application shell. The actual pages and components would be developed from here.</p>
    </main>
  </div>
</template>

<script>
export default {
  name: 'App',
};
</script>

<style>
/* Basic styling for the app shell */
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
header {
  margin-bottom: 2rem;
}
</style>
