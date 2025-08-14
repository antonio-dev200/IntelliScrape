import { createRouter, createWebHistory } from 'vue-router';
import ThemeManagement from '../views/ThemeManagement.vue';
import StandardizationWorkbench from '../views/StandardizationWorkbench.vue';
import CrawlTaskManagement from '../views/CrawlTaskManagement.vue';

const routes = [
  {
    path: '/',
    name: 'ThemeManagement',
    component: ThemeManagement,
  },
  {
    path: '/workbench/:themeName',
    name: 'StandardizationWorkbench',
    component: StandardizationWorkbench,
    props: true, // This allows the :themeName param to be passed as a prop
  },
  {
    path: '/tasks',
    name: 'CrawlTaskManagement',
    component: CrawlTaskManagement,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
