<template>
  <div class="app-shell">
    <aside class="app-side">
      <h1 class="app-title">非遗手工艺传承工作台</h1>
      <nav class="nav-list">
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item">
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>
    <main class="app-main">
      <header class="app-head">
        <span class="head-desc">手工艺传承人、学徒和技艺保护专员共同管理技艺图谱、传承档案与作品认证，确保每一项非遗技艺有完整的师徒传承与作品记录。</span>
        <span class="head-user">当前值班：应用开发组</span>
      </header>
      <RouterView v-slot="{ Component, route }">
        <component :is="Component" :key="route.path" />
      </RouterView>
    </main>
  </div>
</template>

<script setup lang="ts">
const navItems = [{ label: "运营概览", path: "/" }, { label: "技艺分类", path: "/craft_category" }, { label: "传承人档案", path: "/artisan" }, { label: "学徒培养", path: "/apprentice" }, { label: "技艺图谱", path: "/skill_card" }, { label: "原材料管理", path: "/raw_material" }, { label: "工具器械", path: "/tooling" }, { label: "传习所管理", path: "/workshop" }, { label: "培训方案", path: "/training_plan" }, { label: "作品创作", path: "/creation_work" }, { label: "作品认证", path: "/authentication" }, { label: "展览策划", path: "/exhibition" }, { label: "资助经费", path: "/grant_fund" }, { label: "田野调查", path: "/field_survey" }, { label: "数字化采集", path: "/digitization" }, { label: "出版成果", path: "/publication" }, { label: "知识产权", path: "/ip_right" }, { label: "传承评估", path: "/evaluation" }, { label: "濒危抢救", path: "/emer_rescue" }]
</script>
