<template>
  <main><h1>Reverse Vibe Coding</h1><nav><button @click="screen = 'home'">Home</button><button @click="screen = 'todos'">Todos</button></nav><p v-if="screen === 'home'">Choose a project screen.</p><p v-else>Todo screen placeholder.</p></main>
</template>
<script setup lang="ts">
import { ref } from "vue";
const screen = ref<"home" | "todos">("home");
</script>
