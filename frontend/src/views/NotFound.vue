<template>
  <div class="not-found">
    <h1>404</h1>
    <p>{{ $t('notFound.message') }}</p>
    <router-link to="/" class="home-link">{{ $t('notFound.goHome') }}</router-link>
  </div>
</template>

<style scoped>
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  font-family: var(--font-mono, 'Courier New', monospace);
  color: #e0e0e0;
}

.not-found h1 {
  font-size: 6rem;
  margin: 0;
  background: linear-gradient(135deg, #00e5ff, #7b2ff7);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.not-found p {
  font-size: 1.2rem;
  margin: 1rem 0 2rem;
  color: #999;
}

.home-link {
  padding: 0.75rem 2rem;
  border: 1px solid rgba(0, 229, 255, 0.3);
  border-radius: 8px;
  color: #00e5ff;
  text-decoration: none;
  transition: all 0.3s ease;
}

.home-link:hover {
  background: rgba(0, 229, 255, 0.1);
  border-color: #00e5ff;
}
</style>
