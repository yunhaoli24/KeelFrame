<template>
  <div class="page-container">
    <h1>{{ pageTitle }}</h1>
    <div class="todo-notice">
      <p>🚧 此页面正在开发中</p>
      <p>页面路径：{{ route.path }}</p>
      <p>功能：{{ pageDescription }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();

// 根据路由路径设置页面标题和描述
const pageTitle = computed(() => {
  const path = route.path;
  // 可以从路径中提取有意义的标题
  const parts = path.split("/").filter((p) => p);
  return parts.length > 0 ? `${parts[parts.length - 1]} 管理` : "页面";
});

const pageDescription = computed(() => {
  const path = route.path;
  // 简化的描述映射
  if (path.includes("dashboard")) return "仪表板相关功能";
  if (path.includes("system")) return "系统管理功能";
  if (path.includes("log")) return "日志查看功能";
  if (path.includes("monitor")) return "系统监控功能";
  if (path.includes("scheduler")) return "任务调度功能";

  if (path.includes("_core")) return "核心功能";
  return "功能待实现";
});
</script>

<style scoped>
.page-container {
  padding: 20px;
}

.todo-notice {
  margin-top: 20px;
  padding: 20px;
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  color: #6c757d;
}
</style>
