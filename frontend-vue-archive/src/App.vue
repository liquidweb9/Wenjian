<script setup>
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="app-shell">
    <nav class="top-nav">
      <router-link to="/" class="nav-brand">简历深度面试</router-link>
      <div class="nav-links">
        <router-link to="/upload">上传简历</router-link>
      </div>
    </nav>
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.top-nav {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 0.75rem 1.5rem;
  background: #1a1a2e;
  color: #fff;
}
.nav-brand {
  font-size: 1.1rem;
  font-weight: 700;
  color: #fff;
  text-decoration: none;
}
.nav-links a {
  color: rgba(255,255,255,0.8);
  text-decoration: none;
  font-size: 0.9rem;
}
.nav-links a:hover { color: #fff; }
.main-content {
  flex: 1;
  padding: 1.5rem;
  max-width: 960px;
  width: 100%;
  margin: 0 auto;
}
</style>
