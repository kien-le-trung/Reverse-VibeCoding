<template><ul><li v-for="todo in todos" :key="todo.id">{{ todo.title }} - {{ todo.completed ? "Done" : "Open" }}</li></ul></template>
<script setup lang="ts">
defineProps<{ todos: { id: number; title: string; completed: boolean }[] }>();
</script>
